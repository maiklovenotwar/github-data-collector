# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (informally, as it's a script-based project).

## [Unreleased] - YYYY-MM-DD

## [2025-05-10]

### Added
- SQLite WAL (Write-Ahead Logging) mode is now enabled by default when using a SQLite database. This significantly improves concurrency, allowing scripts like `collect_repositories.py` and `update_location_geocoding.py` to run in parallel with a greatly reduced risk of "database is locked" errors.

### Changed
- The summary output at the end of repository collection (in `collect_repositories.py`) now displays total collection time, processing time, and overhead time in minutes instead of seconds for better readability with longer collection runs. Average time per repository remains in seconds.

### Fixed
- Corrected access to `total_count` from GitHub API responses in `collect_repositories.py` interactive mode.
- Improved handling of SQLAlchemy `DATABASE_URL` for SQLite paths in `cli.export_command.py`.
- Addressed `LONGTEXT` data type issues for compatibility between MySQL and SQLite in `models.Repository.description`.
- Optimized interactive period calculation in `collect_repositories.py`: queries GitHub API upfront to estimate total matching repositories and suggests an appropriate number of collection periods.