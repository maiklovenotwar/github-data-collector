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
        import os
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(project_dir, ".env")
        load_dotenv(dotenv_path, override=True)
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    try:
        # Datenbankpfad bestimmen
        db_url = os.environ.get("DATABASE_URL")
        resolved_db_path = None

        if db_url:
            resolved_db_path = db_url
        elif args.db_path:
            resolved_db_path = args.db_path
        else:
            resolved_db_path = config.DEFAULT_DB_PATH

        # Sicherstellen, dass es eine gültige URL für SQLite ist, falls es nur ein Pfad ist
        if not (":///" in resolved_db_path or "://" in resolved_db_path): # Einfache Prüfung, ob es wie eine URL aussieht
            # Prüfen, ob der Pfad relativ ist und ihn zum Projektverzeichnis auflösen
            if not os.path.isabs(resolved_db_path):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                resolved_db_path = os.path.join(project_root, resolved_db_path)
            resolved_db_path = f"sqlite:///{resolved_db_path}"

        logger.info(f"Verwende Datenbank-URL: {resolved_db_path}")
        
        # Initialisiere Datenbank
        db = GitHubDatabase(resolved_db_path)
        
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
