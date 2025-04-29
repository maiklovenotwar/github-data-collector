# GitHub API- und GraphQL-Komponente des GitHub Data Collectors

## Übersicht

Die API-Komponenten sind verantwortlich für die Kommunikation mit der GitHub REST API v3 **und** der GitHub GraphQL API. Für das Enrichment der Repository-Statistiken wird die GraphQL API genutzt. Beide Komponenten bieten robustes Token-Handling, Caching und Fehlerbehandlung.

## GraphQL-Integration und Fehlerbehandlung

- Für die Anreicherung von Repository-Statistiken wird die GitHub GraphQL API verwendet (siehe `enrichment/graphql_handler.py`).
- Fehler bei einzelnen Repositories führen nicht zum Abbruch des gesamten Batches, sondern werden individuell geloggt.
- Stacktraces und detaillierte Fehlerursachen werden im Logfile dokumentiert.
- Temporäre API-Fehler (z.B. 502 Bad Gateway) werden automatisch erneut versucht (Retry-Logik).
- IDs von dauerhaft fehlgeschlagenen Repositories werden in `failed_repo_ids_*.txt` gespeichert und können gezielt nachbearbeitet werden.

## Hauptfunktionalitäten

### 1. Token-Pool-Management

Die API-Komponente unterstützt die Verwendung mehrerer GitHub API-Tokens, um die Rate-Limits zu erhöhen. Der Token-Pool wird automatisch verwaltet, wobei immer der Token mit der höchsten Anzahl verbleibender Anfragen verwendet wird.

```python
# Beispiel für die Verwendung mehrerer Tokens
api_client = GitHubAPI(["token1", "token2", "token3"])
```

### 2. Rate-Limit-Handling

Die API-Komponente implementiert ein intelligentes Rate-Limit-Handling, das automatisch auf Rate-Limit-Überschreitungen reagiert:

- Automatisches Warten, wenn ein Rate-Limit erreicht wird
- Automatischer Wechsel zu einem anderen Token, wenn verfügbar
- Detaillierte Logging-Informationen zu Rate-Limits und Wartezeiten
- Vorhersage von Reset-Zeiten für Rate-Limits

### 3. Caching

Die API-Komponente implementiert ein Caching-System, um die Anzahl der API-Aufrufe zu reduzieren:

- Disk-basiertes Caching von API-Antworten
- Konfigurierbare Cache-Lebensdauer
- Automatische Invalidierung des Caches bei Änderungen

```python
# Beispiel für die Verwendung des Caches
api_client = GitHubAPI(["token"], cache_dir="api_cache")
```

### 4. Fehlerbehandlung

Die API-Komponente implementiert eine robuste Fehlerbehandlung:

- Automatische Wiederholungsversuche bei transienten Fehlern
- Detaillierte Fehlerprotokolle
- Spezifische Ausnahmen für verschiedene Fehlertypen

## Hauptmethoden

### Allgemeine API-Methoden

- `request(method, endpoint, params=None, data=None)`: Führt eine allgemeine API-Anfrage aus
- `get(endpoint, params=None)`: Führt eine GET-Anfrage aus
- `post(endpoint, data=None)`: Führt eine POST-Anfrage aus
- `put(endpoint, data=None)`: Führt eine PUT-Anfrage aus
- `delete(endpoint, data=None)`: Führt eine DELETE-Anfrage aus

### Repository-Methoden

- `get_repository(owner, repo)`: Ruft Informationen zu einem Repository ab
- `get_repository_by_id(repo_id)`: Ruft Informationen zu einem Repository anhand seiner ID ab
- `search_repositories(query, sort=None, order=None, per_page=100, page=1)`: Sucht nach Repositories
- `get_repository_contributors(owner, repo)`: Ruft die Contributors eines Repositories ab
- `get_repository_languages(owner, repo)`: Ruft die Sprachen eines Repositories ab
- `get_repository_commits(owner, repo)`: Ruft die Commits eines Repositories ab

### Benutzer-Methoden

- `get_user(username)`: Ruft Informationen zu einem Benutzer ab
- `get_user_by_id(user_id)`: Ruft Informationen zu einem Benutzer anhand seiner ID ab
- `get_user_repositories(username)`: Ruft die Repositories eines Benutzers ab
- `get_user_organizations(username)`: Ruft die Organisationen eines Benutzers ab

### Organisations-Methoden

- `get_organization(org)`: Ruft Informationen zu einer Organisation ab
- `get_organization_by_id(org_id)`: Ruft Informationen zu einer Organisation anhand ihrer ID ab
- `get_organization_repositories(org)`: Ruft die Repositories einer Organisation ab
- `get_organization_members(org)`: Ruft die Mitglieder einer Organisation ab

