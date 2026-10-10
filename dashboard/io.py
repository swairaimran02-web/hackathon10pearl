"""Frontend-only file helpers: temp uploads, generated artefacts and CSVs.

Nothing here touches the core extraction logic — it only reads/writes files so
the dashboard can display real data and offer real downloads.
"""
from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

_SAFE_ID = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-")


def _safe_stem(name: str) -> str:
    """A filesystem/cache-safe bill id from the original file name."""
    stem = Path(name).stem.strip()
    stem = "".join(ch if ch in _SAFE_ID else "_" for ch in stem)
    stem = re.sub(r"_+", "_", stem).strip("_") or "bill"
    return stem[:64]  # keep ids short enough for cache keys and labels


def uploaded_to_temp(uploaded, name: str = "", folder: str | Path | None = None) -> Path:
    """Persist an uploaded Streamlit file to a temp path and return it.

    The temp file keeps the ORIGINAL file name (sanitised) so the extracted
    bill id matches the official templates (e.g. ``KESC_0006.png`` -> bill
    ``KESC_0006``) and cache tags stay stable — re-uploading a bill that was
    already processed is instant and free.

    The returned file lives in a session-scoped temp folder, never in
    output/ or source/.
    """
    original = Path(uploaded.name or name or "file").name
    stem = _safe_stem(original)
    suffix = Path(original).suffix.lower() or ".img"
    target_dir = Path(folder) if folder else Path(tempfile.gettempdir())
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{stem}{suffix}"
    # Only rename on a real collision (same name uploaded twice this session).
    if target.exists():
        target = target_dir / f"{stem}_{datetime.now():%H%M%S}{suffix}"
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