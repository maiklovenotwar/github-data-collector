#!/usr/bin/env python3
"""
Skript zum Sammeln von GitHub-Repositories.

Dieses Skript bietet einen interaktiven und nicht-interaktiven Modus zur Sammlung von GitHub-Repositories mit Unterstützung für Star-Range-Filter, Zeitbereiche und weitere Optionen.
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
from dateutil import tz

# Immer das src-Verzeichnis in den Modulpfad aufnehmen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from github_collector.api.github_api import GitHubAPI
from github_collector.database.database import GitHubDatabase
from github_collector.repository_collector import RepositoryCollector
from github_collector.ui.stats import show_database_stats
from github_collector.utils.logging_config import setup_logging

from github_collector import config
logger = setup_logging(log_file=config.REPOSITORY_LOG)

def setup_api_client():
    """Richte den GitHub API-Client ein."""
    try:
        from dotenv import load_dotenv
        import os
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dotenv_path = os.path.join(project_dir, ".env")
        load_dotenv(dotenv_path, override=True)
    except ImportError:
        logger.warning("python-dotenv nicht installiert, überspringe .env-Laden")
    github_token = os.environ.get("GITHUB_API_TOKEN")
    github_tokens = os.environ.get("GITHUB_API_TOKENS")
    if github_tokens:
        tokens = [token.strip() for token in github_tokens.split(",")]
        logger.info(f"{len(tokens)} GitHub API-Tokens gefunden")
    elif github_token:
        tokens = [github_token]
        logger.info("GitHub API-Token gefunden")
    else:
        logger.warning("Kein GitHub API-Token in Umgebungsvariablen gefunden")
        github_token = input("Bitte gib dein GitHub API-Token ein: ").strip()
        if not github_token:
            raise ValueError("GitHub API-Token ist erforderlich")
        tokens = [github_token]
    cache_dir = os.environ.get("CACHE_DIR", ".github_cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return GitHubAPI(tokens, cache_dir=cache_dir)

def parse_arguments():
    """Parse Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(description="Sammle GitHub-Repositories")
    time_group = parser.add_argument_group("Zeitbereichsoptionen")
    time_group.add_argument("--time-range", choices=["week", "month", "year", "custom"], 
                           help="Vordefinierter Zeitbereich für die Repository-Sammlung")
    time_group.add_argument("--start-date", help="Startdatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)")
    time_group.add_argument("--end-date", help="Enddatum für benutzerdefinierten Zeitbereich (YYYY-MM-DD)")
    collection_group = parser.add_argument_group("Sammlungsoptionen")
    collection_group.add_argument("--limit", type=int, help="Maximale Anzahl zu sammelnder Repositories")
    collection_group.add_argument("--all", action="store_true", help="Alle verfügbaren Repositories sammeln")
    collection_group.add_argument("--min-stars", type=int, default=100, 
                                help="Minimale Anzahl von Stars für Repositories (Standard: 100)")
    collection_group.add_argument("--star-range", nargs=2, type=int, metavar=("MIN", "MAX"),
                                help="Sammle Repositories mit einer Anzahl an Stars im Bereich MIN bis MAX (inklusive). Ignoriert --min-stars, falls gesetzt.")
    db_group = parser.add_argument_group("Datenbankoptionen")
    db_group.add_argument("--db-path", help="Pfad zur Datenbankdatei oder vollständige SQLAlchemy-URL (z.B. mysql+pymysql://user:pw@host/db)")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Im nicht-interaktiven Modus ausführen (erfordert Zeitbereichs- und Limit-Optionen)")
    parser.add_argument("--stats", action="store_true", 
                       help="Datenbankstatistiken anzeigen und beenden")
    return parser.parse_args()

