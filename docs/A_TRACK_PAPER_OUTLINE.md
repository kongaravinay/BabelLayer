# A-Track Design Science Paper Outline

## Working Title
BabelLayer: A Desktop Data Translation and Quality Intelligence System for Multi-Format Operational Data

## 1. Problem Motivation
- Organizations receive heterogeneous files with incompatible schemas.
- Manual mapping and validation are slow and error-prone.
- Need: a practical desktop artifact for ingestion, mapping, quality analysis, and reporting.

## 2. Research Question
How can a desktop decision-support artifact reduce schema translation effort while preserving reportable data quality outcomes for non-technical users?

## 3. Design Science Framing
- Artifact type: Construct + instantiation.
- Relevance cycle: Operational users need explainable data preparation workflows.
- Rigor cycle: Uses prior work in schema matching, anomaly detection, and reporting UX.
- Design cycle: Build-evaluate-refine iterations across ingestion, mapping, and reporting modules.

## 4. Artifact Description
- GUI workflow: Login, project management, data load, mapping, transform, reports.
- Persistence: SQLAlchemy models for users/projects/datasets/mappings/jobs/reports.
- Intelligence modules:
  1. Semantic/lexical field mapping.
  2. Statistical anomaly detection (Isolation Forest).
  3. Natural-language explanation service.
- Output: transformed files and PDF reports.

## 5. Evaluation Plan
- Functional validation via automated tests.
- Scenario-based user walkthrough with representative datasets.
- Metrics:
  - mapping coverage rate,
  - anomaly detection incidence,
  - time-to-report,
  - task completion rate for novice users.

## 6. Results to Report
- What worked well in real workflows.
- Failure modes (missing fields, malformed files, low-confidence mapping).
- Security and governance constraints observed.

## 7. Contribution
- Practical design pattern for desktop-first data translation systems.
- Repeatable modular architecture balancing usability and technical depth.

## 8. Limitations
- Prototype-scale data and environment.
- Dependence on configured external services for some explanation features.
- Role-based controls implemented but not enterprise IAM depth.

## 9. Future Work
- Stronger policy engine and audit controls.
- Expanded model benchmarking for mapping/anomaly tasks.
- Potential deployment packaging and organizational pilot.

## 10. Conference Packaging Checklist
- Include reproducibility appendix.
- Include artifact architecture figure.
- Include design decisions and rejected alternatives.
- Include evaluation protocol and validity threats.
