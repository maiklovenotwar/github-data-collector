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
import pycountry
import re

# Konfiguriere Logging
logger = get_geocoding_logger()

# === Utility Functions and Constants for Robust Geocoding ===
NON_GEO_LOCATIONS = {
    "earth", "remote", "worldwide", "internet", "decentralized", "nowhere", "the moon", "metaverse", "cyberspace", "cloud",
    "virtual", "everywhere", "anywhere"
}

def is_valid_country_code(code: Optional[str]) -> bool:
    if not code or not isinstance(code, str):
        return False
    if not re.match(r"^[A-Za-z]{2}$", code):
        return False
    try:
        return pycountry.countries.get(alpha_2=code.upper()) is not None
    except Exception as e:
        logger.error(f"Error validating country code '{code}' with pycountry: {e}")
        return False

def is_non_geographic_location(location: str, non_geo_terms: set) -> bool:
    if not location:
        return False
    location_lower = location.lower().strip()
    if location_lower in non_geo_terms:
        return True
    # Check for exact matches in comma/space/pipe separated parts
    parts = set(re.split(r'[\s,|/]+', location_lower))
    return bool(parts.intersection(non_geo_terms))


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
    
    parser.add_argument("--clear-cache", action="store_true",
                      help="Leere den Geocoding-Cache vor der Aktualisierung")
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
            
            # Filter non-geographic locations
            if is_non_geographic_location(contributor.location, NON_GEO_LOCATIONS):
                logger.info(f"Überspringe non-geographischen Standort '{contributor.location}' für Contributor {contributor.login}")
                continue
            
            # Geocodiere den Standort
            geocoding_result = geocoder.geocode(contributor.location)
            
            if geocoding_result:
                # Validate output
                country_code = geocoding_result.get("country_code")
                if not is_valid_country_code(country_code):
                    logger.warning(f"Ungültiger Ländercode '{country_code}' für Contributor {contributor.login} mit Standort '{contributor.location}'")
                    continue
                
                # Erstelle ein Dictionary mit den aktualisierten Informationen
                update_data = {
                    "login": contributor.login,
                    "country_code": country_code,
                    "country_name": geocoding_result.get("country_name"),
                    "longitude": geocoding_result.get("longitude"),
                    "latitude": geocoding_result.get("latitude")
                }
                
                # Aktualisiere den Contributor in der Datenbank
                db.update_contributor(contributor, update_data)
                
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
    organizations = db.get_organizations_without_country_code(limit=limit)
    if force:
        logger.info(f"{len(organizations)} Organisationen gefunden (mit force=True)")
    else:
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
            
            # Filter non-geographic locations
            if is_non_geographic_location(organization.location, NON_GEO_LOCATIONS):
                logger.info(f"Überspringe non-geographischen Standort '{organization.location}' für Organisation {organization.login}")
                continue
            
            # Geocodiere den Standort
            geocoding_result = geocoder.geocode(organization.location)
            
            if geocoding_result:
                # Validate output
                country_code = geocoding_result.get("country_code")
                if not is_valid_country_code(country_code):
                    logger.warning(f"Ungültiger Ländercode '{country_code}' für Organisation {organization.login} mit Standort '{organization.location}'")
                    continue
                
                # Erstelle ein Dictionary mit den aktualisierten Informationen
                update_data = {
                    "login": organization.login,
                    "country_code": country_code,
                    "country_name": geocoding_result.get("country_name"),
                    "longitude": geocoding_result.get("longitude"),
                    "latitude": geocoding_result.get("latitude")
                }
                
                # Aktualisiere die Organisation in der Datenbank
                db.update_organization(organization, update_data)
                
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
    try:
        import os
        args = parse_arguments()
        db_path = args.db_path or os.environ.get("DATABASE_URL") or config.DEFAULT_DB_PATH
        # Falls es noch keine SQLAlchemy-URL ist, baue eine daraus
        if isinstance(db_path, str) and not (db_path.startswith("sqlite:///") or "://" in db_path):
            db_path = f"sqlite:///{db_path}"
        db = GitHubDatabase(str(db_path))
        cache_file = args.cache_file
        user_agent = args.user_agent
        geocoder = GeocodingService(cache_file=cache_file, user_agent=user_agent)

        # Optionally clear the geocoding cache if requested
        if getattr(args, "clear_cache", False):
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Geocoding-Cache '{cache_file}' wurde gelöscht.")
            # Also clear in-memory cache if needed
            if hasattr(geocoder, "cache"):
                geocoder.cache.cache = {}

        # Statistiken vor der Aktualisierung ermitteln
        contributor_stats_before = db.get_contributor_location_stats()
        org_stats_before = db.get_organization_location_stats()
        show_geocoding_stats_before(contributor_stats_before, org_stats_before)
        
        # Aktualisiere Contributors und/oder Organisationen
        updated_contributors = 0
        updated_organizations = 0
        
        if args.contributors or not args.organizations:
            updated_contributors = update_contributors(db, geocoder, limit=args.limit, force=args.force)
            logger.info(f"{updated_contributors} Contributors aktualisiert")
        
        if args.organizations or not args.contributors:
            updated_organizations = update_organizations(db, geocoder, limit=args.limit, force=args.force)
            logger.info(f"{updated_organizations} Organisationen aktualisiert")
        
        # Statistiken nach der Aktualisierung ermitteln
        contributor_stats_after = db.get_contributor_location_stats()
        org_stats_after = db.get_organization_location_stats()
        show_geocoding_stats_after(contributor_stats_after, org_stats_after, updated_contributors, updated_organizations)
        
        # Schließe Datenbankverbindung
        db.close()
        
        return 0
    
    except Exception as e:
        logger.exception(f"Fehler bei der Aktualisierung der Geocoding-Informationen: {e}")
        return 1
