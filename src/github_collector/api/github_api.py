"""GitHub API Client für die effiziente Kommunikation mit der GitHub API."""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import random

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class GitHubAPIError(Exception):
    """Fehler bei der Kommunikation mit der GitHub API."""
    pass

class GitHubRateLimitError(GitHubAPIError):
    """Rate Limit der GitHub API erreicht."""
    pass

class GitHubClient:
    """
    Basis-Client für die GitHub API.
    
    Diese Klasse bietet grundlegende Funktionen für die Kommunikation mit der GitHub API,
    einschließlich Authentifizierung, Rate-Limit-Handling und Fehlerbehandlung.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, cache_dir: Optional[str] = None):
        """
        Initialisiere den GitHub API Client.
        
        Args:
            token: GitHub API Token
            cache_dir: Verzeichnis für den Cache (optional)
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Data-Collector"
        })
        
        # Rate Limit Tracking
        self.rate_limit = 5000
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        
        # Cache
        self.cache_dir = cache_dir
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """
        Aktualisiere die Rate-Limit-Informationen aus dem Response-Header.
        
        Args:
            response: Response-Objekt
        """
        if 'X-RateLimit-Limit' in response.headers:
            self.rate_limit = int(response.headers['X-RateLimit-Limit'])
        
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
        
        # Logge Rate-Limit-Informationen
        logger.debug(
            f"Rate Limit: {self.rate_limit_remaining}/{self.rate_limit} "
            f"(Reset: {datetime.fromtimestamp(self.rate_limit_reset).strftime('%Y-%m-%d %H:%M:%S')})"
        )
    
    def _wait_for_rate_limit(self) -> None:
        """
        Warte, bis das Rate Limit zurückgesetzt wird, falls notwendig.
        """
        if self.rate_limit_remaining <= 1:
            now = datetime.now().timestamp()
            wait_time = max(0, self.rate_limit_reset - now) + 1  # +1 Sekunde Puffer
            
            if wait_time > 0:
                logger.warning(f"Rate Limit erreicht. Warte {wait_time:.1f} Sekunden...")
                time.sleep(wait_time)
    
    def _get_cache_path(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[str]:
        """
        Generiere den Pfad zur Cache-Datei für einen API-Aufruf.
        
        Args:
            endpoint: API-Endpunkt
            params: Query-Parameter
            
        Returns:
            Pfad zur Cache-Datei oder None, wenn kein Cache verwendet wird
        """
        if not self.cache_dir:
            return None
        
        # Erstelle einen eindeutigen Schlüssel für den Cache
        cache_key = endpoint
        if params:
            # Sortiere Parameter für konsistente Schlüssel
            sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key += f"?{sorted_params}"
        
        # Erstelle einen Dateinamen aus dem Schlüssel
        import hashlib
        cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + ".json"
        
        return os.path.join(self.cache_dir, cache_filename)
    
    def _get_from_cache(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Versuche, eine Antwort aus dem Cache zu laden.
        
        Args:
            endpoint: API-Endpunkt
            params: Query-Parameter
            
        Returns:
            Gecachte Antwort oder None, wenn nicht im Cache
        """
        cache_path = self._get_cache_path(endpoint, params)
        if not cache_path or not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Prüfe, ob der Cache abgelaufen ist (1 Tag)
            cache_time = cache_data.get('_cache_time', 0)
            if datetime.now().timestamp() - cache_time > 86400:  # 24 Stunden
                logger.debug(f"Cache abgelaufen für {endpoint}")
                return None
            
            logger.debug(f"Cache-Treffer für {endpoint}")
            return cache_data.get('data')
        
        except Exception as e:
            logger.warning(f"Fehler beim Laden aus dem Cache: {e}")
            return None
    
    def _save_to_cache(self, endpoint: str, params: Dict[str, Any], data: Dict[str, Any]) -> None:
        """
        Speichere eine Antwort im Cache.
        
        Args:
            endpoint: API-Endpunkt
            params: Query-Parameter
            data: Zu speichernde Daten
        """
        cache_path = self._get_cache_path(endpoint, params)
        if not cache_path:
            return
        
        try:
            cache_data = {
                '_cache_time': datetime.now().timestamp(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            logger.debug(f"In Cache gespeichert: {endpoint}")
        
        except Exception as e:
            logger.warning(f"Fehler beim Speichern im Cache: {e}")
    
    def request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                data: Dict[str, Any] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Sende eine Anfrage an die GitHub API.
        
        Args:
            method: HTTP-Methode (GET, POST, etc.)
            endpoint: API-Endpunkt
            params: Query-Parameter
            data: Request-Body für POST/PUT
            use_cache: Cache verwenden (nur für GET)
            
        Returns:
            API-Antwort als Dictionary
            
        Raises:
            GitHubAPIError: Bei API-Fehlern
            GitHubRateLimitError: Bei Rate-Limit-Überschreitung
        """
        # Prüfe, ob wir die Antwort aus dem Cache laden können
        if method.upper() == 'GET' and use_cache:
            cached_response = self._get_from_cache(endpoint, params)
            if cached_response:
                return cached_response
        
        # Warte, falls das Rate Limit erreicht wurde
        self._wait_for_rate_limit()
        
        # Erstelle die vollständige URL
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            # Sende die Anfrage
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            
            # Aktualisiere Rate-Limit-Informationen
            self._handle_rate_limit(response)
            
            # Prüfe auf Fehler
            response.raise_for_status()
            
            # Parse die Antwort
            if response.content:
                result = response.json()
            else:
                result = {}
            
            # Speichere im Cache für GET-Anfragen
            if method.upper() == 'GET' and use_cache:
                self._save_to_cache(endpoint, params, result)
            
            return result
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                raise GitHubRateLimitError(f"GitHub API Rate Limit überschritten: {response.text}")
            elif response.status_code == 404:
                logger.warning(f"Ressource nicht gefunden: {url}")
                return {}
            else:
                raise GitHubAPIError(f"HTTP-Fehler: {e} - {response.text if 'response' in locals() else ''}")
        
        except RequestException as e:
            raise GitHubAPIError(f"Request-Fehler: {e}")
        
        except Exception as e:
            raise GitHubAPIError(f"Unerwarteter Fehler: {e}")

class GitHubTokenPool:
    """
    Verwaltet einen Pool von GitHub API Tokens.
    
    Diese Klasse ermöglicht die Rotation von Tokens, um die Rate-Limits
    der GitHub API optimal auszunutzen.
    """
    
    def __init__(self, tokens: List[str]):
        """
        Initialisiere den Token-Pool.
        
        Args:
            tokens: Liste von GitHub API Tokens
        """
        self.tokens = tokens
        self.token_info = {}
        
        for token in tokens:
            self.token_info[token] = {
                'remaining': 5000,
                'reset_time': 0,
                'last_used': 0
            }
    
    def get_best_token(self) -> str:
        """
        Wähle das beste Token aus dem Pool.
        
        Returns:
            Das Token mit den meisten verbleibenden Anfragen
        """
        now = datetime.now().timestamp()
        available_tokens = []
        
        for token, info in self.token_info.items():
            # Prüfe, ob das Rate Limit zurückgesetzt wurde
            if now > info['reset_time']:
                info['remaining'] = 5000
                info['reset_time'] = now + 3600  # Annahme: 1 Stunde bis zum Reset
            
            # Füge verfügbare Tokens hinzu
            if info['remaining'] > 0:
                available_tokens.append((token, info['remaining'], info['last_used']))
        
        if not available_tokens:
            # Alle Tokens haben das Rate Limit erreicht, wähle das mit der frühesten Reset-Zeit
            token = min(self.token_info.items(), key=lambda x: x[1]['reset_time'])[0]
            wait_time = self.token_info[token]['reset_time'] - now
            logger.warning(f"Alle Tokens haben das Rate Limit erreicht. Warte {wait_time:.1f} Sekunden...")
            time.sleep(max(0, wait_time) + 1)  # +1 Sekunde Puffer
            return token
        
        # Sortiere nach verbleibenden Anfragen (absteigend) und letzter Verwendung (aufsteigend)
        available_tokens.sort(key=lambda x: (-x[1], x[2]))
        token = available_tokens[0][0]
        
        # Aktualisiere die letzte Verwendung
        self.token_info[token]['last_used'] = now
        
        return token
    
    def update_token_info(self, token: str, remaining: int, reset_time: int) -> None:
        """
        Aktualisiere die Informationen für ein Token.
        
        Args:
            token: GitHub API Token
            remaining: Verbleibende Anfragen
            reset_time: Unix-Timestamp für den Reset des Rate Limits
        """
        if token in self.token_info:
            self.token_info[token]['remaining'] = remaining
            self.token_info[token]['reset_time'] = reset_time

class GitHubAPI:
    """
    Hauptschnittstelle für die GitHub API.
    
    Diese Klasse kombiniert den Token-Pool und den GitHub-Client, um eine
    effiziente und robuste Kommunikation mit der GitHub API zu ermöglichen.
    """
    
    def __init__(self, tokens: Union[str, List[str]], cache_dir: Optional[str] = None):
        """
        Initialisiere die GitHub API.
        
        Args:
            tokens: Ein einzelnes Token oder eine Liste von Tokens
            cache_dir: Verzeichnis für den Cache (optional)
        """
        # Konvertiere einzelnes Token in Liste
        if isinstance(tokens, str):
            tokens = [tokens]
        
        self.token_pool = GitHubTokenPool(tokens)
        self.clients = {token: GitHubClient(token, cache_dir) for token in tokens}
        self.cache_dir = cache_dir
    
    def _get_client(self) -> GitHubClient:
        """
        Wähle den besten Client basierend auf dem Token-Pool.
        
        Returns:
            GitHub-Client mit dem besten Token
        """
        token = self.token_pool.get_best_token()
        client = self.clients[token]
        
        # Aktualisiere Token-Pool mit aktuellen Informationen
        self.token_pool.update_token_info(
            token,
            client.rate_limit_remaining,
            client.rate_limit_reset
        )
        
        return client
    
    def request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                data: Dict[str, Any] = None, use_cache: bool = True, retries: int = 3) -> Dict[str, Any]:
        """
        Sende eine Anfrage an die GitHub API mit automatischer Token-Rotation.
        
        Args:
            method: HTTP-Methode (GET, POST, etc.)
            endpoint: API-Endpunkt
            params: Query-Parameter
            data: Request-Body für POST/PUT
            use_cache: Cache verwenden (nur für GET)
            retries: Anzahl der Wiederholungsversuche bei Fehlern
            
        Returns:
            API-Antwort als Dictionary
        """
        for attempt in range(retries):
            try:
                client = self._get_client()
                return client.request(method, endpoint, params, data, use_cache)
            
            except GitHubRateLimitError:
                if attempt < retries - 1:
                    logger.warning(f"Rate Limit erreicht, versuche einen anderen Token (Versuch {attempt + 1}/{retries})")
                    # Kurze Pause vor dem nächsten Versuch
                    time.sleep(random.uniform(1, 3))
                else:
                    raise
            
            except GitHubAPIError as e:
                if attempt < retries - 1:
                    logger.warning(f"API-Fehler: {e}, wiederhole (Versuch {attempt + 1}/{retries})")
                    # Exponentielles Backoff
                    time.sleep(2 ** attempt + random.uniform(0, 1))
                else:
                    raise
    
    # Hilfreiche Methoden für häufige API-Aufrufe
    
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Rufe Informationen zu einem Repository ab.
        
        Args:
            owner: Repository-Eigentümer (Benutzer oder Organisation)
            repo: Repository-Name
            
        Returns:
            Repository-Informationen
        """
        endpoint = f"repos/{owner}/{repo}"
        return self.request("GET", endpoint)
    
    def get_repositories(self, since: Optional[int] = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Rufe eine Liste von Repositories ab.
        
        Args:
            since: Repository-ID, ab der die Ergebnisse beginnen sollen
            per_page: Anzahl der Ergebnisse pro Seite (max. 100)
            
        Returns:
            Liste von Repositories
        """
        params = {"per_page": per_page}
        if since is not None:
            params["since"] = since
        
        return self.request("GET", "repositories", params)
    
    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc", 
                           per_page: int = 100, page: int = 1) -> Dict[str, Any]:
        """
        Suche nach Repositories.
        
        Args:
            query: Suchanfrage
            sort: Sortierkriterium (stars, forks, updated)
            order: Sortierreihenfolge (asc, desc)
            per_page: Anzahl der Ergebnisse pro Seite (max. 100)
            page: Seitennummer
            
        Returns:
            Suchergebnisse
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page
        }
        
        return self.request("GET", "search/repositories", params)
    
    def get_contributor(self, username: str) -> Dict[str, Any]:
        """
        Rufe Informationen zu einem Contributor ab.
        
        Args:
            username: GitHub-Benutzername
            
        Returns:
            Contributor-Informationen
        """
        endpoint = f"users/{username}"
        return self.request("GET", endpoint)
    
    def get_repository_contributors(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """
        Rufe die Contributors eines Repositories ab.
        
        Args:
            owner: Repository-Eigentümer (Benutzer oder Organisation)
            repo: Repository-Name
            per_page: Anzahl der Ergebnisse pro Seite (max. 100)
            page: Seitennummer
            
        Returns:
            Liste von Contributors
        """
        endpoint = f"repos/{owner}/{repo}/contributors"
        params = {
            "per_page": per_page,
            "page": page,
            "anon": "true"  # Auch anonyme Contributors einbeziehen
        }
        
        return self.request("GET", endpoint, params)
    
    def get_organization(self, org_name: str) -> Dict[str, Any]:
        """
        Rufe Informationen zu einer Organisation ab.
        
        Args:
            org_name: Name der Organisation
            
        Returns:
            Organisations-Informationen
        """
        endpoint = f"orgs/{org_name}"
        return self.request("GET", endpoint)
    
    def get_organization_repositories(self, org_name: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """
        Rufe die Repositories einer Organisation ab.
        
        Args:
            org_name: Name der Organisation
            per_page: Anzahl der Ergebnisse pro Seite (max. 100)
            page: Seitennummer
            
        Returns:
            Liste von Repositories
        """
        endpoint = f"orgs/{org_name}/repos"
        params = {
            "per_page": per_page,
            "page": page
        }
        
        return self.request("GET", endpoint, params)
    
    def get_repository_commits(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """
        Rufe die Commits eines Repositories ab.
        
        Args:
            owner: Repository-Eigentümer (Benutzer oder Organisation)
            repo: Repository-Name
            per_page: Anzahl der Ergebnisse pro Seite (max. 100)
            page: Seitennummer
            
        Returns:
            Liste von Commits
        """
        endpoint = f"repos/{owner}/{repo}/commits"
        params = {
            "per_page": per_page,
            "page": page
        }
        
        return self.request("GET", endpoint, params)
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Rufe Informationen zum Rate Limit ab.
        
        Returns:
            Rate-Limit-Informationen
        """
        return self.request("GET", "rate_limit")