def interactive_mode(args, api_client, db):
    """
    Startet die Repository-Sammlung im interaktiven Modus.
    
    Fragt den Nutzer nach Zeitbereich und weiteren Parametern, zeigt Statistiken an
    und startet die Sammlung der Repositories über den RepositoryCollector.
    
    :param args: Kommandozeilenargumente bzw. Namespace
    :param api_client: Initialisierter GitHub API Client
    :param db: Datenbank-Objekt
    """
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
    
    # Frage nach Star-Range oder minimalen Stars
    use_star_range = input("\nMöchtest du einen Star-Bereich verwenden? (j/n): ").strip().lower()
    if use_star_range in ("j", "ja", "y", "yes"):
        try:
            min_stars = int(input("Minimale Anzahl von Stars (inklusive): ").strip())
            max_stars = int(input("Maximale Anzahl von Stars (inklusive): ").strip())
        except ValueError:
            logger.error("Ungültige Eingabe für Star-Bereich.")
            return
        use_range = True
    else:
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
        use_range = False

    # Frage nach Anzahl der Perioden
    time_diff = end_date - start_date
    days_total = time_diff.days
    if days_total <= 7:
        default_periods = 1
    elif days_total <= 30:
        default_periods = 3
    elif days_total <= 90:
        default_periods = 6
    elif days_total <= 365:
        default_periods = 12
    else:
        default_periods = days_total // 30
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
    if use_range:
        print(f"Star-Bereich: {min_stars} bis {max_stars}")
    else:
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
    period_size = days_total / periods_count
    periods = []
    current_start = start_date
    for i in range(periods_count):
        if i == periods_count - 1:
            current_end = end_date
        else:
            current_end = current_start + timedelta(days=period_size)
        periods.append((current_start, current_end))
        current_start = current_end
    try:
        collector.state.reset(start_date, end_date)
        collector.state.set_time_periods(periods)
        if use_range:
            collector.collect_repositories_by_star_range(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                max_stars=max_stars,
                max_repos=limit,
                resume=True
            )
        else:
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
    """
    Führt die Repository-Sammlung im nicht-interaktiven (Batch-)Modus aus.
    Nutzt direkt die übergebenen Parameter und sammelt Repositories automatisiert.
    Zeigt Fortschritt und schreibt Logs.
    :param args: Kommandozeilenargumente bzw. Namespace
    :param api_client: Initialisierter GitHub API Client
    :param db: Datenbank-Objekt
    """
    collector = RepositoryCollector(github_client=api_client, db=db)

    # Zeitbereich bestimmen
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=tz.UTC)
    else:
        now = datetime.now(tz.UTC)
        if args.time_range == "week":
            end_date = now
            start_date = now - timedelta(days=7)
        elif args.time_range == "month":
            end_date = now
            start_date = now - timedelta(days=30)
        elif args.time_range == "year":
            end_date = now
            start_date = now - timedelta(days=365)
        else:
            raise ValueError("Zeitbereich muss angegeben werden")

    limit = args.limit if args.limit else None

    # Star-Range-Modus: Wenn --star-range gesetzt ist, wird die neue Methode verwendet
    try:
        if args.star_range:
            min_stars, max_stars = args.star_range
            collector.collect_repositories_by_star_range(
                start_date=start_date,
                end_date=end_date,
                min_stars=min_stars,
                max_stars=max_stars,
                max_repos=limit,
                resume=True
            )
        else:
            min_stars = args.min_stars if args.min_stars else 0
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
    except KeyboardInterrupt:
        print("\nSammlung unterbrochen. Der Fortschritt wurde gespeichert und kann später fortgesetzt werden.")
    except Exception as e:
        logger.error(f"Fehler bei der Repository-Sammlung: {e}")


def main():
    import os
    print("DEBUG: DATABASE_URL =", os.environ.get("DATABASE_URL"))
    """
    Einstiegspunkt für die Repository-Sammlung.
    
    Parsed die Kommandozeilenargumente, initialisiert API-Client und Datenbank,
    und startet je nach Modus (interaktiv/nicht-interaktiv) die Sammlung.
    
    Beendet das Skript mit entsprechendem Exit-Code.
    """
    args = parse_arguments()
    db_path = None

    # 1. Priorität: --db-path
    if args.db_path:
        if '://' in args.db_path:
            db_path = args.db_path
        else:
            db_path = f"sqlite:///{os.path.abspath(args.db_path)}"
    # 2. Priorität: Umgebungsvariable DATABASE_URL
    elif os.environ.get("DATABASE_URL"):
        db_path = os.environ["DATABASE_URL"]
    # 3. Fallback: SQLite im data/-Verzeichnis
    else:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_file_path = os.path.join(project_dir, "data", "github_data.db")
        db_path = f"sqlite:///{db_file_path}"
    
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
            # Im interaktiven Modus: Falls --star-range gesetzt ist, Hinweis anzeigen
            if hasattr(args, 'star_range') and args.star_range:
                print("Hinweis: Die Star-Range-Option (--star-range) ist nur im nicht-interaktiven Modus direkt verfügbar. Für interaktive Nutzung bitte den nicht-interaktiven Modus verwenden.")
            interactive_mode(args, api_client, db)
    finally:
        # Schließe Datenbankverbindung
        db.close()


if __name__ == "__main__":
    sys.exit(main())
