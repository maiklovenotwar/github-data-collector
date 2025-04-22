# Datensammlung mit dem GitHub Data Collector

Diese Anleitung beschreibt die Verwendung des GitHub Data Collectors zur Sammlung von GitHub-Repository-Daten.

## Voraussetzungen

- Python 3.11 oder 3.12 (NICHT 3.13, siehe Kompatibilitätshinweise in requirements.txt)
- Installation aller Pakete aus `requirements.txt`
- GitHub Personal Access Token (PAT) als Umgebungsvariable `GITHUB_API_TOKEN` setzen
- SQLite-Datenbank (wird automatisch angelegt, falls nicht vorhanden)

## Grundlegende Verwendung

Der GitHub Data Collector bietet verschiedene Skripte für die Datensammlung, die im `scripts`-Verzeichnis zu finden sind.

### Repository-Sammlung

Das Hauptskript für die Sammlung von Repository-Daten ist `collect_repositories.py`:

```bash
python scripts/collect_repositories.py
```

Ohne Parameter startet das Skript im interaktiven Modus und führt Sie durch den Prozess der Repository-Sammlung.

### Nicht-interaktiver Modus

Für automatisierte Abläufe können Sie den nicht-interaktiven Modus verwenden:

```bash
python scripts/collect_repositories.py --non-interactive --time-range week --limit 1000 --min-stars 100
```

Dieser Befehl sammelt bis zu 1000 Repositories aus der letzten Woche mit mindestens 100 Stars.

### Verfügbare Parameter

Das Skript `collect_repositories.py` unterstützt folgende Parameter:

#### Zeitbereichsoptionen
- `--time-range`: Vordefinierter Zeitbereich (`week`, `month`, `year`, `custom`)
- `--start-date`: Startdatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)
- `--end-date`: Enddatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)

#### Sammlungsoptionen
- `--limit`: Maximale Anzahl zu sammelnder Repositories
- `--all`: Alle verfügbaren Repositories sammeln
- `--min-stars`: Minimale Anzahl von Stars für Repositories (Standard: 100)

#### Datenbankoptionen
- `--db-path`: Pfad zur SQLite-Datenbankdatei

#### Andere Optionen
- `--non-interactive`: Im nicht-interaktiven Modus ausführen
- `--stats`: Datenbankstatistiken anzeigen und beenden
- `--cleanup-owners`: Verwaiste Owner-Einträge bereinigen
- `--cleanup-dry-run`: Simulationsmodus für die Bereinigung

#### Performance-Tracking-Optionen
- `--disable-performance-tracking`: Deaktiviert das Performance-Tracking
- `--performance-output`: Format für die Ausgabe der Performance-Daten (`json`, `csv`, `log`)
- `--performance-output-path`: Pfad für die Ausgabe der Performance-Daten
- `--owner-analysis`: Führt eine detaillierte Analyse der Owner-Metadaten durch

## Fortgeschrittene Verwendung

### Geocoding von Standorten

Um Geocoding-Informationen für Standorte von Contributors und Organisationen zu aktualisieren, verwenden Sie das Skript `update_location_geocoding.py`:

```bash
python scripts/update_location_geocoding.py
```

Verfügbare Parameter:

- `--db-path`: Pfad zur SQLite-Datenbankdatei
- `--cache-file`: Pfad zur Geocoding-Cache-Datei
- `--user-agent`: User-Agent für Nominatim
- `--contributors`: Nur Contributors aktualisieren
- `--organizations`: Nur Organisationen aktualisieren
- `--limit`: Maximale Anzahl zu aktualisierender Einträge
- `--force`: Auch Einträge mit vorhandenen Ländercodes aktualisieren

### Export von Daten

Um Daten aus der Datenbank in CSV-Dateien zu exportieren, verwenden Sie das Skript `export_tables_to_csv.py`:

```bash
python scripts/export_tables_to_csv.py
```

Verfügbare Parameter:

- `--db-path`: Pfad zur SQLite-Datenbankdatei
- `--output-dir`: Verzeichnis für die exportierten CSV-Dateien
- `--tables`: Zu exportierende Tabellen (`contributors`, `organizations`, `repositories`, `all`)
- `--limit`: Maximale Anzahl zu exportierender Zeilen pro Tabelle
- `--with-timestamp`: Zeitstempel zum Dateinamen hinzufügen

### Bereinigung verwaister Owner-Einträge

Um verwaiste Owner-Einträge (Contributors und Organisationen ohne zugehörige Repositories) zu bereinigen, verwenden Sie das Skript `cleanup_orphaned_owners.py`:

```bash
python scripts/maintenance/cleanup_orphaned_owners.py
```

Verfügbare Parameter:

- `--db-path`: Pfad zur SQLite-Datenbankdatei
- `--dry-run`: Simulationsmodus (keine Änderungen vornehmen)

### Zurücksetzen und Neusammlung

Um die Datenbank zurückzusetzen und eine neue Sammlung zu starten, verwenden Sie das Skript `reset_and_collect.py`:

```bash
python scripts/maintenance/reset_and_collect.py
```

**Achtung**: Dieses Skript löscht alle vorhandenen Daten in der Datenbank!

## Beispiele für typische Anwendungsfälle

### 1. Sammlung von populären Repositories der letzten Woche

