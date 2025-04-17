"""
CLI-Modul für die Aktualisierung der Geocoding-Informationen für Standorte.

Dieses Modul implementiert die Kommandozeilenschnittstelle für die Aktualisierung
der Geocoding-Informationen für Standorte von Contributors und Organisationen.
"""
import os
import sys
import logging
import argparse
import time
from typing import List, Dict, Any, Optional, Tuple

from github_collector import config
from github_collector.database.database import GitHubDatabase
from github_collector.geocoding.geocoding_service import GeocodingService
from github_collector.ui.stats import show_geocoding_stats_before, show_geocoding_stats_after
from github_collector.utils.logging_config import get_geocoding_logger

# Konfiguriere Logging
logger = get_geocoding_logger()


def parse_arguments() -> argparse.Namespace:
    """
    Parse Kommandozeilenargumente.
    
    Returns:
        Geparste Argumente
    """
    parser = argparse.ArgumentParser(description="Aktualisiere Geocoding-Informationen für Standorte")
    
    # Datenbankoptionen
    parser.add_argument("--db-path", help="Pfad zur SQLite-Datenbankdatei")
    
    # Geocoding-Optionen
    parser.add_argument("--cache-file", default="geocoding_cache.json",
                      help="Pfad zur Geocoding-Cache-Datei (Standard: geocoding_cache.json)")
    parser.add_argument("--user-agent", default="GitHub-Data-Collector",
                      help="User-Agent für Nominatim (Standard: GitHub-Data-Collector)")
    
    # Aktualisierungsoptionen
    parser.add_argument("--contributors", action="store_true",
                      help="Nur Contributors aktualisieren")
    parser.add_argument("--organizations", action="store_true",
                      help="Nur Organisationen aktualisieren")
    parser.add_argument("--limit", type=int,
                      help="Maximale Anzahl zu aktualisierender Einträge")
    parser.add_argument("--force", action="store_true",
                      help="Auch Einträge mit vorhandenen Ländercodes aktualisieren")
    
    return parser.parse_args()


def update_contributors(db: GitHubDatabase, geocoder: GeocodingService, 
                      limit: Optional[int] = None, force: bool = False) -> int:
    """
    Aktualisiere Geocoding-Informationen für Contributors.
    
    Args:
        db: Datenbankverbindung
        geocoder: Geocoding-Service
        limit: Maximale Anzahl zu aktualisierender Contributors
        force: Auch Contributors mit vorhandenen Ländercodes aktualisieren
        
    Returns:
        Anzahl der aktualisierten Contributors
    """
    # Hole Contributors ohne Ländercode oder mit force=True
    if force:
        contributors = db.get_contributors(limit=limit)
        logger.info(f"{len(contributors)} Contributors gefunden (mit force=True)")
    else:
        contributors = db.get_contributors_without_country_code(limit=limit)
        logger.info(f"{len(contributors)} Contributors ohne Ländercode gefunden")
    
    # Zähle Contributors mit Standort
    contributors_with_location = [c for c in contributors if c.location]
    logger.info(f"{len(contributors_with_location)} Contributors mit Standortangabe")
    
    # Aktualisiere Geocoding-Informationen
    updated_count = 0
    for i, contributor in enumerate(contributors_with_location):
        try:
            # Überspringe Contributors ohne Standort
            if not contributor.location:
                continue
            
            # Geocodiere den Standort
            geocoding_result = geocoder.geocode(contributor.location)
            
            if geocoding_result:
                # Erstelle ein Dictionary mit den aktualisierten Informationen
                update_data = {
                    "login": contributor.login,
                    "country_code": geocoding_result.get("country_code"),
                    "country_name": geocoding_result.get("country_name"),
                    "longitude": geocoding_result.get("longitude"),
                    "latitude": geocoding_result.get("latitude")
                }
                
                # Aktualisiere den Contributor in der Datenbank
                db.update_contributor(contributor.id, update_data)
                
                # Logge Erfolg
                logger.info(
                    f"Contributor {contributor.login} aktualisiert: "
                    f"Standort '{contributor.location}' -> "
                    f"Land '{geocoding_result.get('country_name')}' ({geocoding_result.get('country_code')}), "
                    f"Koordinaten: {geocoding_result.get('latitude')}, {geocoding_result.get('longitude')}"
                )
                
                updated_count += 1
            else:
                logger.warning(f"Kein Geocoding-Ergebnis für Contributor {contributor.login} mit Standort '{contributor.location}'")
            
            # Warte kurz, um den Geocoding-Service nicht zu überlasten
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung des Contributors {contributor.login}: {e}")
    
    return updated_count


