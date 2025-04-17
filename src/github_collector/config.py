"""Zentrale Konfiguration für GitHub Data Collector.

Diese Datei enthält alle Konfigurationsparameter für den GitHub Data Collector,
einschließlich Pfaden, Datenbankeinstellungen, API-Konfiguration und Logging-Einstellungen.
"""

import os
from pathlib import Path

# Basispfade
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Stellen Sie sicher, dass die Verzeichnisse existieren
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Datenbankeinstellungen
DEFAULT_DB_PATH = BASE_DIR / "github_data.db"  # Behalte ursprünglichen Pfad für Abwärtskompatibilität
DB_URL = f"sqlite:///{os.getenv('DB_PATH', DEFAULT_DB_PATH)}"

# API-Einstellungen
API_TOKEN = os.getenv("GITHUB_API_TOKEN")
API_TOKENS = os.getenv("GITHUB_API_TOKENS", "").split(",") if os.getenv("GITHUB_API_TOKENS") else []

# Logging-Einstellungen
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REPOSITORY_LOG = LOG_DIR / "repository_collection.log"
GEOCODING_LOG = LOG_DIR / "geocoding.log"
EXPORT_LOG = LOG_DIR / "export.log"
RESET_LOG = LOG_DIR / "reset_and_collect.log"

# Cache-Einstellungen
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
GEOCODING_CACHE = CACHE_DIR / "geocoding_cache.json"

# Collection-State-Einstellungen
COLLECTION_STATE_FILE = BASE_DIR / "collection_state.json"  # Behalte ursprünglichen Pfad für Abwärtskompatibilität

# Performance-Tracking
ENABLE_PERFORMANCE_TRACKING = os.getenv("GITHUB_COLLECTOR_PERFORMANCE_TRACKING", "true").lower() not in ("false", "0", "no", "off")
PERFORMANCE_OUTPUT_DIR = LOG_DIR / "performance"
PERFORMANCE_OUTPUT_DIR.mkdir(exist_ok=True)
