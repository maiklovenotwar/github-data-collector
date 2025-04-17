# Datenbankschema des GitHub Data Collectors

## Übersicht

Der GitHub Data Collector verwendet eine SQLite-Datenbank zur Speicherung der gesammelten Daten. Das Datenbankschema umfasst drei Haupttabellen:

1. **Contributors**: Speichert Informationen über GitHub-Benutzer (Contributors)
2. **Organizations**: Speichert Informationen über GitHub-Organisationen
3. **Repositories**: Speichert Informationen über GitHub-Repositories

## Tabellenschema

### Contributors

Die `contributors`-Tabelle speichert Informationen über GitHub-Benutzer.

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | Integer | Primärschlüssel, GitHub-ID des Contributors |
| login | String | GitHub-Benutzername |
| name | String | Vollständiger Name des Contributors |
| email | String | E-Mail-Adresse des Contributors |
| company | String | Unternehmen des Contributors |
| blog | String | Blog oder Website des Contributors |
| location | String | Standort des Contributors |
| bio | String | Biografie des Contributors |
| twitter_username | String | Twitter-Benutzername des Contributors |
| public_repos | Integer | Anzahl der öffentlichen Repositories |
| public_gists | Integer | Anzahl der öffentlichen Gists |
| followers | Integer | Anzahl der Follower |
| following | Integer | Anzahl der gefolgten Benutzer |
| created_at | DateTime | Erstellungsdatum des GitHub-Kontos |
| updated_at | DateTime | Letztes Aktualisierungsdatum des GitHub-Kontos |
| country_code | String | ISO-Ländercode (aus Geocoding) |
| country_name | String | Ländername (aus Geocoding) |
| longitude | Float | Längengrad des Standorts (aus Geocoding) |
| latitude | Float | Breitengrad des Standorts (aus Geocoding) |

### Organizations

Die `organizations`-Tabelle speichert Informationen über GitHub-Organisationen.

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | Integer | Primärschlüssel, GitHub-ID der Organisation |
| login | String | GitHub-Benutzername der Organisation |
| name | String | Name der Organisation |
| email | String | E-Mail-Adresse der Organisation |
| description | String | Beschreibung der Organisation |
| blog | String | Blog oder Website der Organisation |
| location | String | Standort der Organisation |
| twitter_username | String | Twitter-Benutzername der Organisation |
| public_repos | Integer | Anzahl der öffentlichen Repositories |
| public_gists | Integer | Anzahl der öffentlichen Gists |
| followers | Integer | Anzahl der Follower |
| following | Integer | Anzahl der gefolgten Benutzer |
| created_at | DateTime | Erstellungsdatum der Organisation |
| updated_at | DateTime | Letztes Aktualisierungsdatum der Organisation |
| country_code | String | ISO-Ländercode (aus Geocoding) |
| country_name | String | Ländername (aus Geocoding) |
| longitude | Float | Längengrad des Standorts (aus Geocoding) |
| latitude | Float | Breitengrad des Standorts (aus Geocoding) |

### Repositories

Die `repositories`-Tabelle speichert Informationen über GitHub-Repositories.

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | Integer | Primärschlüssel, GitHub-ID des Repositories |
| name | String | Name des Repositories |
| full_name | String | Vollständiger Name des Repositories (owner/name) |
| description | String | Beschreibung des Repositories |
| homepage | String | Homepage des Repositories |
| language | String | Hauptsprache des Repositories |
| fork | Boolean | Gibt an, ob das Repository ein Fork ist |
| forks_count | Integer | Anzahl der Forks |
| stargazers_count | Integer | Anzahl der Stars |
| watchers_count | Integer | Anzahl der Watcher |
| size | Integer | Größe des Repositories in KB |
| open_issues_count | Integer | Anzahl der offenen Issues |
| owner_id | Integer | ID des Besitzers (Contributor oder Organisation) |
| owner_type | String | Typ des Besitzers ("contributor" oder "organization") |
| created_at | DateTime | Erstellungsdatum des Repositories |
| updated_at | DateTime | Letztes Aktualisierungsdatum des Repositories |
| pushed_at | DateTime | Letztes Push-Datum des Repositories |
| contributors_count | Integer | Anzahl der Contributors |
| commits_count | Integer | Anzahl der Commits |

