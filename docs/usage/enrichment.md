# Enrichment von Repository-Statistiken

Dieses Dokument beschreibt die Verwendung des Enrichment-Skripts zur nachträglichen Anreicherung von Repository-Daten mit Commit- und Pull-Request-Zahlen.

## Zweck des Skripts
Das Skript `enrich_repository_stats.py` ergänzt bestehende Repository-Datensätze in der Datenbank um zusätzliche Zählwerte (commits_count, pull_requests_count) mittels der GitHub GraphQL API. Das ermöglicht eine detailliertere Analyse der Repositories.

## Wichtige Einschränkungen & Hinweise
- **contributors_count** wird aktuell nicht gesammelt, da dies mit der GitHub API performant nicht möglich ist.
- **commits_count** bezieht sich ausschließlich auf den Default Branch eines Repositories.
- Das Skript ist für große Datenmengen ausgelegt und unterstützt Checkpointing sowie Retry-Logik.
- Fehlerhafte oder unvollständige Repositories werden in einer separaten Datei (`failed_repo_ids_...txt`) dokumentiert.

## Voraussetzungen
- Python 3.11 oder 3.12 (NICHT 3.13, siehe Kompatibilitätshinweise)
- Installation aller Pakete aus `requirements.txt` (inkl. `gql[requests]` für GraphQL)
- GitHub Personal Access Token (PAT) als Umgebungsvariable `GITHUB_API_TOKEN` setzen
- SQLite- oder MySQL-Datenbank mit vorhandenen Repository-Daten
- Die Datenbank wird über die Umgebungsvariable `DATABASE_URL` (z.B. `sqlite:///data/github_data.db` oder `mysql+pymysql://user:pass@localhost/github_data`) oder per `--db-path` angegeben. Der Wert für `--db-path` wird automatisch zu einer SQLAlchemy-URL umgewandelt, falls nötig.

## Kommandozeilenargumente
- `--db-path`: Pfad zur SQLite-Datenbank
- `--batch-size`: Anzahl der Repositories pro API-Batch (Performance-Optimierung)
- `--limit`: Maximale Anzahl zu verarbeitender Repositories
- `--force`: Auch bereits angereicherte Repositories erneut verarbeiten
- `--dry-run`: Simulationsmodus (keine Änderungen vornehmen)
- `--retry-failed`: Nur fehlgeschlagene Repositories erneut versuchen

## Beispielaufrufe
**Mit SQLite (Standard):**
```bash
python scripts/enrich_repository_stats.py --db-path data/github_data.db --batch-size 50 --limit 200
```
**Mit MySQL (über Umgebungsvariable):**
```bash
export DATABASE_URL="mysql+pymysql://user:pass@localhost/github_data"
python scripts/enrich_repository_stats.py --batch-size 50 --limit 200
```
**Dry-Run:**
```bash
python scripts/enrich_repository_stats.py --db-path data/github_data.db --dry-run
```
**Retry fehlgeschlagener Repos:**
```bash
python scripts/enrich_repository_stats.py --db-path data/github_data.db --retry-failed
```

## Besonderheiten der Implementierung
- **Rate Limit Handling:** Das Skript erkennt automatisch GitHub API Rate Limits und pausiert, bis weitere Anfragen möglich sind.
- **Retry-Logik:** Fehlerhafte Repositories werden gesammelt und können gezielt erneut verarbeitet werden.
- **Checkpointing:** Der Fortschritt wird gespeichert, sodass abgebrochene Läufe fortgesetzt werden können.
- **Output-Datei:** IDs von nicht verarbeitbaren Repositories werden in einer Datei (`failed_repo_ids_...txt`) gespeichert.
- **Logging:** Alle Aktivitäten und Fehler werden in `logs/enrich_repository_stats.log` protokolliert.

## Code-Dokumentation
Die wichtigsten Funktionen und Klassen sind im Quellcode mit Docstrings dokumentiert:
- Hauptfunktionen im Orchestrierungsskript (`main`, `get_repos_to_enrich`, etc.)
- `GraphQLHandler` für die Kommunikation mit der GitHub GraphQL API
- `map_and_update_stats` für das Update der Datenbank
- Komplexe Logikabschnitte (z.B. Rate-Limit-Wartefunktion, Retry-Logik, Checkpoint-Handling) sind kommentiert

Für Details siehe den Quellcode in `scripts/enrich_repository_stats.py`, `src/github_collector/enrichment/graphql_handler.py` und `src/github_collector/enrichment/updater.py`.

## Troubleshooting
- Prüfe das Logfile `logs/enrich_repository_stats.log` für Fehler und Hinweise.
- Bei API-Problemen ggf. Batch-Größe reduzieren oder mehrere Tokens verwenden.
- Fehlerhafte Repositories können gezielt mit `--retry-failed` erneut verarbeitet werden.
