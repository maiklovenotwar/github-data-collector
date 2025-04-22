#!/usr/bin/env python3
"""
Skript zum Exportieren von Datenbanktabellen in CSV-Dateien.

Dieses Skript ist ein Wrapper für die CLI-Funktionalität des GitHub Data Collectors.
Es verwendet die Implementierung aus dem cli-Modul, um den Export durchzuführen.
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.export_command import main
from github_collector.utils.logging_config import setup_logging

from github_collector.config import EXPORT_LOG
logger = setup_logging(log_file=EXPORT_LOG)


if __name__ == "__main__":
    sys.exit(main())
