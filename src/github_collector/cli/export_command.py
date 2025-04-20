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
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    try:
        # Datenbankpfad
        db_path = args.db_path or config.DEFAULT_DB_PATH
        
        # Initialisiere Datenbank
        db = GitHubDatabase(str(db_path))
        
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
