"""
File parsers for CSV, JSON, XML, and Excel.

Instead of the original one-class-per-format hierarchy (BaseParser → CSVParser,
JSONParser, …), this module uses a single `load_file()` function that picks the
right pandas reader based on extension.  The per-format classes still exist for
when callers need schema profiling, but they share a common mixin to
avoid repeating the column-profiling logic four times.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_file(path: str) -> pd.DataFrame:
    """Load a data file into a DataFrame.  Raises on unsupported formats."""
    p = Path(path)
    ext = p.suffix.lower()
    readers = {
        ".csv": _read_csv,
        ".json": _read_json,
        ".xml": _read_xml,
        ".xlsx": _read_excel,
        ".xls": _read_excel,
    }
    reader = readers.get(ext)
    if reader is None:
        raise ValueError(f"Unsupported file type: {ext}")
    df = reader(p)
    log.info("Loaded %s: %d rows × %d cols", p.name, len(df), len(df.columns))
    return df


def profile_columns(df: pd.DataFrame) -> list[dict]:
    """Quick column-level profile: dtype, nulls, uniques, sample values."""
    return [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "unique_count": int(df[col].nunique()),
            "samples": df[col].dropna().head(3).tolist(),
        }
        for col in df.columns
    ]


# ---------------------------------------------------------------------------
# Format-specific readers
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> pd.DataFrame:
    """Try common delimiters if the default comma fails."""
    for delim in [",", ";", "\t", "|"]:
        try:
            return pd.read_csv(path, delimiter=delim, low_memory=False)
        except Exception:
            continue
    raise ValueError(f"Could not parse CSV: {path}")


def _read_json(path: Path) -> pd.DataFrame:
    # pandas can handle most JSON shapes directly
    try:
        return pd.read_json(path)
    except ValueError:
        pass

    # Fall back to manual parsing for nested / wrapped JSON
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        return pd.DataFrame(raw)

    # Try common wrapper keys like {"data": [...]}
    for key in ("data", "records", "items", "results"):
        if key in raw and isinstance(raw[key], list):
            return pd.DataFrame(raw[key])

    return pd.DataFrame([raw])


def _read_xml(path: Path) -> pd.DataFrame:
    import xmltodict

    with open(path, encoding="utf-8") as f:
        tree = xmltodict.parse(f.read())

    records = _dig_for_list(tree)
    if not records:
        raise ValueError(f"No record array found in XML: {path}")
    return pd.DataFrame(records)


def _read_excel(path: Path) -> pd.DataFrame:
    engine = "openpyxl" if path.suffix == ".xlsx" else None
    return pd.read_excel(path, engine=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dig_for_list(d: dict) -> list | None:
    """Walk a nested dict looking for the first list of records."""
    for v in d.values():
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            found = _dig_for_list(v)
            if found:
                return found
    return None
