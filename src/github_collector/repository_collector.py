"""Repository Collector für die effiziente Sammlung von GitHub-Repositories."""

import os
import time
import logging
import json
from datetime import datetime, timedelta
from dateutil import tz
from typing import Dict, List, Tuple, Any, Optional, Iterator

from github_collector.ui.progress import (
    show_period_progress,
    show_repositories_found,
    show_period_too_large,
    show_collection_progress,
    show_collection_complete,
    show_api_limit_reached,
    show_max_repos_reached,
    show_collection_summary
)
from dateutil import tz

from .api.github_api import GitHubAPI, GitHubAPIError, GitHubRateLimitError
from .database.database import GitHubDatabase

logger = logging.getLogger(__name__)

class CollectionState:
    """
    Verwaltet den Zustand der Repository-Sammlung.
    
    Diese Klasse speichert und lädt den Zustand der Sammlung, um eine
    unterbrechbare und fortsetzbare Sammlung zu ermöglichen.
    """
    
    def __init__(self, state_file: str = "collection_state.json"):
        """
        Initialisiere den Sammlungszustand.
        
        Args:
            state_file: Pfad zur Zustandsdatei
        """
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Lade den Zustand aus der Datei.
        
        Returns:
            Zustandsdaten oder leeres Dictionary, wenn keine Datei existiert
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Sammlungszustands: {e}")
        
        # Standardzustand, wenn keine Datei existiert oder ein Fehler auftritt
        return {
            "last_run": None,
            "time_periods": [],
            "current_period_index": 0,
            "current_period_page": 1,
            "repositories_collected": 0,
            "start_date": None,
            "end_date": None
        }
    
    def save(self) -> None:
        """
        Speichere den aktuellen Zustand in der Datei.
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            logger.debug(f"Sammlungszustand gespeichert in {self.state_file}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Sammlungszustands: {e}")
    
    def update(self, **kwargs) -> None:
        """
        Aktualisiere den Zustand mit den angegebenen Werten.
        
        Args:
            **kwargs: Schlüssel-Wert-Paare für die Aktualisierung
        """
        self.state.update(kwargs)
        self.save()
    
    def reset(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> None:
        """
        Setze den Zustand zurück für eine neue Sammlung.
        
        Args:
            start_date: Startdatum für die Sammlung
            end_date: Enddatum für die Sammlung
        """
        self.state = {
            "last_run": datetime.now().isoformat(),
            "time_periods": [],
            "current_period_index": 0,
            "current_period_page": 1,
            "repositories_collected": 0,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
        self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Rufe einen Wert aus dem Zustand ab.
        
        Args:
            key: Schlüssel
            default: Standardwert, falls der Schlüssel nicht existiert
            
        Returns:
            Wert oder Standardwert
        """
        return self.state.get(key, default)
    
    def set_time_periods(self, periods: List[Tuple[datetime, datetime]]) -> None:
        """
        Setze die Zeitperioden für die Sammlung.
        
        Args:
            periods: Liste von (Start, Ende) Tupeln
        """
        self.state["time_periods"] = [
            {"start": start.isoformat(), "end": end.isoformat()}
            for start, end in periods
        ]
        self.save()
    
    def get_current_period(self) -> Optional[Tuple[datetime, datetime]]:
        """
        Rufe die aktuelle Zeitperiode ab.
        
        Returns:
            Tupel (Start, Ende) oder None, wenn keine Perioden definiert sind
        """
        periods = self.state.get("time_periods", [])
        index = self.state.get("current_period_index", 0)
        
        if not periods or index >= len(periods):
            return None
        
        period = periods[index]
        start = datetime.fromisoformat(period["start"])
        end = datetime.fromisoformat(period["end"])
        
        return (start, end)
    
    def next_period(self) -> bool:
        """
        Wechsle zur nächsten Zeitperiode.
        
        Returns:
            True, wenn eine weitere Periode verfügbar ist, sonst False
        """
        index = self.state.get("current_period_index", 0)
        periods = self.state.get("time_periods", [])
        
        if index + 1 < len(periods):
            self.state["current_period_index"] = index + 1
            self.state["current_period_page"] = 1
            self.save()
            return True
        
        return False

