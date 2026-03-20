"""
Data quality analysis: anomaly detection + completeness reporting.

Uses Isolation Forest for multivariate anomaly detection and basic
pandas profiling for the quality scorecard.
"""
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import logging

from config import ANOMALY_CONTAMINATION

log = logging.getLogger(__name__)


class QualityAnalyzer:
    """Finds outliers and produces quality scorecards for tabular data."""

    def __init__(self, contamination: float = None):
        self._contamination = contamination or ANOMALY_CONTAMINATION

    # -- Anomaly detection ----------------------------------------------------

    def detect_anomalies(self, df: pd.DataFrame, columns=None):
        """
        Run Isolation Forest across numeric (and optionally categorical) columns.
        Returns a dict with total_rows, anomalies_found, anomaly_indices,
        anomaly_scores, and per-column details.
        """
        if columns is None:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()[:5]
            columns = num_cols + cat_cols

        result = {
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

    def quality_report(self, df: pd.DataFrame):
        """
        Profile the dataset: completeness per column, duplicates, basic stats,
        and an overall quality score (0–100).
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "duplicates": int(df.duplicated().sum()),
            "completeness": {},
            "data_types": {},
            "statistics": {},
        }

        for col in df.columns:
            nulls = int(df[col].isnull().sum())
            pct = (1 - nulls / len(df)) * 100 if len(df) else 100
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

        avg_completeness = np.mean([v["completeness_pct"] for v in report["completeness"].values()])
        dup_penalty = (report["duplicates"] / len(df) * 100) if len(df) else 0
        report["overall_quality_score"] = max(0.0, float(avg_completeness - dup_penalty))

        return report

    # -- Internal helpers -----------------------------------------------------

    def _encode_for_ml(self, df, columns):
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
    def _column_detail(series, anomaly_mask):
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
