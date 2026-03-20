"""
Main application window.

The 980-line original has been broken down by responsibility:
  - Tab construction (each tab is a private method returning a QWidget)
    - Business logic is delegated to service modules (mapping/, transformation/, etc.)
  - Styling lives in theme.py
  - File loading uses ingestion.load_file()
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QMessageBox, QTextEdit,
    QFileDialog, QStatusBar, QTableWidget, QTableWidgetItem,
    QLineEdit, QProgressBar, QGroupBox, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QInputDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QColor
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

from gui.login_dialog import LoginDialog
from gui.theme import app_stylesheet, COLORS
from auth import current_session
from config import APP_TITLE, APP_VERSION, ROOT_DIR
from database import db_session
from database.models import Project, User, AuditLog

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # App state
        self._user = None
        self._source_df = None
        self._target_df = None
        self._source_path = None
        self._target_path = None
        self._mappings = []
        self._result_df = None

        if not self._login():
            import sys
            sys.exit(0)

        self._build_ui()

    # ======================================================================
    # Login
    # ======================================================================

    def _login(self) -> bool:
        dlg = LoginDialog(self)
        if dlg.exec() == LoginDialog.DialogCode.Accepted:
            self._user = dlg.user_info
            return True
        return False

    # ======================================================================
    # UI construction
    # ======================================================================

    def _build_ui(self):
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(app_stylesheet())

        self._build_menus()

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        display_name = self._user.get("full_name") or self._user["username"]
        header = QLabel(f"Welcome, {display_name}")
        header.setObjectName("welcomeHeader")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._tab_dashboard(),   "Dashboard")
        tabs.addTab(self._tab_projects(),    "Projects")
        tabs.addTab(self._tab_data(),        "Data")
        tabs.addTab(self._tab_mapping(),     "Mapping")
        tabs.addTab(self._tab_transform(),   "Transform")
        tabs.addTab(self._tab_reports(),     "Reports")
        tabs.addTab(self._tab_audit(),       "Audit")
        layout.addWidget(tabs)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _build_menus(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        file_menu.addAction(self._action("Logout", self._logout))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close))

        help_menu = mb.addMenu("Help")
        help_menu.addAction(self._action("About", self._about))

    def _action(self, text, slot):
        a = QAction(text, self)
        a.triggered.connect(slot)
        return a

    # ======================================================================
    # Dashboard tab
    # ======================================================================

    def _tab_dashboard(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(self._heading("Dashboard"))

        # Stat cards
        cards = QHBoxLayout()
        proj_n, ds_n = 0, 0
        try:
            with db_session() as s:
                proj_n = s.query(Project).filter_by(owner_id=self._user["id"]).count()
        except Exception:
            pass

        for label, value, color in [
            ("Projects", str(proj_n), COLORS["primary"]),
            ("User",     self._user["username"], "#8b5cf6"),
            ("Role",     "Admin" if self._user.get("is_admin") else "Analyst", COLORS["warning"]),
        ]:
            card = self._stat_card(label, value, color)
            cards.addWidget(card)
        lay.addLayout(cards)

        # Quick start
        info = QTextEdit()
        info.setReadOnly(True)
        info.setHtml("""
        <h3>Quick Start</h3>
        <ol>
          <li><b>Projects</b> — Create a project to organize your work</li>
          <li><b>Data</b> — Upload source &amp; target files (CSV, JSON, XML, Excel)</li>
                    <li><b>Mapping</b> — Generate suggested field mappings between datasets</li>
          <li><b>Transform</b> — Execute mappings and export transformed data</li>
          <li><b>Reports</b> — Analyze data quality and export PDF reports</li>
        </ol>
        """)
        lay.addWidget(info)
        return w

    def _stat_card(self, label: str, value: str, color: str) -> QGroupBox:
        box = QGroupBox()
        box.setStyleSheet(
            f"QGroupBox {{ background: {color}; border-radius: 8px; border: none; }}"
            f" QLabel {{ color: white; }}"
        )
        vl = QVBoxLayout(box)
        v = QLabel(value)
        v.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(v)
        l = QLabel(label)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(l)
        return box

    # ======================================================================
    # Projects tab
    # ======================================================================

    def _tab_projects(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Projects"))

        btns = QHBoxLayout()
        btns.addWidget(self._btn("+ New Project", self._new_project))
        btns.addWidget(self._btn("Refresh", self._refresh_projects))
        btns.addWidget(self._btn("Delete Selected", self._delete_project, "danger"))
        btns.addStretch()
        lay.addLayout(btns)

        self._proj_table = self._table(["ID", "Name", "Description", "Status", "Created"])
        self._proj_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self._proj_table)

        self._refresh_projects()
        return w

    def _new_project(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("New Project")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        name_in = QLineEdit()
        name_in.setPlaceholderText("Project name")
        desc_in = QTextEdit()
        desc_in.setPlaceholderText("Description (optional)")
        desc_in.setMaximumHeight(80)
        form.addRow("Name:", name_in)
        form.addRow("Description:", desc_in)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name = name_in.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required.")
            return
        try:
            with db_session() as s:
                s.add(Project(name=name, description=desc_in.toPlainText().strip(),
                              owner_id=self._user["id"]))
            self._refresh_projects()
            self._status.showMessage(f"Project '{name}' created")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _refresh_projects(self):
        try:
            with db_session() as s:
                rows = s.query(Project).filter_by(owner_id=self._user["id"]).all()
                self._proj_table.setRowCount(len(rows))
                for i, p in enumerate(rows):
                    self._proj_table.setItem(i, 0, QTableWidgetItem(str(p.id)))
                    self._proj_table.setItem(i, 1, QTableWidgetItem(p.name))
                    self._proj_table.setItem(i, 2, QTableWidgetItem(p.description or ""))
                    self._proj_table.setItem(i, 3, QTableWidgetItem(p.status))
                    ts = p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else ""
                    self._proj_table.setItem(i, 4, QTableWidgetItem(ts))
        except Exception as exc:
            log.error("Failed to load projects: %s", exc)

    def _delete_project(self):
        row = self._proj_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a project first.")
            return
        name = self._proj_table.item(row, 1).text()
        if QMessageBox.question(self, "Confirm", f"Delete '{name}'?") != QMessageBox.StandardButton.Yes:
            return
        pid = int(self._proj_table.item(row, 0).text())
        try:
            with db_session() as s:
                p = s.query(Project).get(pid)
                if p:
                    s.delete(p)
            self._refresh_projects()
            self._status.showMessage(f"Deleted '{name}'")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    # ======================================================================
    # Data tab
    # ======================================================================

    def _tab_data(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Data Management"))

        # External imports
        ext = QGroupBox("Import from External Sources")
        el = QHBoxLayout(ext)
        el.addWidget(self._btn("Google Drive", self._import_gdrive))
        el.addWidget(self._btn("REST API", self._import_rest))
        el.addStretch()
        lay.addWidget(ext)

        # Source
        src = QGroupBox("Source Dataset")
        sl = QVBoxLayout(src)
        sh = QHBoxLayout()
        self._src_label = QLabel("No file loaded")
        sh.addWidget(self._src_label, 1)
        sh.addWidget(self._btn("Load Source", lambda: self._load_file("source")))
        sl.addLayout(sh)
        self._src_table = QTableWidget()
        self._src_table.setAlternatingRowColors(True)
        sl.addWidget(self._src_table)
        lay.addWidget(src)

        # Target
        tgt = QGroupBox("Target Dataset (for schema mapping)")
        tl = QVBoxLayout(tgt)
        th = QHBoxLayout()
        self._tgt_label = QLabel("No file loaded")
        th.addWidget(self._tgt_label, 1)
        th.addWidget(self._btn("Load Target", lambda: self._load_file("target")))
        tl.addLayout(th)
        self._tgt_table = QTableWidget()
        self._tgt_table.setAlternatingRowColors(True)
        tl.addWidget(self._tgt_table)
        lay.addWidget(tgt)

        return w

    def _load_file(self, role: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {role.title()} File",
            str(ROOT_DIR / "data" / "samples"),
            "Data Files (*.csv *.json *.xml *.xlsx *.xls)",
        )
        if not path:
            return

        try:
            from ingestion import load_file
            df = load_file(path)

            if role == "source":
                self._source_df, self._source_path = df, path
                self._src_label.setText(f"{Path(path).name}  ({len(df)} rows × {len(df.columns)} cols)")
                self._fill_table(self._src_table, df)
            else:
                self._target_df, self._target_path = df, path
                self._tgt_label.setText(f"{Path(path).name}  ({len(df)} rows × {len(df.columns)} cols)")
                self._fill_table(self._tgt_table, df)

            self._status.showMessage(f"Loaded {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load:\n{exc}")

    def _fill_table(self, table: QTableWidget, df: pd.DataFrame, limit=200):
        chunk = df.head(limit)
        table.setRowCount(len(chunk))
        table.setColumnCount(len(chunk.columns))
        table.setHorizontalHeaderLabels([str(c) for c in chunk.columns])

        for r in range(len(chunk)):
            for c in range(len(chunk.columns)):
                val = chunk.iloc[r, c]
                item = QTableWidgetItem(str(val) if pd.notna(val) else "")
                if pd.isna(val):
                    item.setBackground(QColor(COLORS["highlight_yellow"]))
                table.setItem(r, c, item)
        table.resizeColumnsToContents()

    # ======================================================================
    # Mapping tab
    # ======================================================================

    def _tab_mapping(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Schema Mapping"))

        info = QLabel("Load source and target datasets in the Data tab, then generate mappings.")
        info.setWordWrap(True)
        lay.addWidget(info)

        btns = QHBoxLayout()
        btns.addWidget(self._btn("Generate Mappings", self._gen_mappings, "success"))
        btns.addWidget(self._btn("Explain Selected", self._explain_mapping))
        btns.addWidget(self._btn("Clear", self._clear_mappings))
        btns.addStretch()
        lay.addLayout(btns)

        self._map_progress = QProgressBar()
        self._map_progress.setVisible(False)
        lay.addWidget(self._map_progress)

        self._map_table = self._table(["Source Field", "Target Field", "Confidence", "Type"])
        self._map_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self._map_table)

        self._explain_box = QTextEdit()
        self._explain_box.setReadOnly(True)
        self._explain_box.setMaximumHeight(110)
        self._explain_box.setPlaceholderText("Select a row and click 'Explain Selected' to view the mapping rationale.")
        lay.addWidget(self._explain_box)

        return w

    def _gen_mappings(self):
        if self._source_df is None or self._target_df is None:
            QMessageBox.warning(self, "Error", "Load both source and target files first.")
            return

        self._map_progress.setVisible(True)
        self._map_progress.setRange(0, 0)
        self._status.showMessage("Computing mappings...")

        try:
            from ai.schema_mapper import SchemaMapper
            mapper = SchemaMapper()
            suggestions = mapper.suggest_mappings(
                list(self._source_df.columns),
                list(self._target_df.columns),
            )
            self._mappings = suggestions

            self._map_table.setRowCount(len(suggestions))
            for i, s in enumerate(suggestions):
                self._map_table.setItem(i, 0, QTableWidgetItem(s["source_field"]))
                self._map_table.setItem(i, 1, QTableWidgetItem(s["target_field"]))

                conf = s["confidence"]
                ci = QTableWidgetItem(f"{conf:.0%}")
                if conf >= 0.8:
                    ci.setBackground(QColor(COLORS["highlight_green"]))
                elif conf >= 0.6:
                    ci.setBackground(QColor(COLORS["highlight_yellow"]))
                else:
                    ci.setBackground(QColor(COLORS["highlight_red"]))
                self._map_table.setItem(i, 2, ci)
                self._map_table.setItem(i, 3, QTableWidgetItem("Suggested"))

            self._map_progress.setVisible(False)
            self._status.showMessage(f"{len(suggestions)} mappings generated")
        except Exception as exc:
            self._map_progress.setVisible(False)
            QMessageBox.critical(self, "Error", f"Mapping failed:\n{exc}")

    def _explain_mapping(self):
        row = self._map_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a mapping row first.")
            return

        src = self._map_table.item(row, 0).text()
        tgt = self._map_table.item(row, 1).text()
        conf = float(self._map_table.item(row, 2).text().replace("%", "")) / 100

        self._status.showMessage("Generating explanation…")
        try:
            from ai.llm_explainer import Explainer
            explanation = Explainer().explain_mapping(src, tgt, conf)
            if explanation:
                self._explain_box.setHtml(
                    f"<b>{src} → {tgt}</b> ({conf:.0%})<br><br>{explanation}"
                )
            else:
                self._explain_box.setPlainText(
                    f"Could not generate explanation.\n"
                    f"Make sure Ollama is running or set OPENAI_API_KEY in .env"
                )
            self._status.showMessage("Explanation ready")
        except Exception as exc:
            self._explain_box.setPlainText(f"Error: {exc}")

    def _clear_mappings(self):
        self._map_table.setRowCount(0)
        self._mappings.clear()
        self._explain_box.clear()
        self._status.showMessage("Mappings cleared")

    # ======================================================================
    # Transform tab
    # ======================================================================

    def _tab_transform(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Data Transformation"))

        info = QLabel("Generate mappings first, then execute the transformation here.")
        info.setWordWrap(True)
        lay.addWidget(info)

        btns = QHBoxLayout()
        btns.addWidget(self._btn("Execute", self._run_transform, "success"))
        btns.addWidget(self._btn("Export CSV", self._export_result))
        btns.addStretch()
        lay.addLayout(btns)

        self._txn_log = QTextEdit()
        self._txn_log.setReadOnly(True)
        self._txn_log.setMaximumHeight(110)
        self._txn_log.setPlaceholderText("Transformation log…")
        lay.addWidget(self._txn_log)

        self._result_table = QTableWidget()
        self._result_table.setAlternatingRowColors(True)
        lay.addWidget(self._result_table)

        return w

    def _run_transform(self):
        if self._source_df is None:
            QMessageBox.warning(self, "Error", "No source data.")
            return
        if not self._mappings:
            QMessageBox.warning(self, "Error", "No mappings. Generate them first.")
            return

        try:
            from transformation.engine import TransformEngine
            engine = TransformEngine()

            self._txn_log.clear()
            ts = datetime.now().strftime("%H:%M:%S")
            self._txn_log.append(f"[{ts}] Starting transformation…")

            for m in self._mappings:
                engine.add(m["source_field"], m["target_field"], "direct")
                self._txn_log.append(f"  {m['source_field']} → {m['target_field']}")

            self._result_df = engine.run(self._source_df)
            stats = engine.stats

            ts = datetime.now().strftime("%H:%M:%S")
            self._txn_log.append(f"\n[{ts}] Done — {len(self._result_df)} rows, "
                                 f"{stats['errors']} errors")
            if stats["errors"]:
                for err in stats["error_messages"]:
                    self._txn_log.append(f"  ERROR: {err}")

            self._fill_table(self._result_table, self._result_df)
            self._status.showMessage(f"Transformed {len(self._result_df)} rows")

        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_result(self):
        if self._result_df is None:
            QMessageBox.warning(self, "Error", "Run a transformation first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export", str(ROOT_DIR / "data" / "output.csv"),
            "CSV (*.csv);;JSON (*.json);;Excel (*.xlsx)",
        )
        if not path:
            return
        ext = Path(path).suffix.lower()
        try:
            if ext == ".csv":
                self._result_df.to_csv(path, index=False)
            elif ext == ".json":
                self._result_df.to_json(path, orient="records", indent=2)
            elif ext == ".xlsx":
                self._result_df.to_excel(path, index=False)
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    # ======================================================================
    # Reports tab
    # ======================================================================

    def _tab_reports(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Quality Reports"))

        info = QLabel("Load a dataset, then run quality analysis or anomaly detection.")
        info.setWordWrap(True)
        lay.addWidget(info)

        btns = QHBoxLayout()
        btns.addWidget(self._btn("Quality Analysis", self._run_quality, "success"))
        btns.addWidget(self._btn("Anomaly Detection", self._run_anomalies))
        btns.addWidget(self._btn("Export PDF", self._export_pdf))
        btns.addStretch()
        lay.addLayout(btns)

        self._report_box = QTextEdit()
        self._report_box.setReadOnly(True)
        self._report_box.setPlaceholderText("Analysis results appear here…")
        lay.addWidget(self._report_box)

        return w

    def _run_quality(self):
        if self._source_df is None:
            QMessageBox.warning(self, "Error", "Load a file first.")
            return
        try:
            from ai.anomaly_detector import QualityAnalyzer
            report = QualityAnalyzer().quality_report(self._source_df)
            self._quality_data = report

            out = self._report_box
            out.clear()
            out.append("=" * 50)
            out.append("DATA QUALITY REPORT")
            out.append("=" * 50)
            name = Path(self._source_path).name if self._source_path else "?"
            out.append(f"\nDataset: {name}")
            out.append(f"Rows: {report['total_rows']}  |  Columns: {report['total_columns']}")
            out.append(f"Duplicates: {report['duplicates']}")

            score = report["overall_quality_score"]
            rating = "EXCELLENT" if score >= 90 else "GOOD" if score >= 75 else "FAIR" if score >= 60 else "POOR"
            out.append(f"\nQuality Score: {score:.1f}/100  ({rating})")

            out.append("\n--- COMPLETENESS ---")
            for field, d in report["completeness"].items():
                pct = d["completeness_pct"]
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                out.append(f"  {field:25s} [{bar}] {pct:.0f}%  (nulls: {d['null_count']})")

            if report["statistics"]:
                out.append("\n--- NUMERIC STATS ---")
                for field, st in report["statistics"].items():
                    out.append(f"  {field}: mean={st['mean']:.1f}, std={st['std']:.1f}, "
                               f"range=[{st['min']:.1f}, {st['max']:.1f}]")

            self._status.showMessage("Quality analysis complete")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _run_anomalies(self):
        if self._source_df is None:
            QMessageBox.warning(self, "Error", "Load a file first.")
            return
        try:
            from ai.anomaly_detector import QualityAnalyzer
            results = QualityAnalyzer().detect_anomalies(self._source_df)
            self._anomaly_data = results

            out = self._report_box
            out.clear()
            out.append("=" * 50)
            out.append("ANOMALY DETECTION")
            out.append("=" * 50)
            out.append(f"\nRows analyzed: {results['total_rows']}")
            out.append(f"Anomalies found: {results['anomalies_found']}")

            rate = results["anomalies_found"] / max(results["total_rows"], 1) * 100
            out.append(f"Anomaly rate: {rate:.1f}%")

            if results.get("anomaly_indices"):
                out.append(f"\nAnomalous rows (first 20): {results['anomaly_indices'][:20]}")

            for col, det in results.get("column_anomalies", {}).items():
                out.append(f"\n  {col}: {det.get('anomaly_count', 0)} anomalies")
                if det.get("normal_mean") is not None:
                    out.append(f"    Normal range: {det['normal_min']:.1f}–{det['normal_max']:.1f}")

            self._status.showMessage(f"Found {results['anomalies_found']} anomalies")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_pdf(self):
        if not hasattr(self, "_quality_data"):
            QMessageBox.warning(self, "Error", "Run quality analysis first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", str(ROOT_DIR / "data" / "quality_report.pdf"), "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            from reporting.pdf_generator import generate_quality_pdf
            name = Path(self._source_path).name if self._source_path else "Unknown"
            data = dict(self._quality_data)
            if hasattr(self, "_anomaly_data"):
                data["anomalies"] = self._anomaly_data
            generate_quality_pdf(name, data, path)
            QMessageBox.information(self, "Done", f"PDF saved:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    # ======================================================================
    # Audit tab
    # ======================================================================

    def _tab_audit(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._heading("Audit Log"))

        btns = QHBoxLayout()
        btns.addWidget(self._btn("Refresh", self._refresh_audit))
        btns.addStretch()
        lay.addLayout(btns)

        self._audit_table = self._table(["Timestamp", "User", "Action", "Entity", "Details"])
        self._audit_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self._audit_table)

        self._refresh_audit()
        return w

    def _refresh_audit(self):
        try:
            with db_session() as s:
                logs = s.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
                self._audit_table.setRowCount(len(logs))
                for i, entry in enumerate(logs):
                    ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else ""
                    self._audit_table.setItem(i, 0, QTableWidgetItem(ts))
                    user = s.query(User).get(entry.user_id)
                    self._audit_table.setItem(i, 1, QTableWidgetItem(user.username if user else "?"))
                    self._audit_table.setItem(i, 2, QTableWidgetItem(entry.action or ""))
                    entity = f"{entry.entity_type or ''} #{entry.entity_id or ''}".strip()
                    self._audit_table.setItem(i, 3, QTableWidgetItem(entity))
                    self._audit_table.setItem(i, 4, QTableWidgetItem(str(entry.details or "")))
        except Exception as exc:
            log.error("Audit load failed: %s", exc)

    # ======================================================================
    # External imports (Google Drive, REST API)
    # ======================================================================

    def _import_gdrive(self):
        try:
            from api.google_drive import GoogleDriveClient
            client = GoogleDriveClient()
            if not client.authenticate():
                QMessageBox.warning(self, "Google Drive", "Authentication failed.")
                return

            files = client.list_files()
            if not files:
                QMessageBox.information(self, "Google Drive", "No data files found.")
                return

            names = [f"{f['name']} ({f.get('mimeType', '')})" for f in files]
            chosen, ok = QInputDialog.getItem(self, "Select File", "Import:", names, 0, False)
            if ok and chosen:
                idx = names.index(chosen)
                local = client.download(files[idx]["id"], str(ROOT_DIR / "data" / "imports"))
                if local:
                    self._load_from_path(local, "source")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _import_rest(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Import from REST API")
        dlg.setMinimumWidth(480)
        form = QFormLayout(dlg)

        url_in = QLineEdit()
        url_in.setPlaceholderText("https://api.example.com/data")
        form.addRow("URL:", url_in)

        token_in = QLineEdit()
        token_in.setPlaceholderText("Bearer token (optional)")
        form.addRow("Token:", token_in)

        path_in = QLineEdit()
        path_in.setPlaceholderText("e.g. data.results (optional)")
        form.addRow("Records path:", path_in)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        url = url_in.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "URL is required.")
            return
        try:
            from api.rest_client import RestClient
            client = RestClient(url, token=token_in.text().strip() or None)
            df = client.to_dataframe(records_path=path_in.text().strip() or None)
            if df is not None and len(df) > 0:
                self._source_df = df
                self._source_path = url
                self._src_label.setText(f"REST API ({len(df)} rows × {len(df.columns)} cols)")
                self._fill_table(self._src_table, df)
                self._status.showMessage(f"Imported {len(df)} rows")
            else:
                QMessageBox.warning(self, "Error", "No data returned.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _load_from_path(self, path: str, role: str):
        try:
            from ingestion import load_file
            df = load_file(path)
            if role == "source":
                self._source_df, self._source_path = df, path
                self._src_label.setText(f"{Path(path).name} ({len(df)} rows)")
                self._fill_table(self._src_table, df)
            else:
                self._target_df, self._target_path = df, path
                self._tgt_label.setText(f"{Path(path).name} ({len(df)} rows)")
                self._fill_table(self._tgt_table, df)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    # ======================================================================
    # Menu actions
    # ======================================================================

    def _logout(self):
        if QMessageBox.question(self, "Logout", "Log out?") == QMessageBox.StandardButton.Yes:
            current_session.logout()
            self.close()

    def _about(self):
        QMessageBox.about(self, f"About {APP_TITLE}", f"""
        <h2>{APP_TITLE}</h2>
        <p>Version {APP_VERSION}</p>
                <p>Data Translation Platform</p>
        <ul>
                    <li>Schema Mapping</li>
          <li>Multi-Format Ingestion</li>
          <li>Anomaly Detection</li>
          <li>PDF Reporting</li>
        </ul>
        """)

    # ======================================================================
    # Widget factories — reduce boilerplate in tab builders
    # ======================================================================

    @staticmethod
    def _heading(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        return lbl

    @staticmethod
    def _btn(text: str, slot, style_id: str = None) -> QPushButton:
        b = QPushButton(text)
        if style_id:
            b.setObjectName(style_id)
        b.clicked.connect(slot)
        return b

    @staticmethod
    def _table(headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        return t
