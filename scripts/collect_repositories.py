#!/usr/bin/env python3
"""
Skript zum Sammeln von GitHub-Repositories.
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dateutil import tz

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.api.github_api import GitHubAPI
from github_collector.database.database import GitHubDatabase
from github_collector.repository_collector import RepositoryCollector
from github_collector.ui.stats import show_database_stats

# Konfiguriere Logging
from github_collector.utils.logging_config import setup_logging

logger = setup_logging(log_file="repository_collection.log")


def setup_api_client():
    """Richte den GitHub API-Client ein."""
    # Lade Umgebungsvariablen aus .env-Datei, falls verfügbar
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    
    # Hole GitHub API-Token aus Umgebungsvariable
    github_token = os.environ.get("GITHUB_API_TOKEN")
    github_tokens = os.environ.get("GITHUB_API_TOKENS")
    
    if github_tokens:
        # Mehrere Tokens verwenden
        tokens = [token.strip() for token in github_tokens.split(",")]
        logger.info(f"{len(tokens)} GitHub API-Tokens gefunden")
    elif github_token:
        # Einzelnes Token verwenden
        tokens = [github_token]
        logger.info("GitHub API-Token gefunden")
    else:
        # Kein Token gefunden
        logger.warning("Kein GitHub API-Token in Umgebungsvariablen gefunden")
        github_token = input("Bitte gib dein GitHub API-Token ein: ").strip()
        if not github_token:
            raise ValueError("GitHub API-Token ist erforderlich")
        tokens = [github_token]
    
    # Cache-Verzeichnis
    cache_dir = os.environ.get("CACHE_DIR", ".github_cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Erstelle und gib den API-Client zurück
    return GitHubAPI(tokens, cache_dir=cache_dir)


def parse_arguments():
    """Parse Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(description="Sammle GitHub-Repositories")
    
    # Zeitbereichsoptionen
    time_group = parser.add_argument_group("Zeitbereichsoptionen")
    time_group.add_argument("--time-range", choices=["week", "month", "year", "custom"], 
                           help="Vordefinierter Zeitbereich für die Repository-Sammlung")
    time_group.add_argument("--start-date", help="Startdatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)")
    time_group.add_argument("--end-date", help="Enddatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)")
    
    # Sammlungsoptionen
    collection_group = parser.add_argument_group("Sammlungsoptionen")
    collection_group.add_argument("--limit", type=int, help="Maximale Anzahl zu sammelnder Repositories")
    collection_group.add_argument("--all", action="store_true", help="Alle verfügbaren Repositories sammeln")
    collection_group.add_argument("--min-stars", type=int, default=100, 
                                help="Minimale Anzahl von Stars für Repositories (Standard: 100)")
    
    # Datenbankoptionen
    db_group = parser.add_argument_group("Datenbankoptionen")
    db_group.add_argument("--db-path", help="Pfad zur SQLite-Datenbankdatei")
    
    # Andere Optionen
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Im nicht-interaktiven Modus ausführen (erfordert Zeitbereichs- und Limit-Optionen)")
    parser.add_argument("--stats", action="store_true", 
                       help="Datenbankstatistiken anzeigen und beenden")
    
    return parser.parse_args()





