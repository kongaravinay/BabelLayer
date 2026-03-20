"""
Visual theme for the BabelLayer desktop app.

Centralizes all colors, fonts, and stylesheet definitions so the
UI code stays focused on layout and behavior.
"""

# -- Color palette (inspired by modern dark-accent UIs) --------------------
COLORS = {
    "bg":          "#f0f2f5",
    "surface":     "#ffffff",
    "primary":     "#3b82f6",
    "primary_hover": "#2563eb",
    "success":     "#10b981",
    "success_hover": "#059669",
    "danger":      "#ef4444",
    "danger_hover": "#dc2626",
    "warning":     "#f59e0b",
    "text":        "#1e293b",
    "text_muted":  "#64748b",
    "border":      "#e2e8f0",
    "header_bg":   "#1e293b",
    "header_fg":   "#ffffff",
    "stripe":      "#f8fafc",
    "highlight_green": "#d1fae5",
    "highlight_yellow": "#fef3c7",
    "highlight_red": "#fee2e2",
}

FONT_FAMILY = "Segoe UI, Arial, sans-serif"


def app_stylesheet() -> str:
    """Return the global QSS stylesheet for the application."""
    c = COLORS
    return f"""
        /* ---- Global ---- */
        QMainWindow {{
            background: {c['bg']};
            font-family: {FONT_FAMILY};
        }}

        /* ---- Header label ---- */
        #welcomeHeader {{
            font-size: 15px;
            font-weight: 600;
            color: {c['text']};
            padding: 12px 16px;
        }}

        /* ---- Tabs ---- */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            background: {c['surface']};
            border-radius: 6px;
        }}
        QTabBar::tab {{
            padding: 9px 22px;
            margin-right: 3px;
            background: {c['border']};
            border-radius: 6px 6px 0 0;
            color: {c['text_muted']};
        }}
        QTabBar::tab:selected {{
            background: {c['surface']};
            font-weight: bold;
            color: {c['text']};
        }}

        /* ---- Buttons ---- */
        QPushButton {{
            background: {c['primary']};
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 5px;
            font-weight: 600;
            font-size: 13px;
        }}
        QPushButton:hover {{ background: {c['primary_hover']}; }}

        QPushButton#success {{
            background: {c['success']};
        }}
        QPushButton#success:hover {{ background: {c['success_hover']}; }}

        QPushButton#danger {{
            background: {c['danger']};
        }}
        QPushButton#danger:hover {{ background: {c['danger_hover']}; }}

        /* ---- Group boxes ---- */
        QGroupBox {{
            font-weight: 600;
            border: 1px solid {c['border']};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 18px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }}

        /* ---- Tables ---- */
        QTableWidget {{
            gridline-color: {c['border']};
            alternate-background-color: {c['stripe']};
            selection-background-color: {c['primary']};
            selection-color: white;
        }}
        QHeaderView::section {{
            background: {c['header_bg']};
            color: {c['header_fg']};
            padding: 7px;
            border: none;
            font-weight: 600;
        }}

        /* ---- Inputs ---- */
        QLineEdit, QTextEdit {{
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 6px 10px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {c['primary']};
        }}
    """
