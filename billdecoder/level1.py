"""Level 1 CSV builder: one row per bill with its JSON object."""
from __future__ import annotations

from pathlib import Path

from .io_utils import dump_json, read_csv_rows

LEVEL1_COLUMNS = ["bill_id", "json"]


def build_level1_rows(
    records: dict[str, dict], template_path: str | Path | None = None
) -> tuple[list[str], list[dict]]:
    """Return (fieldnames, rows) for output/level1.csv.

    When a template is supplied its row order and bill_ids are preserved.
    """
    if template_path and Path(template_path).exists():
        fieldnames, template_rows = read_csv_rows(template_path)
        rows = []
        for row in template_rows:
            bill_id = (row.get("bill_id") or "").strip()
            record = records.get(bill_id)
            rows.append(
                {
                    "bill_id": bill_id,
                    "json": dump_json(record["bill"]) if record else "",
                }
            )
        return (fieldnames or LEVEL1_COLUMNS), rows

    rows = [
        {"bill_id": bill_id, "json": dump_json(record["bill"])}
        for bill_id, record in records.items()
    ]
    return LEVEL1_COLUMNS, rows
