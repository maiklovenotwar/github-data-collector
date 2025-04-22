#!/usr/bin/env python3
"""
Skript zur Aktualisierung der Geocoding-Informationen für Contributor- und Organisationsstandorte.

Dieses Skript dient als Einstiegspunkt für die Geocoding-Anreicherung des GitHub Data Collectors.
Es ruft die CLI-Implementierung auf, verarbeitet Kommandozeilenargumente und schreibt die Ergebnisse
sowie alle Logs in die Datenbank und ins Logfile `logs/geocoding.log`.

Besonderheiten:
- Nutzt einen lokalen Cache zur Reduktion von API-Aufrufen (geocoding_cache.json)
- Unterstützt gezielte Geocodierung für Contributors und/oder Organisationen
- Unterstützt Limitierung, erneute Geocodierung und Cache-Reset
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.geocoding_command import main
from github_collector.utils.logging_config import setup_logging

from github_collector.config import GEOCODING_LOG
logger = setup_logging(log_file=GEOCODING_LOG)


if __name__ == "__main__":
    sys.exit(main())
