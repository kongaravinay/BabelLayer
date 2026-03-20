"""Presentation helpers used by the main window.

These functions keep the UI rendering rules in one place so the main
window can focus on workflow orchestration.
"""
from pathlib import Path

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QTextEdit


def render_mapping_table(table: QTableWidget, suggestions: list[dict], colors: dict) -> None:
    """Render mapping suggestions into the mapping table."""
    table.setRowCount(len(suggestions))

    for row_index, suggestion in enumerate(suggestions):
        table.setItem(row_index, 0, QTableWidgetItem(suggestion["source_field"]))
        table.setItem(row_index, 1, QTableWidgetItem(suggestion["target_field"]))

        confidence = suggestion["confidence"]
        confidence_item = QTableWidgetItem(f"{confidence:.0%}")
        confidence_item.setBackground(_confidence_color(confidence, colors))

        table.setItem(row_index, 2, confidence_item)
        table.setItem(row_index, 3, QTableWidgetItem("Suggested"))


def render_quality_report(report_box: QTextEdit, report: dict, source_path: str | None) -> None:
    """Render a quality scorecard into the reports text widget."""
    report_box.clear()
    report_box.append("=" * 60)
    report_box.append("DATA QUALITY REPORT")
    report_box.append("=" * 60)

    dataset_name = Path(source_path).name if source_path else "?"
    report_box.append(f"\nDataset: {dataset_name}")
    report_box.append(f"Rows: {report['total_rows']}  |  Columns: {report['total_columns']}")
    duplicate_pct = (report["duplicates"] / max(report["total_rows"], 1)) * 100
    report_box.append(f"Duplicates: {report['duplicates']} ({duplicate_pct:.1f}%)")

    score = report["overall_quality_score"]
    rating = _quality_rating(score)
    report_box.append(f"\nQuality Score: {score:.1f}/100  ({rating})")

    dimensions = report.get("quality_dimensions", {})
    if dimensions:
        report_box.append("\n--- QUALITY DIMENSIONS ---")
        report_box.append(f"  Completeness: {dimensions.get('completeness', 0):.1f}")
        report_box.append(f"  Uniqueness:   {dimensions.get('uniqueness', 0):.1f}")
        report_box.append(f"  Validity:     {dimensions.get('validity', 0):.1f}")
        report_box.append(f"  Consistency:  {dimensions.get('consistency', 0):.1f}")

    report_box.append("\n--- COMPLETENESS ---")
    for field_name, details in report["completeness"].items():
        completeness = details["completeness_pct"]
        bar = "#" * int(completeness / 5) + "-" * (20 - int(completeness / 5))
        report_box.append(
            f"  {field_name:25s} [{bar}] {completeness:.0f}%  (nulls: {details['null_count']})"
        )

    statistics = report.get("statistics", {})
    if statistics:
        report_box.append("\n--- NUMERIC STATS ---")
        for field_name, stat in statistics.items():
            report_box.append(
                f"  {field_name}: mean={stat['mean']:.1f}, std={stat['std']:.1f}, "
                f"range=[{stat['min']:.1f}, {stat['max']:.1f}]"
            )

    findings = report.get("quality_findings", [])
    if findings:
        report_box.append("\n--- FINDINGS ---")
        for item in findings:
            report_box.append(f"  - {item}")


def render_anomaly_report(report_box: QTextEdit, results: dict) -> None:
    """Render anomaly detection output into the reports text widget."""
    report_box.clear()
    report_box.append("=" * 50)
    report_box.append("ANOMALY DETECTION")
    report_box.append("=" * 50)
    report_box.append(f"\nRows analyzed: {results['total_rows']}")
    report_box.append(f"Anomalies found: {results['anomalies_found']}")

    anomaly_rate = results["anomalies_found"] / max(results["total_rows"], 1) * 100
    report_box.append(f"Anomaly rate: {anomaly_rate:.1f}%")

    if results.get("anomaly_indices"):
        report_box.append(f"\nAnomalous rows (first 20): {results['anomaly_indices'][:20]}")

    for field_name, details in results.get("column_anomalies", {}).items():
        report_box.append(f"\n  {field_name}: {details.get('anomaly_count', 0)} anomalies")
        if details.get("normal_mean") is not None:
            report_box.append(
                f"    Normal range: {details['normal_min']:.1f}-{details['normal_max']:.1f}"
            )


def _confidence_color(confidence: float, colors: dict) -> QColor:
    if confidence >= 0.8:
        return QColor(colors["highlight_green"])
    if confidence >= 0.6:
        return QColor(colors["highlight_yellow"])
    return QColor(colors["highlight_red"])


def _quality_rating(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 60:
        return "FAIR"
    return "POOR"
