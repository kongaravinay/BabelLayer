"""
Chart generation for quality reports.

All charts are rendered to PNG files using matplotlib, suitable
for embedding in PDF reports or displaying in the GUI.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import logging

log = logging.getLogger(__name__)

# House style
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 11,
})

_CHART_DIR = Path("temp_charts")
_CHART_DIR.mkdir(exist_ok=True)


def completeness_chart(completeness: dict, out: str = "completeness.png") -> str:
    """Horizontal bar chart of per-field completeness percentages."""
    fields = list(completeness.keys())
    pcts = [completeness[f]["completeness_pct"] for f in fields]
    colors = ["#27ae60" if p >= 95 else "#f39c12" if p >= 80 else "#e74c3c" for p in pcts]

    fig, ax = plt.subplots()
    ax.barh(fields, pcts, color=colors, alpha=0.85)
    ax.set_xlabel("Completeness (%)")
    ax.set_xlim(0, 105)
    for i, p in enumerate(pcts):
        ax.text(p + 1, i, f"{p:.1f}%", va="center", fontsize=9)
    ax.set_title("Data Completeness by Field")
    plt.tight_layout()

    path = _CHART_DIR / out
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def anomaly_histogram(scores: list, out: str = "anomalies.png") -> str:
    """Histogram of anomaly scores with a mean line."""
    fig, ax = plt.subplots()
    ax.hist(scores, bins=50, color="#2980b9", alpha=0.7, edgecolor="white")
    mean = np.mean(scores)
    ax.axvline(mean, color="#e74c3c", ls="--", label=f"Mean: {mean:.3f}")
    ax.set_xlabel("Anomaly Score")
    ax.set_ylabel("Frequency")
    ax.set_title("Anomaly Score Distribution")
    ax.legend()
    plt.tight_layout()

    path = _CHART_DIR / out
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def dtype_pie(data_types: dict, out: str = "data_types.png") -> str:
    """Pie chart showing the distribution of column data types."""
    counts = {}
    for dtype in data_types.values():
        simple = str(dtype).split("[")[0]
        counts[simple] = counts.get(simple, 0) + 1

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(counts.values(), labels=counts.keys(), autopct="%1.0f%%", startangle=90)
    ax.set_title("Column Type Distribution")
    plt.tight_layout()

    path = _CHART_DIR / out
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)
