# Datenexport mit dem GitHub Data Collector

Diese Anleitung beschreibt, wie Sie die mit dem GitHub Data Collector gesammelten Daten exportieren können.

## Grundlegende Verwendung

Der GitHub Data Collector bietet ein Skript zum Exportieren der gesammelten Daten in CSV-Dateien. Das Skript befindet sich im `scripts`-Verzeichnis:

```bash
python scripts/export_tables_to_csv.py
```

Ohne Parameter exportiert das Skript alle Tabellen in das Verzeichnis `exports`.

## Verfügbare Parameter

Das Skript `export_tables_to_csv.py` unterstützt folgende Parameter:

- `--db-path`: Pfad zur SQLite-Datenbankdatei
- `--output-dir`: Verzeichnis für die exportierten CSV-Dateien (Standard: `exports`)
- `--tables`: Zu exportierende Tabellen (`contributors`, `organizations`, `repositories`, `all`)
- `--limit`: Maximale Anzahl zu exportierender Zeilen pro Tabelle
- `--with-timestamp`: Zeitstempel zum Dateinamen hinzufügen

## Beispiele

### Export aller Tabellen

```bash
python scripts/export_tables_to_csv.py --tables all
```

### Export einer bestimmten Tabelle

```bash
python scripts/export_tables_to_csv.py --tables repositories
```

### Export mit Zeitstempel

```bash
python scripts/export_tables_to_csv.py --with-timestamp
```

Dies fügt einen Zeitstempel zum Dateinamen hinzu, z.B. `repositories_2025-04-17_120000.csv`.

### Export mit Limit

```bash
python scripts/export_tables_to_csv.py --limit 1000
```

Dies exportiert maximal 1000 Zeilen pro Tabelle.

### Export in ein bestimmtes Verzeichnis

```bash
python scripts/export_tables_to_csv.py --output-dir /path/to/export/directory
```

## Exportierte Daten

Die exportierten CSV-Dateien enthalten alle Spalten der entsprechenden Tabellen. Die Dateien werden im UTF-8-Format mit Komma als Trennzeichen erstellt.

### contributors.csv

Die Datei `contributors.csv` enthält Informationen über GitHub-Benutzer (Contributors):

- `id`: GitHub-ID des Contributors
- `login`: GitHub-Benutzername
- `name`: Vollständiger Name des Contributors
- `email`: E-Mail-Adresse des Contributors
- `company`: Unternehmen des Contributors
- `blog`: Blog oder Website des Contributors
- `location`: Standort des Contributors
- `bio`: Biografie des Contributors
- `twitter_username`: Twitter-Benutzername des Contributors
- `public_repos`: Anzahl der öffentlichen Repositories
- `public_gists`: Anzahl der öffentlichen Gists
- `followers`: Anzahl der Follower
- `following`: Anzahl der gefolgten Benutzer
- `created_at`: Erstellungsdatum des GitHub-Kontos
- `updated_at`: Letztes Aktualisierungsdatum des GitHub-Kontos
- `country_code`: ISO-Ländercode (aus Geocoding)
- `country_name`: Ländername (aus Geocoding)
- `longitude`: Längengrad des Standorts (aus Geocoding)
- `latitude`: Breitengrad des Standorts (aus Geocoding)

### organizations.csv

Die Datei `organizations.csv` enthält Informationen über GitHub-Organisationen:

- `id`: GitHub-ID der Organisation
- `login`: GitHub-Benutzername der Organisation
- `name`: Name der Organisation
- `email`: E-Mail-Adresse der Organisation
- `description`: Beschreibung der Organisation
- `blog`: Blog oder Website der Organisation
- `location`: Standort der Organisation
- `twitter_username`: Twitter-Benutzername der Organisation
- `public_repos`: Anzahl der öffentlichen Repositories
- `public_gists`: Anzahl der öffentlichen Gists
- `followers`: Anzahl der Follower
- `following`: Anzahl der gefolgten Benutzer
- `created_at`: Erstellungsdatum der Organisation
- `updated_at`: Letztes Aktualisierungsdatum der Organisation
- `country_code`: ISO-Ländercode (aus Geocoding)
- `country_name`: Ländername (aus Geocoding)
- `longitude`: Längengrad des Standorts (aus Geocoding)
- `latitude`: Breitengrad des Standorts (aus Geocoding)

### repositories.csv

Die Datei `repositories.csv` enthält Informationen über GitHub-Repositories:

