#!/usr/bin/env python3
"""
Test-Skript für die Logging-Konfiguration.
"""
import os
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from github_collector.utils.logging_config import setup_logging

# Konfiguriere Logging
logger = setup_logging(log_file="test_logging.log")

# Teste das Logging
logger.debug("Debug-Nachricht")
logger.info("Info-Nachricht")
logger.warning("Warnung-Nachricht")
logger.error("Fehler-Nachricht")

print("Logging-Test abgeschlossen. Prüfe die Datei 'test_logging.log'.")
