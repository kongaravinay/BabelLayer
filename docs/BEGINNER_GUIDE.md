# BabelLayer Explained for a 13-Year-Old

Imagine your school has data in different formats:
- one file has `student_name`
- another has `name`
- another has `fullName`

All of them mean almost the same thing, but computers do not guess that automatically.

BabelLayer helps people:
1. load messy data files,
2. match columns between files,
3. transform the data into one clean shape,
4. check for weird values,
5. export the results and a report.

## What This App Does in Real Life

- A hospital could load patient and billing files, then map `patient_id` to `member_id`.
- A shop could combine online orders and POS sales, then detect strange transactions.
- A finance team could normalize account data from different systems.

## The Big Parts (Simple View)

- GUI: the windows, buttons, tabs, and tables you click.
- Database: remembers users, projects, logs, and metadata.
- Mapping and analytics: suggests field matches and finds anomalies.
- Ingestion: reads CSV, JSON, XML, and Excel.
- Reporting: makes charts and PDF summaries.

## Step-by-Step User Journey

### 1) User logs in
- The login dialog asks for username and password.
- Password is checked with bcrypt.
- A session token is created and kept in memory.

### 2) User creates a project
- In the Projects tab, user clicks New Project.
- Project is stored in the database.

### 3) User uploads data
- In the Data tab, user loads source and target files.
- Parsers read the file into pandas DataFrames.
- Data preview appears in tables.

### 4) User runs schema mapping
- In the Mapping tab, user clicks Generate Mappings.
- The mapper compares source and target column names.
- It uses embeddings when available, otherwise a lexical fallback.
- Best matches with confidence scores are shown.

### 5) User runs anomaly detection
- In Reports tab, user clicks Anomaly Detection.
- Isolation Forest checks numeric and selected categorical fields.
- App lists suspicious rows and summary counts.

### 6) User exports results and reports
- In Transform tab, user applies mappings to create output data.
- User can export CSV/JSON/Excel.
- In Reports tab, user can export PDF report with quality stats and charts.

## Why This Project Is Good for Learning

- It is a complete real app: UI + DB + data science + reporting.
- Modules are separated by purpose, so it is easier to read.
- Tests show expected behavior for parsing, auth, mapping, and transform logic.
