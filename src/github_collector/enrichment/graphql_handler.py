"""
GraphQL Handler für Repository Stats Enrichment via GitHub GraphQL API
"""
import os
import time
import logging
from typing import List, Dict, Any
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

class GraphQLHandler:
    """
    Handler für die Kommunikation mit der GitHub GraphQL API zur Anreicherung von Repository-Statistiken.

    Initialisiert einen GraphQL-Client mit Token und Endpunkt, unterstützt Batching und Fehlerbehandlung.

    :param github_token: GitHub API Token (optional, sonst via Umgebungsvariable)
    :param batch_size: Anzahl der Repositories pro API-Batch
    """
    def __init__(self, github_token: str = None, batch_size: int = 50):
        self.github_token = github_token or os.getenv("GITHUB_API_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub API Token nicht gefunden (Umgebungsvariable GITHUB_API_TOKEN)")
        self.batch_size = batch_size
        self.endpoint = "https://api.github.com/graphql"
        self.client = Client(
            transport=RequestsHTTPTransport(
                url=self.endpoint,
                headers={"Authorization": f"Bearer {self.github_token}"},
                retries=3,
                timeout=20,  # Timeout in Sekunden
            ),
            fetch_schema_from_transport=False,
        )

    def fetch_repo_stats(self, repos: List[Dict[str, str]]) -> (List[Dict[str, Any]], List[List[Dict[str, str]]]):
        """
        Fragt für eine Liste von Repositories (owner/name) die gewünschten Statistiken per GitHub GraphQL API ab.
        
        Führt die Abfrage in Batches durch, behandelt Rate-Limits, implementiert Retry-Logik (3 Versuche)
        mit exponentiellem Backoff und speichert den Fortschritt in einer Checkpoint-Datei.
        
        :param repos: Liste von Dictionaries mit owner und name der Repositories
        :return: Tuple (Liste mit Ergebnis-Dicts, Liste der fehlgeschlagenen Batches)
        
        Jedes Ergebnis-Dict enthält: repo_id, calculated_pr_count, calculated_commit_count, calculated_contributor_count
        Bei Fehlern werden die betroffenen Batches gesammelt und zurückgegeben.
        Fortschritt kann über die Checkpoint-Datei wieder aufgenommen werden.
        """
        import requests
        import json
        logger = logging.getLogger(__name__)
        results = []
        failed_batches = []
        checkpoint_path = "enrich_checkpoint.txt"
        # Checkpoint laden
        start_batch_idx = 0
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r') as f:
                    start_batch_idx = int(f.read().strip())
                logger.info(f"Checkpoint gefunden: Starte ab Batch-Index {start_batch_idx}.")
            except Exception as e:
                logger.warning(f"Checkpoint-Datei konnte nicht gelesen werden: {e}. Ignoriere Checkpoint.")
                start_batch_idx = 0
        all_batches = list(self._batch(repos, self.batch_size))
        for batch_idx, batch in enumerate(all_batches):
            if batch_idx < start_batch_idx:
                continue  # Überspringe bereits verarbeitete Batches
            query, variables = self._build_batch_query(batch)
            success = False
            last_exception = None
            for attempt in range(3):  # 3 Versuche pro Batch
                try:
                    logger.debug(f"Starte GraphQL-Request für Batch {batch_idx+1}/{len(all_batches)} mit {len(batch)} Repos (Versuch {attempt+1})")
                    # --- Direkter POST-Request für RateLimit-Header ---
                    session = requests.Session()
                    headers = {
                        "Authorization": f"Bearer {self.github_token}",
                        "Content-Type": "application/json"
                    }
                    gql_payload = {"query": query, "variables": variables}
                    resp = session.post(self.endpoint, headers=headers, data=json.dumps(gql_payload), timeout=20)
                    # Rate Limit Handling
                    remaining = int(resp.headers.get("X-RateLimit-Remaining", "999"))
                    reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
                    logger.info(f"GitHub RateLimit: remaining={remaining}, reset={reset_ts}")
                    if remaining <= 3:
                        wait_sec = max(0, reset_ts - int(time.time()) + 2)
                        logger.warning(f"Rate Limit fast erreicht! Schlafe {wait_sec} Sekunden bis zum Reset...")
                        time.sleep(wait_sec)
                    # Fehlerbehandlung HTTP
                    if resp.status_code >= 500:
                        logger.error(f"HTTP 5xx Fehler: {resp.status_code} {resp.reason}. Versuch {attempt+1}")
                        raise requests.exceptions.HTTPError(f"HTTP 5xx Fehler: {resp.status_code} {resp.reason}")
                    if resp.status_code == 403 and remaining == 0:
                        logger.warning(f"Rate Limit erreicht (403)! Schlafe bis zum Reset...")
                        wait_sec = max(0, reset_ts - int(time.time()) + 2)
                        time.sleep(wait_sec)
                        continue
                    resp.raise_for_status()
                    response = resp.json()["data"]
                    logger.debug(f"GraphQL-Rohantwort: {response}")
                    for repo_key, repo_data in response.items():
                        if repo_data and repo_data.get("id"):
                            history = repo_data.get("defaultBranchRef", {}).get("target", {}).get("history", {})
                            results.append({
                                "repo_id": repo_data["id"],
                                "database_id": repo_data.get("databaseId"),
                                "calculated_pr_count": repo_data.get("pullRequests", {}).get("totalCount", 0),
                                "calculated_commit_count": history.get("totalCount", 0),
                                "calculated_contributor_count": 0,
                            })
                    logger.debug(f"Extrahierte results für Batch: {results}")
                    success = True
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    logger.error(f"Netzwerkfehler/Timeout bei Batch {batch_idx+1} (Versuch {attempt+1}): {e}. Batch: {[r['owner'] + '/' + r['name'] for r in batch]}")
                    last_exception = e
                    time.sleep(2 ** attempt)  # Exponentielles Backoff
                except requests.exceptions.HTTPError as e:
                    logger.error(f"HTTPError bei Batch {batch_idx+1} (Versuch {attempt+1}): {e}")
                    last_exception = e
                    time.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"Allgemeiner Fehler bei Batch {batch_idx+1} (Versuch {attempt+1}): {e}. Batch: {[r['owner'] + '/' + r['name'] for r in batch]}")
                    last_exception = e
                    time.sleep(2 ** attempt)
            # Checkpoint nach jedem Batch schreiben
            with open(checkpoint_path, 'w') as f:
                f.write(str(batch_idx + 1))
            if not success:
                logger.error(f"Batch endgültig fehlgeschlagen: {[r['owner'] + '/' + r['name'] for r in batch]}")
                failed_batches.append(batch)
        # Checkpoint entfernen, wenn alles erfolgreich
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
        logger.debug(f"Alle extrahierten results (gesamt): {results}")
        return results, failed_batches

    def _batch(self, iterable, n):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    def _build_batch_query(self, batch):
        query_parts = []
        variables = {}
        for idx, repo in enumerate(batch):
            owner = repo["owner"]
            name = repo["name"]
            var_owner = f"owner{idx}"
            var_name = f"name{idx}"
            query_parts.append(f"""repo{idx}: repository(owner: ${var_owner}, name: ${var_name}) {{
  id
  databaseId
  pullRequests {{ totalCount }}
  defaultBranchRef {{
    target {{ ... on Commit {{
      history(first: 100) {{
        totalCount
      }}
    }} }}
  }}
}}""")
            variables[var_owner] = owner
            variables[var_name] = name
        query = f"query({', '.join([f'${k}: String!' for k in variables.keys()])}) {{\n{chr(10).join(query_parts)}\n}}"
        return query, variables
