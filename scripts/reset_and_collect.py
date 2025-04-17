#!/usr/bin/env python3
"""
Hilfsskript zum Zurücksetzen der Datenbank und Ausführen der Repository-Sammlung.
Dieses Skript löscht die Datenbank und initialisiert sie neu,
bevor collect_repositories.py ausgeführt wird.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import init_db

# Konfiguriere Logging
from github_collector.utils.logging_config import setup_logging
from github_collector import config

logger = setup_logging(log_file=config.RESET_LOG)


def reset_database():
    """
    Setzt die Datenbank zurück, indem die Datenbankdatei gelöscht und neu initialisiert wird.
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    # Verwende die Standard-Datenbank aus der Umgebungsvariable oder den Standardwert
    db_path = os.environ.get("DATABASE_URL", "github_data.db")
    
    # Stelle sicher, dass der Pfad im richtigen Format ist
    if not db_path.startswith('sqlite:///'):
        db_url = f'sqlite:///{db_path}'
        db_file_path = db_path
    else:
        db_url = db_path
        db_file_path = db_path.replace('sqlite:///', '')
    
    logger.info(f"Setze Datenbank zurück: {db_file_path}")
    
    # Lösche die Datenbankdatei, falls sie existiert
    db_file = Path(db_file_path)
    if db_file.exists():
        try:
            db_file.unlink()
            logger.info(f"Datenbank-Datei gelöscht: {db_file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Datenbank-Datei: {e}")
            return False
    
    # Initialisiere die Datenbank neu
    try:
        init_db(db_url)
        logger.info("Datenbank erfolgreich zurückgesetzt und neu initialisiert")
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Datenbank-Initialisierung: {e}")
        return False


def run_collect_repositories():
    """
    Führt das collect_repositories.py-Skript aus.
    
    Returns:
        True, wenn das Skript erfolgreich ausgeführt wurde, sonst False
    """
    collect_script = os.path.join(os.path.dirname(__file__), "collect_repositories.py")
    
    # Stelle sicher, dass das Skript existiert
    if not os.path.exists(collect_script):
        logger.error(f"Sammlung-Skript nicht gefunden: {collect_script}")
        return False
    
    # Führe das Skript aus
    cmd = [sys.executable, collect_script]
    logger.info(f"Führe aus: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, check=True)
        logger.info("Repository-Sammlung erfolgreich abgeschlossen")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Fehler bei der Repository-Sammlung: {e}")
        return False


def main():
    """Hauptfunktion."""
    # Datenbank zurücksetzen
    if not reset_database():
        logger.error("Datenbank-Reset fehlgeschlagen, breche ab")
        return 1
    
    # Repository-Sammlung ausführen
    if not run_collect_repositories():
        logger.error("Repository-Sammlung fehlgeschlagen")
        return 1
    
    logger.info("Datenbank-Reset und Repository-Sammlung erfolgreich abgeschlossen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