## Beziehungen

Die Datenbank verwendet eine vereinfachte Beziehungsstruktur:

1. **Repository zu Owner**: Ein Repository gehört entweder zu einem Contributor oder einer Organisation. Diese Beziehung wird über die Spalten `owner_id` und `owner_type` in der `repositories`-Tabelle abgebildet.

## Indizes

Die Datenbank verwendet folgende Indizes zur Optimierung der Abfragen:

1. **repositories_owner_idx**: Index auf `owner_id` und `owner_type` in der `repositories`-Tabelle
2. **contributors_login_idx**: Index auf `login` in der `contributors`-Tabelle
3. **organizations_login_idx**: Index auf `login` in der `organizations`-Tabelle
4. **repositories_full_name_idx**: Index auf `full_name` in der `repositories`-Tabelle

## Datenintegrität

Die Datenbank stellt die Integrität der Daten durch folgende Maßnahmen sicher:

1. **Primärschlüssel**: Jede Tabelle hat einen Primärschlüssel, der die Eindeutigkeit der Datensätze gewährleistet.
2. **Nicht-Null-Constraints**: Wichtige Spalten wie `login` und `name` sind als NOT NULL definiert.
3. **Unique-Constraints**: Die Spalte `login` ist in den Tabellen `contributors` und `organizations` als UNIQUE definiert.

## Datenbankzugriff

Der Zugriff auf die Datenbank erfolgt über die `GitHubDatabase`-Klasse, die eine Abstraktion über SQLAlchemy bietet. Diese Klasse implementiert Methoden für den Zugriff auf die Daten, wie z.B.:

- `add_contributor(contributor_data)`: Fügt einen neuen Contributor hinzu oder aktualisiert einen bestehenden
- `add_organization(org_data)`: Fügt eine neue Organisation hinzu oder aktualisiert eine bestehende
- `add_repository(repo_data)`: Fügt ein neues Repository hinzu oder aktualisiert ein bestehendes
- `get_contributor(contributor_id)`: Ruft einen Contributor anhand seiner ID ab
- `get_organization(organization_id)`: Ruft eine Organisation anhand ihrer ID ab
- `get_repository(repository_id)`: Ruft ein Repository anhand seiner ID ab
- `get_contributors()`: Ruft alle Contributors ab
- `get_organizations()`: Ruft alle Organisationen ab
- `get_repositories()`: Ruft alle Repositories ab
- `get_contributors_without_country_code()`: Ruft alle Contributors ohne Ländercode ab
- `get_organizations_without_country_code()`: Ruft alle Organisationen ohne Ländercode ab
- `check_repository_exists(repository_id)`: Prüft, ob ein Repository existiert
- `get_all_contributor_logins()`: Ruft alle Contributor-Logins ab
- `get_all_organization_logins()`: Ruft alle Organisations-Logins ab

## Datenbankmigration

Die Datenbank verwendet Alembic für Datenbankmigrationen. Die Migrationsskripte befinden sich im Verzeichnis `migrations/`. Neue Migrationen können mit dem Befehl `alembic revision --autogenerate -m "Beschreibung"` erstellt werden.

## Datenbankinitialisierung

Die Datenbank wird bei der ersten Verwendung automatisch initialisiert. Die Initialisierung kann auch manuell mit der Funktion `init_db(db_url)` durchgeführt werden.

## Datenbankoptimierung

Die Datenbank ist für die effiziente Speicherung und den Zugriff auf große Datenmengen optimiert. Folgende Optimierungen wurden implementiert:

1. **Indizes**: Indizes auf häufig abgefragten Spalten
2. **Batch-Verarbeitung**: Batch-Verarbeitung für das Einfügen und Aktualisieren von Daten
3. **Caching**: Caching von häufig abgefragten Daten
4. **Deduplizierung**: Deduplizierung von Daten vor dem Einfügen in die Datenbank

## Datenbankbackup

Die Datenbank kann mit dem SQLite-Befehl `.backup` gesichert werden. Es wird empfohlen, regelmäßige Backups der Datenbank durchzuführen, insbesondere vor größeren Datensammlungen oder Datenbankmigrationen.
