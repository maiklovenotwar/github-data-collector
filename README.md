# GitHub Data Collector

Ein leistungsstarkes ETL-System zur Sammlung von GitHub-Daten über Repositories, Contributoren und Organisationen. Dieses System konzentriert sich auf die effiziente Sammlung und Speicherung von GitHub-Daten in einer SQLite-Datenbank für externe Analysezwecke.

## 🌍 Projektfokus

Dieses Projekt konzentriert sich ausschließlich auf die effiziente Sammlung von GitHub-Daten:

1. **Sammlung umfassender GitHub-Repository-Daten** mit effizienten Sammlungsstrategien
2. **Erfassung von Contributor-Informationen** einschließlich Standortdaten
3. **Sammlung von Organisationsdaten** mit Metadaten und Standortinformationen
4. **Geokodierung von Standortdaten** zur Anreicherung mit Länder- und Regionsinformationen
5. **Speicherung aller Daten in einer SQLite-Datenbank** für externe Analysezwecke

## 🌟 Hauptfunktionen

- **Effiziente GitHub API-Integration**: Optimiert für die Sammlung detaillierter Repository-, Contributor- und Organisationsmetadaten
- **Geografische Anreicherung**: Extrahiert und geokodiert Standortdaten von Mitwirkenden und Organisationen
- **Effiziente Sammlungsstrategien**:
  - Sternbasierte Sammlung für beliebte Repositories
  - Zeitraumbasierte Sammlung für historische Daten mit optimierter Periodengröße
- **Leistungsoptimierungen**:
  - Token-Pool-Management für die Handhabung von GitHub API-Ratenlimits
  - Intelligentes Caching-System zur Reduzierung von API-Aufrufen
  - Fortschrittsverfolgung mit Wiederaufnahmefähigkeit
- **Einfacher Datenexport**: Export der gesammelten Daten in CSV-Dateien für externe Analysen

## 🚀 Erste Schritte

### Voraussetzungen

- Python 3.8+
- GitHub API-Token(s)
- SQLAlchemy-kompatible Datenbank (standardmäßig SQLite)

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

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.