def interactive_mode(args, api_client, db):
    """Führe im interaktiven Modus aus."""
    # Zeige aktuelle Statistiken an
    show_database_stats(db)
    
    # Initialisiere Repository-Collector
    collector = RepositoryCollector(github_client=api_client, db=db)
    
    # Frage nach Zeitbereich, falls nicht angegeben
    if not args.time_range:
        print("\nWähle einen Zeitbereich für die Repository-Sammlung:")
        print("1. Letzte Woche")
        print("2. Letzter Monat")
        print("3. Letztes Jahr")
        print("4. Benutzerdefinierter Zeitbereich")
        
        choice = input("Deine Wahl (1-4): ").strip()
        
        if choice == "1":
            args.time_range = "week"
        elif choice == "2":
            args.time_range = "month"
        elif choice == "3":
            args.time_range = "year"
        elif choice == "4":
            args.time_range = "custom"
        else:
            logger.error("Ungültige Auswahl")
            return
    
    # Berechne Zeitbereich
    now = datetime.now(tz.UTC)
    
    if args.time_range == "week":
        # Letzte Woche
        end_date = now
        start_date = now - timedelta(days=7)
    elif args.time_range == "month":
        # Letzter Monat
        end_date = now
        start_date = now - timedelta(days=30)
    elif args.time_range == "year":
        # Letztes Jahr
        end_date = now
        start_date = now - timedelta(days=365)
    elif args.time_range == "custom":
        # Benutzerdefinierter Zeitbereich
        if args.start_date and args.end_date:
            try:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
            except ValueError as e:
                logger.error(f"Ungültiges Datumsformat: {e}")
                return
        else:
            try:
                print("Startdatum (YYYY-MM-DD):")
                start_date_str = input().strip()
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=tz.UTC)
                
                print("Enddatum (YYYY-MM-DD):")
                end_date_str = input().strip()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=tz.UTC)
            except ValueError as e:
                logger.error(f"Ungültiges Datumsformat: {e}")
                return
    else:
        logger.error(f"Ungültiger Zeitbereich: {args.time_range}")
        return
    
    # Frage nach Limit, falls nicht angegeben
    limit = args.limit
    if not limit and not args.all:
        try:
            print("\nMaximale Anzahl zu sammelnder Repositories (leer für unbegrenzt):")
            limit_str = input().strip()
            if limit_str:
                limit = int(limit_str)
        except ValueError:
            logger.error("Ungültige Anzahl")
            return
    
    # Frage nach minimaler Anzahl von Stars
    try:
        default_stars = args.min_stars if args.min_stars else 10
        print(f"\nMinimale Anzahl von Stars (Standard: {default_stars}):")
        min_stars_str = input().strip()
        if min_stars_str:
            min_stars = int(min_stars_str)
        else:
            min_stars = default_stars
    except ValueError:
        logger.error("Ungültige Anzahl von Stars")
        return
            
    # Frage nach Anzahl der Perioden
    time_diff = end_date - start_date
    days_total = time_diff.days
    
    # Berechne eine sinnvolle Standardanzahl von Perioden basierend auf der Zeitspanne
    if days_total <= 7:
        default_periods = 1
    elif days_total <= 30:
        default_periods = 3
    elif days_total <= 90:
        default_periods = 6
    elif days_total <= 365:
        default_periods = 12
    else:
        default_periods = days_total // 30  # Etwa eine Periode pro Monat
    
    periods_count = None
    while periods_count is None:
        try:
            print(f"\nIn wie viele Perioden soll der Zeitraum unterteilt werden?")
            print(f"(Zeitraum: {days_total} Tage, Vorschlag: {default_periods} Perioden)")
            periods_str = input("Anzahl der Perioden: ").strip()
            
            if periods_str:
                periods_count = int(periods_str)
                if periods_count <= 0:
                    print("Die Anzahl der Perioden muss größer als 0 sein.")
                    periods_count = None
            else:
                periods_count = default_periods
                print(f"Standard-Wert wird verwendet: {periods_count} Perioden")
        except ValueError:
            print("Bitte geben Sie eine gültige Zahl ein.")
    
    # Bestätige die Sammlung
    print(f"\nSammle Repositories von {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')}")
    print(f"Minimale Anzahl von Stars: {min_stars}")
    print(f"Zeitraum wird in {periods_count} Perioden unterteilt")
    if limit:
        print(f"Maximale Anzahl zu sammelnder Repositories: {limit}")
    else:
        print("Keine Begrenzung der Anzahl zu sammelnder Repositories")
    
    confirm = input("\nFortfahren? (j/n): ").strip().lower()
    if confirm != "j" and confirm != "ja":
        print("Sammlung abgebrochen")
        return
    
    # Berechne die Perioden manuell, um die vom Benutzer angegebene Anzahl zu verwenden
    period_size = days_total / periods_count
    periods = []
    current_start = start_date
    
    for i in range(periods_count):
        # Berechne das Ende dieser Periode
        if i == periods_count - 1:
            # Letzte Periode endet genau am Ende des Zeitraums
            current_end = end_date
        else:
            # Berechne das Ende basierend auf der Periodengröße
            current_end = current_start + timedelta(days=period_size)
        
        # Füge die Periode hinzu
        periods.append((current_start, current_end))
        
        # Nächste Periode
        current_start = current_end
    
    # Sammle Repositories
    try:
        # Setze den Zustand zurück und setze die benutzerdefinierten Perioden
        collector.state.reset(start_date, end_date)
        collector.state.set_time_periods(periods)
        
        # Starte die Sammlung
        collector.collect_repositories(
            start_date=start_date,
            end_date=end_date,
            min_stars=min_stars,
            max_repos=limit,
            resume=True
        )
    except KeyboardInterrupt:
        print("\nSammlung unterbrochen. Der Fortschritt wurde gespeichert und kann später fortgesetzt werden.")
    except Exception as e:
        logger.error(f"Fehler bei der Repository-Sammlung: {e}")
    
    # Zeige aktualisierte Statistiken an
    show_database_stats(db)


