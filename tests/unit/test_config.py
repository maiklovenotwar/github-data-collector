"""
Unit-Tests für die Konfigurationskomponente.

Diese Tests überprüfen die korrekte Funktionsweise der Konfigurationskomponente.
"""
import os
import pytest
from pathlib import Path

from github_collector import config


def test_config_paths():
    """Testet, ob die Konfigurationspfade korrekt gesetzt sind."""
    # Teste, ob BASE_DIR korrekt gesetzt ist
    expected_base_dir = Path(__file__).resolve().parent.parent.parent
    assert config.BASE_DIR == expected_base_dir
    
    # Teste, ob DATA_DIR korrekt gesetzt ist
    assert config.DATA_DIR == expected_base_dir / "data"
    
    # Teste, ob LOG_DIR korrekt gesetzt ist
    assert config.LOG_DIR == expected_base_dir / "logs"
    
    # Teste, ob CACHE_DIR korrekt gesetzt ist
    assert config.CACHE_DIR == config.DATA_DIR / "cache"
    
    # Teste, ob PERFORMANCE_OUTPUT_DIR korrekt gesetzt ist
    assert config.PERFORMANCE_OUTPUT_DIR == config.LOG_DIR / "performance"


def test_config_db_settings():
    """Testet, ob die Datenbankeinstellungen korrekt gesetzt sind."""
    # Teste, ob DEFAULT_DB_PATH korrekt gesetzt ist
    assert config.DEFAULT_DB_PATH == config.BASE_DIR / "github_data.db"
    
    # Teste, ob DB_URL korrekt gesetzt ist
    expected_db_url = f"sqlite:///{config.DEFAULT_DB_PATH}"
    assert config.DB_URL == expected_db_url


def test_config_log_settings():
    """Testet, ob die Logging-Einstellungen korrekt gesetzt sind."""
    # Teste, ob LOG_LEVEL korrekt gesetzt ist
    assert hasattr(config, "LOG_LEVEL")
    
    # Teste, ob die Log-Dateipfade korrekt gesetzt sind
    assert config.REPOSITORY_LOG == config.LOG_DIR / "repository_collection.log"
    assert config.GEOCODING_LOG == config.LOG_DIR / "geocoding.log"
    assert config.EXPORT_LOG == config.LOG_DIR / "export.log"
    assert config.RESET_LOG == config.LOG_DIR / "reset_and_collect.log"


def test_config_collection_state():
    """Testet, ob die Collection-State-Einstellungen korrekt gesetzt sind."""
    # Teste, ob COLLECTION_STATE_FILE korrekt gesetzt ist
    assert config.COLLECTION_STATE_FILE == config.BASE_DIR / "collection_state.json"


def test_config_performance_tracking():
    """Testet, ob die Performance-Tracking-Einstellungen korrekt gesetzt sind."""
    # Teste, ob ENABLE_PERFORMANCE_TRACKING korrekt gesetzt ist
    assert isinstance(config.ENABLE_PERFORMANCE_TRACKING, bool)
    
    # Teste, ob PERFORMANCE_OUTPUT_DIR korrekt gesetzt ist
    assert config.PERFORMANCE_OUTPUT_DIR == config.LOG_DIR / "performance"
