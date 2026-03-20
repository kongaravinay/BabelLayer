"""Tests for the quality analyzer (anomaly detection + reporting)."""
import pytest
from ai.anomaly_detector import QualityAnalyzer


class TestQualityAnalyzer:

    def test_detect_anomalies(self, outlier_df):
        results = QualityAnalyzer().detect_anomalies(outlier_df)
        assert results["total_rows"] == len(outlier_df)
        assert results["anomalies_found"] > 0

    def test_quality_report(self, sample_df):
        report = QualityAnalyzer().quality_report(sample_df)
        assert "total_rows" in report
        assert "overall_quality_score" in report
        assert report["overall_quality_score"] >= 0
        assert report["total_rows"] == len(sample_df)

    def test_completeness_reported(self, sample_df):
        report = QualityAnalyzer().quality_report(sample_df)
        for col in sample_df.columns:
            assert col in report["completeness"]

    def test_empty_dataframe(self):
        import pandas as pd
        report = QualityAnalyzer().quality_report(pd.DataFrame({"x": []}))
        assert report["total_rows"] == 0