def non_interactive_mode(args, api_client, db):
    """Führe im nicht-interaktiven Modus aus."""
    # Prüfe, ob alle erforderlichen Argumente angegeben sind
    if not args.time_range and not (args.start_date and args.end_date):
        logger.error("Im nicht-interaktiven Modus muss entweder --time-range oder --start-date und --end-date angegeben werden")
        return
    
    # Berechne Zeitbereich
    now = datetime.now(tz.UTC)
    
    if args.time_range == "week":
        # Letzte Woche
        end_date = now
        start_date = now - timedelta(days=7)
    elif args.time_range == "month":
        # Letzter Monat
        end_date = now
        start_date = now - timedelta(days=30)
    elif args.time_range == "year":
        # Letztes Jahr
        end_date = now
        start_date = now - timedelta(days=365)
    elif args.time_range == "custom" or (args.start_date and args.end_date):
        # Benutzerdefinierter Zeitbereich
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
        except ValueError as e:
            logger.error(f"Ungültiges Datumsformat: {e}")
            return
    else:
        logger.error(f"Ungültiger Zeitbereich: {args.time_range}")
        return
    
    # Initialisiere Repository-Collector
    collector = RepositoryCollector(github_client=api_client, db=db)
    
    # Sammle Repositories
    try:
        collector.collect_repositories(
            start_date=start_date,
            end_date=end_date,
            min_stars=args.min_stars,
            max_repos=args.limit,
            resume=True
        )
    except KeyboardInterrupt:
        print("\nSammlung unterbrochen. Der Fortschritt wurde gespeichert und kann später fortgesetzt werden.")
    except Exception as e:
        logger.error(f"Fehler bei der Repository-Sammlung: {e}")


def main():
    """Hauptfunktion."""
    args = parse_arguments()
    
    # Datenbankpfad
    db_path = args.db_path or os.environ.get("DATABASE_URL", "github_data.db")
    if not db_path.startswith("sqlite:///"):
        db_path = f"sqlite:///{db_path}"
    
    # Initialisiere Datenbank
    db = GitHubDatabase(db_path)
    
    # Zeige nur Statistiken an, falls angefordert
    if args.stats:
        show_database_stats(db)
        return
    
    # Initialisiere API-Client
    try:
        api_client = setup_api_client()
    except ValueError as e:
        logger.error(f"Fehler beim Einrichten des API-Clients: {e}")
        return
    
    # Führe im interaktiven oder nicht-interaktiven Modus aus
    try:
        if args.non_interactive:
            non_interactive_mode(args, api_client, db)
        else:
            interactive_mode(args, api_client, db)
    finally:
        # Schließe Datenbankverbindung
        db.close()


if __name__ == "__main__":
    main()
