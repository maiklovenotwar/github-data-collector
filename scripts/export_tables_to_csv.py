#!/usr/bin/env python3
"""
Skript zum Exportieren von Datenbanktabellen in CSV-Dateien.
"""
import os
import sys
import logging
import argparse
from typing import List, Optional

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import GitHubDatabase
from github_collector.export.csv_export import export_tables

# Konfiguriere Logging
from github_collector.utils.logging_config import setup_logging

logger = setup_logging(log_file="export.log")


def parse_arguments():
    """Parse Kommandozeilenargumente."""
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





def main():
    """Hauptfunktion."""
    args = parse_arguments()
    
    # Lade Umgebungsvariablen aus .env-Datei, falls verfügbar
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    # Datenbankpfad
    db_path = args.db_path or os.environ.get("DATABASE_URL", "github_data.db")
    if not db_path.startswith("sqlite:///"):
        db_path = f"sqlite:///{db_path}"
    
    # Initialisiere Datenbank
    db = GitHubDatabase(db_path)
    
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


if __name__ == "__main__":
    main()
