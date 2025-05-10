#!/usr/bin/env python3
"""
Hilfsskript zum Zurücksetzen der Datenbank und Ausführen der Repository-Sammlung.

Dieses Skript implementiert eine erweiterte Logik zum Zurücksetzen verschiedener
Datenbanktypen (SQLite und MySQL). Für MySQL wird die Datenbank gelöscht (DROP DATABASE)
und neu erstellt (CREATE DATABASE). Anschließend wird die Funktion `init_db` aus
`github_collector.database.database` verwendet, um das Datenbankschema zu initialisieren.
Danach wird die Repository-Sammlung über `collect_repositories.py` gestartet.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url
import sqlalchemy
from sqlalchemy import text

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import init_db
# reset_command.main wird nicht verwendet, da dieses Skript eine eigene, erweiterte Reset-Logik hat.
# from github_collector.cli.reset_command import main as reset_command_main 
from github_collector.utils.logging_config import setup_logging

from github_collector.config import RESET_LOG
logger = setup_logging(log_file=RESET_LOG)

# Lade Umgebungsvariablen aus .env (immer aus Projekt-Hauptverzeichnis)
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_dir, ".env")
load_dotenv(dotenv_path)


def reset_database():
    """
    Setzt die Datenbank zurück, je nach Typ (SQLite, MySQL, ...).
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_file_path = os.path.join(project_dir, "data", "github_data.db")
        db_url = f"sqlite:///{db_file_path}"

    url = make_url(db_url)

    if url.drivername.startswith("sqlite"):
        db_file_path = url.database
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
        init_db(db_url)
        logger.info("SQLite-Datenbank zurückgesetzt.")
        return True

    elif url.drivername.startswith("mysql"):
        tmp_url = url.set(database=None)
        engine = sqlalchemy.create_engine(tmp_url)
        db_name = url.database
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
            conn.execute(text(f"CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET utf8mb4"))
        engine = sqlalchemy.create_engine(db_url)
        init_db(db_url)
        logger.info("MySQL-Datenbank zurückgesetzt.")
        return True

    else:
        logger.error(f"Reset für Datenbanktyp {url.drivername} nicht implementiert.")
        return False


def run_collect_repositories():
    """
    Führt das collect_repositories.py-Skript aus.
    
    Returns:
        True, wenn das Skript erfolgreich ausgeführt wurde, sonst False
    """
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    collect_script = os.path.join(project_dir, "scripts", "collect_repositories.py")
    db_url = os.environ.get("DATABASE_URL")
    
    # Stelle sicher, dass das Skript existiert
    if not os.path.exists(collect_script):
        logger.error(f"Sammlung-Skript nicht gefunden: {collect_script}")
        return False
    
    # Führe das Skript aus
    cmd = [sys.executable, collect_script]
    # Nur wenn KEINE DATABASE_URL gesetzt ist, --db-path übergeben!
    if not db_url:
        db_file_path = os.path.join(project_dir, "data", "github_data.db")
        cmd += ["--db-path", db_file_path]
    logger.info(f"Führe aus: {' '.join(cmd)}")
    
    try:
        env = os.environ.copy()
        process = subprocess.run(cmd, check=True, env=env)
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
