"""
CSV-Export-Funktionalität für den GitHub Data Collector.

Dieses Modul bietet Funktionen zum Exportieren von Datenbanktabellen in CSV-Dateien.
"""
import os
import csv
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


def export_table_to_csv(db, table_name: str, output_file: str, limit: Optional[int] = None) -> int:
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


def export_tables(db, tables: List[str], output_dir: str, limit: Optional[int] = None, 
                 with_timestamp: bool = False) -> int:
    """
    Exportiere mehrere Tabellen in CSV-Dateien.
    
    Args:
        db: Datenbankverbindung
        tables: Liste der zu exportierenden Tabellen
        output_dir: Verzeichnis für die exportierten CSV-Dateien
        limit: Maximale Anzahl zu exportierender Zeilen pro Tabelle
        with_timestamp: Zeitstempel zum Dateinamen hinzufügen
        
    Returns:
        Gesamtanzahl der exportierten Zeilen
    """
    # Erstelle das Ausgabeverzeichnis, falls es nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    # Zeitstempel für Dateinamen, falls gewünscht
    timestamp = ""
    if with_timestamp:
        timestamp = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Exportiere jede Tabelle
    total_exported = 0
    
    for table_name in tables:
        output_file = os.path.join(output_dir, f"{table_name}{timestamp}.csv")
        
        try:
            rows_exported = export_table_to_csv(
                db=db,
                table_name=table_name,
                output_file=output_file,
                limit=limit
            )
            
            total_exported += rows_exported
        
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Tabelle {table_name}: {e}")
    
    logger.info(f"Export abgeschlossen. Insgesamt {total_exported} Zeilen exportiert.")
    return total_exported
