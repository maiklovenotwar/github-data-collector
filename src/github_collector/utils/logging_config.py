"""
Konfiguration des Loggings für den GitHub Data Collector.

Dieses Modul bietet eine einheitliche Konfiguration für das Logging in allen Teilen
des GitHub Data Collectors. Es ermöglicht eine konsistente Formatierung und Handhabung
von Log-Nachrichten über das gesamte Projekt hinweg.
"""
import logging
import os
from typing import Optional


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO, logger_name: Optional[str] = None) -> logging.Logger:
    """
    Richtet das Logging für den GitHub Data Collector ein.
    
    Diese Funktion konfiguriert einen Logger mit konsistenter Formatierung für die Verwendung
    im gesamten Projekt. Sie unterstützt sowohl Konsolen- als auch Datei-Logging.
    
    Args:
        log_file: Pfad zur Log-Datei (optional). Wenn nicht angegeben, wird nur auf die Konsole geloggt.
        level: Logging-Level (Standard: INFO)
        logger_name: Name des Loggers (optional). Wenn nicht angegeben, wird der Name des aufrufenden Moduls verwendet.
    
    Returns:
        Logger-Instanz, die für das Logging verwendet werden kann
    """
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
        # Stelle sicher, dass das Verzeichnis existiert
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