class RepositoryCollector:
    """
    Sammelt GitHub-Repositories mit einer zeitbasierten Strategie.
    
    Diese Klasse implementiert eine effiziente Strategie zur Sammlung von
    GitHub-Repositories, indem sie die Sammlung in kleine Zeitperioden aufteilt,
    um die API-Limits zu umgehen und eine vollständige Sammlung zu ermöglichen.
    """
    
    def __init__(self, github_client: GitHubAPI, db: GitHubDatabase, 
                state_file: str = "collection_state.json"):
        """
        Initialisiere den Repository Collector.
        
        Args:
            github_client: GitHub API Client
            db: Datenbankverbindung
            state_file: Pfad zur Zustandsdatei
        """
        self.github = github_client
        self.db = db
        self.state = CollectionState(state_file)
    
    def _calculate_time_periods(self, start_date: datetime, end_date: datetime, 
                              initial_period_days: int = 30) -> List[Tuple[datetime, datetime]]:
        """
        Berechne optimale Zeitperioden für die Sammlung.
        
        Diese Methode teilt den Zeitraum in kleinere Perioden auf, wobei die Größe
        der Perioden dynamisch angepasst wird, um die API-Limits zu berücksichtigen.
        
        Args:
            start_date: Startdatum für die Sammlung
            end_date: Enddatum für die Sammlung
            initial_period_days: Anfängliche Periodengröße in Tagen
            
        Returns:
            Liste von (Start, Ende) Tupeln für die Zeitperioden
        """
        periods = []
        current_start = start_date
        period_days = initial_period_days
        
        while current_start < end_date:
            # Berechne das Ende dieser Periode
            current_end = min(current_start + timedelta(days=period_days), end_date)
            
            # Füge die Periode hinzu
            periods.append((current_start, current_end))
            
            # Nächste Periode
            current_start = current_end
        
        return periods
    
    def _adjust_period_size(self, period: Tuple[datetime, datetime], 
                           results_count: int, max_results: int = 1000) -> List[Tuple[datetime, datetime]]:
        """
        Passe die Größe einer Zeitperiode an, wenn zu viele Ergebnisse gefunden wurden.
        
        Args:
            period: Zeitperiode als (Start, Ende) Tupel
            results_count: Anzahl der gefundenen Repositories
            max_results: Maximale Anzahl von Ergebnissen pro Periode
            
        Returns:
            Liste von angepassten Zeitperioden
        """
        start, end = period
        
        # Wenn die Anzahl der Ergebnisse akzeptabel ist, behalte die Periode bei
        if results_count <= max_results:
            return [period]
        
        # Berechne, wie viele Unterperioden wir benötigen
        num_subperiods = (results_count // max_results) + 1
        
        # Berechne die Dauer jeder Unterperiode
        total_seconds = (end - start).total_seconds()
        subperiod_seconds = total_seconds / num_subperiods
        
        # Erstelle die Unterperioden
        subperiods = []
        subperiod_start = start
        
        for i in range(num_subperiods):
            subperiod_end = subperiod_start + timedelta(seconds=subperiod_seconds)
            
            # Stelle sicher, dass die letzte Unterperiode genau bis zum Ende der Originalperiode geht
            if i == num_subperiods - 1:
                subperiod_end = end
            
            subperiods.append((subperiod_start, subperiod_end))
            subperiod_start = subperiod_end
        
        return subperiods
    
    def _search_repositories_in_period(self, start_date: datetime, end_date: datetime, 
                                      min_stars: int = 0, page: int = 1) -> dict:
        """
        Suche nach Repositories in einer bestimmten Zeitperiode.
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            page: Seitennummer
            
        Returns:
            Suchergebnisse als Dictionary
        """
        # Erstelle die Suchanfrage
        query = f"created:{start_date.isoformat()}..{end_date.isoformat()} stars:>={min_stars}"
        
        # Führe die Suche durch
        try:
            results = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc",
                per_page=100,
                page=page
            )
            
            return results
        except GitHubAPIError as e:
            logger.error(f"Fehler bei der Repository-Suche: {e}")
            return {"items": [], "total_count": 0}
    
    def _get_total_repositories_in_timeframe(self, start_date: datetime, end_date: datetime, 
                                          min_stars: int = 0) -> int:
        """
        Ermittle die Gesamtanzahl der Repositories im angegebenen Zeitraum.
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            
        Returns:
            Gesamtanzahl der Repositories
        """
        try:
            # Führe die Suche durch (nur erste Seite, um die Gesamtanzahl zu ermitteln)
            results = self._search_repositories_in_period(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                page=1
            )
            
            # Extrahiere die Gesamtanzahl
            if "total_count" in results:
                return results["total_count"]
            
            return 0
        except Exception as e:
            logger.error(f"Fehler bei der Ermittlung der Gesamtanzahl der Repositories: {e}")
            return 0
    
    def _process_repository(self, repo_data: Dict[str, Any]) -> None:
        """
        Verarbeite ein Repository und speichere es in der Datenbank.
        
        Args:
            repo_data: Repository-Daten von der GitHub API
        """
        try:
            # Prüfe, ob das Repository einer Organisation gehört
            owner_data = repo_data.get('owner', {})
            if owner_data and owner_data.get('type') == 'Organization':
                # Wenn der Eigentümer eine Organisation ist, aber keine Organisationsdaten vorhanden sind
                if 'organization' not in repo_data or not repo_data['organization']:
                    # Setze die Organisationsdaten basierend auf dem Eigentümer
                    repo_data['organization'] = owner_data
                    logger.debug(f"Organisationsdaten aus Owner-Feld für {repo_data.get('full_name')} hinzugefügt")
                    
                    # Hole erweiterte Organisationsdaten, wenn möglich
                    try:
                        org_login = owner_data.get('login')
                        if org_login:
                            org_details = self.api.get_organization(org_login)
                            if org_details:
                                # Aktualisiere die Organisationsdaten mit den erweiterten Details
                                repo_data['organization'] = org_details
                                logger.debug(f"Erweiterte Organisationsdaten für {org_login} abgerufen")
                    except Exception as org_err:
                        logger.warning(f"Fehler beim Abrufen erweiterter Organisationsdaten für {owner_data.get('login')}: {org_err}")
            
            # Hole die Anzahl der Contributors, falls nicht bereits vorhanden
            if 'contributors_count' not in repo_data or not repo_data['contributors_count']:
                try:
                    owner_login = owner_data.get('login')
                    repo_name = repo_data.get('name')
                    if owner_login and repo_name:
                        contributors_count = self.api.get_repository_contributors_count(owner_login, repo_name)
                        repo_data['contributors_count'] = contributors_count
                        logger.debug(f"Contributors-Anzahl für {repo_data.get('full_name')}: {contributors_count}")
                except Exception as contrib_err:
                    logger.warning(f"Fehler beim Abrufen der Contributors-Anzahl für {repo_data.get('full_name')}: {contrib_err}")
            
            # Überwache das Rate-Limit nach API-Aufrufen
            rate_limit_info = self.api.monitor_rate_limit(threshold_percent=10)
            if rate_limit_info.get('has_warnings', False):
                for warning in rate_limit_info.get('warnings', []):
                    logger.warning(warning)
            
            # Füge das Repository in die Datenbank ein
            repo = self.db.insert_repository(repo_data)
            
            if repo:
                logger.info(f"Repository verarbeitet: {repo.full_name} (ID: {repo.id}, Contributors: {repo.contributors_count})")
                if repo.organization_id:
                    logger.debug(f"Repository {repo.full_name} ist mit Organisation ID {repo.organization_id} verknüpft")
            else:
                logger.warning(f"Repository konnte nicht verarbeitet werden: {repo_data.get('full_name')}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung des Repositories {repo_data.get('full_name')}: {e}")
    
    def _collect_repositories_in_period(self, start_date: datetime, end_date: datetime, 
                                      min_stars: int = 0, max_repos: Optional[int] = None) -> int:
        """
        Sammle Repositories in einer bestimmten Zeitperiode.
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            max_repos: Maximale Anzahl zu sammelnder Repositories (optional)
            
        Returns:
            Anzahl der gesammelten Repositories
        """
        page = self.state.get("current_period_page", 1)
        collected_count = 0
        total_count = None
        last_count = 0
        
        # Hole die aktuelle Periode und Gesamtanzahl der Perioden
        current_period_index = self.state.state.get("current_period_index", 0)
        total_periods = len(self.state.state.get("time_periods", []))
        
        # Berechne den Gesamtfortschritt
        overall_progress = 0
        if total_periods > 0:
            overall_progress = min(100, (current_period_index * 100) // total_periods)
        
        while True:
            # Suche nach Repositories in dieser Periode
            results = self._search_repositories_in_period(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                page=page
            )
            
            # Aktualisiere die Gesamtanzahl, falls verfügbar
            if total_count is None and "total_count" in results:
                total_count = results["total_count"]
                logger.info(f"Gefunden: {total_count} Repositories in der Periode {start_date} bis {end_date}")
                
                # Zeige die Anzahl der gefundenen Repositories in dieser Periode an
                show_repositories_found(total_count)
                
                # Prüfe, ob wir die Periode aufteilen müssen
                if total_count > 1000:
                    # Zeige eine Meldung an, dass die Periode aufgeteilt werden muss
                    show_period_too_large(total_count)
                    
                    # Teile die Periode auf und aktualisiere den Zustand
                    new_periods = self._adjust_period_size((start_date, end_date), total_count)
                    
                    # Hole die aktuellen Perioden und ersetze die aktuelle durch die neuen
                    all_periods = self.state.state.get("time_periods", [])
                    
                    # Konvertiere die neuen Perioden in das richtige Format
                    new_period_dicts = [
                        {"start": start.isoformat(), "end": end.isoformat()}
                        for start, end in new_periods
                    ]
                    
                    # Ersetze die aktuelle Periode durch die neuen
                    updated_periods = (
                        all_periods[:current_period_index] + 
                        new_period_dicts + 
                        all_periods[current_period_index+1:]
                    )
                    
                    # Aktualisiere den Zustand
                    self.state.state["time_periods"] = updated_periods
                    self.state.state["current_period_index"] = current_period_index
                    self.state.state["current_period_page"] = 1
                    self.state.save()
                    
                    # Starte mit der ersten neuen Periode
                    return 0
            
            # Verarbeite die gefundenen Repositories
            items = results.get("items", [])
            
            if not items:
                logger.info(f"Keine weiteren Repositories in dieser Periode (Seite {page})")
                # Wenn wir keine Ergebnisse mehr bekommen, aber noch nicht alle Repositories gesammelt haben,
                # zeigen wir eine abschließende Fortschrittsmeldung an
                if collected_count < total_count and collected_count > 0:
                    # Zeige den Sammlungsfortschritt an
                    show_collection_progress(collected_count, total_count)
                break
            
            # Verarbeite die Repositories dieser Seite
            for repo_data in items:
                self._process_repository(repo_data)
                collected_count += 1
                
                # Aktualisiere den Sammlungszustand
                total_collected = self.state.get("repositories_collected", 0) + 1
                self.state.update(
                    repositories_collected=total_collected,
                    current_period_page=page
                )
                
                # Prüfe, ob wir das Maximum erreicht haben
                if max_repos and total_collected >= max_repos:
                    # Zeige eine Meldung an, dass die maximale Anzahl erreicht wurde
                    show_max_repos_reached(max_repos)
                    return collected_count
            
            # Zeige den Fortschritt in 100er-Schritten an
            if collected_count // 100 > last_count // 100 and total_count > 0:
                last_count = collected_count
                # Zeige den Sammlungsfortschritt an
                show_collection_progress(collected_count, total_count)
            
            # Nächste Seite
            page += 1
            self.state.update(current_period_page=page)
            
            # Prüfe, ob wir alle Ergebnisse verarbeitet haben
            # Die GitHub Search API gibt maximal 1000 Ergebnisse zurück (10 Seiten mit je 100 Ergebnissen)
            if len(items) < 100 or page > 10:
                # Zeige eine abschließende Fortschrittsmeldung an
                if collected_count > 0:
                    # Wenn wir alle Repositories gesammelt haben
                    if collected_count >= total_count:
                        # Zeige eine Meldung an, dass alle Repositories gesammelt wurden
                        show_collection_complete(total_count)
                    # Wenn wir nicht alle Repositories sammeln konnten
                    else:
                        # Zeige den Sammlungsfortschritt an
                        show_collection_progress(collected_count, total_count)
                        if page > 10:
                            # Zeige eine Meldung an, dass die API-Beschränkung erreicht wurde
                            show_api_limit_reached()
                break
            
            # Kurze Pause, um die API nicht zu überlasten
            time.sleep(1)
        
        return collected_count
    
    def collect_repositories(self, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None, min_stars: int = 0, 
                             max_repos: Optional[int] = None, resume: bool = True) -> int:
        """
        Sammle Repositories in einem bestimmten Zeitraum.
        
        Args:
            start_date: Startdatum (optional, Standard: vor einem Monat)
            end_date: Enddatum (optional, Standard: jetzt)
            min_stars: Minimale Anzahl von Stars
            max_repos: Maximale Anzahl zu sammelnder Repositories (optional)
            resume: Sammlung fortsetzen, falls unterbrochen
            
        Returns:
            Anzahl der gesammelten Repositories
        """
        # Standardwerte für Start- und Enddatum
        if end_date is None:
            end_date = datetime.now(tz.UTC)
        
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Stelle sicher, dass die Datumsangaben UTC-Zeitzonen haben
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=tz.UTC)
        
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=tz.UTC)
        
        # Prüfe, ob wir eine unterbrochene Sammlung fortsetzen sollen
        if resume and self.state.get("time_periods") and self.state.get_current_period():
            logger.info("Setze unterbrochene Sammlung fort")
            
            # Hole die Sammlung-Parameter aus dem Zustand
            state_start_date = datetime.fromisoformat(self.state.get("start_date"))
            state_end_date = datetime.fromisoformat(self.state.get("end_date"))
            
            # Zeige auch bei fortgesetzter Sammlung eine Übersicht über die Gesamtanzahl der Repositories
            total_repos = self._get_total_repositories_in_timeframe(state_start_date, state_end_date, min_stars)
            if total_repos > 0:
                print(f"\nInsgesamt gefundene Repositories im Zeitraum {state_start_date.strftime('%Y-%m-%d')} bis {state_end_date.strftime('%Y-%m-%d')} mit mindestens {min_stars} Stars: {total_repos}")
        else:
            # Starte eine neue Sammlung
            logger.info(f"Starte neue Sammlung von {start_date} bis {end_date}")
            
            # Zeige eine Übersicht über die Gesamtanzahl der Repositories im Zeitraum
            total_repos = self._get_total_repositories_in_timeframe(start_date, end_date, min_stars)
            if total_repos > 0:
                print(f"\nInsgesamt gefundene Repositories im Zeitraum {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')} mit mindestens {min_stars} Stars: {total_repos}")
            
            # Berechne die Zeitperioden
            periods = self._calculate_time_periods(start_date, end_date)
            
            # Setze den Zustand zurück
            self.state.reset(start_date, end_date)
            self.state.set_time_periods(periods)
        
        total_collected = 0
        
        # Sammle Repositories in jeder Zeitperiode
        while True:
            # Hole die aktuelle Periode
            period = self.state.get_current_period()
            if not period:
                logger.info("Keine weiteren Zeitperioden verfügbar")
                break
            
            period_start, period_end = period
            # Hole die aktuelle Periode und Gesamtanzahl der Perioden
            current_period_index = self.state.state.get("current_period_index", 0)
            total_periods = len(self.state.state.get("time_periods", []))
            
            # Zeige den Periodenfortschritt an
            show_period_progress(current_period_index, total_periods)
            logger.info(f"Sammle Repositories in der Periode {period_start} bis {period_end}")
            
            # Sammle Repositories in dieser Periode
            period_collected = self._collect_repositories_in_period(
                start_date=period_start,
                end_date=period_end,
                min_stars=min_stars,
                max_repos=max_repos
            )
            
            total_collected += period_collected
            
            # Prüfe, ob wir das Maximum erreicht haben
            if max_repos and total_collected >= max_repos:
                # Zeige eine Meldung an, dass die maximale Anzahl erreicht wurde
                show_max_repos_reached(max_repos)
                break
            
            # Gehe zur nächsten Periode
            if not self.state.next_period():
                logger.info("Alle Zeitperioden abgeschlossen")
                break
        
        # Zeige eine Zusammenfassung der gesamten Sammlung an
        show_collection_summary(total_collected)
        return total_collected
