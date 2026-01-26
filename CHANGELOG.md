# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-26

### Added
- **Domain Layer**:
    - `CandidateSchema`: Added `id` and `education` fields.
    - `CandidateSchema`: Changed `experience` type to `list[str]`.
- **Infrastructure Layer**:
    - **OCCScraper**:
        - Robust selectors for `title`, `location`, `experience`, and `education` (based on HTML structure).
        - Logic to select **50 candidates per page** automatically.
        - **Deduplication logic** using scraped IDs to avoid re-processing candidates.
        - Automatic pagination stop when no "Next" button is found.
        - Integration with `JsonExporter` to save data incrementally (page by page).
    - **Persistence**:
        - Candidates are now saved to `data/candidates_occ_{keyword}_{location}.json`.

## [0.1.0] - 2026-01-23

### Added
- **Domain Layer**:
    - `CandidateSchema` (Pydantic model) for strict typing.
    - `BaseScraper` and `DataExporter` interfaces.
- **Infrastructure Layer**:
    - `OCCScraper` implementation using Playwright.
    - `PandapeScraper` implementation using Playwright.
    - `JsonExporter` for data persistence.
    - Custom `Logger` implementation in `src/infraestructura/logging.py`.
- **Application Layer**:
    - `CandidateSearchService` to orchestrate scraping and export.
- **UI**:
    - Streamlit application (`src/ui/app.py`) with scraper selection and data export.
    - Added **Location Filter** (CDMX, Edo Mex, etc.).
    - Added placeholders for future scrapers (LinkedIn, Glassdoor, Indeed).
    - CLI entry point (`main.py`).
- **Project Configuration**:
    - `pyproject.toml` and `uv.lock` for dependency management.
    - `README.md` with installation and usage instructions.
    - `.gitignore` for Python, Playwright, and Streamlit.
    - `.env.example` for credential configuration.
- **Architecture**:
    - Added `_login` abstract method and stub implementations.
    - Standardized `SELECTORS` dictionary in scrapers.
