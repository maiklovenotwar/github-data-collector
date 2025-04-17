"""
Pytest-Konfiguration für den GitHub Data Collector.

Diese Datei enthält Fixtures und Konfigurationen für die Tests des GitHub Data Collectors.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.database.database import GitHubDatabase, init_db
from github_collector.api.github_api import GitHubAPI


@pytest.fixture
def temp_db_path():
    """Erstellt einen temporären Pfad für eine Testdatenbank."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_path = tmp.name
    return f"sqlite:///{db_path}"


@pytest.fixture
def test_db(temp_db_path):
    """Erstellt eine Testdatenbank und gibt eine Datenbankverbindung zurück."""
    # Initialisiere die Datenbank
    init_db(temp_db_path)
    
    # Erstelle eine Datenbankverbindung
    db = GitHubDatabase(temp_db_path)
    
    yield db
    
    # Bereinige nach dem Test
    db.close()
    
    # Lösche die Datenbankdatei
    db_path = temp_db_path.replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def mock_github_api():
    """Erstellt eine Mock-Version des GitHub API-Clients."""
    # Erstelle einen API-Client mit einem Dummy-Token
    api = GitHubAPI(["dummy_token"])
    
    # Überschreibe die request-Methode, um keine echten API-Aufrufe zu machen
    original_request = api.request
    
    def mock_request(method, endpoint, params=None, data=None):
        # Hier könnten je nach Endpoint Mock-Daten zurückgegeben werden
        if endpoint == "/users/octocat":
            return {
                "login": "octocat",
                "id": 1,
                "name": "The Octocat",
                "company": "GitHub",
                "blog": "https://github.blog",
                "location": "San Francisco, CA",
                "email": None,
                "hireable": None,
                "bio": "I'm the GitHub mascot!",
                "twitter_username": None,
                "public_repos": 8,
                "public_gists": 8,
                "followers": 3938,
                "following": 9,
                "created_at": "2011-01-25T18:44:36Z",
                "updated_at": "2023-01-22T12:16:22Z"
            }
        elif endpoint == "/repos/octocat/Hello-World":
            return {
                "id": 1296269,
                "name": "Hello-World",
                "full_name": "octocat/Hello-World",
                "owner": {
                    "login": "octocat",
                    "id": 1,
                    "type": "User"
                },
                "private": False,
                "description": "My first repository on GitHub!",
                "fork": False,
                "created_at": "2011-01-26T19:01:12Z",
                "updated_at": "2023-01-22T12:16:22Z",
                "pushed_at": "2023-01-22T12:16:22Z",
                "homepage": "https://github.com",
                "size": 108,
                "stargazers_count": 2000,
                "watchers_count": 2000,
                "language": "Python",
                "forks_count": 1000,
                "open_issues_count": 0,
                "default_branch": "main"
            }
        else:
            # Für unbekannte Endpoints leere Antwort zurückgeben
            return {}
    
    # Ersetze die request-Methode durch die Mock-Version
    api.request = mock_request
    
    yield api
    
    # Stelle die ursprüngliche Methode wieder her
    api.request = original_request