def update_organizations(db: GitHubDatabase, geocoder: GeocodingService, 
                       limit: Optional[int] = None, force: bool = False) -> int:
    """
    Aktualisiere Geocoding-Informationen für Organisationen.
    
    Args:
        db: Datenbankverbindung
        geocoder: Geocoding-Service
        limit: Maximale Anzahl zu aktualisierender Organisationen
        force: Auch Organisationen mit vorhandenen Ländercodes aktualisieren
        
    Returns:
        Anzahl der aktualisierten Organisationen
    """
    # Hole Organisationen ohne Ländercode oder mit force=True
    if force:
        organizations = db.get_organizations(limit=limit)
        logger.info(f"{len(organizations)} Organisationen gefunden (mit force=True)")
    else:
        organizations = db.get_organizations_without_country_code(limit=limit)
        logger.info(f"{len(organizations)} Organisationen ohne Ländercode gefunden")
    
    # Zähle Organisationen mit Standort
    organizations_with_location = [o for o in organizations if o.location]
    logger.info(f"{len(organizations_with_location)} Organisationen mit Standortangabe")
    
    # Aktualisiere Geocoding-Informationen
    updated_count = 0
    for i, organization in enumerate(organizations_with_location):
        try:
            # Überspringe Organisationen ohne Standort
            if not organization.location:
                continue
            
            # Geocodiere den Standort
            geocoding_result = geocoder.geocode(organization.location)
            
            if geocoding_result:
                # Erstelle ein Dictionary mit den aktualisierten Informationen
                update_data = {
                    "login": organization.login,
                    "country_code": geocoding_result.get("country_code"),
                    "country_name": geocoding_result.get("country_name"),
                    "longitude": geocoding_result.get("longitude"),
                    "latitude": geocoding_result.get("latitude")
                }
                
                # Aktualisiere die Organisation in der Datenbank
                db.update_organization(organization.id, update_data)
                
                # Logge Erfolg
                logger.info(
                    f"Organisation {organization.login} aktualisiert: "
                    f"Standort '{organization.location}' -> "
                    f"Land '{geocoding_result.get('country_name')}' ({geocoding_result.get('country_code')}), "
                    f"Koordinaten: {geocoding_result.get('latitude')}, {geocoding_result.get('longitude')}"
                )
                
                updated_count += 1
            else:
                logger.warning(f"Kein Geocoding-Ergebnis für Organisation {organization.login} mit Standort '{organization.location}'")
            
            # Warte kurz, um den Geocoding-Service nicht zu überlasten
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung der Organisation {organization.login}: {e}")
    
    return updated_count


def main() -> int:
    """
    Hauptfunktion für die Aktualisierung der Geocoding-Informationen.
    
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
        db = GitHubDatabase(db_path)
        
        # Initialisiere Geocoding-Service
        cache_file = args.cache_file or config.GEOCODING_CACHE
        geocoder = GeocodingService(cache_file=cache_file, user_agent=args.user_agent)
        
        # Zeige Statistiken vor der Aktualisierung
        show_geocoding_stats_before(db)
        
        # Aktualisiere Contributors und/oder Organisationen
        updated_contributors = 0
        updated_organizations = 0
        
        if args.contributors or not args.organizations:
            updated_contributors = update_contributors(db, geocoder, limit=args.limit, force=args.force)
            logger.info(f"{updated_contributors} Contributors aktualisiert")
        
        if args.organizations or not args.contributors:
            updated_organizations = update_organizations(db, geocoder, limit=args.limit, force=args.force)
            logger.info(f"{updated_organizations} Organisationen aktualisiert")
        
        # Zeige Statistiken nach der Aktualisierung
        show_geocoding_stats_after(db, updated_contributors, updated_organizations)
        
        # Schließe Datenbankverbindung
        db.close()
        
        return 0
    
    except Exception as e:
        logger.exception(f"Fehler bei der Aktualisierung der Geocoding-Informationen: {e}")
        return 1
