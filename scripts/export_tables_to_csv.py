#!/usr/bin/env python3
"""
Skript zum Exportieren von Datenbanktabellen in CSV-Dateien.
"""
import os
import sys
import logging
import argparse
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import GitHubDatabase

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


def export_table_to_csv(db: GitHubDatabase, table_name: str, output_file: str, limit: Optional[int] = None) -> int:
    """
    Exportiere eine Tabelle in eine CSV-Datei.
    
    Args:
        db: Datenbankverbindung
        table_name: Name der zu exportierenden Tabelle
        output_file: Pfad zur Ausgabedatei
        limit: Maximale Anzahl zu exportierender Zeilen
        
    Returns:
        Anzahl der exportierten Zeilen
    """
    # Verwende SQL-Abfrage, um die Daten direkt zu holen
    # Dies umgeht das Problem mit den Metadaten
    from sqlalchemy import text, inspect
    
    # Hole die Tabelle aus dem Model
    model = None
    if table_name == "contributors":
        from github_collector.database.models import Contributor
        model = Contributor
    elif table_name == "organizations":
        from github_collector.database.models import Organization
        model = Organization
    elif table_name == "repositories":
        from github_collector.database.models import Repository
        model = Repository
    else:
        raise ValueError(f"Unbekannte Tabelle: {table_name}")
    
    # Hole die Daten mit dem ORM
    query = db.session.query(model)
    
    # Begrenze die Anzahl der Zeilen, falls angegeben
    if limit:
        query = query.limit(limit)
    
    # Führe die Abfrage aus
    results = query.all()
    
    if not results:
        logger.warning(f"Keine Daten in Tabelle {table_name} gefunden")
        return 0
    
    # Hole die Spalten aus dem Modell
    mapper = inspect(model)
    columns = [column.key for column in mapper.columns]
    
    # Erstelle das Ausgabeverzeichnis, falls es nicht existiert
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Schreibe die CSV-Datei
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Schreibe die Kopfzeile
        writer.writerow(columns)
        
        # Schreibe die Daten
        for result in results:
            row = [getattr(result, column, None) for column in columns]
            writer.writerow(row)
    
    logger.info(f"{len(results)} Zeilen aus Tabelle {table_name} nach {output_file} exportiert")
    return len(results)


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
    
    # Erstelle das Ausgabeverzeichnis, falls es nicht existiert
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Zeitstempel für Dateinamen, falls gewünscht
    timestamp = ""
    if args.with_timestamp:
        timestamp = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Exportiere jede Tabelle
    total_exported = 0
    
    for table_name in tables:
        output_file = os.path.join(args.output_dir, f"{table_name}{timestamp}.csv")
        
        try:
            rows_exported = export_table_to_csv(
                db=db,
                table_name=table_name,
                output_file=output_file,
                limit=args.limit
            )
            
            total_exported += rows_exported
        
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Tabelle {table_name}: {e}")
    
    logger.info(f"Export abgeschlossen. Insgesamt {total_exported} Zeilen exportiert.")
    
    # Schließe Datenbankverbindung
    db.close()


if __name__ == "__main__":
    main()
