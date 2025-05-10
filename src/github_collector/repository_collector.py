"""Repository Collector für die effiziente Sammlung von GitHub-Repositories."""

import os
import time
import logging
import json
from datetime import datetime, timedelta
from dateutil import tz
from typing import Dict, List, Tuple, Any, Optional, Iterator
from time import perf_counter

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
from .owners.owner_processor import OwnerProcessor
from .utils.performance_tracker import PerformanceTracker, PerformanceReporter

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
                 state_file: str = "collection_state.json",
                 enable_performance_tracking: bool = None):
        """
        Initialisiere den Repository Collector.
        
        Args:
            github_client: GitHub API Client
            db: Datenbankverbindung
            state_file: Pfad zur Zustandsdatei
            enable_performance_tracking: Aktiviert oder deaktiviert das Performance-Tracking
        """
        # Performance-Tracker initialisieren
        self.performance_tracker = PerformanceTracker(enable_tracking=enable_performance_tracking)
        
        # API-Client mit Performance-Tracker initialisieren
        self.github = github_client
        self.api = github_client  # Alias für die neuen Funktionen
        
        # Setze den Performance-Tracker im API-Client
        if hasattr(self.api, 'performance_tracker'):
            self.api.performance_tracker = self.performance_tracker
        
        # Datenbankverbindung und Zustand
        self.db = db
        self.state = CollectionState(state_file)
        
        # Owner-Processor initialisieren
        self.owner_processor = OwnerProcessor(self.api, self.db, self.performance_tracker)
    
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
                                      min_stars: int = 0, page: int = 1, max_stars: int = None) -> dict:
        """
        Suche nach Repositories in einer bestimmten Zeitperiode.
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            max_stars: Maximale Anzahl von Stars (optional)
            page: Seitennummer
            
        Returns:
            Suchergebnisse als Dictionary
        """
        # Erstelle die Suchanfrage
        if max_stars is not None:
            query = f"created:{start_date.isoformat()}..{end_date.isoformat()} stars:{min_stars}..{max_stars}"
        else:
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

    def collect_repositories_by_star_range(self, start_date: Optional[datetime] = None, 
                                           end_date: Optional[datetime] = None, min_stars: int = 0, 
                                           max_stars: int = 100, max_repos: Optional[int] = None, resume: bool = True) -> int:
        """
        Sammle Repositories in einem bestimmten Zeitraum und Star-Bereich.
        
        Args:
            start_date: Startdatum (optional)
            end_date: Enddatum (optional)
            min_stars: Minimale Anzahl von Stars (inklusive)
            max_stars: Maximale Anzahl von Stars (inklusive)
            max_repos: Maximale Anzahl zu sammelnder Repositories (optional)
            resume: Sammlung fortsetzen, falls unterbrochen
        Returns:
            Anzahl der gesammelten Repositories
        """
        from time import perf_counter
        collection_start_time = perf_counter()
        # Standardwerte für Zeitraum setzen
        now = datetime.now(tz.UTC)
        if end_date is None:
            end_date = now
        if start_date is None:
            start_date = now - timedelta(days=30)
        # Resume-Logik wie bei collect_repositories
        if resume and self.state.state.get("time_periods"):
            state_start_date = datetime.fromisoformat(self.state.get("start_date"))
            state_end_date = datetime.fromisoformat(self.state.get("end_date"))
            total_repos = self._get_total_repositories_in_timeframe(
                start_date=state_start_date,
                end_date=state_end_date,
                min_stars=min_stars,
                max_stars=max_stars
            )
            if total_repos > 0:
                print(f"\nInsgesamt gefundene Repositories im Zeitraum {state_start_date.strftime('%Y-%m-%d')} bis {state_end_date.strftime('%Y-%m-%d')} mit Stars {min_stars}..{max_stars}: {total_repos}")
        else:
            logger.info(f"Starte neue Sammlung von {start_date} bis {end_date} für Stars {min_stars}..{max_stars}")
            total_repos = self._get_total_repositories_in_timeframe(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                max_stars=max_stars
            )
            if total_repos > 0:
                print(f"\nInsgesamt gefundene Repositories im Zeitraum {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')} mit Stars {min_stars}..{max_stars}: {total_repos}")
            periods = self._calculate_time_periods(start_date, end_date)
            self.state.reset(start_date, end_date)
            self.state.set_time_periods(periods)
        total_collected = 0
        while True:
            period = self.state.get_current_period()
            if not period:
                logger.info("Keine weiteren Zeitperioden verfügbar")
                break
            period_start, period_end = period
            current_period_index = self.state.state.get("current_period_index", 0)
            total_periods = len(self.state.state.get("time_periods", []))
            show_period_progress(current_period_index, total_periods)
            logger.info(f"Sammle Repositories in der Periode {period_start} bis {period_end} (Stars {min_stars}..{max_stars})")
            period_collected = self._collect_repositories_in_period_by_star_range(
                start_date=period_start,
                end_date=period_end,
                min_stars=min_stars,
                max_stars=max_stars,
                max_repos=max_repos
            )
            total_collected += period_collected
            if max_repos and total_collected >= max_repos:
                show_max_repos_reached(max_repos)
                break
            if not self.state.next_period():
                logger.info("Alle Zeitperioden abgeschlossen")
                break
        show_collection_summary(total_collected)
        collection_end_time = perf_counter()
        collection_time = collection_end_time - collection_start_time
        collection_time_min = collection_time / 60
        print(f"\n\u23F0 Gesamtzeit: {collection_time_min:.2f} Minuten für {total_collected} Repositories")
        if total_collected > 0:
            print(f"   Durchschnitt gesamt: {collection_time / total_collected:.2f} Sekunden pro Repository")
        print(f"   Reine Verarbeitungszeit: {(self.__class__._total_processing_time / 60):.2f} Minuten") # Korrigiert: In Minuten
        print(f"   Overhead (API, Suche, etc.): {(collection_time - self.__class__._total_processing_time) / 60:.2f} Minuten")
        return total_collected

    def _collect_repositories_in_period_by_star_range(self, start_date: datetime, end_date: datetime, 
                                                      min_stars: int = 0, max_stars: int = 100, max_repos: Optional[int] = None) -> int:
        """
        Sammle Repositories in einer bestimmten Zeitperiode und Star-Range.
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            max_stars: Maximale Anzahl von Stars
            max_repos: Maximale Anzahl zu sammelnder Repositories (optional)
        Returns:
            Anzahl der gesammelten Repositories
        """
        page = self.state.get("current_period_page", 1)
        collected_count = 0
        total_count = None
        last_count = 0
        while True:
            results = self._search_repositories_in_period(start_date, end_date, min_stars=min_stars, max_stars=max_stars, page=page)
            if total_count is None:
                total_count = results.get("total_count", 0)
            items = results.get("items", [])
            if not items:
                logger.info(f"Keine weiteren Repositories in dieser Periode (Seite {page})")
                if collected_count < total_count and collected_count > 0:
                    show_collection_progress(collected_count, total_count)
                break
            if items:
                self._process_repositories_batch(items)
                collected_count += len(items)
                total_collected = self.state.get("repositories_collected", 0) + len(items)
                self.state.update(
                    repositories_collected=total_collected,
                    current_period_page=page
                )
                if max_repos and total_collected >= max_repos:
                    show_max_repos_reached(max_repos)
                    return collected_count
            if collected_count // 100 > last_count // 100 and total_count > 0:
                last_count = collected_count
                show_collection_progress(collected_count, total_count)
            page += 1
            self.state.update(current_period_page=page)
            if len(items) < 100 or page > 10:
                if collected_count > 0:
                    if collected_count >= total_count:
                        show_collection_complete(total_count)
                    else:
                        show_collection_progress(collected_count, total_count)
                break
        return collected_count

    def _get_total_repositories_in_timeframe(self, start_date: datetime, end_date: datetime, 
                                             min_stars: int = 0, max_stars: int = None) -> int:
        """
        Ermittle die Gesamtanzahl der Repositories im angegebenen Zeitraum und Star-Bereich.
        Args:
            start_date: Startdatum
            end_date: Enddatum
            min_stars: Minimale Anzahl von Stars
            max_stars: Maximale Anzahl von Stars (optional)
        Returns:
            Gesamtanzahl der Repositories
        """
        try:
            results = self._search_repositories_in_period(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                max_stars=max_stars,
                page=1
            )
            if "total_count" in results:
                return results["total_count"]
            return 0
        except Exception as e:
            logger.error(f"Fehler bei der Ermittlung der Gesamtanzahl der Repositories: {e}")
            return 0
    
    def _collect_contributors_metadata_batch(self, contributor_logins: List[str]) -> None:
        """
        Sammelt Metadaten für mehrere Contributors in einem Batch.
        
        Args:
            contributor_logins: Liste der GitHub-Benutzernamen der Contributors
        """
        # Verwende den Owner-Processor für die Verarbeitung der Contributors
        self.owner_processor.process_contributors_batch(contributor_logins)
    
    # Performance-Tracking
    _total_processing_time = 0.0
    _repositories_processed = 0
    
    def _process_repository(self, repo_data: Dict[str, Any]) -> None:
        """
        Verarbeite ein einzelnes Repository und füge es in die Datenbank ein.
        
        Args:
            repo_data: Repository-Daten aus der GitHub API
        """
        # Starte Zeitmessung
        start_time = perf_counter() if self.performance_tracker and self.performance_tracker.enabled else 0
        processing_time = 0.0
        
        try:
            # Prüfe, ob das Repository bereits existiert (um redundante API-Aufrufe zu vermeiden)
            repo_id = repo_data.get('id')
            if repo_id and self.db.check_repository_exists(repo_id):
                if self.performance_tracker:
                    self.performance_tracker.record_duplicate_repository()
                logger.debug(f"Repository {repo_data.get('full_name')} (ID: {repo_id}) existiert bereits in der Datenbank")
                return
            
            # Setze den Batch-Tracking zurück, wenn ein neues Repository verarbeitet wird
            self.owner_processor.reset_batch_tracking()
            
            # Verarbeite den Owner des Repositories (Organisation oder Contributor)
            repo_data = self.owner_processor.process_repository_owner(repo_data)
            
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
        
        finally:
            # Ende der Zeitmessung und Aktualisierung der Statistiken, wenn Performance-Tracking aktiviert ist
            if start_time > 0:
                end_time = perf_counter()
                processing_time = end_time - start_time
                
                # Aktualisiere Statistiken
                self.__class__._total_processing_time += processing_time
                self.__class__._repositories_processed += 1
                
                # Zeichne die Repository-Verarbeitung im Performance-Tracker auf
                repo_name = repo_data.get('full_name', 'unbekannt')
                self.performance_tracker.end_repository_processing(start_time, repo_name)
            
            # Zeige Performance-Informationen an
            repo_name = repo_data.get('full_name', 'Unbekannt')
            print(f"\r\u23F1 Repository {repo_name} verarbeitet in {processing_time:.2f} Sekunden")
            
            # Zeige Durchschnitt an, wenn mehrere Repositories verarbeitet wurden
            if self.__class__._repositories_processed > 1:
                avg_time = self.__class__._total_processing_time / self.__class__._repositories_processed
                print(f"   Durchschnitt: {avg_time:.2f} Sekunden pro Repository ({self.__class__._repositories_processed} gesamt)")
    
    def _process_repositories_batch(self, repositories_data: List[Dict[str, Any]]) -> None:
        """
        Verarbeite mehrere Repositories in einem Batch.
        
        Args:
            repositories_data: Liste von Repository-Daten aus der GitHub API
        """
        if not repositories_data:
            return
            
        # Starte Zeitmessung für den Batch
        batch_start_time = perf_counter()
        batch_size = len(repositories_data)
        logger.info(f"Starte Verarbeitung von Batch mit {batch_size} Repositories")
        
        # Sammle alle einzigartigen Contributor-Logins
        contributor_logins = set()
        organization_logins = set()
        
        # Analysiere zuerst alle Owner-Daten
        for repo_data in repositories_data:
            owner_data = repo_data.get('owner', {})
            if not owner_data:
                continue
                
            owner_login = owner_data.get('login')
            owner_type = owner_data.get('type')
            
            if owner_type == 'User' and owner_login:
                contributor_logins.add(owner_login)
            elif owner_type == 'Organization' and owner_login:
                organization_logins.add(owner_login)
        
        # Überwache das Rate-Limit vor dem Batch
        rate_limit_info = self.api.monitor_rate_limit(threshold_percent=15)
        if rate_limit_info.get('has_critical', False):
            logger.warning("Kritisches Rate-Limit vor Repository-Batch-Verarbeitung erkannt")
            print("\n[Warnung] Kritisches Rate-Limit vor Repository-Batch-Verarbeitung!\n")
        
        # Sammle Metadaten für alle Contributors in einem Batch
        if contributor_logins:
            logger.info(f"Sammle Metadaten für {len(contributor_logins)} Contributors")
            self._collect_contributors_metadata_batch(list(contributor_logins))
        
        # Verarbeite jedes Repository einzeln
        processed_count = 0
        for repo_data in repositories_data:
            try:
                self._process_repository(repo_data)
                processed_count += 1
                
                # Zeige Fortschritt an
                if batch_size > 10 and processed_count % 10 == 0:
                    progress_percent = (processed_count / batch_size) * 100
                    print(f"\rBatch-Fortschritt: {processed_count}/{batch_size} Repositories ({progress_percent:.1f}%)...", end="")
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von Repository {repo_data.get('full_name', 'unbekannt')}: {e}")
        
        # Ende der Zeitmessung für den Batch
        batch_end_time = perf_counter()
        batch_processing_time = batch_end_time - batch_start_time
        avg_time_per_repo = batch_processing_time / max(1, processed_count)
        
        # Zeige Performance-Informationen für den Batch an
        print(f"\n\u23F3 Batch mit {processed_count} von {batch_size} Repositories verarbeitet in {batch_processing_time:.2f} Sekunden")
        print(f"   Durchschnitt im Batch: {avg_time_per_repo:.2f} Sekunden pro Repository")
        
        # Überwache das Rate-Limit nach dem Batch
        self.api.monitor_rate_limit(threshold_percent=10)
    
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
            try:
                # Überwache das Rate-Limit vor der Suche
                rate_limit_info = self.api.monitor_rate_limit(threshold_percent=15)
                if rate_limit_info.get('has_critical', False):
                    # Bei kritischem Rate-Limit kurz pausieren, um die Warnmeldung anzuzeigen
                    time.sleep(2)
                
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
            
            except GitHubRateLimitError as e:
                logger.warning(f"Rate-Limit erreicht während der Sammlung in Periode {start_date} bis {end_date}. Warte auf Reset...")
                print(f"\n[RateLimit] Rate-Limit erreicht während der Sammlung. Automatischer Neuversuch nach Reset.\n")
                # Warte 60 Sekunden und versuche es erneut - der Token-Pool wird beim nächsten API-Aufruf automatisch warten
                time.sleep(60)
                continue
            except GitHubAPIError as e:
                logger.error(f"API-Fehler während der Sammlung: {e}")
                print(f"\n[Fehler] GitHub API-Fehler: {e}\n")
                time.sleep(10)  # Kurze Pause bei API-Fehlern
                continue
                
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
            
            # Verarbeite die Repositories dieser Seite als Batch
            if items:
                # Verarbeite alle Repositories dieser Seite in einem Batch
                self._process_repositories_batch(items)
                collected_count += len(items)
                
                # Aktualisiere den Sammlungszustand
                total_collected = self.state.get("repositories_collected", 0) + len(items)
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
        # Starte Zeitmessung für den gesamten Sammelprozess
        collection_start_time = perf_counter()
        
        # Setze Performance-Tracking zurück
        self.__class__._total_processing_time = 0.0
        self.__class__._repositories_processed = 0
        
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
        
        # Ende der Zeitmessung für den gesamten Sammelprozess
        collection_end_time = perf_counter()
        collection_time = collection_end_time - collection_start_time
        collection_time_min = collection_time / 60
        
        # Zeige Performance-Informationen für den gesamten Sammelprozess an
        print(f"\n\u23F0 Gesamtzeit: {collection_time_min:.2f} Minuten für {total_collected} Repositories")
        if total_collected > 0:
            print(f"   Durchschnitt gesamt: {collection_time / total_collected:.2f} Sekunden pro Repository")
        print(f"   Reine Verarbeitungszeit: {(self.__class__._total_processing_time / 60):.2f} Minuten") # Korrigiert: In Minuten
        print(f"   Overhead (API, Suche, etc.): {(collection_time - self.__class__._total_processing_time) / 60:.2f} Minuten")
        
        return total_collected
