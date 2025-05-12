# SQL-Abfragen für Datenvisualisierung

Dieses Dokument enthält eine Sammlung von SQL-Abfragen, die zur Extraktion und Aggregation von Daten aus der GitHub Data Collector-Datenbank (SQLite) dienen. Diese Abfragen sind als Grundlage für die Erstellung von Visualisierungen und Analysen im Rahmen des Projekts gedacht.

## Inhaltsverzeichnis

1.  [Repository-Statistiken](#repository-statistiken)
    *   [Verteilung nach Programmiersprache (Top N)](#verteilung-nach-programmiersprache-top-n)
    *   [Verteilung nach Anzahl der Sterne](#verteilung-nach-anzahl-der-sterne)
    *   [Verteilung nach Erstellungsdatum (pro Jahr)](#verteilung-nach-erstellungsdatum-pro-jahr)
    *   [Verteilung nach Erstellungsdatum (pro Monat)](#verteilung-nach-erstellungsdatum-pro-monat)
    *   [Korrelation: Sterne vs. Pull Requests](#korrelation-sterne-vs-pull-requests)
    *   [Korrelation: Sterne vs. Commits](#korrelation-sterne-vs-commits-auf-default-branch)
    *   [Repositories mit vs. ohne Beschreibung](#repositories-mit-vs-ohne-beschreibung)
    *   [Durchschnittliche Commits pro Repository](#durchschnittliche-commits-pro-repository)
    *   [Durchschnittliche Pull Requests pro Repository](#durchschnittliche-pull-requests-pro-repository)
2.  [Contributor-Statistiken](#contributor-statistiken)
3.  [Organisations-Statistiken](#organisations-statistiken)
4.  [Zeitliche Entwicklungen](#zeitliche-entwicklungen)

---

## Repository-Statistiken

### Verteilung nach Programmiersprache (Top N)

*   **Beschreibung:** Ermittelt die Anzahl der Repositories pro Programmiersprache und zeigt die Top N Sprachen.
*   **Nutzen für Visualisierung:** Ideal für ein Balkendiagramm, das die beliebtesten Programmiersprachen im Datensatz darstellt.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        language,
        COUNT(id) AS repository_count
    FROM
        repositories
    WHERE
        language IS NOT NULL AND language != ''
    GROUP BY
        language
    ORDER BY
        repository_count DESC
    LIMIT 10; -- Ändere LIMIT für Top N (z.B. 10, 20)
    ```
*   **Hinweise:**
    *   `language IS NOT NULL AND language != ''` schließt Repositories ohne angegebene Sprache aus.
    *   Passen Sie `LIMIT 10` an, um mehr oder weniger Top-Sprachen anzuzeigen.

### Verteilung nach Anzahl der Sterne

*   **Beschreibung:** Kategorisiert Repositories basierend auf ihrer Sterneanzahl.
*   **Nutzen für Visualisierung:** Nützlich für ein Histogramm oder Balkendiagramm, das die Verteilung der Repository-Popularität zeigt.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN stargazers_count BETWEEN 0 AND 100 THEN '0-100 Sterne'
            WHEN stargazers_count BETWEEN 101 AND 1000 THEN '101-1000 Sterne'
            WHEN stargazers_count BETWEEN 1001 AND 10000 THEN '1001-10000 Sterne'
            ELSE '>10000 Sterne'
        END AS star_category,
        COUNT(id) AS repository_count
    FROM
        repositories
    GROUP BY
        star_category
    ORDER BY
        MIN(stargazers_count); -- Sortiert die Kategorien in aufsteigender Reihenfolge der Sterne
    ```
*   **Hinweise:** Die Kategorien können nach Bedarf angepasst werden.

### Verteilung nach Erstellungsdatum (pro Jahr)

*   **Beschreibung:** Zählt die Anzahl der erstellten Repositories pro Jahr.
*   **Nutzen für Visualisierung:** Geeignet für ein Liniendiagramm oder Balkendiagramm, das das Wachstum der Repository-Erstellungen über die Jahre zeigt.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        STRFTIME('%Y', created_at_date) AS creation_year,
        COUNT(id) AS repository_count
    FROM
        repositories
    WHERE
        created_at_date IS NOT NULL
    GROUP BY
        creation_year
    ORDER BY
        creation_year ASC;
    ```

### Verteilung nach Erstellungsdatum (pro Monat)

*   **Beschreibung:** Zählt die Anzahl der erstellten Repositories pro Monat und Jahr.
*   **Nutzen für Visualisierung:** Detailliertere Ansicht als die jährliche Verteilung, nützlich für Liniendiagramme, um saisonale Trends oder spezifische Wachstumsperioden zu erkennen.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        STRFTIME('%Y-%m', created_at_date) AS creation_month,
        COUNT(id) AS repository_count
    FROM
        repositories
    WHERE
        created_at_date IS NOT NULL
    GROUP BY
        creation_month
    ORDER BY
        creation_month ASC;
    ```

### Korrelation: Sterne vs. Pull Requests

*   **Beschreibung:** Untersucht den Zusammenhang zwischen der Anzahl der Sterne und der Anzahl der Pull Requests. Diese Abfrage liefert Rohdatenpunkte. Für eine echte Korrelationsanalyse wären statistische Werkzeuge oder komplexere SQL-Funktionen (falls von SQLite unterstützt und sinnvoll) oder eine Verarbeitung der Ergebnisse in Python/R besser.
*   **Nutzen für Visualisierung:** Ein Streudiagramm (Scatter Plot) könnte hier erste Hinweise auf einen Zusammenhang geben.
*   **SQL-Abfrage (für Rohdaten):**
    ```sql
    SELECT
        stargazers_count,
        pull_requests_count
    FROM
        repositories
    WHERE
        pull_requests_count IS NOT NULL;
    ```
*   **Hinweise:**
    *   Um die Datenmenge für ein Streudiagramm zu reduzieren oder die Analyse zu vereinfachen, könnte man die Daten aggregieren (z.B. Durchschnittliche Pull Requests pro Sterne-Kategorie) oder filtern (z.B. nur Repos mit > X Sternen).
    *   Eine tatsächliche Korrelationskoeffizient-Berechnung erfolgt typischerweise außerhalb von SQL oder mit spezifischen SQL-Erweiterungen.

    **Aggregierte Version (Durchschnittliche PRs pro Sterne-Kategorie):**
    ```sql
    SELECT
        CASE
            WHEN stargazers_count BETWEEN 0 AND 100 THEN '0-100 Sterne'
            WHEN stargazers_count BETWEEN 101 AND 1000 THEN '101-1000 Sterne'
            WHEN stargazers_count BETWEEN 1001 AND 10000 THEN '1001-10000 Sterne'
            WHEN stargazers_count BETWEEN 10001 AND 50000 THEN '10001-50000 Sterne'
            ELSE '>50000 Sterne'
        END AS star_category,
        AVG(pull_requests_count) AS avg_pr_count,
        COUNT(id) AS repo_count_in_category
    FROM
        repositories
    WHERE
        pull_requests_count IS NOT NULL
    GROUP BY
        star_category
    ORDER BY
        MIN(stargazers_count);
    ```

### Korrelation: Sterne vs. Commits (auf Default Branch)

*   **Beschreibung:** Untersucht den Zusammenhang zwischen der Anzahl der Sterne und der Anzahl der Commits auf dem Default Branch. Ähnlich wie bei Pull Requests, liefert diese Abfrage primär Rohdaten.
*   **Nutzen für Visualisierung:** Streudiagramm.
*   **SQL-Abfrage (für Rohdaten):**
    ```sql
    SELECT
        stargazers_count,
        commits_count -- Annahme: commits_count bezieht sich auf den Default Branch
    FROM
        repositories
    WHERE
        commits_count IS NOT NULL;
    ```
*   **Hinweise:** Siehe Hinweise bei "Korrelation: Sterne vs. Pull Requests". `commits_count` in unserer Tabelle bezieht sich bereits auf den Default Branch.

    **Aggregierte Version (Durchschnittliche Commits pro Sterne-Kategorie):**
    ```sql
    SELECT
        CASE
            WHEN stargazers_count BETWEEN 0 AND 100 THEN '0-100 Sterne'
            WHEN stargazers_count BETWEEN 101 AND 1000 THEN '101-1000 Sterne'
            WHEN stargazers_count BETWEEN 1001 AND 10000 THEN '1001-10000 Sterne'
            WHEN stargazers_count BETWEEN 10001 AND 50000 THEN '10001-50000 Sterne'
            ELSE '>50000 Sterne'
        END AS star_category,
        AVG(commits_count) AS avg_commit_count,
        COUNT(id) AS repo_count_in_category
    FROM
        repositories
    WHERE
        commits_count IS NOT NULL
    GROUP BY
        star_category
    ORDER BY
        MIN(stargazers_count);
    ```

### Repositories mit vs. ohne Beschreibung

*   **Beschreibung:** Zählt die Anzahl der Repositories, die eine Beschreibung haben, im Vergleich zu denen ohne.
*   **Nutzen für Visualisierung:** Einfaches Balken- oder Kuchendiagramm, das den Anteil zeigt.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN description IS NULL OR description = '' THEN 'Ohne Beschreibung'
            ELSE 'Mit Beschreibung'
        END AS has_description,
        COUNT(id) AS repository_count
    FROM
        repositories
    GROUP BY
        has_description;
    ```

### Durchschnittliche Commits pro Repository

*   **Beschreibung:** Berechnet die durchschnittliche Anzahl von Commits über alle Repositories.
*   **Nutzen für Visualisierung:** Eine einzelne Kennzahl (KPI) oder Vergleich mit Durchschnittswerten pro Sprache.
*   **SQL-Abfrage (Gesamtdurchschnitt):**
    ```sql
    SELECT
        AVG(commits_count) AS overall_avg_commits
    FROM
        repositories
    WHERE
        commits_count IS NOT NULL;
    ```
*   **SQL-Abfrage (Durchschnitt pro Top N Sprachen):**
    ```sql
    WITH TopLanguages AS (
        SELECT
            language,
            COUNT(id) AS repo_count
        FROM
            repositories
        WHERE
            language IS NOT NULL AND language != ''
        GROUP BY
            language
        ORDER BY
            repo_count DESC
        LIMIT 5 -- Top 5 Sprachen, anpassen bei Bedarf
    )
    SELECT
        r.language,
        AVG(r.commits_count) AS avg_commits_per_repo
    FROM
        repositories r
    JOIN
        TopLanguages tl ON r.language = tl.language
    WHERE
        r.commits_count IS NOT NULL
    GROUP BY
        r.language
    ORDER BY
        avg_commits_per_repo DESC;
    ```

### Durchschnittliche Pull Requests pro Repository

*   **Beschreibung:** Berechnet die durchschnittliche Anzahl von Pull Requests über alle Repositories.
*   **Nutzen für Visualisierung:** Eine einzelne Kennzahl (KPI) oder Vergleich mit Durchschnittswerten pro Sprache.
*   **SQL-Abfrage (Gesamtdurchschnitt):**
    ```sql
    SELECT
        AVG(pull_requests_count) AS overall_avg_prs
    FROM
        repositories
    WHERE
        pull_requests_count IS NOT NULL;
    ```
*   **SQL-Abfrage (Durchschnitt pro Top N Sprachen):**
    ```sql
    WITH TopLanguages AS (
        SELECT
            language,
            COUNT(id) AS repo_count
        FROM
            repositories
        WHERE
            language IS NOT NULL AND language != ''
        GROUP BY
            language
        ORDER BY
            repo_count DESC
        LIMIT 5 -- Top 5 Sprachen, anpassen bei Bedarf
    )
    SELECT
        r.language,
        AVG(r.pull_requests_count) AS avg_prs_per_repo
    FROM
        repositories r
    JOIN
        TopLanguages tl ON r.language = tl.language
    WHERE
        r.pull_requests_count IS NOT NULL
    GROUP BY
        r.language
    ORDER BY
        avg_prs_per_repo DESC;
    ```

---
(Weitere Abschnitte für zeitliche Entwicklungen folgen hier)

---

## Contributor-Statistiken

### Verteilung nach Herkunftsland (Top N)

*   **Beschreibung:** Zeigt die häufigsten Herkunftsländer der Kontributoren basierend auf dem `country_code`.
*   **Nutzen für Visualisierung:** Balkendiagramm oder Weltkarte zur Darstellung der geografischen Verteilung.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        country_code,
        COUNT(id) AS contributor_count
    FROM
        contributors
    WHERE
        country_code IS NOT NULL AND country_code != ''
    GROUP BY
        country_code
    ORDER BY
        contributor_count DESC
    LIMIT 10; -- Top 10 Länder, anpassen bei Bedarf
    ```

### Kontributoren mit vs. ohne Standortangabe

*   **Beschreibung:** Zählt Kontributoren, die einen Standort (`location`) angegeben haben, im Vergleich zu denen ohne Angabe.
*   **Nutzen für Visualisierung:** Kuchendiagramm oder Balkendiagramm.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN location IS NULL OR location = '' THEN 'Ohne Standortangabe'
            ELSE 'Mit Standortangabe'
        END AS has_location,
        COUNT(id) AS contributor_count
    FROM
        contributors
    GROUP BY
        has_location;
    ```

### Kontributoren mit vs. ohne Geokodierung (Country Code)

*   **Beschreibung:** Zählt Kontributoren, für die ein `country_code` ermittelt werden konnte (Geokodierung erfolgreich), im Vergleich zu denen ohne.
*   **Nutzen für Visualisierung:** Kuchendiagramm oder Balkendiagramm, um die Qualität der Geokodierungsdaten zu beurteilen.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN country_code IS NULL OR country_code = '' THEN 'Ohne Country Code (nicht geokodiert)'
            ELSE 'Mit Country Code (geokodiert)'
        END AS has_country_code,
        COUNT(id) AS contributor_count
    FROM
        contributors
    GROUP BY
        has_country_code;
    ```

### Durchschnittliche Anzahl öffentlicher Repositories pro Kontributor

*   **Beschreibung:** Berechnet die durchschnittliche Anzahl öffentlicher Repositories, die Kontributoren auf GitHub haben.
*   **Nutzen für Visualisierung:** KPI-Wert.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        AVG(public_repos) AS avg_public_repos_per_contributor
    FROM
        contributors
    WHERE
        public_repos IS NOT NULL;
    ```

### Verteilung der Kontributoren nach Anzahl öffentlicher Repositories

*   **Beschreibung:** Kategorisiert Kontributoren basierend auf der Anzahl ihrer öffentlichen Repositories.
*   **Nutzen für Visualisierung:** Histogramm oder Balkendiagramm, das zeigt, ob die meisten Kontributoren wenige oder viele öffentliche Repos haben.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN public_repos BETWEEN 0 AND 5 THEN '0-5 Repos'
            WHEN public_repos BETWEEN 6 AND 20 THEN '6-20 Repos'
            WHEN public_repos BETWEEN 21 AND 50 THEN '21-50 Repos'
            WHEN public_repos BETWEEN 51 AND 100 THEN '51-100 Repos'
            ELSE '>100 Repos'
        END AS public_repos_category,
        COUNT(id) AS contributor_count
    FROM
        contributors
    WHERE
        public_repos IS NOT NULL
    GROUP BY
        public_repos_category
    ORDER BY
        MIN(public_repos); -- Sortiert die Kategorien sinnvoll
    ```

---
(Weitere Abschnitte für Organisations-Statistiken und zeitliche Entwicklungen folgen hier)

---

## Organisations-Statistiken

### Verteilung nach Herkunftsland (Top N)

*   **Beschreibung:** Zeigt die häufigsten Herkunftsländer der Organisationen basierend auf dem `country_code`.
*   **Nutzen für Visualisierung:** Balkendiagramm oder Weltkarte zur Darstellung der geografischen Verteilung von Organisationen.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        country_code,
        COUNT(id) AS organization_count
    FROM
        organizations
    WHERE
        country_code IS NOT NULL AND country_code != ''
    GROUP BY
        country_code
    ORDER BY
        organization_count DESC
    LIMIT 10; -- Top 10 Länder, anpassen bei Bedarf
    ```

### Organisationen mit vs. ohne Standortangabe

*   **Beschreibung:** Zählt Organisationen, die einen Standort (`location`) angegeben haben, im Vergleich zu denen ohne Angabe.
*   **Nutzen für Visualisierung:** Kuchendiagramm oder Balkendiagramm.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN location IS NULL OR location = '' THEN 'Ohne Standortangabe'
            ELSE 'Mit Standortangabe'
        END AS has_location,
        COUNT(id) AS organization_count
    FROM
        organizations
    GROUP BY
        has_location;
    ```

### Organisationen mit vs. ohne Geokodierung (Country Code)

*   **Beschreibung:** Zählt Organisationen, für die ein `country_code` ermittelt werden konnte (Geokodierung erfolgreich), im Vergleich zu denen ohne.
*   **Nutzen für Visualisierung:** Kuchendiagramm oder Balkendiagramm, um die Vollständigkeit der Geokodierungsdaten für Organisationen zu beurteilen.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        CASE
            WHEN country_code IS NULL OR country_code = '' THEN 'Ohne Country Code (nicht geokodiert)'
            ELSE 'Mit Country Code (geokodiert)'
        END AS has_country_code,
        COUNT(id) AS organization_count
    FROM
        organizations
    GROUP BY
        has_country_code;
    ```

---
(Weitere Abschnitte für zeitliche Entwicklungen folgen hier)

---

## Zeitliche Entwicklungen

Dieser Abschnitt konzentriert sich auf Trends im Zeitverlauf, hauptsächlich basierend auf dem Erstellungsdatum von Repositories.

### Trend: Durchschnittliche Sterne neu erstellter Repositories (pro Jahr)

*   **Beschreibung:** Zeigt die durchschnittliche Anzahl an Sternen für Repositories, die in einem bestimmten Jahr erstellt wurden.
*   **Nutzen für Visualisierung:** Liniendiagramm, um zu sehen, ob neuer erstellte Repositories tendenziell mehr oder weniger populär (gemessen an Sternen) werden.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        STRFTIME('%Y', created_at_date) AS creation_year,
        AVG(stargazers_count) AS avg_stars_for_new_repos
    FROM
        repositories
    WHERE
        created_at_date IS NOT NULL
    GROUP BY
        creation_year
    ORDER BY
        creation_year ASC;
    ```

### Trend: Durchschnittliche Commits neu erstellter Repositories (pro Jahr)

*   **Beschreibung:** Zeigt die durchschnittliche Anzahl an Commits (auf dem Default Branch) für Repositories, die in einem bestimmten Jahr erstellt wurden.
*   **Nutzen für Visualisierung:** Liniendiagramm, um Entwicklungstrends in der initialen Aktivität neuer Projekte zu erkennen.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        STRFTIME('%Y', created_at_date) AS creation_year,
        AVG(commits_count) AS avg_commits_for_new_repos
    FROM
        repositories
    WHERE
        created_at_date IS NOT NULL AND commits_count IS NOT NULL
    GROUP BY
        creation_year
    ORDER BY
        creation_year ASC;
    ```

### Trend: Durchschnittliche Pull Requests neu erstellter Repositories (pro Jahr)

*   **Beschreibung:** Zeigt die durchschnittliche Anzahl an Pull Requests für Repositories, die in einem bestimmten Jahr erstellt wurden.
*   **Nutzen für Visualisierung:** Liniendiagramm, um Trends in der Kollaborationsaktivität oder Komplexität neuer Projekte zu analysieren.
*   **SQL-Abfrage:**
    ```sql
    SELECT
        STRFTIME('%Y', created_at_date) AS creation_year,
        AVG(pull_requests_count) AS avg_prs_for_new_repos
    FROM
        repositories
    WHERE
        created_at_date IS NOT NULL AND pull_requests_count IS NOT NULL
    GROUP BY
        creation_year
    ORDER BY
        creation_year ASC;
    ```

---

## Top 10 Auswertungen

### Top 10 Organisationen nach Gesamtsternen ihrer Repositories

*   **Beschreibung:** Listet die 10 Organisationen auf, deren Repositories in der Datenbank zusammengenommen die meisten Sterne haben.
*   **Nutzen für Visualisierung:** Rangliste (Balkendiagramm oder Tabelle).
*   **SQL-Abfrage:**
    ```sql
    SELECT
        o.login AS organization_login,
        SUM(r.stargazers_count) AS total_stars
    FROM
        repositories r
    JOIN
        organizations o ON r.organization_id = o.id
    WHERE
        r.stargazers_count IS NOT NULL
    GROUP BY
        o.id, o.login
    ORDER BY
        total_stars DESC
    LIMIT 10;
    ```

### Top 10 Organisationen nach Gesamtforks ihrer Repositories

*   **Beschreibung:** Listet die 10 Organisationen auf, deren Repositories in der Datenbank zusammengenommen die meisten Forks haben.
*   **Nutzen für Visualisierung:** Rangliste (Balkendiagramm oder Tabelle).
*   **SQL-Abfrage:**
    ```sql
    SELECT
        o.login AS organization_login,
        SUM(r.forks_count) AS total_forks
    FROM
        repositories r
    JOIN
        organizations o ON r.organization_id = o.id
    WHERE
        r.forks_count IS NOT NULL
    GROUP BY
        o.id, o.login
    ORDER BY
        total_forks DESC
    LIMIT 10;
    ```

### Top 10 Kontributoren nach Gesamtsternen ihrer Repositories

*   **Beschreibung:** Listet die 10 Kontributoren (Benutzer) auf, deren eigene Repositories (nicht die von Organisationen, bei denen sie Mitglied sind) in der Datenbank zusammengenommen die meisten Sterne haben.
*   **Nutzen für Visualisierung:** Rangliste (Balkendiagramm oder Tabelle).
*   **SQL-Abfrage:**
    ```sql
    SELECT
        c.login AS contributor_login,
        SUM(r.stargazers_count) AS total_stars
    FROM
        repositories r
    JOIN
        contributors c ON r.owner_id = c.id
    -- Sicherstellen, dass es sich um ein Benutzer-Repository handelt (owner ist der contributor UND es gibt keine explizite Org ID ODER die Org ID ist die des Owners, was aber im ORM unüblich wäre)
    -- Annahme: Wenn organization_id gesetzt ist, gehört es einer Org. Wenn nur owner_id gesetzt ist, einem User.
    WHERE
        r.organization_id IS NULL 
        AND r.stargazers_count IS NOT NULL
    GROUP BY
        c.id, c.login
    ORDER BY
        total_stars DESC
    LIMIT 10;
    ```

### Top 10 Kontributoren nach Gesamtforks ihrer Repositories

*   **Beschreibung:** Listet die 10 Kontributoren (Benutzer) auf, deren eigene Repositories in der Datenbank zusammengenommen die meisten Forks haben.
*   **Nutzen für Visualisierung:** Rangliste (Balkendiagramm oder Tabelle).
*   **SQL-Abfrage:**
    ```sql
    SELECT
        c.login AS contributor_login,
        SUM(r.forks_count) AS total_forks
    FROM
        repositories r
    JOIN
        contributors c ON r.owner_id = c.id
    WHERE
        r.organization_id IS NULL 
        AND r.forks_count IS NOT NULL
    GROUP BY
        c.id, c.login
    ORDER BY
        total_forks DESC
    LIMIT 10;
    ```

**Hinweis zu Commits:** Abfragen nach Commits sind hier nicht enthalten, da Commit-Zahlen pro Repository/User/Org typischerweise nicht direkt im Basis-Repository- oder User/Org-Datenmodell gespeichert werden und eine separate Sammlung erfordern würden.
