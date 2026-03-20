# Data Provenance and Sourcing Plan

## Purpose
This document records where BabelLayer datasets come from, how they are prepared, and what usage constraints apply.

## Datasets Used

### 1. Retail Transactions Dataset
- **Primary Source**: Generated synthetic data modeled after Kaggle retail transaction patterns.
- **Reference**: Based structure on "Online Retail Dataset" by UCI ML Repository (Daqing Chen, Sai Liang Tan)
- **License**: Educational use (CC BY-SA 4.0)
- **Storage Path**: data/samples/retail_transactions.json, data/samples/retail/ecommerce_orders.json, data/samples/retail/pos_sales.csv
- **Fields**: OrderID, CustomerID, ProductName, Quantity, UnitPrice, TransactionDate, Amount, Store
- **Use in Project**: 
  - Schema mapping demo (ecommerce_orders.json → pos_sales.csv with field name mismatches)
  - Transformation testing (unit price × quantity = total amount)
  - Anomaly detection on negative prices, outlier order quantities
  - Multi-format ingestion (JSON vs CSV).
- **Quality Issues Intentionally Included**: ~5% null OrderIDs, 3 duplicate transactions, 2 negative prices (to test data validity checks), 1 future-dated transaction (to test consistency checks).

### 2. Healthcare Records Dataset
- **Source Type**: Synthetic educational records (no real PHI, HIPAA-compliant).
- **Generated With**: Faker library + domain knowledge to create realistic healthcare structure.
- **License**: Project-created, freely redistributable for educational purposes.
- **Storage Path**: data/samples/healthcare_patients.csv, data/samples/healthcare/billing_records.json, data/samples/healthcare/lab_results.xml, data/samples/healthcare/patients_demographics.csv
- **Fields**: PatientID, FirstName, LastName, DOB, Gender, Insurance, BillingAmount, LabTest, Result, ResultDate
- **Use in Project**: 
  - Multi-format ingestion (CSV, JSON, XML; tests parser robustness across 3 formats)
  - Data quality reporting (test validity checks for dates, email formats)
  - Schema mapping between demographic file (broad patient info) and billing records (narrower transaction view)
  - Consistency checks (patient age vs DOB should match).
- **Quality Issues Intentionally Included**: 2 invalid DOB values (future dates), 1 mismatched age, 4 null insurance codes, 1 duplicate patient record with slight name variation.

### 3. Finance Accounts Dataset
- **Source Type**: Synthetic account and transaction data generated for testing numeric/financial logic.
- **Generated With**: Python Faker + pandas to create realistic account structures and transaction volumes.
- **License**: Project-created, freely redistributable.
- **Storage Path**: data/samples/finance_accounts.csv, data/samples/finance/bank_statements.csv, data/samples/finance/merchant_pos.json
- **Fields**: AccountID, AccountHolder, Balance, TransactionID, Amount, TransactionType (debit/credit), Date, Merchant
- **Use in Project**: 
  - Transformation testing (field-level math: running balance calculations)
  - Anomaly detection on balance changes (isolation forest to flag suspicious transaction sizes)
  - Role-based reporting (admin sees all accounts; staff see only assigned accounts)
  - Numeric data validation (negative transaction amounts, unrealistic processing fees).
- **Quality Issues Intentionally Included**: 2 records with negative balances (rare but valid), 5 outlier transaction amounts (>$50k, flagged by anomaly detector), 1 transaction reversing a previous entry (tests consistency detection).

## Compliance and Ethical Notes
- **No Real Data**: All datasets are synthetic or heavily anonymized derivatives.
- **Educational Use Only**: Datasets exist solely to demonstrate BabelLayer's ingest → map → transform → report workflow.
- **Reproducibility**: Each dataset is static and stored in version control; no external dependency on live data sources.
- **Audit Trail**: All dataset loads are logged in the database with timestamp and user ID via src/database/models.py ProjectRun table.

## Data Preparation Workflow
1. **Ingest**: Raw files loaded through src/ingestion/parsers.py (CSV reader, JSON parser, XML handler).
2. **Profile**: Schema inferred and null/type profile computed via src/ai/anomaly_detector.py profile_columns().
3. **Persist**: Ingest metadata stored in database (ProjectRun, DataProfile tables) for traceability.
4. **Map**: User-configured schema mappings executed via src/ai/schema_mapper.py suggest_mapping().
5. **Transform**: Field-level rules applied through src/transformation/engine.py (safe rule DSL, no eval).
6. **Report**: Quality metrics computed (src/ai/anomaly_detector.py) and exported as PDF or charts.

## Reproducibility Information
- **Dataset Access Date**: March 2026
- **Python Version**: 3.12+
- **Libraries**: pandas 2.0+, faker (for synthetic generation), openpyxl for Excel support
- **Checksum Reference**: See data/CHECKSUMS.txt (generated on first run) for dataset integrity validation.
- **Extension Path**: To add external datasets: update DATA_PROVENANCE.md with URL, license, access_date, and field sensitivity classification (public/sensitive/restricted).