```bash
python scripts/collect_repositories.py --non-interactive --time-range week --min-stars 100
```

### 2. Sammlung von Python-Repositories des letzten Jahres

```bash
python scripts/collect_repositories.py --non-interactive --time-range year --min-stars 10
```

Nach der Sammlung können Sie die Repositories nach Sprache filtern.

### 3. Sammlung von Repositories eines bestimmten Zeitraums

```bash
python scripts/collect_repositories.py --non-interactive --time-range custom --start-date 2023-01-01 --end-date 2023-12-31 --min-stars 50
```

### 4. Aktualisierung der Geocoding-Informationen

```bash
python scripts/update_location_geocoding.py --limit 1000
```

### 5. Export der gesammelten Daten

```bash
python scripts/export_tables_to_csv.py --tables all --with-timestamp
```

### 6. Anreicherung von Repository-Statistiken (Enrichment)

Das Skript `scripts/enrich_repository_stats.py` dient der nachträglichen Anreicherung von Commit- und Pull-Request-Zahlen über die GitHub GraphQL API.

**Beispielaufruf:**
```bash
python scripts/enrich_repository_stats.py --db-path data/github_data.db --batch-size 50 --limit 200
```

**Hinweis:**
- Das Enrichment-Skript ist separat auszuführen und benötigt einen gültigen GitHub PAT mit entsprechenden Berechtigungen.
- Die Zählwerte werden in den bestehenden Repository-Einträgen ergänzt.
- Details zu Einschränkungen und Besonderheiten siehe Abschnitt "Besonderheiten & Hinweise".
## Überwachung und Protokollierung

Alle wichtigen Skripte schreiben Logdateien ins `logs`-Verzeichnis. Die wichtigsten Logdateien sind:

- `logs/repository_collection.log`: Sammlung der Repositories
- `logs/geocoding.log`: Geocoding-Prozess
- `logs/enrich_repository_stats.log`: Enrichment-Prozess
- `logs/export.log`: Exportvorgänge

Weitere Details und Fehleranalysen finden sich jeweils in den Logdateien.

Der GitHub Data Collector protokolliert ausführliche Informationen während der Datensammlung. Die Protokolldateien befinden sich im `logs`-Verzeichnis:

- `logs/repository_collection.log`: Protokoll der Repository-Sammlung
- `logs/geocoding.log`: Protokoll der Geocoding-Aktualisierung
- `logs/export.log`: Protokoll des Datenexports
- `logs/performance/`: Verzeichnis für Performance-Tracking-Daten

## Leistungsoptimierung

### Verwendung mehrerer API-Tokens

Um die Rate-Limits der GitHub API zu erhöhen, können Sie mehrere API-Tokens verwenden. Fügen Sie diese in der `.env`-Datei hinzu:

```
GITHUB_API_TOKENS=token1,token2,token3
```

### Optimierung der Batch-Größe

Die Batch-Größe für die Verarbeitung von Repositories kann angepasst werden, um die Leistung zu optimieren. Eine kleinere Batch-Größe reduziert den Speicherverbrauch, während eine größere Batch-Größe die Verarbeitungsgeschwindigkeit erhöhen kann.

### Caching

Der GitHub Data Collector implementiert ein Caching-System, um die Anzahl der API-Aufrufe zu reduzieren. Der Cache wird im Verzeichnis `data/cache` gespeichert.

## Besonderheiten & Hinweise

- Das Enrichment-Skript (`enrich_repository_stats.py`) sammelt aktuell **keinen** `contributors_count`, da dies mit der GitHub API performant nicht möglich ist.
- Der Wert `commits_count` bezieht sich ausschließlich auf den Default Branch eines Repositories.
- Für große Datenmengen empfiehlt sich die Nutzung von `--limit` und einer ausreichend großen Batch-Größe unter Berücksichtigung der API-Limits.
- Checkpointing und Retry-Logik sorgen dafür, dass abgebrochene Läufe fortgesetzt werden können.
- Fehlerhafte Repositories werden in einer separaten Datei (`failed_repo_ids_...txt`) dokumentiert.

## Fehlerbehebung

### Problem: Rate-Limit-Überschreitungen

Wenn Sie häufig Rate-Limit-Überschreitungen erleben, können Sie folgende Maßnahmen ergreifen:

1. Verwenden Sie mehrere API-Tokens
2. Reduzieren Sie die Batch-Größe
3. Erhöhen Sie die Wartezeit zwischen den Anfragen

### Problem: Hoher Speicherverbrauch

Wenn der GitHub Data Collector zu viel Speicher verbraucht, können Sie folgende Maßnahmen ergreifen:

1. Reduzieren Sie die Batch-Größe
2. Sammeln Sie Daten in kleineren Zeiträumen
3. Begrenzen Sie die Anzahl der zu sammelnden Repositories mit dem `--limit`-Parameter

### Problem: Langsame Datensammlung

Wenn die Datensammlung zu langsam ist, können Sie folgende Maßnahmen ergreifen:

1. Verwenden Sie mehrere API-Tokens
2. Erhöhen Sie die Batch-Größe
3. Begrenzen Sie die Anzahl der zu sammelnden Repositories mit dem `--min-stars`-Parameter

## Nächste Schritte

Nach der erfolgreichen Datensammlung können Sie mit dem [Export der Daten](export.md) fortfahren.
