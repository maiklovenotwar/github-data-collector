# Architekturübersicht des GitHub Data Collectors

## Einführung

Der GitHub Data Collector ist eine Python-Anwendung zur effizienten Sammlung von Metadaten über GitHub-Repositories, Contributors und Organisationen. Die Anwendung ist modular aufgebaut und folgt dem Prinzip der Separation of Concerns, um eine hohe Wartbarkeit und Erweiterbarkeit zu gewährleisten.

## Architekturprinzipien

1. **Modularität**: Die Anwendung ist in klar definierte Module unterteilt, die jeweils eine spezifische Aufgabe erfüllen.
2. **Separation of Concerns**: Jedes Modul ist für einen bestimmten Aspekt der Anwendung verantwortlich.
3. **Konfigurierbarkeit**: Die Anwendung ist über eine zentrale Konfigurationsdatei konfigurierbar.
4. **Testbarkeit**: Die Anwendung ist so gestaltet, dass sie gut testbar ist.
5. **Erweiterbarkeit**: Die Anwendung kann leicht um neue Funktionen erweitert werden.

## Hauptkomponenten

### 1. Konfiguration (`config.py`)

Die zentrale Konfigurationsdatei enthält alle Konfigurationsparameter für die Anwendung, einschließlich Pfaden, Datenbankeinstellungen, API-Konfiguration und Logging-Einstellungen.

### 2. API-Client & GraphQL-Handler (`api/github_api.py`, `enrichment/graphql_handler.py`)

Der API-Client ist verantwortlich für die Kommunikation mit der GitHub REST API. Für die Anreicherung von Repository-Statistiken wird zusätzlich ein spezialisierter GraphQL-Handler eingesetzt (`enrichment/graphql_handler.py`).

- Token-Pool-Management für mehrere API-Tokens
- Rate-Limit-Handling
- Caching von API-Antworten
- Fehlerbehandlung
- **GraphQL-Integration:** Für das Enrichment von Repositories wird die GitHub GraphQL API genutzt. Die Fehlerbehandlung ist besonders robust: Einzelne Fehler im Batch führen nicht mehr zum Abbruch der Verarbeitung, sondern werden individuell geloggt und können gezielt nachbearbeitet werden (z.B. mit `failed_repo_ids_*.txt`).
- **Stacktrace-Logging:** Fehlerursachen werden mit Stacktrace erfasst, um die Nachvollziehbarkeit und gezielte Fehlerbehebung zu ermöglichen.
- **Retry-Mechanismen:** Bei temporären API-Fehlern (z.B. 5xx) werden automatische Wiederholungsversuche durchgeführt.

### 3. Datenbank (`database/`)

Die Datenbankkomponente ist verantwortlich für die Speicherung und den Zugriff auf die gesammelten Daten. Sie umfasst:

- Datenbankmodelle (`models.py`)
- Datenbankzugriff (`database.py`)
- Datenbankmigrationen (über Alembic)

### 4. Repository-Collector (`repository_collector.py`)

Der Repository-Collector ist das Herzstück der Anwendung und verantwortlich für die Sammlung von Repository-Daten. Er implementiert:

- Zeitbasierte Sammlungsstrategie
- Fortschritts-Tracking
- Batch-Verarbeitung
- Fehlerbehandlung und Wiederaufnahme

### 5. Owner-Processor (`owners/owner_processor.py`)

Der Owner-Processor ist verantwortlich für die Verarbeitung von Owner-Metadaten (Contributors und Organisationen). Er implementiert:

- Batch-Verarbeitung von Owner-Metadaten
- Caching und Deduplizierung
- Performance-Tracking

### 6. Geocoding-Service (`geocoding/geocoding_service.py`)

Der Geocoding-Service ist verantwortlich für die Geocodierung von Standorten. Er implementiert:

- Geocodierung von Standorten über Nominatim
- Caching von Geocoding-Ergebnissen
- Fehlerbehandlung

### 7. Export-Funktionalität (`export/csv_export.py`)

Die Export-Funktionalität ist verantwortlich für den Export von Daten aus der Datenbank in CSV-Dateien.

### 8. Benutzeroberfläche (`ui/`)

Die Benutzeroberfläche umfasst Module für die Anzeige von Fortschritt und Statistiken:

