# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (informally, as it's a script-based project).

## [Unreleased] - YYYY-MM-DD

## [2025-05-10]

### Added
- SQLite WAL (Write-Ahead Logging) mode is now enabled by default when using a SQLite database. This significantly improves concurrency, allowing scripts like `collect_repositories.py` and `update_location_geocoding.py` to run in parallel with a greatly reduced risk of "database is locked" errors. (`09ad663`)

### Changed
- The summary output at the end of repository collection (in `collect_repositories.py`) now displays total collection time, processing time, and overhead time in minutes instead of seconds for better readability with longer collection runs. Average time per repository remains in seconds. (Part of `0dc61da`)
- Updated `.gitignore` to better handle generated files, log files, and the `data/` directory. (`ce51309`)
- Untracked previously committed generated files (`collection_state.json`, `geocoding_cache.json`, etc.) from Git history. (`20c9d36`)

### Fixed
- Corrected access to `total_count` from GitHub API responses in `collect_repositories.py` interactive mode. (Part of `0dc61da`)
- Improved handling of SQLAlchemy `DATABASE_URL` for SQLite paths in `cli.export_command.py`. (Part of `0dc61da` or `6c72fd3`)
- Optimized interactive period calculation in `collect_repositories.py`: queries GitHub API upfront to estimate total matching repositories and suggests an appropriate number of collection periods. (Part of `0dc61da`)
- General SQLAlchemy compatibility improvements and script cleanups. (Covers parts of `6c72fd3`)

## [2025-05-01]

### Fixed
- Ensured `repository.description` uses `LONGTEXT` data type for MySQL compatibility and updated database documentation regarding long text fields. (`28a3615`)

## [2025-04-30]

### Added
- Enhanced logging in `updater.py`: now logs all skipped repository updates with a reason. (`26a85ef`)
- Documentation: Added notes on MySQL support and SQLAlchemy `DATABASE_URL` usage to README and usage docs. (`0b1dd87`)

### Changed
- **MySQL Compatibility & SQLAlchemy Refactor:** Major effort to refactor database interaction layer to use SQLAlchemy more consistently, improving MySQL compatibility and removing direct SQLite-specific code.
  - `updater.py` refactored for pure SQLAlchemy operations. (`183bcec`)
  - `map_and_update_stats.py` refactored for SQLAlchemy, removing direct SQLite cursor usage. (`e679f66`, `6be9c72`)
  - `enrich_repository_stats.py` refactored for SQLAlchemy. (`c247c2b`)

### Fixed
- Ensured `db_path` is always a valid SQLAlchemy URL in `geocoding_command.py` for MySQL/SQLite compatibility. (`71ffcaa`)
- Improved robustness of ID handling in `updater.py`: now accepts numeric strings as well as integers for repository IDs to update. (`26a85ef`)
- Corrected repository update logic to only process numeric repository IDs, skipping base64/GraphQL node IDs, for robust MySQL compatibility. (`4e98424`)
- Addressed SQLAlchemy transaction handling issues and removed erroneous `sqlite3` calls. (`420fab6`)
- Corrected `map_and_update_stats` to be called with `db_url` instead of `db_path`. (`96b1457`)
- Ensured `.env` file is loaded at the beginning of `update_location_geocoding.py`. (`3706efa`)
- Ensured `.env` file is loaded at the beginning of `collect_repositories.py`. (`df44423`)
- Corrected `db_path` to `db_url` when calling `get_repos_to_enrich` in `update_location_geocoding.py`. (`1b598ad`)