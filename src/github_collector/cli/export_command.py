"""
CLI-Modul für den Export von Datenbanktabellen in CSV-Dateien.

Dieses Modul implementiert die Kommandozeilenschnittstelle für den Export
von Datenbanktabellen in CSV-Dateien.
"""
import os
import sys
import logging
import argparse
from typing import List, Optional
from pathlib import Path

from github_collector import config
from github_collector.database.database import GitHubDatabase
from github_collector.export.csv_export import export_tables
from github_collector.utils.logging_config import get_export_logger

# Konfiguriere Logging
logger = get_export_logger()


def parse_arguments() -> argparse.Namespace:
    """
    Parse Kommandozeilenargumente.
    
    Returns:
        Geparste Argumente
    """
    parser = argparse.ArgumentParser(description="Exportiere Datenbanktabellen in CSV-Dateien")
    
    # Datenbankoptionen
    parser.add_argument("--db-path", help="Pfad zur SQLite-Datenbankdatei")
    
    # Exportoptionen
    parser.add_argument("--output-dir", default="exports",
                      help="Verzeichnis für die exportierten CSV-Dateien (Standard: exports)")
    parser.add_argument("--tables", nargs="+", choices=["contributors", "organizations", "repositories", "all"],
                      default=["all"], help="Zu exportierende Tabellen (Standard: all)")
    parser.add_argument("--limit", type=int,
                      help="Maximale Anzahl zu exportierender Zeilen pro Tabelle")
    parser.add_argument("--with-timestamp", action="store_true",
                      help="Zeitstempel zum Dateinamen hinzufügen")
    
    return parser.parse_args()


def main() -> int:
    """
    Hauptfunktion für den Export von Datenbanktabellen.
    
    Returns:
        Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    args = parse_arguments()
    
    # Lade Umgebungsvariablen aus .env-Datei, falls verfügbar
    try:
        from dotenv import load_dotenv
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(project_dir, ".env")
        load_dotenv(dotenv_path, override=True)
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    try:
        # Datenbankpfad bestimmen
        # Priorität: 1. Umgebungsvariable DATABASE_URL, 2. --db-path Argument, 3. config.DEFAULT_DB_PATH
        db_path_or_url = os.getenv('DATABASE_URL')
        source = "Umgebungsvariable DATABASE_URL"

        if not db_path_or_url:
            if args.db_path:
                db_path_or_url = args.db_path
                source = "--db-path Argument"
            else:
                db_path_or_url = str(config.DEFAULT_DB_PATH) # Sicherstellen, dass es ein String ist
                source = "config.DEFAULT_DB_PATH"
        
        logger.info(f"Verwende Datenbank von: {source} ('{db_path_or_url}')")

        # Sicherstellen, dass es eine gültige SQLAlchemy-URL ist
        final_db_url = str(db_path_or_url) # Nochmal sicherstellen, dass es ein String ist
        if "://" not in final_db_url and not final_db_url.startswith("sqlite:///") and final_db_url != ":memory:":
            # Es ist wahrscheinlich ein lokaler Pfad, der das Präfix 'sqlite:///' benötigt.
            final_db_url = f"sqlite:///{final_db_url}"
            logger.info(f"Konvertiere Pfad zu SQLAlchemy URL: {final_db_url}")
        
        # Initialisiere Datenbank
        db = GitHubDatabase(final_db_url)
        
        # Bestimme die zu exportierenden Tabellen
        tables = []
        if "all" in args.tables:
            tables = ["contributors", "organizations", "repositories"]
        else:
            tables = args.tables
        
        # Exportiere die Tabellen
        export_tables(
            db=db,
            tables=tables,
            output_dir=args.output_dir,
            limit=args.limit,
            with_timestamp=args.with_timestamp
        )
        
        # Schließe Datenbankverbindung
        db.close()
        
        return 0
    
    except Exception as e:
        logger.exception(f"Fehler beim Export der Datenbanktabellen: {e}")
        return 1
