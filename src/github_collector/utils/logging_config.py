"""
Konfiguration des Loggings für den GitHub Data Collector.

Dieses Modul bietet eine einheitliche Konfiguration für das Logging in allen Teilen
des GitHub Data Collectors. Es ermöglicht eine konsistente Formatierung und Handhabung
von Log-Nachrichten über das gesamte Projekt hinweg.
"""
import logging
import os
from typing import Optional
from pathlib import Path

from github_collector import config


def setup_logging(log_file: Optional[str] = None, level: Optional[int] = None, logger_name: Optional[str] = None) -> logging.Logger:
    """
    Richtet das Logging für den GitHub Data Collector ein.
    
    Diese Funktion konfiguriert einen Logger mit konsistenter Formatierung für die Verwendung
    im gesamten Projekt. Sie unterstützt sowohl Konsolen- als auch Datei-Logging.
    
    Args:
        log_file: Pfad zur Log-Datei (optional). Wenn nicht angegeben, wird der Pfad aus der Konfiguration verwendet.
        level: Logging-Level (optional). Wenn nicht angegeben, wird der Level aus der Konfiguration verwendet.
        logger_name: Name des Loggers (optional). Wenn nicht angegeben, wird der Name des aufrufenden Moduls verwendet.
    
    Returns:
        Logger-Instanz, die für das Logging verwendet werden kann
    """
    # Verwende Konfigurationsparameter, wenn nicht explizit angegeben
    if level is None:
        level_str = config.LOG_LEVEL
        level = getattr(logging, level_str) if hasattr(logging, level_str) else logging.INFO
    
    # Bestimme den Logger-Namen
    if logger_name is None:
        # Verwende den Namen des aufrufenden Moduls
        import inspect
        caller_frame = inspect.stack()[1]
        module = inspect.getmodule(caller_frame[0])
        logger_name = module.__name__ if module else "__main__"
    
    # Erstelle Logger mit dem bestimmten Namen
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Entferne bestehende Handler, um Duplikate zu vermeiden
    if logger.handlers:
        logger.handlers.clear()
    
    # Erstelle Formatter für konsistentes Log-Format
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Erstelle und konfiguriere Konsolen-Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Erstelle und konfiguriere Datei-Handler, falls log_file angegeben
    if log_file:
        # Konvertiere String zu Path-Objekt, falls notwendig
        log_file_path = Path(log_file) if isinstance(log_file, str) else log_file
        
        # Stelle sicher, dass das Verzeichnis existiert
        log_dir = log_file_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_repository_logger() -> logging.Logger:
    """Erstellt einen Logger für die Repository-Sammlung."""
    return setup_logging(log_file=config.REPOSITORY_LOG)


def get_geocoding_logger() -> logging.Logger:
    """Erstellt einen Logger für die Geocoding-Funktionalität."""
    return setup_logging(log_file=config.GEOCODING_LOG)


def get_export_logger() -> logging.Logger:
    """Erstellt einen Logger für die Export-Funktionalität."""
    return setup_logging(log_file=config.EXPORT_LOG)
