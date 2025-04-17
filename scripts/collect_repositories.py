#!/usr/bin/env python3
"""
Skript zum Sammeln von GitHub-Repositories.

Dieses Skript ist ein Wrapper für die CLI-Funktionalität des GitHub Data Collectors.
Es verwendet die Implementierung aus dem cli-Modul, um die Repository-Sammlung durchzuführen.
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.collect_command import main


if __name__ == "__main__":
    sys.exit(main())
