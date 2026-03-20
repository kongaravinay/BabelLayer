import numpy as np
import pandas as pd
import logging
import re
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

from config import ANOMALY_CONTAMINATION

log = logging.getLogger(__name__)


class DataQualityChecker:
    """Analyzes data for quality issues: missing values, duplicates, anomalies, and data validity."""

    def __init__(self, contamination: float = None):
        self.contamination = contamination or ANOMALY_CONTAMINATION

    # -- Anomaly detection ----------------------------------------------------

    def detect_anomalies(self, df: pd.DataFrame, columns: list[str] | None = None) -> dict:
        """
        Run Isolation Forest across numeric (and optionally categorical) columns.
        Returns a dict with total_rows, anomalies_found, anomaly_indices,
        anomaly_scores, and per-column details.
        """
        if columns is None:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()[:5]
            columns = num_cols + cat_cols

        result: dict = {
            "total_rows": len(df),
            "anomalies_found": 0,
            "anomaly_indices": [],
            "anomaly_scores": [],
            "column_anomalies": {},
        }

        X = self._encode_for_ml(df, columns)
        if X.shape[1] == 0:
            log.warning("No usable columns for anomaly detection")
            return result

        model = IsolationForest(
            contamination=self._contamination,
            n_estimators=100,
            random_state=42,
        )
        labels = model.fit_predict(X)
        scores = model.score_samples(X)

        anomaly_mask = labels == -1
        result["anomalies_found"] = int(anomaly_mask.sum())
        result["anomaly_indices"] = df.index[anomaly_mask].tolist()
        result["anomaly_scores"] = scores.tolist()

        for col in columns:
            if col in df.columns:
                result["column_anomalies"][col] = self._column_detail(df[col], anomaly_mask)

        log.info("Anomalies: %d / %d rows", result["anomalies_found"], len(df))
        return result

    # -- Quality scorecard ----------------------------------------------------

    def quality_report(self, df: pd.DataFrame) -> dict:
        """
        Profile the dataset: completeness per column, duplicates, basic stats,
        and an overall quality score (0–100).
        """
        total_rows = len(df)
        duplicate_count = int(df.duplicated().sum())

        report = {
            "total_rows": total_rows,
            "total_columns": len(df.columns),
            "duplicates": duplicate_count,
            "completeness": {},
            "data_types": {},
            "statistics": {},
            "quality_dimensions": {},
            "quality_findings": [],
        }

        for col in df.columns:
            nulls = int(df[col].isnull().sum())
            pct = (1 - nulls / total_rows) * 100 if total_rows else 100
            report["completeness"][col] = {"null_count": nulls, "completeness_pct": pct}
            report["data_types"][col] = str(df[col].dtype)

        for col in df.select_dtypes(include=[np.number]).columns:
            report["statistics"][col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
            }

        avg_completeness = float(np.mean([v["completeness_pct"] for v in report["completeness"].values()]))
        uniqueness_score = max(0.0, 100.0 - self._ratio(duplicate_count, total_rows) * 100)

        validity = self._validity_checks(df)
        consistency = self._consistency_checks(df)

        report["quality_dimensions"] = {
            "completeness": round(avg_completeness, 1),
            "uniqueness": round(uniqueness_score, 1),
            "validity": round(validity["score"], 1),
            "consistency": round(consistency["score"], 1),
        }

        report["quality_findings"] = self._build_findings(
            duplicate_count=duplicate_count,
            validity=validity,
            consistency=consistency,
        )

        weighted_score = (
            0.45 * report["quality_dimensions"]["completeness"]
            + 0.20 * report["quality_dimensions"]["uniqueness"]
            + 0.20 * report["quality_dimensions"]["validity"]
            + 0.15 * report["quality_dimensions"]["consistency"]
        )
        report["overall_quality_score"] = round(max(0.0, min(100.0, weighted_score)), 1)

        return report

    # -- Internal helpers -----------------------------------------------------

    def _encode_for_ml(self, df: pd.DataFrame, columns: list[str]) -> np.ndarray:
        """Build a numeric matrix from a mix of numeric and categorical columns."""
        parts = []
        for col in columns:
            if col not in df.columns:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                vals = df[col].fillna(df[col].median()).values.reshape(-1, 1)
            else:
                enc = LabelEncoder()
                vals = enc.fit_transform(df[col].fillna("__MISSING__").astype(str)).reshape(-1, 1)
            parts.append(vals)
        return np.hstack(parts) if parts else np.empty((len(df), 0))

    @staticmethod
    def _column_detail(series: pd.Series, anomaly_mask: np.ndarray) -> dict:
        """Summarize the anomalous vs. normal values for one column."""
        anomalous = series[anomaly_mask]
        normal = series[~anomaly_mask]
        info = {
            "anomaly_count": int(len(anomalous)),
            "anomaly_values": anomalous.tolist()[:10],
        }
        if pd.api.types.is_numeric_dtype(series) and len(normal) > 0:
            info.update({
                "normal_mean": float(normal.mean()),
                "normal_std": float(normal.std()),
                "normal_min": float(normal.min()),
                "normal_max": float(normal.max()),
            })
        return info

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return float(numerator / denominator)

    def _validity_checks(self, df: pd.DataFrame) -> dict:
        """Check data validity for emails, dates, and non-negative numeric fields."""
        total_checks = 0
        invalid_count = 0
        invalid_email_count = 0
        invalid_date_count = 0
        negative_value_count = 0

        email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

        for col in df.columns:
            series = df[col]
            col_name = str(col).lower()

            if "email" in col_name:
                non_null = series.dropna().astype(str)
                total_checks += len(non_null)
                bad = int((~non_null.str.match(email_pattern)).sum())
                invalid_email_count += bad
                invalid_count += bad

            if any(k in col_name for k in ("date", "time")):
                non_null = series.dropna().astype(str)
                total_checks += len(non_null)
                parsed = pd.to_datetime(non_null, errors="coerce")
                bad = int(parsed.isna().sum())
                invalid_date_count += bad
                invalid_count += bad

            if pd.api.types.is_numeric_dtype(series) and any(
                k in col_name for k in ("quantity", "price", "total", "amount", "count", "num")
            ):
                non_null = series.dropna()
                total_checks += len(non_null)
                bad = int((non_null < 0).sum())
                negative_value_count += bad
                invalid_count += bad

        invalid_ratio = self._ratio(invalid_count, total_checks)
        score = max(0.0, 100.0 - invalid_ratio * 100)

        return {
            "score": score,
            "invalid_count": invalid_count,
            "checks": total_checks,
            "invalid_email_count": invalid_email_count,
            "invalid_date_count": invalid_date_count,
            "negative_value_count": negative_value_count,
        }

    def _consistency_checks(self, df: pd.DataFrame) -> dict:
        """Estimate consistency using row-level outlier incidence (IQR rule)."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(df) == 0:
            return {"score": 100.0, "outlier_rows": 0, "outlier_rate": 0.0}

        outlier_mask = np.zeros(len(df), dtype=bool)
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if len(series) < 5:
                continue
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            col_outliers = (numeric_df[col] < lower) | (numeric_df[col] > upper)
            outlier_mask = outlier_mask | col_outliers.fillna(False).to_numpy()

        outlier_rows = int(outlier_mask.sum())
        outlier_rate = self._ratio(outlier_rows, len(df))
        score = max(0.0, 100.0 - outlier_rate * 100)

        return {
            "score": score,
            "outlier_rows": outlier_rows,
            "outlier_rate": outlier_rate,
        }

    @staticmethod
    def _build_findings(duplicate_count: int, validity: dict, consistency: dict) -> list[str]:
        findings = []
        if duplicate_count:
            findings.append(f"{duplicate_count} duplicate rows detected.")
        if validity.get("invalid_email_count"):
            findings.append(f"{validity['invalid_email_count']} invalid email values detected.")
        if validity.get("invalid_date_count"):
            findings.append(f"{validity['invalid_date_count']} invalid date/time values detected.")
        if validity.get("negative_value_count"):
            findings.append(f"{validity['negative_value_count']} negative values found in non-negative numeric fields.")
        if consistency.get("outlier_rows"):
            findings.append(
                f"{consistency['outlier_rows']} rows flagged as numeric outliers (IQR rule)."
            )
        if not findings:
            findings.append("No major quality issues detected by current rules.")
        return findings
