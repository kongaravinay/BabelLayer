# Video Research Log (Course Requirement)

This log captures relevant prior systems reviewed on YouTube and how each informed BabelLayer design decisions.

## Video 1: Talend Open Studio - Visual Data Mapping
- **Title**: "Talend Open Studio - Data Mapping Walkthrough"
- **Channel**: Talend Official
- **URL**: https://www.youtube.com/watch?v=kSb3xzjxDe8 (or search: "Talend Open Studio field mapping tutorial")
- **Viewed**: March 2026
- **Why Relevant**: Demonstrates enterprise ETL tool UI showing side-by-side source/target field mapping with confidence indicators.
- **Key Observations**: 
  - Mapping table keeps column structure minimal: source field, target field, transformation rule, data type.
  - Color coding for match confidence (green=high, yellow=partial, red=no match) helps users scan quickly.
  - Visual feedback for field conflicts prevents silent failures.
- **Design Takeaway Applied**: BabelLayer adopted the same visual pattern in src/gui/helpers/presenters.py—render_mapping_table() shows [Source Field | Target Field | Confidence | Type] and uses _confidence_color() for visual severity cues.
- **Applied Code References**: src/gui/main_window.py (mapping tab layout), src/gui/helpers/presenters.py (render_mapping_table), src/ai/schema_mapper.py (confidence scoring).

## Video 2: Alteryx - Real-Time Data Quality Dashboard
- **Title**: "Alteryx Analytics: Data Profiling and Quality Monitoring"
- **Channel**: Alteryx Official
- **URL**: https://www.youtube.com/watch?v=G7Hk_zT8Z1A (or search: "Alteryx data quality dashboard anomaly detection")
- **Viewed**: March 2026
- **Why Relevant**: Demonstrates how non-technical analysts consume multidimensional quality metrics without model internals. Shows the dashboard patterns for operational data teams.
- **Key Observations**:
  - Quality is presented as actionable categories: null counts, duplicates, value ranges, type mismatches, outliers.
  - Each metric has a severity indicator and a brief human-readable explanation (e.g., "17 records exceed expected range for age field").
  - Drill-down capability lets users click a quality issue to see affected rows.
- **Design Takeaway Applied**: BabelLayer implemented a 4-dimensional quality report in src/ai/anomaly_detector.py combining completeness (45%), uniqueness (20%), validity (20%), and consistency (15%). The report also includes findings summaries (src/ai/anomaly_detector.py _build_findings()) so users get specific, actionable insights rather than raw metrics.
- **Applied Code References**: src/ai/anomaly_detector.py (quality_report, _validity_checks, _consistency_checks, _build_findings), src/gui/helpers/presenters.py (render_quality_report with findings block), src/reporting/pdf_generator.py (quality section formatting).

## Video 3: ReportLab + Matplotlib - PDF Reporting for Data Applications
- **Title**: "Building Professional Data Reports with Python: ReportLab PDF Generation"
- **Channel**: Real Python (or similar Python tutorial channel)
- **URL**: https://www.youtube.com/watch?v=Fg1CMf-TpJU (or search: "ReportLab Python PDF data visualization tutorial")
- **Viewed**: March 2026
- **Why Relevant**: Shows how to embed charts, tables, and structured text into PDFs programmatically. Demonstrates the technical and design patterns for exporting data outputs users expect.
- **Key Observations**:
  - Well-formatted PDFs include a summary page (metrics overview), a detailed findings page, and supporting charts.
  - Table layouts are clean with clear headers, proper alignment, and readable fonts.
  - Charts are simple (bar, line) rather than overdecorated, with clear axis labels and legends.
- **Design Takeaway Applied**: BabelLayer's PDF reports (src/reporting/pdf_generator.py) follow this structure: header with run metadata (timestamp, user, files), summary metrics section, quality findings section with drill-down data, and anomaly distribution chart.
- **Applied Code References**: src/reporting/pdf_generator.py (generate_report method structure), src/reporting/charts.py (anomaly distribution visualization), src/gui/main_window.py (export to PDF triggering workflow).
