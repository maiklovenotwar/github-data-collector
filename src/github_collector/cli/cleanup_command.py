"""
CLI-Modul zur Bereinigung verwaister Owner-Einträge (Contributors und Organisationen).

Dieses Modul implementiert die Kommandozeilenschnittstelle für die Bereinigung
verwaister Owner-Einträge (Contributors und Organisationen ohne zugehörige Repositories).
"""
import os
import sys
import logging
import argparse
from typing import Tuple

from github_collector import config
from github_collector.database.database import GitHubDatabase
from github_collector.database.models import Contributor, Organization, Repository
from github_collector.utils.logging_config import setup_logging

# Konfiguriere Logging
logger = setup_logging(log_file=config.LOG_DIR / "cleanup_orphaned_owners.log")


def parse_arguments() -> argparse.Namespace:
    """
    Parse Kommandozeilenargumente.
    
    Returns:
        Geparste Argumente
    """
    parser = argparse.ArgumentParser(description="Bereinige verwaiste Owner-Einträge (Contributors und Organisationen)")
    
    # Datenbankoptionen
    parser.add_argument("--db-path", help="Pfad zur SQLite-Datenbankdatei")
    
    # Bereinigungsoptionen
    parser.add_argument("--dry-run", action="store_true",
                      help="Simulationsmodus: Zeigt an, welche Einträge entfernt würden, ohne Änderungen vorzunehmen")
    
    return parser.parse_args()


def cleanup_orphaned_owners(db: GitHubDatabase, dry_run: bool = False) -> Tuple[int, int]:
    """
    Entfernt Owner (Contributors/Organisationen) ohne zugehörige Repositories.
    
    Args:
        db: Datenbankverbindung
        dry_run: Wenn True, werden keine Änderungen vorgenommen, sondern nur angezeigt,
                 welche Einträge entfernt würden
    
    Returns:
        Tuple mit der Anzahl der entfernten Contributors und Organisationen
    """
    session = db.session
    
    # Finde Contributors ohne zugehörige Repositories
    orphaned_contributors = session.query(Contributor).filter(
        ~Contributor.id.in_(
            session.query(Repository.owner_id).filter(Repository.owner_type == "contributor")
        )
    ).all()
    
    logger.info(f"{len(orphaned_contributors)} verwaiste Contributors gefunden")
    
    # Finde Organisationen ohne zugehörige Repositories
    orphaned_organizations = session.query(Organization).filter(
        ~Organization.id.in_(
            session.query(Repository.owner_id).filter(Repository.owner_type == "organization")
        )
    ).all()
    
    logger.info(f"{len(orphaned_organizations)} verwaiste Organisationen gefunden")
    
    # Entferne verwaiste Contributors
    removed_contributors = 0
    for contributor in orphaned_contributors:
        logger.debug(f"Verwaister Contributor: {contributor.login} (ID: {contributor.id})")
        if not dry_run:
            session.delete(contributor)
            removed_contributors += 1
    
    # Entferne verwaiste Organisationen
    removed_organizations = 0
    for organization in orphaned_organizations:
        logger.debug(f"Verwaiste Organisation: {organization.login} (ID: {organization.id})")
        if not dry_run:
            session.delete(organization)
            removed_organizations += 1
    
    # Commit Änderungen, falls nicht im Simulationsmodus
    if not dry_run and (removed_contributors > 0 or removed_organizations > 0):
        session.commit()
        logger.info(f"{removed_contributors} Contributors und {removed_organizations} Organisationen entfernt")
    else:
        logger.info(f"Simulationsmodus: {len(orphaned_contributors)} Contributors und {len(orphaned_organizations)} Organisationen würden entfernt werden")
    
    return removed_contributors, removed_organizations


def main() -> int:
    """
    Hauptfunktion zur Bereinigung verwaister Owner-Einträge.
    
    Returns:
        Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    args = parse_arguments()
    
    # Lade Umgebungsvariablen aus .env-Datei, falls verfügbar
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    try:
        # Datenbankpfad
        db_path = args.db_path or config.DEFAULT_DB_PATH
        
        # Initialisiere Datenbank
        db = GitHubDatabase(db_path)
        
        # Bereinige verwaiste Owner-Einträge
        removed_contributors, removed_organizations = cleanup_orphaned_owners(db, dry_run=args.dry_run)
        
        # Schließe Datenbankverbindung
        db.close()
        
        # Ausgabe der Ergebnisse
        if args.dry_run:
            logger.info(f"Simulationsmodus: {removed_contributors} Contributors und {removed_organizations} Organisationen würden entfernt werden")
        else:
            logger.info(f"Bereinigung abgeschlossen: {removed_contributors} Contributors und {removed_organizations} Organisationen entfernt")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Fehler bei der Bereinigung verwaister Owner-Einträge: {e}")
        return 1
