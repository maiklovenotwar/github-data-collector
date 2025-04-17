"""
CLI-Modul zum Zurücksetzen der Datenbank und Ausführen der Repository-Sammlung.

Dieses Modul implementiert die Kommandozeilenschnittstelle für das Zurücksetzen
der Datenbank und das anschließende Ausführen der Repository-Sammlung.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

from github_collector import config
from github_collector.database.database import init_db
from github_collector.utils.logging_config import setup_logging

# Konfiguriere Logging
logger = setup_logging(log_file=config.RESET_LOG)


def reset_database() -> bool:
    """
    Setzt die Datenbank zurück, indem die Datenbankdatei gelöscht und neu initialisiert wird.
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    # Verwende die Standard-Datenbank aus der Konfiguration
    db_path = config.DEFAULT_DB_PATH
    
    logger.info(f"Setze Datenbank zurück: {db_path}")
    
    # Lösche die Datenbankdatei, falls sie existiert
    db_file = Path(db_path)
    if db_file.exists():
        try:
            db_file.unlink()
            logger.info(f"Datenbank-Datei gelöscht: {db_path}")
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Datenbank-Datei: {e}")
            return False
    
    # Initialisiere die Datenbank neu
    try:
        init_db(config.DB_URL)
        logger.info("Datenbank erfolgreich zurückgesetzt und neu initialisiert")
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Datenbank-Initialisierung: {e}")
        return False


def run_collect_repositories() -> bool:
    """
    Führt das collect_repositories.py-Skript aus.
    
    Returns:
        True, wenn das Skript erfolgreich ausgeführt wurde, sonst False
    """
    collect_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                "scripts", "collect_repositories.py")
    
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


def main() -> int:
    """
    Hauptfunktion zum Zurücksetzen der Datenbank und Ausführen der Repository-Sammlung.
    
    Returns:
        Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    # Lade Umgebungsvariablen aus .env-Datei, falls verfügbar
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    try:
        # Datenbank zurücksetzen
        if not reset_database():
            logger.error("Datenbank-Reset fehlgeschlagen, breche ab")
            return 1
        
        # Repository-Sammlung ausführen
        if not run_collect_repositories():
            logger.error("Repository-Sammlung fehlgeschlagen")
            return 1
        
        logger.info("Reset und Sammlung erfolgreich abgeschlossen")
        return 0
    
    except Exception as e:
        logger.exception(f"Fehler beim Reset und der Sammlung: {e}")
        return 1
