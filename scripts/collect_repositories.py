#!/usr/bin/env python3
"""
Skript zum Sammeln von GitHub-Repositories.

Dieses Skript ist ein Wrapper für die CLI-Funktionalität des GitHub Data Collectors.
Es verwendet die Implementierung aus dem cli-Modul, um die Repository-Sammlung durchzuführen.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_collector.cli.collect_command import main

if __name__ == "__main__":
    sys.exit(main())





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
    """
    Führt die Repository-Sammlung im nicht-interaktiven (Batch-)Modus aus.
    
    Nutzt direkt die übergebenen Parameter und sammelt Repositories automatisiert.
    Zeigt Fortschritt und schreibt Logs.
    
    :param args: Kommandozeilenargumente bzw. Namespace
    :param api_client: Initialisierter GitHub API Client
    :param db: Datenbank-Objekt
    """
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
    """
    Einstiegspunkt für die Repository-Sammlung.
    
    Parsed die Kommandozeilenargumente, initialisiert API-Client und Datenbank,
    und startet je nach Modus (interaktiv/nicht-interaktiv) die Sammlung.
    
    Beendet das Skript mit entsprechendem Exit-Code.
    """
    args = parse_arguments()
    
    # Datenbankpfad
    if args.db_path:
        db_path = args.db_path
        if not db_path.startswith("sqlite:///"):
            db_path = f"sqlite:///{db_path}"
    else:
        # Erzwinge immer den absoluten Pfad zur Datenbank im data/-Verzeichnis relativ zum Projektverzeichnis
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
            interactive_mode(args, api_client, db)
    finally:
        # Schließe Datenbankverbindung
        db.close()


if __name__ == "__main__":
    sys.exit(main())
