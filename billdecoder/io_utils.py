"""Small I/O helpers: JSON parsing, CSV read/write with stable column order."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def parse_json(text: str) -> dict:
    """Parse JSON from a model response, tolerating markdown code fences."""
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


def read_csv_rows(path: str | Path) -> tuple[list[str], list[dict]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, list(reader)


def write_csv(path: str | Path, fieldnames: list[str], rows: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # csv module doubles quotation marks inside quoted cells (section 7.2).
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def dump_json(obj) -> str:
    """Compact single-line JSON for the level1.csv json column."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
