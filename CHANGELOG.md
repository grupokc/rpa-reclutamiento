# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2026-02-06
### Added
- **Persistence Layer**:
    - **CsvExporter**: Export data to CSV optimized for Excel (UTF-8-SIG).
        - **Hybrid Flattening**: Latest experience in dedicated columns (`latest_position`, `latest_company`) for filtering, plus full history in `experience_summary_text`.
    - **TomlExporter**: Export to TOML format (best for configuration or small datasets).
    - **ToonExporter**: Export to **TOON** (Token-Oriented Object Notation) for AI token efficiency.
- **CLI Tools**:
    - `main_exporters.py`: Unified CLI to convert JSONL files to any supported format (CSV, TOML, TOON).
    - Usage: `uv run main_exporters.py <input_file> <format>`
- **Core Improvements**:
    - **Text Sanitization**: Added `clean_text` regex-based utility to `PandapeScraper`.
    - Applied globally to remove excessive whitespace, tabs, and newlines from all extracted fields.

## [0.3.1] - 2026-02-06

### Added
- **Architecture & Performance**:
    - **Producer-Consumer Pattern**: Split `PandapeBasePropiaScraper` into two phases:
        - **Harvest (Cosecha)**: Fast collection of candidate IDs/URLs by location.
        - **Process (Worker)**: Detailed enrichment of queued items with strict validation.
    - **JSONL Persistence**: Adopted JSON Lines for efficient, append-only storage of large datasets (60,000+).
    - **Methods**: Added `harvest_candidates` and `process_queue` to scraper, `append_jsonl` to `JsonExporter`.
- **Logic & Integrity**:
    - **State-by-State Harvesting**: Iterates through `loc_map` to respect limits per state.
    - **Strict Enrichment Validation**: Prevents saving unenriched (empty) records to the final database.
    - **Automated Filter Handling**: Auto-clicks "Show all" and handles hidden inputs for location filtering.

## [0.3.0] - 2026-02-06

### Added
- **Infrastructure Layer**:
    - **PandapeBasePropiaScraper**:
        - New scraper specialized for "Base Propia" in Pandape.
        - **Robust Pagination**: Added multiple selector strategies (`.js_btnPaginationNext`, ID, Icons) and `force=True` click handling to bypass UI obstructions.
        - **Incremental Saving**: Implemented `on_page_callback` to save data to disk immediately after each page is processed.
        - **ID-Based Deduplication**: Loads existing JSON database at startup and ignores candidates with already processed IDs.
    - **PandapeScraper (Base)**:
        - Refactored `_change_page` and `_has_next_page` for higher reliability.
        - Improved location filtering with explicit value mapping and fallback to JS clicks.
- **Execution**:
    - New entry point `main_base_propia.py` for standalone execution of the Base Propia scraper.
- **UI**:
    - Updated `app.py` to generate unique filenames using timestamps, preventing overwrites in general searches.

## [0.2.1] - 2026-01-27

### Added
- **Domain Layer**:
    - `CandidateSchema`: Added `last_updated` field to track candidate activity freshness.
    - Updated `Experience` model to be a structured object (Position, Company, Dates, Description) instead of a simple string list.
- **Infrastructure Layer**:
    - **OCCScraper**:
        - Implemented **Detailed Experience Extraction**: Now extracts experience as structured objects, parsing position, company, and dates from the HTML.
        - **Nested DOM Handling**: Improved extraction logic to handle nested wrapper `div`s in the experience list, ensuring all items are captured.
        - **Last Activity Extraction**: Parsed "Última actividad" from candidate profile metadata.
        - **Robustness**: Added fallback logic to Parse DOM if JSON extraction fails or is incomplete.

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
        - Added `limit` parameter to control the number of pages to scrape.
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
