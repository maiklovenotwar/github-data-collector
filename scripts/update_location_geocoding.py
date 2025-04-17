#!/usr/bin/env python3
"""
Skript zur Aktualisierung der Geocoding-Informationen für Standorte.

Dieses Skript ist ein Wrapper für die CLI-Funktionalität des GitHub Data Collectors.
Es verwendet die Implementierung aus dem cli-Modul, um die Geocoding-Aktualisierung durchzuführen.
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.geocoding_command import main


if __name__ == "__main__":
    sys.exit(main())
