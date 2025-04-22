# Geocoding von Standorten

Dieses Dokument beschreibt die Verwendung des Geocoding-Skripts zur Anreicherung von Contributor- und Organisationsdaten mit Länder- und Regionsinformationen.

## Zweck des Skripts
Das Skript `update_location_geocoding.py` reichert die Standortangaben (z.B. "Berlin, Germany") von Contributors und Organisationen mithilfe eines Geocoding-Services automatisch mit Länder- und Regionsinformationen an. Die Ergebnisse werden in der Datenbank gespeichert und können für Analysen genutzt werden.

## Voraussetzungen
- Python 3.11 oder 3.12 (NICHT 3.13, siehe Kompatibilitätshinweise)
- Installation aller Pakete aus `requirements.txt`
- SQLite-Datenbank mit gesammelten Contributor- und Organisationsdaten

## Kommandozeilenargumente
- `--db-path`: Pfad zur SQLite-Datenbank
- `--contributors`: Nur Contributors geokodieren
- `--organizations`: Nur Organisationen geokodieren
- `--limit`: Maximale Anzahl zu verarbeitender Einträge
- `--force`: Auch bereits angereicherte Einträge erneut geokodieren
- `--clear-cache`: Geocoding-Cache zurücksetzen

## Beispielaufruf
```bash
python scripts/update_location_geocoding.py --db-path data/github_data.db --contributors --limit 100
```

## Hinweise
- Das Skript nutzt einen lokalen Cache (`geocoding_cache.json`), um wiederholte Geocoding-Anfragen zu vermeiden.
- Der User-Agent für Geocoding-Anfragen kann in der Konfiguration angepasst werden.
- Die Ergebnisse werden in den Feldern `country_code`, `country`, `region`, `latitude`, `longitude` der jeweiligen Datenbanktabellen gespeichert.
- Logging erfolgt standardmäßig in die Datei `logs/geocoding.log`.

## Code-Dokumentation
Die wichtigsten Funktionen und Klassen sind im Code mit Docstrings dokumentiert:
- `main`: Einstiegspunkt, verarbeitet Argumente und steuert den Ablauf.
- `update_contributors`: Aktualisiert Contributor-Standorte.
- `update_organizations`: Aktualisiert Organisations-Standorte.
- `GeocodingService`: Kapselt die Geocoding-Logik und den Cache.

Für Details siehe den Quellcode in `src/github_collector/cli/geocoding_command.py` und `src/github_collector/geocoding/geocoding_service.py`.

## Troubleshooting
- Prüfe das Logfile `logs/geocoding.log` für Fehlermeldungen.
- Bei Problemen mit dem Geocoding-Cache kann dieser mit `--clear-cache` zurückgesetzt werden.
- Für große Datenmengen empfiehlt sich die Nutzung der `--limit`-Option, um API-Limits zu berücksichtigen.
