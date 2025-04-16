"""
Statistikanzeige für den GitHub Data Collector.

Dieses Modul bietet Funktionen zur Anzeige von Datenbankstatistiken und
Fortschrittsinformationen für die Geocoding-Aktualisierung.
"""
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def show_database_stats(db) -> None:
    """
    Zeigt Statistiken über die Datenbank an.
    
    Args:
        db: Datenbankverbindung mit entsprechenden Methoden zur Statistikabfrage
    """
    print("\n=== Datenbankstatistiken ===")
    print(f"Repositories: {db.get_repository_count()}")
    print(f"Contributors: {db.get_contributor_count()}")
    print(f"Organisationen: {db.get_organization_count()}")
    
    # Zeige Sprachstatistiken an, falls verfügbar
    try:
        languages = db.get_language_statistics()
        if languages:
            print("\nTop-Sprachen:")
            for lang, count in languages[:10]:
                print(f"  {lang}: {count} Repositories")
    except Exception as e:
        logger.debug(f"Konnte keine Sprachstatistiken abrufen: {e}")
    
    # Zeige Erstellungsdatumsbereich an
    try:
        date_range = db.get_repository_date_range()
        if date_range:
            print(f"\nRepository-Datumsbereich: {date_range[0]} bis {date_range[1]}")
    except Exception as e:
        logger.debug(f"Konnte keinen Repository-Datumsbereich abrufen: {e}")
        
    # Zeige Standort- und Ländercode-Statistiken für Contributors an
    try:
        contributor_stats = db.get_contributor_location_stats()
        if contributor_stats:
            print("\nContributor-Standortstatistiken:")
            print(f"  Gesamtzahl Contributors: {contributor_stats['total']}")
            print(f"  Contributors mit Standort: {contributor_stats['with_location']} ({contributor_stats['location_percentage']:.1f}%)")
            print(f"  Contributors mit Ländercode: {contributor_stats['with_country_code']} ({contributor_stats['country_code_percentage']:.1f}%)")
            if contributor_stats['with_location'] > 0:
                print(f"  Ländercode-Auflösungsrate: {contributor_stats['country_code_from_location_percentage']:.1f}% der Contributors mit Standort")
    except Exception as e:
        logger.debug(f"Konnte keine Contributor-Standortstatistiken abrufen: {e}")
        
    # Zeige Standort- und Ländercode-Statistiken für Organisationen an
    try:
        org_stats = db.get_organization_location_stats()
        if org_stats:
            print("\nOrganisations-Standortstatistiken:")
            print(f"  Gesamtzahl Organisationen: {org_stats['total']}")
            print(f"  Organisationen mit Standort: {org_stats['with_location']} ({org_stats['location_percentage']:.1f}%)")
            print(f"  Organisationen mit Ländercode: {org_stats['with_country_code']} ({org_stats['country_code_percentage']:.1f}%)")
            if org_stats['with_location'] > 0:
                print(f"  Ländercode-Auflösungsrate: {org_stats['country_code_from_location_percentage']:.1f}% der Organisationen mit Standort")
    except Exception as e:
        logger.debug(f"Konnte keine Organisations-Standortstatistiken abrufen: {e}")


def show_geocoding_stats_before(contributor_stats: Dict, org_stats: Dict) -> None:
    """
    Zeigt Statistiken vor der Geocoding-Aktualisierung an.
    
    Args:
        contributor_stats: Statistiken zu Contributors
        org_stats: Statistiken zu Organisationen
    """
    print("\n=== Statistiken vor der Aktualisierung ===")
    print(f"Contributors mit Standort: {contributor_stats['with_location']} von {contributor_stats['total']} ({contributor_stats['location_percentage']:.1f}%)")
    print(f"Contributors mit Ländercode: {contributor_stats['with_country_code']} von {contributor_stats['total']} ({contributor_stats['country_code_percentage']:.1f}%)")
    print(f"Organisationen mit Standort: {org_stats['with_location']} von {org_stats['total']} ({org_stats['location_percentage']:.1f}%)")
    print(f"Organisationen mit Ländercode: {org_stats['with_country_code']} von {org_stats['total']} ({org_stats['country_code_percentage']:.1f}%)")


def show_geocoding_stats_after(contributor_stats: Dict, org_stats: Dict, 
                              updated_contributors: int, updated_organizations: int) -> None:
    """
    Zeigt Statistiken nach der Geocoding-Aktualisierung an.
    
    Args:
        contributor_stats: Statistiken zu Contributors
        org_stats: Statistiken zu Organisationen
        updated_contributors: Anzahl der aktualisierten Contributors
        updated_organizations: Anzahl der aktualisierten Organisationen
    """
    print("\n=== Statistiken nach der Aktualisierung ===")
    print(f"Contributors mit Standort: {contributor_stats['with_location']} von {contributor_stats['total']} ({contributor_stats['location_percentage']:.1f}%)")
    print(f"Contributors mit Ländercode: {contributor_stats['with_country_code']} von {contributor_stats['total']} ({contributor_stats['country_code_percentage']:.1f}%)")
    print(f"Organisationen mit Standort: {org_stats['with_location']} von {org_stats['total']} ({org_stats['location_percentage']:.1f}%)")
    print(f"Organisationen mit Ländercode: {org_stats['with_country_code']} von {org_stats['total']} ({org_stats['country_code_percentage']:.1f}%)")
    
    print(f"\nInsgesamt {updated_contributors} Contributors und {updated_organizations} Organisationen aktualisiert.")
