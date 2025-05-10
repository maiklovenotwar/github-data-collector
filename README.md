# GitHub Data Collector

Ein leistungsstarkes ETL-System zur Sammlung von GitHub-Daten über Repositories, Contributoren und Organisationen. Dieses System konzentriert sich auf die effiziente Sammlung und Speicherung von GitHub-Daten in einer SQLite-Datenbank für externe Analysezwecke.

## 🌍 Projektfokus

Dieses Projekt konzentriert sich ausschließlich auf die effiziente Sammlung von GitHub-Daten:

1. **Sammlung umfassender GitHub-Repository-Daten** mit effizienten Sammlungsstrategien
2. **Erfassung von Contributor-Informationen** einschließlich Standortdaten
3. **Sammlung von Organisationsdaten** mit Metadaten und Standortinformationen
4. **Geokodierung von Standortdaten** zur Anreicherung mit Länder- und Regionsinformationen
5. **Speicherung aller Daten in einer SQLite- oder MySQL-Datenbank** für externe Analysezwecke

## 🌟 Hauptfunktionen

- **Effiziente GitHub API-Integration**: Optimiert für die Sammlung detaillierter Repository-, Contributor- und Organisationsmetadaten
- **Geografische Anreicherung**: Extrahiert und geokodiert Standortdaten von Mitwirkenden und Organisationen
- **Unterstützung für MySQL und SQLite**: Die Datenbank kann über die Umgebungsvariable `DATABASE_URL` als SQLite- oder MySQL-URL angegeben werden (siehe unten).
- **Effiziente Sammlungsstrategien**:
  - Sternbasierte Sammlung für beliebte Repositories
  - Zeitraumbasierte Sammlung für historische Daten mit optimierter Periodengröße
- **Leistungsoptimierungen**:
  - Token-Pool-Management für die Handhabung von GitHub API-Ratenlimits
  - Intelligentes Caching-System zur Reduzierung von API-Aufrufen
  - Fortschrittsverfolgung mit Wiederaufnahmefähigkeit
  - **Verbesserte Nebenläufigkeit für SQLite**: Der standardmäßig aktivierte WAL-Modus (Write-Ahead Logging) für SQLite-Datenbanken reduziert Sperrkonflikte erheblich und ermöglicht eine stabilere parallele Ausführung von Sammel- und Anreicherungsskripten.
- **Einfacher Datenexport**: Export der gesammelten Daten in CSV-Dateien für externe Analysen

## 🚀 Erste Schritte

### Voraussetzungen

- Python 3.8+
- GitHub API-Token(s)
- SQLAlchemy-kompatible Datenbank (SQLite oder MySQL)

**Unterstützte Datenbanken:**
- SQLite (Standard): `DATABASE_URL=sqlite:///data/github_data.db`
- MySQL: `DATABASE_URL=mysql+pymysql://user:pass@localhost/github_data`

Die Umgebungsvariable `DATABASE_URL` kann in der `.env`-Datei gesetzt werden. Alle Skripte erkennen diese Variable automatisch. Alternativ kann bei den meisten Skripten der Parameter `--db-path` verwendet werden (wird automatisch zu einer SQLAlchemy-URL umgewandelt, falls nötig).

### Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/github-data-collector.git
cd github-data-collector

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.template .env
# Bearbeite .env und füge deine GitHub API-Token hinzu
```

### Grundlegende Verwendung

```bash
# GitHub-Repositories sammeln
python scripts/collect_repositories.py --time-range month --min-stars 100

# Standortdaten geokodieren
python scripts/update_location_geocoding.py

# Daten in CSV-Dateien exportieren
python scripts/export_tables_to_csv.py

