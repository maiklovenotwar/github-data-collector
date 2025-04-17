"""
Owner-Verarbeitungsmodul für GitHub Data Collector.

Dieses Modul enthält Funktionen und Klassen zur Verarbeitung von
Owner-Metadaten (Contributor und Organization).
"""

import logging
from typing import Dict, List, Any, Optional, Set

from github_collector.api.github_api import GitHubAPI
from github_collector.database.database import GitHubDatabase
from github_collector.utils.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class OwnerProcessor:
    """
    Verarbeitet Owner-Metadaten (Contributor und Organization).
    
    Diese Klasse kapselt die Logik zur Verarbeitung von Owner-Metadaten,
    einschließlich Caching, Batch-Verarbeitung und Performance-Tracking.
    """
    
    def __init__(self, api: GitHubAPI, db: GitHubDatabase, 
                 performance_tracker: Optional[PerformanceTracker] = None):
        """
        Initialisiert den Owner-Processor.
        
        Args:
            api: GitHub API Client
            db: Datenbankverbindung
            performance_tracker: Performance-Tracker (optional)
        """
        self.api = api
        self.db = db
        self.performance_tracker = performance_tracker
        
        # Caches für Owner-Daten
        self._org_cache: Dict[str, Dict[str, Any]] = {}
        self._contributor_cache: Dict[str, Dict[str, Any]] = {}
        
        # Sets für die Erkennung von Duplikaten im aktuellen Batch
        self._batch_owners: Set[str] = set()
        
        # Bekannte Owner (bereits in der Datenbank)
        self._known_owners: Set[str] = set()
        
        # Initialisiere die bekannten Owner aus der Datenbank
        self._preload_known_owners()
    
    def reset_batch_tracking(self) -> None:
        """Setzt die Batch-Tracking-Daten zurück."""
        self._batch_owners = set()
        
    def _preload_known_owners(self) -> None:
        """
        Lädt bekannte Owner aus der Datenbank, um redundante API-Aufrufe zu vermeiden.
        Diese Methode wird beim Initialisieren des OwnerProcessors aufgerufen.
        """
        try:
            # Lade bekannte Contributors
            contributor_logins = self.db.get_all_contributor_logins()
            for login in contributor_logins:
                self._known_owners.add(login)
                
            # Lade bekannte Organisationen
            org_logins = self.db.get_all_organization_logins()
            for login in org_logins:
                self._known_owners.add(login)
                
            logger.info(f"Vorgeladen: {len(self._known_owners)} bekannte Owner (Contributors und Organisationen)")
        except Exception as e:
            logger.warning(f"Fehler beim Vorladen bekannter Owner: {e}")
            # Fehler beim Vorladen sollten den Prozess nicht stoppen
    
    def process_organization(self, owner_login: str, owner_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeitet Organisationsdaten.
        
        Args:
            owner_login: Login-Name der Organisation
            owner_data: Basis-Daten der Organisation
            
        Returns:
            Erweiterte Organisationsdaten
        """
        # Prüfe, ob die Organisation bereits im aktuellen Batch verarbeitet wurde
        if owner_login in self._batch_owners:
            if self.performance_tracker:
                self.performance_tracker.record_duplicate_owner_in_batch()
            logger.debug(f"Organisation {owner_login} wurde bereits im aktuellen Batch verarbeitet")
        else:
            self._batch_owners.add(owner_login)
        
        # Prüfe, ob die Organisation bereits in den bekannten Ownern ist (vorgeladene Datenbank)
        if owner_login in self._known_owners:
            if self.performance_tracker:
                self.performance_tracker.record_known_owner_requested()
            logger.debug(f"Organisation {owner_login} ist bereits als bekannter Owner vorgeladen")
            # Prüfe, ob die Organisation bereits im Cache ist
            if owner_login in self._org_cache:
                org_details = self._org_cache[owner_login]
                logger.debug(f"Organisationsdaten für {owner_login} aus Cache verwendet")
                return org_details
            # Wenn nicht im Cache, aber bekannt, verwende die Basis-Daten
            return owner_data
        
        # Prüfe, ob die Organisation bereits in der Datenbank existiert (Fallback, falls nicht vorgeladen)
        org_exists = self.db.check_organization_exists(owner_login)
        if org_exists:
            if self.performance_tracker:
                self.performance_tracker.record_known_owner_requested()
            logger.debug(f"Organisation {owner_login} existiert bereits in der Datenbank")
            self._known_owners.add(owner_login)  # Für zukünftige Abfragen merken
            return owner_data
        
        # Prüfe, ob die Organisation bereits im Cache ist
        if owner_login in self._org_cache:
            org_details = self._org_cache[owner_login]
            logger.debug(f"Organisationsdaten für {owner_login} aus Cache verwendet")
            return org_details
        
        try:
            # Hole Organisationsdaten von der API und speichere sie im Cache
            org_details = self.api.get_organization(owner_login)
            if org_details:
                self._org_cache[owner_login] = org_details
                logger.debug(f"Erweiterte Organisationsdaten für {owner_login} abgerufen und gecacht")
                
                # Füge die Organisation in die Datenbank ein oder aktualisiere sie
                org = self.db.insert_organization(org_details)
                
                # Erfasse neue Organisation für Performance-Tracking
                if self.performance_tracker:
                    self.performance_tracker.record_new_owner('organizations')
                
                # Füge zu bekannten Ownern hinzu
                self._known_owners.add(owner_login)
                
                return org_details
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen erweiterter Organisationsdaten für {owner_login}: {e}")
        
        # Fallback: Verwende die Basis-Daten, wenn keine erweiterten Daten verfügbar sind
        return owner_data
    
    def process_contributor(self, owner_login: str) -> None:
        """
        Verarbeitet Contributor-Metadaten.
        
        Args:
            owner_login: Login-Name des Contributors
        """
        # Prüfe, ob der Contributor bereits im aktuellen Batch verarbeitet wurde
        if owner_login in self._batch_owners:
            if self.performance_tracker:
                self.performance_tracker.record_duplicate_owner_in_batch()
            logger.debug(f"Contributor {owner_login} wurde bereits im aktuellen Batch verarbeitet")
            return
        else:
            self._batch_owners.add(owner_login)
        
        # Prüfe, ob der Contributor bereits in den bekannten Ownern ist (vorgeladene Datenbank)
        if owner_login in self._known_owners:
            if self.performance_tracker:
                self.performance_tracker.record_known_owner_requested()
            logger.debug(f"Contributor {owner_login} ist bereits als bekannter Owner vorgeladen")
            return
        
        # Prüfe, ob der Contributor bereits in der Datenbank existiert (Fallback, falls nicht vorgeladen)
        contributor_exists = self.db.check_contributor_exists(owner_login)
        if contributor_exists:
            if self.performance_tracker:
                self.performance_tracker.record_known_owner_requested()
            logger.debug(f"Contributor {owner_login} existiert bereits in der Datenbank")
            self._known_owners.add(owner_login)  # Für zukünftige Abfragen merken
            return
        
        # Prüfe, ob der Contributor bereits im Cache ist
        if owner_login in self._contributor_cache:
            logger.debug(f"Contributor-Daten für {owner_login} aus Cache verwendet")
            return
        
        try:
            # Hole Contributor-Daten von der API
            contributor_data = self.api.get_contributor(owner_login)
            if contributor_data:
                # Speichere im Cache
                self._contributor_cache[owner_login] = contributor_data
                # Füge in die Datenbank ein oder aktualisiere
                self.db.insert_contributor(contributor_data)
                logger.debug(f"Erweiterte Contributor-Metadaten für {owner_login} abgerufen und gecacht")
                
                # Erfasse neuen Contributor für Performance-Tracking
                if self.performance_tracker:
                    self.performance_tracker.record_new_owner('contributors')
                
                # Füge zu bekannten Ownern hinzu
                self._known_owners.add(owner_login)
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen von Contributor-Metadaten für {owner_login}: {e}")
    
    def process_contributors_batch(self, contributor_logins: List[str]) -> None:
        """
        Verarbeitet mehrere Contributors in einem Batch.
        
        Args:
            contributor_logins: Liste der GitHub-Benutzernamen der Contributors
        """
        if not contributor_logins:
            return
            
        # Entferne Duplikate
        unique_logins = list(set(contributor_logins))
        logger.info(f"Verarbeite Batch mit {len(unique_logins)} einzigartigen Contributors (von {len(contributor_logins)} gesamt)")
        
        # Filtere bereits bekannte Contributors
        unknown_logins = [login for login in unique_logins if login not in self._known_owners]
        
        if len(unknown_logins) < len(unique_logins):
            skipped_count = len(unique_logins) - len(unknown_logins)
            logger.info(f"Überspringe {skipped_count} bereits bekannte Contributors")
            if self.performance_tracker:
                for _ in range(skipped_count):
                    self.performance_tracker.record_known_owner_requested()
        
        # Verarbeite die unbekannten Contributors
        if unknown_logins:
            logger.info(f"Hole Metadaten für {len(unknown_logins)} unbekannte Contributors")
            
            # Überwache das Rate-Limit vor dem Batch
            rate_limit_info = self.api.monitor_rate_limit(threshold_percent=15)
            if rate_limit_info.get('has_critical', False):
                logger.warning("Kritisches Rate-Limit vor Contributor-Batch-Verarbeitung erkannt")
            
            # Verarbeite jeden unbekannten Contributor
            for login in unknown_logins:
                self.process_contributor(login)
            
            # Überwache das Rate-Limit nach dem Batch
            rate_limit_info = self.api.monitor_rate_limit(threshold_percent=10)
            if rate_limit_info.get('has_warnings', False):
                for warning in rate_limit_info.get('warnings', []):
                    logger.warning(warning)
    
    def process_repository_owner(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeitet den Owner eines Repositories.
        
        Args:
            repo_data: Repository-Daten aus der GitHub API
            
        Returns:
            Aktualisierte Repository-Daten mit erweiterten Owner-Informationen
        """
        # Prüfe, ob das Repository einen Owner hat
        owner_data = repo_data.get('owner', {})
        owner_login = owner_data.get('login') if owner_data else None
        owner_type = owner_data.get('type') if owner_data else None
        
        if not owner_login or not owner_type:
            logger.warning(f"Repository {repo_data.get('full_name')} hat keine gültigen Owner-Daten")
            return repo_data
        
        # Verarbeite Organisationsdaten, wenn der Owner eine Organisation ist
        if owner_type == 'Organization':
            if 'organization' not in repo_data or not repo_data['organization']:
                # Setze die Organisationsdaten basierend auf dem Eigentümer
                repo_data['organization'] = owner_data
                logger.debug(f"Organisationsdaten aus Owner-Feld für {repo_data.get('full_name')} hinzugefügt")
                
                # Hole erweiterte Organisationsdaten
                org_details = self.process_organization(owner_login, owner_data)
                repo_data['organization'] = org_details
        
        # Verarbeite Contributor-Metadaten, wenn der Owner ein User ist
        elif owner_type == 'User':
            self.process_contributor(owner_login)
        
        return repo_data