### Rate-Limit-Methoden

- `get_rate_limit()`: Ruft Informationen zum aktuellen Rate-Limit ab
- `get_best_token()`: Wählt den besten Token aus dem Token-Pool aus
- `update_rate_limit(token, response)`: Aktualisiert die Rate-Limit-Informationen für einen Token

## Verwendung

### Grundlegende Verwendung

```python
from github_collector.api.github_api import GitHubAPI

# Erstelle einen API-Client mit einem Token
api_client = GitHubAPI(["your_github_token"])

# Rufe Informationen zu einem Repository ab
repo_data = api_client.get_repository("octocat", "Hello-World")

# Rufe Informationen zu einem Benutzer ab
user_data = api_client.get_user("octocat")

# Rufe Informationen zu einer Organisation ab
org_data = api_client.get_organization("github")
```

### Erweiterte Verwendung

```python
from github_collector.api.github_api import GitHubAPI

# Erstelle einen API-Client mit mehreren Tokens und Cache
api_client = GitHubAPI(
    tokens=["token1", "token2", "token3"],
    cache_dir="api_cache",
    user_agent="GitHub-Data-Collector"
)

# Suche nach Repositories
repos = api_client.search_repositories(
    query="language:python stars:>1000",
    sort="stars",
    order="desc",
    per_page=100
)

# Rufe die Contributors eines Repositories ab
contributors = api_client.get_repository_contributors("octocat", "Hello-World")

# Rufe die Sprachen eines Repositories ab
languages = api_client.get_repository_languages("octocat", "Hello-World")
```

## Konfiguration

Die API-Komponente kann über folgende Parameter konfiguriert werden:

- `tokens`: Liste von GitHub API-Tokens
- `cache_dir`: Verzeichnis für den API-Cache
- `user_agent`: User-Agent für API-Anfragen
- `timeout`: Timeout für API-Anfragen in Sekunden
- `max_retries`: Maximale Anzahl von Wiederholungsversuchen bei transienten Fehlern
- `retry_delay`: Verzögerung zwischen Wiederholungsversuchen in Sekunden

## Rate-Limit-Informationen

Die GitHub API hat folgende Rate-Limits:

- **Authentifizierte Anfragen**: 5.000 Anfragen pro Stunde
- **Unauthentifizierte Anfragen**: 60 Anfragen pro Stunde
- **Search API**: 30 Anfragen pro Minute

Die API-Komponente verwaltet diese Rate-Limits automatisch und stellt sicher, dass die Anwendung nicht mehr Anfragen sendet, als erlaubt sind.

## Caching-Strategie

Die API-Komponente implementiert folgende Caching-Strategie:

1. **Disk-basiertes Caching**: API-Antworten werden auf der Festplatte gespeichert
2. **Endpunkt-basiertes Caching**: Jeder API-Endpunkt hat seinen eigenen Cache
3. **Parameter-basiertes Caching**: Der Cache berücksichtigt die Parameter der Anfrage
4. **Zeitbasierte Invalidierung**: Der Cache wird nach einer konfigurierbaren Zeit invalidiert

## Fehlerbehandlung

Die API-Komponente behandelt folgende Fehlertypen:

- **Rate-Limit-Überschreitungen**: Automatisches Warten und Wiederholung
- **Netzwerkfehler**: Automatische Wiederholung mit exponentieller Verzögerung
- **API-Fehler**: Spezifische Ausnahmen für verschiedene Fehlertypen
- **Authentifizierungsfehler**: Spezifische Ausnahmen für Authentifizierungsprobleme

## Leistungsoptimierung

Die API-Komponente implementiert folgende Leistungsoptimierungen:

1. **Token-Pool**: Erhöht die Anzahl der möglichen Anfragen pro Stunde
2. **Caching**: Reduziert die Anzahl der API-Aufrufe
3. **Batch-Anfragen**: Reduziert den Overhead bei der Verarbeitung
4. **Intelligentes Rate-Limit-Handling**: Minimiert Wartezeiten bei Rate-Limit-Überschreitungen

## Sicherheitsüberlegungen

Die API-Komponente berücksichtigt folgende Sicherheitsaspekte:

1. **Token-Sicherheit**: Tokens werden nicht im Klartext protokolliert
2. **HTTPS**: Alle API-Anfragen verwenden HTTPS
3. **User-Agent**: Ein spezifischer User-Agent wird für alle Anfragen verwendet
4. **Minimale Berechtigungen**: Die Anwendung benötigt nur Lesezugriff auf öffentliche Repositories
