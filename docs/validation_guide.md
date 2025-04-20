# Validierungsanleitung für die neue Projektstruktur

Diese Anleitung hilft bei der systematischen Überprüfung der neuen Projektstruktur des GitHub Data Collectors nach der Reorganisation.

## 1. Überprüfung der Grundfunktionalität

### 1.1 Repository-Sammlung testen

```bash
# Statistiken anzeigen (keine Datensammlung)
python scripts/collect_repositories.py --stats

# Minimale Testsammlung mit wenigen Repositories
python scripts/collect_repositories.py --non-interactive --time-range week --limit 5 --min-stars 1000
```

Erwartetes Ergebnis:
- Der erste Befehl sollte Statistiken zur aktuellen Datenbank anzeigen
- Der zweite Befehl sollte 5 Repositories mit mindestens 1000 Stars aus der letzten Woche sammeln

### 1.2 Geocoding-Aktualisierung testen

```bash
# Geocoding für maximal 5 Einträge aktualisieren
python scripts/update_location_geocoding.py --limit 5
```

Erwartetes Ergebnis:
- Das Skript sollte bis zu 5 Standorte geocodieren und die Ergebnisse in der Datenbank speichern

### 1.3 Datenexport testen

```bash
# Export aller Tabellen mit Zeitstempel
python scripts/export_tables_to_csv.py --with-timestamp
```

Erwartetes Ergebnis:
- Das Skript sollte CSV-Dateien für alle Tabellen im `exports`-Verzeichnis erstellen

## 2. Überprüfung der modularen CLI-Struktur

### 2.1 Direkter Aufruf der CLI-Module

```bash
# Direkter Aufruf des Repository-Sammlungsmoduls
python -m github_collector.cli.collect_command --stats

# Direkter Aufruf des Geocoding-Moduls
python -m github_collector.cli.geocoding_command --limit 5

# Direkter Aufruf des Export-Moduls
python -m github_collector.cli.export_command --tables repositories
```

Erwartetes Ergebnis:
- Alle Module sollten direkt aufrufbar sein und die gleiche Funktionalität wie die Skripte bieten

## 3. Überprüfung der zentralen Konfiguration

### 3.1 Konfiguration über Umgebungsvariablen

```bash
# Setzen einer Umgebungsvariable und Ausführen eines Skripts
export DATABASE_URL=sqlite:///test_data.db
python scripts/collect_repositories.py --stats
unset DATABASE_URL
```

Erwartetes Ergebnis:
- Das Skript sollte die Datenbank `test_data.db` verwenden
- Die Statistiken sollten für diese Datenbank angezeigt werden

### 3.2 Konfiguration über .env-Datei

```bash
# Erstellen einer temporären .env-Datei
echo "DATABASE_URL=sqlite:///env_test.db" > .env.test
cp .env.test .env
python scripts/collect_repositories.py --stats
rm .env
```

Erwartetes Ergebnis:
- Das Skript sollte die Datenbank `env_test.db` verwenden
- Die Statistiken sollten für diese Datenbank angezeigt werden

## 4. Überprüfung des Logging-Systems

### 4.1 Überprüfung der Logdateien

```bash
# Ausführen eines Skripts und Überprüfen der Logdateien
python scripts/collect_repositories.py --non-interactive --time-range week --limit 2 --min-stars 1000
ls -la logs/
cat logs/repository_collection.log | tail -n 20
```

Erwartetes Ergebnis:
- Das Logverzeichnis sollte Logdateien enthalten
- Die Logdatei `repository_collection.log` sollte Einträge zur Datensammlung enthalten

### 4.2 Überprüfung des Performance-Trackings

```bash
# Ausführen eines Skripts mit Performance-Tracking
python scripts/collect_repositories.py --non-interactive --time-range week --limit 5 --min-stars 1000
ls -la logs/performance/
```

Erwartetes Ergebnis:
- Das Verzeichnis `logs/performance/` sollte Performance-Tracking-Dateien enthalten

