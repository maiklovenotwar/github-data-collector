"""Datenbankoperationen für GitHub-Daten."""

import os
import logging
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime

from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Repository, Contributor, Organization

logger = logging.getLogger(__name__)

def init_db(database_url: str, reset_db: bool = False) -> sessionmaker:
    """Datenbank initialisieren.
    
    Args:
        database_url: Datenbank-URL
        reset_db: Wenn True, Datenbank zurücksetzen (für SQLite)
    """
    # Für SQLite-Datenbanken: Prüfen, ob die Datei existiert und löschen, wenn reset_db True ist
    if reset_db and database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            try:
                logger.info(f"Entferne bestehende Datenbankdatei: {db_path}")
                os.remove(db_path)
                logger.info("Bestehende Datenbankdatei erfolgreich entfernt")
            except Exception as e:
                logger.error(f"Fehler beim Entfernen der Datenbankdatei: {e}")
    
    # Engine erstellen und Tabellen erstellen
    engine = create_engine(database_url)
    logger.info("Erstelle Datenbanktabellen, falls sie nicht existieren...")
    Base.metadata.create_all(engine)
    
    # Session-Factory zurückgeben
    return sessionmaker(bind=engine)

class GitHubDatabase:
    """
    Hauptschnittstelle für Datenbankoperationen.
    
    Diese Klasse bietet Methoden zum Einfügen, Abfragen und Aktualisieren
    von GitHub-Daten in der Datenbank.
    """
    
    def __init__(self, db_path: str = None):
        """
        Datenbankverbindung initialisieren.
        
        Args:
            db_path: Vollständige SQLAlchemy-URL (z.B. mysql+pymysql://...) oder None für In-Memory-DB
        """
        if db_path:
            self.db_url = db_path  # Keine Manipulation, akzeptiere jede SQLAlchemy-URL
        else:
            self.db_url = 'sqlite:///:memory:'
        self.Session = init_db(self.db_url)
        self.session = self.Session()
        logger.info(f"Datenbankverbindung initialisiert: {self.db_url}")
    
    def close(self):
        """Datenbankverbindung schließen."""
        if self.session:
            self.session.close()
            logger.info("Datenbankverbindung geschlossen")
    
    def insert_repository(self, repo_data: dict) -> Repository:
        """
        Repository in die Datenbank einfügen.
        
        Args:
            repo_data: Repository-Daten von der GitHub API
            
        Returns:
            Repository-Objekt
        """
        # Prüfen, ob Repository bereits existiert
        existing = self.session.query(Repository).filter_by(id=repo_data['id']).first()
        if existing:
            logger.debug(f"Repository {repo_data['full_name']} existiert bereits, wird aktualisiert")
            return self.update_repository(existing, repo_data)
        
        # Eigentümer einfügen oder abrufen
        owner_data = repo_data.get('owner', {})
        if owner_data:
            owner = self.insert_contributor(owner_data)
        else:
            logger.warning(f"Repository {repo_data['full_name']} hat keinen Eigentümer")
            return None
        
        # Organisation einfügen oder abrufen, falls vorhanden
        organization = None
        if 'organization' in repo_data and repo_data['organization']:
            organization = self.insert_organization(repo_data['organization'])
        
        # Repository erstellen
        repo = Repository(
            id=repo_data['id'],
            name=repo_data['name'],
            full_name=repo_data['full_name'],
            owner_id=owner.id,
            organization_id=organization.id if organization else None,
            description=repo_data.get('description'),
            homepage=repo_data.get('homepage'),
            language=repo_data.get('language'),
            private=repo_data.get('private', False),
            fork=repo_data.get('fork', False),
            default_branch=repo_data.get('default_branch'),
            size=repo_data.get('size'),
            stargazers_count=repo_data.get('stargazers_count', 0),
            watchers_count=repo_data.get('watchers_count', 0),
            forks_count=repo_data.get('forks_count', 0),
            open_issues_count=repo_data.get('open_issues_count', 0),
            contributors_count=repo_data.get('contributors_count'),
            commits_count=repo_data.get('commits_count'),
            pull_requests_count=repo_data.get('pull_requests_count'),
            created_at=self._parse_datetime(repo_data.get('created_at')),
            updated_at=self._parse_datetime(repo_data.get('updated_at')),
            pushed_at=self._parse_datetime(repo_data.get('pushed_at'))
        )
        
        # Repository in die Datenbank einfügen
        self.session.add(repo)
        self.session.commit()
        logger.info(f"Repository {repo.full_name} in die Datenbank eingefügt")
        
        return repo
    
    def update_repository(self, repo: Repository, repo_data: dict) -> Repository:
        """
        Repository in der Datenbank aktualisieren.
        
        Args:
            repo: Bestehendes Repository-Objekt
            repo_data: Neue Repository-Daten
            
        Returns:
            Aktualisiertes Repository-Objekt
        """
        # Felder aktualisieren
        repo.name = repo_data.get('name', repo.name)
        repo.full_name = repo_data.get('full_name', repo.full_name)
        repo.description = repo_data.get('description', repo.description)
        repo.homepage = repo_data.get('homepage', repo.homepage)
        repo.language = repo_data.get('language', repo.language)
        repo.private = repo_data.get('private', repo.private)
        repo.fork = repo_data.get('fork', repo.fork)
        repo.default_branch = repo_data.get('default_branch', repo.default_branch)
        repo.size = repo_data.get('size', repo.size)
        repo.stargazers_count = repo_data.get('stargazers_count', repo.stargazers_count)
        repo.watchers_count = repo_data.get('watchers_count', repo.watchers_count)
        repo.forks_count = repo_data.get('forks_count', repo.forks_count)
        repo.open_issues_count = repo_data.get('open_issues_count', repo.open_issues_count)
        repo.contributors_count = repo_data.get('contributors_count', repo.contributors_count)
        repo.commits_count = repo_data.get('commits_count', repo.commits_count)
        repo.pull_requests_count = repo_data.get('pull_requests_count', repo.pull_requests_count)
        repo.updated_at = self._parse_datetime(repo_data.get('updated_at', repo.updated_at))
        repo.pushed_at = self._parse_datetime(repo_data.get('pushed_at', repo.pushed_at))
        
        # Organisation aktualisieren, falls vorhanden
        if 'organization' in repo_data and repo_data['organization']:
            organization = self.insert_organization(repo_data['organization'])
            repo.organization_id = organization.id
        
        # Änderungen speichern
        self.session.commit()
        logger.debug(f"Repository {repo.full_name} aktualisiert")
        
        return repo
    
    def check_contributor_exists(self, login: str) -> bool:
        """
        Prüft, ob ein Contributor mit dem angegebenen Login bereits in der Datenbank existiert.
        
        Args:
            login: GitHub-Benutzername des Contributors
            
        Returns:
            True, wenn der Contributor existiert, sonst False
        """
        return self.session.query(Contributor).filter_by(login=login).first() is not None
    
    def check_organization_exists(self, login: str) -> bool:
        """
        Prüft, ob eine Organisation mit dem angegebenen Login bereits in der Datenbank existiert.
        
        Args:
            login: GitHub-Benutzername der Organisation
            
        Returns:
            True, wenn die Organisation existiert, sonst False
        """
        return self.session.query(Organization).filter_by(login=login).first() is not None
    
    def check_repository_exists(self, repo_id: int) -> bool:
        """
        Prüft, ob ein Repository mit der angegebenen ID bereits in der Datenbank existiert.
        
        Args:
            repo_id: GitHub-Repository-ID
            
        Returns:
            True, wenn das Repository existiert, sonst False
        """
        return self.session.query(Repository).filter_by(id=repo_id).first() is not None
    
    def get_all_contributor_logins(self) -> List[str]:
        """
        Ruft alle Contributor-Logins aus der Datenbank ab.
        
        Returns:
            Liste aller Contributor-Logins
        """
        try:
            # Optimierte Abfrage, die nur die Login-Spalte abruft
            logins = [row[0] for row in self.session.query(Contributor.login).all()]
            return logins
        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Contributor-Logins: {e}")
            return []

    def get_contributors(self, limit: Optional[int] = None) -> List[Contributor]:
        """
        Gibt alle Contributor-Objekte aus der Datenbank zurück.
        Optional kann ein Limit angegeben werden.

        Args:
            limit: Maximale Anzahl der zurückgegebenen Contributors (optional)
        Returns:
            Liste von Contributor-Objekten
        """
        try:
            query = self.session.query(Contributor)
            if limit is not None:
                query = query.limit(limit)
            contributors = query.all()
            return contributors
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Contributors: {e}")
            return []


    def get_contributors_without_country_code(self, limit: Optional[int] = None) -> List[Contributor]:
        """
        Gibt alle Contributor-Objekte zurück, deren country_code nicht gesetzt ist.
        Optional kann ein Limit angegeben werden.
        
        Args:
            limit: Maximale Anzahl der zurückgegebenen Contributors (optional)
        Returns:
            Liste von Contributor-Objekten ohne country_code
        """
        try:
            query = self.session.query(Contributor).filter(Contributor.country_code.is_(None))
            if limit is not None:
                query = query.limit(limit)
            contributors = query.all()
            return contributors
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Contributors ohne Ländercode: {e}")
            return []

    def get_organizations_without_country_code(self, limit: Optional[int] = None) -> List[Organization]:
        """
        Gibt alle Organization-Objekte zurück, deren country_code nicht gesetzt ist.
        Optional kann ein Limit angegeben werden.
        
        Args:
            limit: Maximale Anzahl der zurückgegebenen Organisationen (optional)
        Returns:
            Liste von Organization-Objekten ohne country_code
        """
        try:
            query = self.session.query(Organization).filter(Organization.country_code.is_(None))
            if limit is not None:
                query = query.limit(limit)
            organizations = query.all()
            return organizations
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Organisationen ohne Ländercode: {e}")
            return []
    
    def get_all_organization_logins(self) -> List[str]:
        """
        Ruft alle Organization-Logins aus der Datenbank ab.
        
        Returns:
            Liste aller Organization-Logins
        """
        try:
            # Optimierte Abfrage, die nur die Login-Spalte abruft
            logins = [row[0] for row in self.session.query(Organization.login).all()]
            return logins
        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Organization-Logins: {e}")
            return []
    
    def insert_contributor(self, contributor_data: dict) -> Contributor:
        """
        Contributor in die Datenbank einfügen oder aktualisieren.
        
        Args:
            contributor_data: Contributor-Daten von der GitHub API
            
        Returns:
            Contributor-Objekt
        """
        # Prüfen, ob Contributor bereits existiert
        existing = self.session.query(Contributor).filter_by(id=contributor_data['id']).first()
        if existing:
            return self.update_contributor(existing, contributor_data)
        
        # Neuen Contributor erstellen
        contributor = Contributor(
            id=contributor_data['id'],
            login=contributor_data['login'],
            name=contributor_data.get('name'),
            email=contributor_data.get('email'),
            type=contributor_data.get('type'),
            avatar_url=contributor_data.get('avatar_url'),
            company=contributor_data.get('company'),
            blog=contributor_data.get('blog'),
            location=contributor_data.get('location'),
            country_code=contributor_data.get('country_code'),
            region=contributor_data.get('region'),
            bio=contributor_data.get('bio'),
            twitter_username=contributor_data.get('twitter_username'),
            public_repos=contributor_data.get('public_repos'),
            public_gists=contributor_data.get('public_gists'),
            followers=contributor_data.get('followers'),
            following=contributor_data.get('following'),
            created_at=self._parse_datetime(contributor_data.get('created_at')),
            updated_at=self._parse_datetime(contributor_data.get('updated_at'))
        )
        
        # Contributor in die Datenbank einfügen
        self.session.add(contributor)
        self.session.commit()
        logger.debug(f"Contributor {contributor.login} in die Datenbank eingefügt")
        
        return contributor
    
    def update_contributor(self, contributor: Contributor, contributor_data: dict) -> Contributor:
        """
        Contributor in der Datenbank aktualisieren.
        
        Args:
            contributor: Bestehendes Contributor-Objekt
            contributor_data: Neue Contributor-Daten
            
        Returns:
            Aktualisiertes Contributor-Objekt
        """
        # Felder aktualisieren
        contributor.login = contributor_data.get('login', contributor.login)
        contributor.name = contributor_data.get('name', contributor.name)
        contributor.email = contributor_data.get('email', contributor.email)
        contributor.type = contributor_data.get('type', contributor.type)
        contributor.avatar_url = contributor_data.get('avatar_url', contributor.avatar_url)
        contributor.company = contributor_data.get('company', contributor.company)
        contributor.blog = contributor_data.get('blog', contributor.blog)
        contributor.location = contributor_data.get('location', contributor.location)
        contributor.country_code = contributor_data.get('country_code', contributor.country_code)
        contributor.region = contributor_data.get('region', contributor.region)
        contributor.bio = contributor_data.get('bio', contributor.bio)
        contributor.twitter_username = contributor_data.get('twitter_username', contributor.twitter_username)
        contributor.public_repos = contributor_data.get('public_repos', contributor.public_repos)
        contributor.public_gists = contributor_data.get('public_gists', contributor.public_gists)
        contributor.followers = contributor_data.get('followers', contributor.followers)
        contributor.following = contributor_data.get('following', contributor.following)
        contributor.updated_at = self._parse_datetime(contributor_data.get('updated_at', contributor.updated_at))
        
        # Änderungen speichern
        self.session.commit()
        logger.debug(f"Contributor {contributor.login} aktualisiert")
        
        return contributor
    
    def insert_organization(self, org_data: dict) -> Organization:
        """
        Organisation in die Datenbank einfügen oder aktualisieren.
        
        Args:
            org_data: Organisations-Daten von der GitHub API
            
        Returns:
            Organisation-Objekt
        """
        # Prüfen, ob Organisation bereits existiert
        existing = self.session.query(Organization).filter_by(id=org_data['id']).first()
        if existing:
            return self.update_organization(existing, org_data)
        
        # Neue Organisation erstellen
        organization = Organization(
            id=org_data['id'],
            login=org_data['login'],
            name=org_data.get('name'),
            email=org_data.get('email'),
            type=org_data.get('type'),
            avatar_url=org_data.get('avatar_url'),
            company=org_data.get('company'),
            blog=org_data.get('blog'),
            location=org_data.get('location'),
            country_code=org_data.get('country_code'),
            region=org_data.get('region'),
            bio=org_data.get('bio'),
            twitter_username=org_data.get('twitter_username'),
            public_repos=org_data.get('public_repos'),
            public_gists=org_data.get('public_gists'),
            followers=org_data.get('followers'),
            following=org_data.get('following'),
            public_members=org_data.get('public_members'),
            created_at=self._parse_datetime(org_data.get('created_at')),
            updated_at=self._parse_datetime(org_data.get('updated_at'))
        )
        
        # Organisation in die Datenbank einfügen
        self.session.add(organization)
        self.session.commit()
        logger.debug(f"Organisation {organization.login} in die Datenbank eingefügt")
        
        return organization
    
    def update_organization(self, organization: Organization, org_data: dict) -> Organization:
        """
        Organisation in der Datenbank aktualisieren.
        
        Args:
            organization: Bestehendes Organisation-Objekt
            org_data: Neue Organisations-Daten
            
        Returns:
            Aktualisiertes Organisation-Objekt
        """
        # Felder aktualisieren
        organization.login = org_data.get('login', organization.login)
        organization.name = org_data.get('name', organization.name)
        organization.email = org_data.get('email', organization.email)
        organization.type = org_data.get('type', organization.type)
        organization.avatar_url = org_data.get('avatar_url', organization.avatar_url)
        organization.company = org_data.get('company', organization.company)
        organization.blog = org_data.get('blog', organization.blog)
        organization.location = org_data.get('location', organization.location)
        organization.country_code = org_data.get('country_code', organization.country_code)
        organization.region = org_data.get('region', organization.region)
        organization.bio = org_data.get('bio', organization.bio)
        organization.twitter_username = org_data.get('twitter_username', organization.twitter_username)
        organization.public_repos = org_data.get('public_repos', organization.public_repos)
        organization.public_gists = org_data.get('public_gists', organization.public_gists)
        organization.followers = org_data.get('followers', organization.followers)
        organization.following = org_data.get('following', organization.following)
        organization.public_members = org_data.get('public_members', organization.public_members)
        organization.updated_at = self._parse_datetime(org_data.get('updated_at', organization.updated_at))
        
        # Änderungen speichern
        self.session.commit()
        logger.debug(f"Organisation {organization.login} aktualisiert")
        
        return organization
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """
        Konvertiert einen Datetime-String in ein datetime-Objekt.
        
        Args:
            dt_str: Datetime-String oder None
            
        Returns:
            datetime-Objekt oder None
        """
        if not dt_str:
            return None
        
        if isinstance(dt_str, datetime):
            return dt_str
            
        try:
            # ISO-Format-String parsen
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Fehler beim Parsen des Datetime-Strings '{dt_str}': {e}")
            return None
    
    # Statistik-Methoden
    
    def get_repository_count(self) -> int:
        """Anzahl der Repositories in der Datenbank."""
        return self.session.query(Repository).count()
    
    def get_contributor_count(self) -> int:
        """Anzahl der Contributors in der Datenbank."""
        return self.session.query(Contributor).count()
    
    def get_organization_count(self) -> int:
        """Anzahl der Organisationen in der Datenbank."""
        return self.session.query(Organization).count()
    
    def get_language_statistics(self) -> List[Tuple[str, int]]:
        """
        Statistik über die verwendeten Programmiersprachen.
        
        Returns:
            Liste von Tupeln (Sprache, Anzahl), sortiert nach Anzahl absteigend
        """
        result = (
            self.session.query(
                Repository.language, 
                func.count(Repository.id).label('count')
            )
            .filter(Repository.language.isnot(None))
            .group_by(Repository.language)
            .order_by(desc('count'))
            .all()
        )
        return [(lang, count) for lang, count in result]
    
    def get_repository_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Datumsbereich der Repositories.
        
        Returns:
            Tupel (ältestes Erstellungsdatum, neuestes Erstellungsdatum)
        """
        min_date = self.session.query(func.min(Repository.created_at)).scalar()
        max_date = self.session.query(func.max(Repository.created_at)).scalar()
        return (min_date, max_date)
    
    def get_contributor_location_stats(self) -> Dict[str, Union[int, float]]:
        """
        Statistik über Contributor-Standorte.
        
        Returns:
            Dictionary mit Statistiken
        """
        total = self.get_contributor_count()
        with_location = self.session.query(Contributor).filter(Contributor.location.isnot(None)).count()
        with_country_code = self.session.query(Contributor).filter(Contributor.country_code.isnot(None)).count()
        
        stats = {
            'total': total,
            'with_location': with_location,
            'with_country_code': with_country_code,
            'location_percentage': (with_location / total * 100) if total > 0 else 0,
            'country_code_percentage': (with_country_code / total * 100) if total > 0 else 0,
            'country_code_from_location_percentage': (with_country_code / with_location * 100) if with_location > 0 else 0
        }
        
        return stats
    
    def get_organization_location_stats(self) -> Dict[str, Union[int, float]]:
        """
        Statistik über Organisations-Standorte.
        
        Returns:
            Dictionary mit Statistiken
        """
        total = self.get_organization_count()
        with_location = self.session.query(Organization).filter(Organization.location.isnot(None)).count()
        with_country_code = self.session.query(Organization).filter(Organization.country_code.isnot(None)).count()
        
        stats = {
            'total': total,
            'with_location': with_location,
            'with_country_code': with_country_code,
            'location_percentage': (with_location / total * 100) if total > 0 else 0,
            'country_code_percentage': (with_country_code / total * 100) if total > 0 else 0,
            'country_code_from_location_percentage': (with_country_code / with_location * 100) if with_location > 0 else 0
        }
        
        return stats
