#!/usr/bin/env python3
"""
Skript zur Aktualisierung der Geocoding-Informationen für Standorte.
"""
import os
import sys
import logging
import argparse
import time
from typing import List, Dict, Any, Optional

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import GitHubDatabase
from github_collector.geocoding.geocoding_service import GeocodingService

# Konfiguriere Logging
from github_collector.utils.logging_config import setup_logging

logger = setup_logging(log_file="geocoding.log")


def parse_arguments():
    """Parse Kommandozeilenargumente."""
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
    # Hole Contributors aus der Datenbank
    contributors = db.session.query(db.session.get_bind().metadata.tables['contributors']).all()
    
    # Filtere Contributors nach Bedarf
    if not force:
        contributors = [c for c in contributors if c.location and not c.country_code]
    else:
        contributors = [c for c in contributors if c.location]
    
    # Begrenze die Anzahl, falls angegeben
    if limit:
        contributors = contributors[:limit]
    
    logger.info(f"Aktualisiere Geocoding-Informationen für {len(contributors)} Contributors")
    
    updated_count = 0
    
    for contributor in contributors:
        try:
            # Konvertiere den Contributor in ein Dictionary für die Aktualisierung
            contributor_dict = {
                "id": contributor.id,
                "login": contributor.login,
                "location": contributor.location,
                "country_code": contributor.country_code,
                "region": contributor.region
            }
            
            # Aktualisiere die Standortdaten
            updated_contributor = geocoder.update_location_data(contributor_dict)
            
            # Aktualisiere die Datenbank, falls sich etwas geändert hat
            if (updated_contributor.get("country_code") != contributor.country_code or
                updated_contributor.get("region") != contributor.region):
                
                # Aktualisiere den Contributor in der Datenbank
                db.session.query(db.session.get_bind().metadata.tables['contributors']).filter_by(id=contributor.id).update({
                    "country_code": updated_contributor.get("country_code", ""),
                    "region": updated_contributor.get("region", "")
                })
                
                db.session.commit()
                updated_count += 1
                
                logger.info(
                    f"Contributor {contributor.login} aktualisiert: "
                    f"Standort='{contributor.location}', "
                    f"Land='{updated_contributor.get('country_code', '')}', "
                    f"Region='{updated_contributor.get('region', '')}'"
                )
            
            # Kurze Pause, um die Geocoding-API nicht zu überlasten
            time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung des Contributors {contributor.login}: {e}")
            db.session.rollback()
    
    logger.info(f"{updated_count} Contributors aktualisiert")
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
    # Hole Organisationen aus der Datenbank
    organizations = db.session.query(db.session.get_bind().metadata.tables['organizations']).all()
    
    # Filtere Organisationen nach Bedarf
    if not force:
        organizations = [o for o in organizations if o.location and not o.country_code]
    else:
        organizations = [o for o in organizations if o.location]
    
    # Begrenze die Anzahl, falls angegeben
    if limit:
        organizations = organizations[:limit]
    
    logger.info(f"Aktualisiere Geocoding-Informationen für {len(organizations)} Organisationen")
    
    updated_count = 0
    
    for organization in organizations:
        try:
            # Konvertiere die Organisation in ein Dictionary für die Aktualisierung
            organization_dict = {
                "id": organization.id,
                "login": organization.login,
                "location": organization.location,
                "country_code": organization.country_code,
                "region": organization.region
            }
            
            # Aktualisiere die Standortdaten
            updated_organization = geocoder.update_location_data(organization_dict)
            
            # Aktualisiere die Datenbank, falls sich etwas geändert hat
            if (updated_organization.get("country_code") != organization.country_code or
                updated_organization.get("region") != organization.region):
                
                # Aktualisiere die Organisation in der Datenbank
                db.session.query(db.session.get_bind().metadata.tables['organizations']).filter_by(id=organization.id).update({
                    "country_code": updated_organization.get("country_code", ""),
                    "region": updated_organization.get("region", "")
                })
                
                db.session.commit()
                updated_count += 1
                
                logger.info(
                    f"Organisation {organization.login} aktualisiert: "
                    f"Standort='{organization.location}', "
                    f"Land='{updated_organization.get('country_code', '')}', "
                    f"Region='{updated_organization.get('region', '')}'"
                )
            
            # Kurze Pause, um die Geocoding-API nicht zu überlasten
            time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung der Organisation {organization.login}: {e}")
            db.session.rollback()
    
    logger.info(f"{updated_count} Organisationen aktualisiert")
    return updated_count


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
    
    # Initialisiere Geocoding-Service
    geocoder = GeocodingService(
        cache_file=args.cache_file,
        user_agent=args.user_agent
    )
    
    try:
        # Zeige Statistiken vor der Aktualisierung
        contributor_stats = db.get_contributor_location_stats()
        org_stats = db.get_organization_location_stats()
        
        print("\n=== Statistiken vor der Aktualisierung ===")
        print(f"Contributors mit Standort: {contributor_stats['with_location']} von {contributor_stats['total']} ({contributor_stats['location_percentage']:.1f}%)")
        print(f"Contributors mit Ländercode: {contributor_stats['with_country_code']} von {contributor_stats['total']} ({contributor_stats['country_code_percentage']:.1f}%)")
        print(f"Organisationen mit Standort: {org_stats['with_location']} von {org_stats['total']} ({org_stats['location_percentage']:.1f}%)")
        print(f"Organisationen mit Ländercode: {org_stats['with_country_code']} von {org_stats['total']} ({org_stats['country_code_percentage']:.1f}%)")
        
        # Aktualisiere Contributors und/oder Organisationen
        updated_contributors = 0
        updated_organizations = 0
        
        if args.contributors or not args.organizations:
            updated_contributors = update_contributors(
                db=db,
                geocoder=geocoder,
                limit=args.limit,
                force=args.force
            )
        
        if args.organizations or not args.contributors:
            updated_organizations = update_organizations(
                db=db,
                geocoder=geocoder,
                limit=args.limit,
                force=args.force
            )
        
        # Zeige Statistiken nach der Aktualisierung
        contributor_stats = db.get_contributor_location_stats()
        org_stats = db.get_organization_location_stats()
        
        print("\n=== Statistiken nach der Aktualisierung ===")
        print(f"Contributors mit Standort: {contributor_stats['with_location']} von {contributor_stats['total']} ({contributor_stats['location_percentage']:.1f}%)")
        print(f"Contributors mit Ländercode: {contributor_stats['with_country_code']} von {contributor_stats['total']} ({contributor_stats['country_code_percentage']:.1f}%)")
        print(f"Organisationen mit Standort: {org_stats['with_location']} von {org_stats['total']} ({org_stats['location_percentage']:.1f}%)")
        print(f"Organisationen mit Ländercode: {org_stats['with_country_code']} von {org_stats['total']} ({org_stats['country_code_percentage']:.1f}%)")
        
        print(f"\nInsgesamt {updated_contributors} Contributors und {updated_organizations} Organisationen aktualisiert.")
    
    finally:
        # Speichere den Geocoding-Cache
        geocoder.cache.save()
        
        # Schließe Datenbankverbindung
        db.close()


if __name__ == "__main__":
    main()