## 5. Überprüfung der Pfad- und Importstrukturen

### 5.1 Überprüfung der Importpfade

```bash
# Starten einer Python-Sitzung und Importieren von Modulen
python -c "from github_collector.config import Config; print(Config.get_instance().database_url)"
python -c "from github_collector.utils.logging_config import setup_logging; print(setup_logging)"
python -c "from github_collector.cli.collect_command import main; print(main)"
```

Erwartetes Ergebnis:
- Alle Importe sollten ohne Fehler funktionieren
- Die Ausgabe sollte die entsprechenden Werte oder Funktionsobjekte zeigen

### 5.2 Überprüfung der Paketstruktur

```bash
# Auflisten der Paketstruktur
find src/github_collector -type d | sort
```

Erwartetes Ergebnis:
- Die Ausgabe sollte die erwartete Verzeichnisstruktur zeigen

## 6. Überprüfung der Tests

### 6.1 Ausführen der Tests

```bash
# Ausführen aller Tests
python -m pytest

# Ausführen spezifischer Tests
python -m pytest tests/unit/
python -m pytest tests/integration/
```

Erwartetes Ergebnis:
- Alle Tests sollten erfolgreich durchlaufen
- Die Ausgabe sollte keine Fehler oder Warnungen enthalten

## 7. Überprüfung der Dokumentation

### 7.1 Überprüfung der Dokumentationsdateien

```bash
# Auflisten der Dokumentationsdateien
find docs -type f | sort
```

Erwartetes Ergebnis:
- Die Ausgabe sollte alle erwarteten Dokumentationsdateien zeigen

## 8. Überprüfung der Kompatibilität mit bestehenden Daten

### 8.1 Überprüfung der Datenbankkompatibilität

```bash
# Kopieren einer bestehenden Datenbank und Ausführen eines Skripts
cp github_data.db github_data_backup.db
python scripts/collect_repositories.py --stats
```

Erwartetes Ergebnis:
- Das Skript sollte die bestehende Datenbank korrekt lesen und Statistiken anzeigen

## 9. Überprüfung der Fehlerbehandlung

### 9.1 Überprüfung der Fehlerbehandlung bei ungültigen Parametern

```bash
# Ausführen eines Skripts mit ungültigen Parametern
python scripts/collect_repositories.py --time-range invalid
```

Erwartetes Ergebnis:
- Das Skript sollte eine hilfreiche Fehlermeldung anzeigen

### 9.2 Überprüfung der Fehlerbehandlung bei fehlenden Abhängigkeiten

```bash
# Temporäres Umbenennen einer Abhängigkeitsdatei
mv src/github_collector/utils/logging_config.py src/github_collector/utils/logging_config.py.bak
python scripts/collect_repositories.py --stats
mv src/github_collector/utils/logging_config.py.bak src/github_collector/utils/logging_config.py
```

Erwartetes Ergebnis:
- Das Skript sollte eine hilfreiche Fehlermeldung anzeigen

## 10. Überprüfung der Abwärtskompatibilität

### 10.1 Überprüfung der Abwärtskompatibilität der Skripte

```bash
# Ausführen eines Skripts mit den gleichen Parametern wie vor der Reorganisation
python scripts/collect_repositories.py --non-interactive --time-range week --limit 5 --min-stars 1000
```

Erwartetes Ergebnis:
- Das Skript sollte wie vor der Reorganisation funktionieren

## Zusammenfassung der Validierung

Nach Abschluss aller Validierungsschritte sollten Sie eine klare Vorstellung davon haben, ob die neue Projektstruktur korrekt funktioniert. Wenn alle Tests erfolgreich waren, ist die Reorganisation bereit für den Merge in den `developer`-Branch.

Bitte dokumentieren Sie alle Probleme, die während der Validierung aufgetreten sind, damit sie vor dem Merge behoben werden können.
