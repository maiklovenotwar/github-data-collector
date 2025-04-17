#!/usr/bin/env python3
"""
Skript zur Bereinigung verwaister Owner-Einträge (Contributors und Organisationen).

Dieses Skript identifiziert und entfernt Contributors und Organisationen,
die keine zugehörigen Repositories in der Datenbank haben.
"""
import os
import sys
import logging
import argparse
from typing import Tuple

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))

from github_collector.database.database import GitHubDatabase
from github_collector.database.models import Contributor, Organization, Repository
from github_collector.utils.logging_config import setup_logging
from github_collector import config

# Erstelle einen spezifischen Logger für die Bereinigung
logger = setup_logging(log_file=config.LOG_DIR / "cleanup_orphaned_owners.log")


def cleanup_orphaned_owners(db: GitHubDatabase, dry_run: bool = False) -> Tuple[int, int]:
    """
    Entfernt Owner (Contributors/Organisationen) ohne zugehörige Repositories.
    
    Args:
        db: Datenbankverbindung
        dry_run: Wenn True, werden keine Änderungen vorgenommen (nur Simulation)
        
    Returns:
        Tuple mit Anzahl der entfernten Contributors und Organisationen
    """
    # Finde alle Contributors ohne Repositories
    orphaned_contributors = db.session.query(Contributor).outerjoin(
        Repository, Repository.owner_id == Contributor.id
    ).filter(Repository.id == None).all()
    
    # Finde alle Organisationen ohne Repositories
    orphaned_organizations = db.session.query(Organization).outerjoin(
        Repository, Repository.organization_id == Organization.id
    ).filter(Repository.id == None).all()
    
    orphaned_contributors_count = len(orphaned_contributors)
    orphaned_organizations_count = len(orphaned_organizations)
    
    if orphaned_contributors_count > 0:
        logger.info(f"Gefunden: {orphaned_contributors_count} Contributors ohne Repositories")
        for contributor in orphaned_contributors:
            logger.debug(f"Verwaister Contributor: {contributor.login} (ID: {contributor.id})")
    else:
        logger.info("Keine verwaisten Contributors gefunden")
    
    if orphaned_organizations_count > 0:
        logger.info(f"Gefunden: {orphaned_organizations_count} Organisationen ohne Repositories")
        for organization in orphaned_organizations:
            logger.debug(f"Verwaiste Organisation: {organization.login} (ID: {organization.id})")
    else:
        logger.info("Keine verwaisten Organisationen gefunden")
    
    if not dry_run:
        # Lösche verwaiste Einträge
        for contributor in orphaned_contributors:
            db.session.delete(contributor)
        
        for organization in orphaned_organizations:
            db.session.delete(organization)
        
        db.session.commit()
        logger.info(f"Bereinigung abgeschlossen: {orphaned_contributors_count} Contributors und {orphaned_organizations_count} Organisationen ohne Repositories entfernt")
    else:
        logger.info(f"Dry-Run: Keine Änderungen vorgenommen. {orphaned_contributors_count} Contributors und {orphaned_organizations_count} Organisationen würden entfernt werden")
    
    return orphaned_contributors_count, orphaned_organizations_count


def parse_arguments():
    """Parse Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(description="Bereinigt verwaiste Owner-Einträge in der Datenbank")
    
    parser.add_argument(
        "--db-path", 
        help="Pfad zur SQLite-Datenbank (Standard: Umgebungsvariable DATABASE_URL oder github_data.db)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulationsmodus: Zeigt an, welche Einträge entfernt würden, ohne Änderungen vorzunehmen"
    )
    
    return parser.parse_args()


def main():
    """Hauptfunktion."""
    args = parse_arguments()
    
    # Datenbankpfad
    db_path = args.db_path or os.environ.get("DATABASE_URL", "github_data.db")
    if not db_path.startswith("sqlite:///"):
        db_path = f"sqlite:///{db_path}"
    
    # Initialisiere Datenbank
    db = GitHubDatabase(db_path)
    
    try:
        # Führe Bereinigung durch
        contributors_removed, organizations_removed = cleanup_orphaned_owners(db, args.dry_run)
        
        # Zeige Zusammenfassung
        total_removed = contributors_removed + organizations_removed
        if args.dry_run:
            print(f"\nSimulationsmodus: {total_removed} verwaiste Owner-Einträge gefunden")
            print(f"- {contributors_removed} Contributors ohne Repositories")
            print(f"- {organizations_removed} Organisationen ohne Repositories")
            print("\nKeine Änderungen vorgenommen. Verwende den Befehl ohne --dry-run, um die Einträge zu entfernen.")
        else:
            print(f"\nBereinigung abgeschlossen: {total_removed} verwaiste Owner-Einträge entfernt")
            print(f"- {contributors_removed} Contributors ohne Repositories")
            print(f"- {organizations_removed} Organisationen ohne Repositories")
    
    finally:
        # Schließe Datenbankverbindung
        db.close()


if __name__ == "__main__":
    main()
