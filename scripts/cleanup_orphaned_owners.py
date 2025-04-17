#!/usr/bin/env python3
"""
Skript zur Bereinigung verwaister Owner-Einträge (Contributors und Organisationen).

Dieses Skript ist ein Wrapper für die CLI-Funktionalität des GitHub Data Collectors.
Es verwendet die Implementierung aus dem cli-Modul, um die Bereinigung verwaister
Owner-Einträge durchzuführen.
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.cleanup_command import main


if __name__ == "__main__":
    sys.exit(main())
