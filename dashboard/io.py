"""Frontend-only file helpers: temp uploads, generated artefacts and CSVs.

Nothing here touches the core extraction logic — it only reads/writes files so
the dashboard can display real data and offer real downloads.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd


def uploaded_to_temp(uploaded, name: str = "") -> Path:
    """Persist an uploaded Streamlit file to a temp path and return it.

    The returned file is deleted by the OS when the session ends, so nothing
    user-uploaded ever lands in the output/ or source/ folders.
    """
    suffix = Path(uploaded.name or name or "file").suffix
    target = Path(tempfile.gettempdir()) / f"wtq_upload_{datetime.now():%Y%m%d%H%M%S%f}{suffix}"
    target.write_bytes(uploaded.getvalue())
    return target


def load_records_from_artefacts(path: str | Path) -> dict:
    """Load previously extracted records from output/extraction_raw.json."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    records = {}
    for bill_id, item in data.items():
        if not isinstance(item, dict) or not item.get("bill"):
            continue
        records[bill_id] = {
            "bill": item.get("bill", {}),
            "history": item.get("history", []),
            "warnings": item.get("warnings", []),
            "raw": item.get("raw", {}),
            "source": item.get("source"),
        }
    return records


def load_level2_df(path: str | Path) -> pd.DataFrame | None:
    """Return output/level2.csv as a DataFrame, or None when missing/empty."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except (pd.errors.ParserError, OSError, ValueError):
        return None
    if df.empty:
        return None
    return df


def file_info(path: str | Path) -> dict:
    """Size (human readable) and last-modified string for a generated file."""
    path = Path(path)
    if not path.exists():
        return {"exists": False, "size": "0 B", "modified": "—"}
    size = path.stat().st_size
    if size >= 1_000_000:
        size_txt = f"{size / 1_000_000:.2f} MB"
    elif size >= 1_000:
        size_txt = f"{size / 1_000:.1f} KB"
    else:
        size_txt = f"{size} B"
    modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return {"exists": True, "size": size_txt, "modified": modified}