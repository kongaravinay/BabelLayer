# BabelLayer Codebase Tour

This file gives a quick map of where things live and why.

## Main Folders

- `src/`
  - App source code.
- `tests/`
  - Automated tests for core behavior.
- `data/`
  - Sample input files used for demos.
- `docs/`
  - Project documentation and walkthroughs.

## Inside `src/`

- `main.py`
  - Application entry point.
  - Configures logging, creates Qt app, opens the main window.

- `config.py`
  - Central configuration from environment variables.
  - Defines paths, JWT settings, model settings, and logging options.

- `gui/`
  - Desktop interface.
  - `login_dialog.py`: sign-in workflow.
  - `main_window.py`: tabs for Projects, Data, Mapping, Transform, Reports, Audit.
  - `theme.py`: visual style.
  - `helpers/presenters.py`: rendering helpers for mapping/results views.

- `database/`
  - SQLAlchemy persistence layer.
  - `models.py`: ORM models for users, projects, datasets, mappings, jobs, reports.
  - `connection.py`: engine and session management.
  - `init_db.py`: create tables and seed default admin.

- `auth/`
  - Authentication helpers.
  - `passwords.py`: bcrypt hash/verify.
  - `session.py`: in-memory session + JWT handling.

- `ingestion/`
  - File parsing and profiling.
  - `parsers.py`: unified load function for CSV/JSON/XML/Excel.

- `ai/`
  - Mapping and data-quality logic.
  - `schema_mapper.py`: field similarity and mapping suggestions.
  - `anomaly_detector.py`: quality report and anomaly detection.
  - `llm_explainer.py`: optional explanation backend integration.

- `transformation/`
  - Data transformation workflow.
  - `engine.py`: applies mapping specs to DataFrames.
  - `validator.py`: rule-based input checks.

- `reporting/`
  - Output reports.
  - `charts.py`: matplotlib chart builders.
  - `pdf_generator.py`: PDF report composition.

- `api/`
  - External data connectors.
  - `rest_client.py`: fetches API data into DataFrames.
  - `google_drive.py`: downloads compatible files from Drive.

## Most Important Files to Read First

1. `src/main.py`
2. `src/gui/main_window.py`
3. `src/gui/helpers/presenters.py`
4. `src/ingestion/parsers.py`
5. `src/ai/schema_mapper.py`
6. `src/ai/anomaly_detector.py`
7. `src/transformation/engine.py`
8. `src/database/models.py`
9. `src/reporting/pdf_generator.py`

## Recommended Learning Path

1. Start app flow: `main.py` -> `gui/login_dialog.py` -> `gui/main_window.py`.
2. Follow Data tab loading into ingestion parser.
3. Follow Mapping tab into schema mapper.
4. Follow Transform tab into transformation engine.
5. Follow Reports tab into anomaly detector and PDF/charts.
6. Open tests to see expected behavior and edge cases.