- Fortschrittsanzeige (`progress.py`)
- Statistikanzeige (`stats.py`)

### 9. Kommandozeilenschnittstelle (`cli/`)

Die Kommandozeilenschnittstelle implementiert die Befehlszeilenbefehle für die Anwendung:

- Repository-Sammlung (`collect_command.py`)
- Export (`export_command.py`)
- Geocoding (`geocoding_command.py`)
- Bereinigung (`cleanup_command.py`)
- Reset (`reset_command.py`)

### 10. Hilfsfunktionen (`utils/`)

Die Hilfsfunktionen umfassen verschiedene Hilfsfunktionen für die Anwendung:

- Logging-Konfiguration (`logging_config.py`)
- Performance-Tracking (`performance_tracker.py`)

## Datenfluss

1. Der Benutzer startet die Anwendung über die Kommandozeilenschnittstelle.
2. Die Kommandozeilenschnittstelle initialisiert die benötigten Komponenten und startet die Repository-Sammlung.
3. Der Repository-Collector ruft Repository-Daten von der GitHub API ab.
4. Der Owner-Processor verarbeitet die Owner-Metadaten.
5. Die gesammelten Daten werden in der Datenbank gespeichert.
6. Der Geocoding-Service geocodiert die Standorte der Owner.
7. Die Daten können über die Export-Funktionalität exportiert werden.

## Abhängigkeiten

Die Anwendung verwendet folgende externe Bibliotheken:

- **SQLAlchemy**: ORM für die Datenbankzugriffe
- **Alembic**: Datenbankmigration
- **Requests**: HTTP-Anfragen an die GitHub API
- **Pandas**: Datenverarbeitung und -export
- **python-dotenv**: Laden von Umgebungsvariablen
- **geopy**: Geocodierung von Standorten
- **pycountry**: Ländercodes und -namen

## Erweiterbarkeit

Die Anwendung kann leicht um neue Funktionen erweitert werden:

1. **Neue Datenquellen**: Durch Hinzufügen neuer API-Clients und Collector-Module.
2. **Neue Exportformate**: Durch Hinzufügen neuer Export-Module.
3. **Neue Analysen**: Durch Hinzufügen neuer Analyse-Module.
4. **Neue Kommandozeilenbefehle**: Durch Hinzufügen neuer CLI-Module.

## Leistungsoptimierung

Die Anwendung implementiert verschiedene Leistungsoptimierungen:

1. **API-Caching**: Reduziert die Anzahl der API-Aufrufe.
2. **Token-Pool**: Ermöglicht die Verwendung mehrerer API-Tokens.
3. **Batch-Verarbeitung**: Reduziert den Overhead bei der Verarbeitung.
4. **Performance-Tracking**: Ermöglicht die Identifizierung von Leistungsengpässen.

## Fehlerbehandlung

Die Anwendung implementiert eine robuste Fehlerbehandlung:

- Einzelne Fehler in der GraphQL-Anreicherung werden pro Repository geloggt, ohne dass der gesamte Batch fehlschlägt.
- Fehlerhafte Repositories werden in `failed_repo_ids_*.txt` protokolliert und können gezielt erneut verarbeitet werden.
- Stacktraces und detaillierte Fehlerursachen werden im Logfile dokumentiert.
- Retry-Mechanismen sorgen für automatische Wiederholungsversuche bei temporären API-Fehlern.

Die Anwendung implementiert eine robuste Fehlerbehandlung:

1. **Wiederaufnahme**: Die Sammlung kann nach einem Fehler oder Abbruch fortgesetzt werden.
2. **Logging**: Ausführliches Logging für die Fehleranalyse.
3. **Rate-Limit-Handling**: Automatisches Warten bei Rate-Limit-Überschreitungen.

## Zukünftige Erweiterungen

Mögliche zukünftige Erweiterungen umfassen:

1. **Parallelisierung**: Parallelisierung der API-Aufrufe und Datenverarbeitung.
2. **GraphQL-Integration**: Verwendung der GitHub GraphQL API für effizientere Datenabfragen.
3. **Erweiterte Analysen**: Implementierung erweiterter Analysen der gesammelten Daten.
4. **Web-Interface**: Implementierung einer webbasierten Benutzeroberfläche.
