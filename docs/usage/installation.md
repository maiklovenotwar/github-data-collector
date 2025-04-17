# Installation des GitHub Data Collectors

Diese Anleitung beschreibt die Installation und Einrichtung des GitHub Data Collectors.

## Voraussetzungen

Bevor Sie den GitHub Data Collector installieren, stellen Sie sicher, dass folgende Voraussetzungen erfüllt sind:

- Python 3.11 oder höher
- pip (Python-Paketmanager)
- Git (für das Klonen des Repositories)
- GitHub API-Token (für den Zugriff auf die GitHub API)

## Installation

### 1. Repository klonen

Klonen Sie das GitHub Data Collector-Repository:

```bash
git clone https://github.com/username/github-data-collector.git
cd github-data-collector
```

### 2. Virtuelle Umgebung erstellen (empfohlen)

Es wird empfohlen, eine virtuelle Python-Umgebung zu erstellen, um Konflikte mit anderen Python-Paketen zu vermeiden:

```bash
# Erstellen einer virtuellen Umgebung
python -m venv venv

# Aktivieren der virtuellen Umgebung
# Unter Windows:
venv\Scripts\activate
# Unter macOS/Linux:
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env`-Datei im Hauptverzeichnis des Projekts und fügen Sie Ihre GitHub API-Token hinzu:

```bash
# Kopieren der Vorlage
cp .env.template .env

# Bearbeiten der .env-Datei
# Fügen Sie Ihre GitHub API-Token hinzu
```

Die `.env`-Datei sollte folgende Einträge enthalten:

```
# GitHub API-Token (erforderlich)
GITHUB_API_TOKEN=your_github_token

# Mehrere GitHub API-Tokens (optional, durch Kommas getrennt)
GITHUB_API_TOKENS=token1,token2,token3

# Datenbankpfad (optional, Standard: github_data.db)
DATABASE_URL=sqlite:///github_data.db

# Performance-Tracking (optional, Standard: true)
GITHUB_COLLECTOR_PERFORMANCE_TRACKING=true

# Log-Level (optional, Standard: INFO)
LOG_LEVEL=INFO
```

### 5. Verzeichnisstruktur erstellen

Der GitHub Data Collector erstellt automatisch die erforderlichen Verzeichnisse beim ersten Start. Sie können diese auch manuell erstellen:

```bash
mkdir -p data/cache logs/performance exports
```

## Überprüfung der Installation

Um zu überprüfen, ob die Installation erfolgreich war, führen Sie den folgenden Befehl aus:

```bash
python scripts/collect_repositories.py --stats
```

Dieser Befehl zeigt die aktuellen Statistiken der Datenbank an, ohne Daten zu sammeln.

## Fehlerbehebung

### Problem: Fehler beim Installieren der Abhängigkeiten

Wenn Sie Probleme beim Installieren der Abhängigkeiten haben, stellen Sie sicher, dass Sie die neueste Version von pip verwenden:

```bash
pip install --upgrade pip
```

Versuchen Sie dann erneut, die Abhängigkeiten zu installieren.

### Problem: "ModuleNotFoundError"

Wenn Sie einen "ModuleNotFoundError" erhalten, stellen Sie sicher, dass Sie die virtuelle Umgebung aktiviert haben und alle Abhängigkeiten installiert sind:

```bash
# Aktivieren der virtuellen Umgebung
source venv/bin/activate  # Unter macOS/Linux
venv\Scripts\activate     # Unter Windows

# Installieren der Abhängigkeiten
pip install -r requirements.txt
```

### Problem: GitHub API-Token wird nicht erkannt

Wenn Ihr GitHub API-Token nicht erkannt wird, stellen Sie sicher, dass Sie die `.env`-Datei korrekt erstellt haben und dass sie sich im Hauptverzeichnis des Projekts befindet. Sie können auch das Token direkt als Umgebungsvariable setzen:

```bash
# Unter Windows:
set GITHUB_API_TOKEN=your_github_token

# Unter macOS/Linux:
export GITHUB_API_TOKEN=your_github_token
```

## Nächste Schritte

Nach der erfolgreichen Installation können Sie mit der [Datensammlung](data_collection.md) beginnen.
