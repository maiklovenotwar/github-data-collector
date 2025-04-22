"""
Updater-Modul für das Aktualisieren der Repository-Statistiken in der SQLite-DB
unterstützt Dry-Run, Logging und Transaktionssicherheit.
"""
import logging
import sqlite3
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def map_and_update_stats(db_path: str, repo_stats: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """
    Aktualisiert die Statistiken für Repositories in der SQLite-DB anhand der vom GraphQLHandler gelieferten Werte.
    :param db_path: Pfad zur SQLite-DB
    :param repo_stats: Liste von Dicts mit repo_id, calculated_pr_count, calculated_commit_count, calculated_contributor_count
    :param dry_run: Wenn True, werden keine Änderungen in die DB geschrieben
    :return: Anzahl der erfolgreich aktualisierten Repositories
    """
    logger.info(f"Starte Repository-Update (dry_run={dry_run}) für {len(repo_stats)} Repositories...")
    updated = 0
    not_found = []

    # Debug: Logge ALLE databaseId-Werte und deren Typen aus repo_stats
    all_dbids = [stat.get('databaseId') if stat.get('databaseId') is not None else stat.get('database_id') for stat in repo_stats]
    logger.debug(f"Alle databaseId/database_id-Werte aus repo_stats: {all_dbids}")
    logger.debug(f"Typen der databaseId/database_id-Werte: {[type(x) for x in all_dbids]}")

    # Debug: Gib die ersten paar Elemente von repo_stats aus, um die Struktur zu sehen
    if repo_stats:
        logger.debug(f"Erstes Element in repo_stats: {repo_stats[0]}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Debug: Zeige alle IDs in der DB (nur beim ersten Durchlauf, für Übersicht)
        cursor.execute("SELECT id FROM repositories LIMIT 10")
        ids_in_db = [row[0] for row in cursor.fetchall()]
        logger.debug(f"Beispiel-IDs in DB (erste 10): {ids_in_db} (Typen: {[type(x) for x in ids_in_db]})")

        if not dry_run:
            conn.execute('BEGIN TRANSACTION;')

        # Mapping: databaseId -> Werte
        update_tuples = []
        for stat in repo_stats:
            # Flexible ID-Erkennung: Unterstützt verschiedene mögliche Schlüsselnamen für die Repo-ID
            id_keys = ["databaseId", "database_id", "repo_id", "id"]
            database_id_value = None
            for key in id_keys:
                if key in stat and stat[key] is not None:
                    database_id_value = stat[key]
                    logger.debug(f"ID-Schlüssel gefunden: '{key}' mit Wert {database_id_value}")
                    break

            # Debug: Zeige den extrahierten Wert und seinen Typ
            logger.debug(f"Prüfe Repo: Extrahierter ID-Wert={database_id_value} (Typ: {type(database_id_value)})")

            # Logge explizit die Typen und Werte, die verglichen werden
            logger.debug(f"Vergleiche extrahierte Repo-ID={database_id_value} (Typ: {type(database_id_value)}) gegen IDs in DB (erste 10): {ids_in_db}")

            pr_count = stat.get("calculated_pr_count", 0)
            commit_count = stat.get("calculated_commit_count", 0)
            contributor_count = stat.get("calculated_contributor_count", 0)

            if database_id_value is None:
                logger.error(f"Konnte keine ID ('databaseId' oder 'database_id') im stat-Objekt finden: {stat}")
                not_found.append(str(stat)) # Logge das ganze Objekt, um zu sehen was fehlt
                continue

            try:
                # **Hypothese 2: Typ-Problem?** Konvertiere sicher zu int
                db_id_int = int(database_id_value)
                logger.debug(f"Konvertierte ID für DB-Check: db_id_int={db_id_int} (Typ: {type(db_id_int)})")
            except (ValueError, TypeError) as e:
                logger.error(f"Kann ID-Wert nicht zu int casten: {database_id_value} (Original-Typ: {type(database_id_value)}). Fehler: {e}")
                not_found.append(str(database_id_value))
                continue

            # Prüfe, ob das Repo existiert
            cursor.execute("SELECT id FROM repositories WHERE id = ?", (db_id_int,))
            result = cursor.fetchone()
            if result:
                logger.debug(f"Repo mit ID {db_id_int} in DB gefunden.")
                logger.debug(f"Update für Repo {db_id_int}: PRs={pr_count}, Commits={commit_count}, Contributors={contributor_count}")
                update_tuples.append((pr_count, commit_count, contributor_count, db_id_int))
                updated += 1
                if dry_run:
                    logger.info(f"[Dry-Run] Repo mit ID {db_id_int} WÜRDE aktualisiert: PRs={pr_count}, Commits={commit_count}, Contributors={contributor_count}")
            else:
                logger.warning(f"Repo mit ID {db_id_int} NICHT in DB gefunden – kein Update möglich.")
                not_found.append(db_id_int)

        if not dry_run and update_tuples:
            logger.info(f"Führe 'executemany' für {len(update_tuples)} Updates aus...")
            cursor.executemany(
                "UPDATE repositories SET pull_requests_count=?, commits_count=?, contributors_count=? WHERE id=?",
                update_tuples
            )
            conn.commit()
            logger.info(f"{len(update_tuples)} Repositories erfolgreich aktualisiert.") # Korrigiert auf tatsächliche Anzahl
        elif not dry_run and not update_tuples:
            logger.info("Keine Updates notwendig oder möglich für diesen Batch.")
            
        if dry_run:
            # Die Zählung 'updated' zählt, wie viele gefunden wurden, nicht wie viele wirklich geändert würden.
            logger.info(f"[Dry-Run] {updated} Repositories WÜRDEN aktualisiert, wenn sie in der DB gefunden werden.")
            
        if not_found:
             logger.warning(f"{len(not_found)} Repositories aus GraphQL-Antwort wurden nicht in der DB gefunden: {not_found[:10]}...") # Zeige die ersten paar

    except sqlite3.Error as e: # Spezifischer auf DB-Fehler eingehen
        logger.error(f"SQLite Fehler beim Update-Prozess: {e}")
        if not dry_run and 'conn' in locals() and conn.in_transaction:
            try:
                conn.rollback()
                logger.info("Transaktion zurückgerollt.")
            except Exception as roll_e:
                logger.error(f"Fehler beim Rollback: {roll_e}")
        return 1 # Fehlercode
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Update-Prozess: {e}", exc_info=True) # exc_info für Traceback
        if not dry_run and 'conn' in locals() and conn.in_transaction:
             try:
                 conn.rollback()
                 logger.info("Transaktion zurückgerollt.")
             except Exception as roll_e:
                 logger.error(f"Fehler beim Rollback: {roll_e}")
        return 1 # Fehlercode
    finally:
        if 'conn' in locals():
            conn.close()
            logger.debug("DB-Verbindung geschlossen.")
            
    logger.info("Update-Prozess abgeschlossen.")
    # Gib die Anzahl der tatsächlich durchgeführten Updates zurück (im Nicht-DryRun) oder der gefundenen Matches (im DryRun)
    return len(update_tuples) if not dry_run else updated
    logger.info("Update-Prozess abgeschlossen.")
    return updated