# --- Parallele Ausführung (Empfohlen für SQLite) ---
# Aufgrund des aktivierten WAL-Modus für SQLite können das Sammeln von Repositories
# und die Geokodierung nun effizient parallel ausgeführt werden, um Zeit zu sparen:
# Terminal 1:
# python scripts/collect_repositories.py --interactive 
# Terminal 2:
# python scripts/update_location_geocoding.py
```

## 📊 Datenmodell

### Haupttabellen

1. **Contributors**: GitHub-Benutzer mit Standortinformationen
2. **Organizations**: GitHub-Organisationen mit Standortinformationen
3. **Repositories**: GitHub-Repositories mit Metadaten und Statistiken

## 📁 Projektstruktur

```
github-data-collector/
├── docs/                  # Dokumentation
├── scripts/               # Ausführbare Skripte
│   ├── collect_repositories.py     # Sammlung von Repositories
│   ├── update_location_geocoding.py # Geokodierung von Standorten
│   └── export_tables_to_csv.py     # Export von Daten
├── src/                   # Quellcode
│   └── github_collector/   # Hauptpaket
│       ├── api/           # GitHub API-Integration
│       ├── database/      # Datenbankmodelle und -operationen
│       ├── geocoding/     # Geokodierungsdienste
│       └── utils/         # Hilfsfunktionen
├── tests/                 # Tests
├── .env.template          # Vorlage für Umgebungsvariablen
├── requirements.txt       # Projektabhängigkeiten
└── README.md              # Projektdokumentation
```

## Tests ausführen

Stelle sicher, dass pytest installiert ist:

    pip install pytest

Führe dann die Tests mit folgendem Befehl aus:

    PYTHONPATH=src pytest

Optional für Coverage:

    pip install pytest-cov
    PYTHONPATH=src pytest --cov=github_collector

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

---

# GitHub Data Collector

A powerful ETL system for collecting GitHub data on repositories, contributors, and organizations. This system focuses on efficient data collection and storage in a SQLite database for external analysis purposes.

## 🌍 Project Focus

This project focuses exclusively on efficient data collection:

1. **Comprehensive GitHub repository data collection** with efficient collection strategies
2. **Contributor information collection** including location data
3. **Organization data collection** with metadata and location information
4. **Geocoding of location data** to enrich with country and region information
5. **Storage of all data in a SQLite database** for external analysis purposes

## 🌟 Main Features

- **Efficient GitHub API integration**: Optimized for collecting detailed repository, contributor, and organization metadata
- **Geographic enrichment**: Extracts and geocodes location data from contributors and organizations
- **Efficient collection strategies**:
  - Star-based collection for popular repositories
  - Time-based collection for historical data with optimized period size
- **Performance optimizations**:
  - Token pool management for handling GitHub API rate limits
  - Intelligent caching system to reduce API calls
  - Progress tracking with resume capability
  - **Improved Concurrency for SQLite**: Write-Ahead Logging (WAL) mode is enabled by default for SQLite databases, significantly reducing locking contention and allowing for more stable parallel execution of collection and enrichment scripts.
- **Easy data export**: Export collected data to CSV files for external analysis

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- GitHub API token(s)
- SQLAlchemy-compatible database (default: SQLite)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/github-data-collector.git
cd github-data-collector

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.template .env
# Edit .env and add your GitHub API token
```

### Basic Usage

```bash
# Collect GitHub repositories
python scripts/collect_repositories.py --time-range month --min-stars 100

# Geocode location data
python scripts/update_location_geocoding.py

# Export data to CSV files
python scripts/export_tables_to_csv.py

# --- Parallel Execution (Recommended for SQLite) ---
# Due to the enabled WAL mode for SQLite, repository collection and geocoding
# can now be run efficiently in parallel to save time:
# Terminal 1:
# python scripts/collect_repositories.py --interactive
# Terminal 2:
# python scripts/update_location_geocoding.py
```

## 📊 Data Model

### Main Tables

1. **Contributors**: GitHub users with location information
2. **Organizations**: GitHub organizations with location information
3. **Repositories**: GitHub repositories with metadata and statistics

## 📁 Project Structure

```
github-data-collector/
├── docs/                  # Documentation
├── scripts/               # Executable scripts
│   ├── collect_repositories.py     # Repository collection
│   ├── update_location_geocoding.py # Location geocoding
│   └── export_tables_to_csv.py     # Data export
├── src/                   # Source code
│   └── github_collector/   # Main package
│       ├── api/           # GitHub API integration
│       ├── database/      # Database models and operations
│       ├── geocoding/     # Geocoding services
│       └── utils/         # Utility functions
├── tests/                 # Tests
├── .env.template          # Environment variable template
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## Running Tests

Make sure pytest is installed:

    pip install pytest

Then run the tests with the following command:

    PYTHONPATH=src pytest

Optional for coverage:

    pip install pytest-cov
    PYTHONPATH=src pytest --cov=github_collector

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