- `id`: GitHub-ID des Repositories
- `name`: Name des Repositories
- `full_name`: Vollständiger Name des Repositories (owner/name)
- `description`: Beschreibung des Repositories
- `homepage`: Homepage des Repositories
- `language`: Hauptsprache des Repositories
- `fork`: Gibt an, ob das Repository ein Fork ist
- `forks_count`: Anzahl der Forks
- `stargazers_count`: Anzahl der Stars
- `watchers_count`: Anzahl der Watcher
- `size`: Größe des Repositories in KB
- `open_issues_count`: Anzahl der offenen Issues
- `owner_id`: ID des Besitzers (Contributor oder Organisation)
- `owner_type`: Typ des Besitzers ("contributor" oder "organization")
- `created_at`: Erstellungsdatum des Repositories
- `updated_at`: Letztes Aktualisierungsdatum des Repositories
- `pushed_at`: Letztes Push-Datum des Repositories
- `contributors_count`: Anzahl der Contributors
- `commits_count`: Anzahl der Commits

## Weiterverarbeitung der exportierten Daten

Die exportierten CSV-Dateien können mit verschiedenen Tools weiterverarbeitet werden:

### Pandas (Python)

```python
import pandas as pd

# Laden der CSV-Dateien
contributors_df = pd.read_csv('exports/contributors.csv')
organizations_df = pd.read_csv('exports/organizations.csv')
repositories_df = pd.read_csv('exports/repositories.csv')

# Beispiel: Anzahl der Repositories pro Sprache
language_counts = repositories_df['language'].value_counts()
print(language_counts)

# Beispiel: Durchschnittliche Anzahl von Stars pro Sprache
avg_stars_by_language = repositories_df.groupby('language')['stargazers_count'].mean()
print(avg_stars_by_language)

# Beispiel: Anzahl der Contributors pro Land
contributors_by_country = contributors_df['country_name'].value_counts()
print(contributors_by_country)
```

### R

```r
# Laden der CSV-Dateien
contributors <- read.csv('exports/contributors.csv')
organizations <- read.csv('exports/organizations.csv')
repositories <- read.csv('exports/repositories.csv')

# Beispiel: Anzahl der Repositories pro Sprache
language_counts <- table(repositories$language)
print(language_counts)

# Beispiel: Durchschnittliche Anzahl von Stars pro Sprache
avg_stars_by_language <- aggregate(stargazers_count ~ language, data = repositories, mean)
print(avg_stars_by_language)

# Beispiel: Anzahl der Contributors pro Land
contributors_by_country <- table(contributors$country_name)
print(contributors_by_country)
```

### Excel/LibreOffice Calc

Die CSV-Dateien können direkt in Excel oder LibreOffice Calc geöffnet werden. Stellen Sie sicher, dass Sie UTF-8 als Zeichenkodierung auswählen.

## Automatisierung des Exports

Sie können den Export automatisieren, indem Sie das Skript in einem Cron-Job oder einer anderen Aufgabenplanung ausführen:

### Linux/macOS (Cron)

```bash
# Beispiel für einen täglichen Export um 2:00 Uhr
0 2 * * * cd /path/to/github-data-collector && /path/to/python scripts/export_tables_to_csv.py --with-timestamp
```

### Windows (Task Scheduler)

Erstellen Sie eine Batch-Datei mit folgendem Inhalt:

```batch
@echo off
cd /d C:\path\to\github-data-collector
C:\path\to\python.exe scripts\export_tables_to_csv.py --with-timestamp
```

Und planen Sie diese Batch-Datei mit dem Task Scheduler.

## Fehlerbehebung

### Problem: Fehler beim Öffnen der CSV-Dateien

Wenn Sie Probleme beim Öffnen der CSV-Dateien haben, stellen Sie sicher, dass Sie die richtige Zeichenkodierung (UTF-8) und das richtige Trennzeichen (Komma) verwenden.

### Problem: Zu große CSV-Dateien

Wenn die CSV-Dateien zu groß sind, können Sie den `--limit`-Parameter verwenden, um die Anzahl der exportierten Zeilen zu begrenzen:

```bash
python scripts/export_tables_to_csv.py --limit 10000
```

### Problem: Fehlende Daten

Wenn in den CSV-Dateien Daten fehlen, stellen Sie sicher, dass die Datenbank korrekt gefüllt ist. Sie können die Datenbankstatistiken mit folgendem Befehl anzeigen:

```bash
python scripts/collect_repositories.py --stats
```
