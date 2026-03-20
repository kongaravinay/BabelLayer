# BabelLayer

BabelLayer is a desktop data translation tool for mapping fields between datasets,
running transformations, validating results, and generating quality reports.

## Features

- PyQt6 desktop interface with guided tabs.
- Username/password authentication with role support.
- Data ingestion from CSV, JSON, XML, and Excel.
- Schema mapping suggestions with confidence scores.
- Data quality profiling and anomaly detection.
- Transformation execution with export to CSV, JSON, and Excel.
- PDF report generation with charts.

## Project Structure

- `src/` application code
- `tests/` automated tests
- `data/samples/` example datasets
- `docs/` learning-oriented documentation

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
	- `pip install -r requirements.txt`
3. Initialize database:
	- `python src/database/init_db.py`
4. Run the app:
	- `python src/main.py`

## Learning Docs

- `docs/BEGINNER_GUIDE.md`
- `docs/CODEBASE_TOUR.md`

## Course Compliance Docs

- `docs/DATA_PROVENANCE.md`
- `docs/VIDEO_RESEARCH.md`
- `docs/A_TRACK_PAPER_OUTLINE.md`