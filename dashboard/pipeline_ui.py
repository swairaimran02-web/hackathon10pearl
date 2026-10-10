"""Thin glue between the dashboard and the billdecoder backend.

This module does NOT re-implement extraction or CSV building — it only calls
the existing billdecoder functions and writes the official output files, so the
dashboard produces exactly the same CSVs as the CLI (run.py).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from billdecoder.extract import extract_bill
from billdecoder.io_utils import write_csv
from billdecoder.level1 import build_level1_rows
from billdecoder.level2 import build_level2_rows

LogFn = Callable[[str, str], None]  # (level: str, message: str) -> None


def _short(value) -> str:
    return "" if value is None else str(value)


def process_paths(client, paths, log: LogFn | None = None, progress=None) -> tuple[dict, list[dict]]:
    """Extract every bill image. Returns (records, failures).

    * records : bill_id -> full extraction record (bill, history, warnings, …)
    * failures: list of {bill_id, error} — extraction never crashes the loop.
    """
    records: dict[str, dict] = {}
    failures: list[dict] = []
    paths = list(paths)
    total = max(len(paths), 1)
    for index, path in enumerate(paths, start=1):
        path = Path(path)
        try:
            if log:
                log("info", f"Extracting {path.name} …")
            rec = extract_bill(client, path)
            records[rec["bill_id"]] = rec
            bill = rec["bill"]
            warnings = rec.get("warnings") or []
            summary = (
                f"{path.name} → {_short(bill.get('provider'))} · "
                f"{_short(bill.get('bill_month'))} · "
                f"{_short(bill.get('units_consumed'))} units · "
                f"current bill {_short(bill.get('current_bill'))}"
            )
            if warnings:
                log("warn", f"{summary} ({len(warnings)} advisory warning{'s' if len(warnings) != 1 else ''})")
            else:
                log("ok", summary)
        except Exception as err:  # noqa: BLE001 - keep processing other bills
            failures.append({"bill_id": path.stem, "error": str(err)})
            if log:
                log("err", f"{path.name} → FAILED: {err}")
        if progress:
            progress(index / total, text=f"Extracting bills… {index}/{len(paths)}")
    return records, failures


def write_artefacts(records: dict[str, dict], output_dir: Path) -> None:
    """Persist records so the dashboard can reload them on the next run."""
    artefacts = {
        bill_id: {
            "bill": record["bill"],
            "history": record.get("history", []),
            "warnings": record.get("warnings", []),
            "raw": record.get("raw", {}),
            "source": record.get("source"),
        }
        for bill_id, record in records.items()
        if record.get("bill")
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "extraction_raw.json").write_text(
        json.dumps(artefacts, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_outputs(
    records: dict[str, dict],
    client,
    level1_tpl: str | Path | None,
    level2_tpl: str | Path | None,
    output_dir: str | Path,
    log: LogFn | None = None,
) -> dict:
    """Write output files from real extraction records.

    * level1.csv is always written when there is at least one good bill.
    * level2.csv is written only when a Level 2 template CSV is provided
      (questions come from the official template, exactly like the CLI).
    Returns a dict of counts: level1_rows, level2_rows, answered.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = {bid: rec for bid, rec in records.items() if rec.get("bill")}
    result = {"level1_rows": 0, "level2_rows": 0, "answered": 0}

    if not valid:
        if log:
            log("err", "No successfully extracted bills — nothing written.")
        return result

    # Level 1 — the official bill_id + json format (row order follows template).
    fieldnames1, rows1 = build_level1_rows(valid, level1_tpl)
    write_csv(output_dir / "level1.csv", fieldnames1, rows1)
    write_artefacts(valid, output_dir)
    result["level1_rows"] = len(rows1)
    if log:
        log("ok", f"Wrote level1.csv ({len(rows1)} rows) → {output_dir / 'level1.csv'}")

    # Level 2 — batched answers, grounded fallbacks, template row order.
    if level2_tpl and Path(level2_tpl).exists():
        fieldnames2, rows2 = build_level2_rows(valid, client, level2_tpl)
        write_csv(output_dir / "level2.csv", fieldnames2, rows2)
        result["level2_rows"] = len(rows2)
        result["answered"] = sum(1 for r in rows2 if (r.get("answer") or "").strip())
        if log:
            log("ok", f"Wrote level2.csv ({len(rows2)} rows, {result['answered']} answered)")
    elif log:
        log("warn", "No Level 2 template provided — skipped Level 2 answers.")

    return result