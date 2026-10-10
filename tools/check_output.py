"""Validate the generated CSVs before submission.

Checks, per section 7 of the guide:
  * level1.csv: columns, one JSON per row, valid JSON, no empty cells.
  * level2.csv: columns, no empty answers; bill_id/question_id match the template.

Exits non-zero if anything is wrong.

Usage:
    python tools/check_output.py --output output \
        --level1-template test/csv/level1.csv \
        --level2-template test/csv/level2.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from billdecoder.io_utils import read_csv_rows

LEVEL1_EXPECTED = {"bill_id", "json"}
LEVEL2_EXPECTED = {"bill_id", "question_id", "question", "answer"}


def check_level1(path: Path) -> list[str]:
    problems: list[str] = []
    fields, rows = read_csv_rows(path)
    if not {"bill_id", "json"} <= set(fields):
        problems.append(f"level1 columns are {fields}, expected bill_id,json")
    for index, row in enumerate(rows, start=2):
        bill_id = (row.get("bill_id") or "").strip()
        raw = (row.get("json") or "").strip()
        if not bill_id:
            problems.append(f"level1 row {index}: empty bill_id")
        if not raw:
            problems.append(f"level1 row {index} ({bill_id}): empty json cell")
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            problems.append(f"level1 row {index} ({bill_id}): invalid JSON ({err})")
            continue
        for key in ("provider", "tariff", "bill_month", "charges", "current_bill"):
            if key not in data:
                problems.append(f"level1 row {index} ({bill_id}): missing {key!r}")
    if not problems:
        print(f"output/{path.name}: OK - {len(rows)} rows, all JSON valid")
    return problems


def check_level2(path: Path, template: Path | None) -> list[str]:
    problems: list[str] = []
    fields, rows = read_csv_rows(path)
    if not LEVEL2_EXPECTED <= set(fields):
        problems.append(
            f"level2 columns are {fields}, expected bill_id,question_id,question,answer"
        )
    expected_ids = None
    if template and template.exists():
        _, tpl = read_csv_rows(template)
        expected_ids = {(r.get("bill_id"), r.get("question_id")) for r in tpl}
        if len(expected_ids) != len(tpl):
            problems.append("level2 template has duplicate bill_id/question_id rows")
    seen: set = set()
    for index, row in enumerate(rows, start=2):
        key = (row.get("bill_id"), row.get("question_id"))
        if key[0] is None or key[0] == "":
            problems.append(f"level2 row {index}: empty bill_id")
        answer = (row.get("answer") or "").strip()
        if not answer:
            problems.append(f"level2 row {index} ({key}): empty answer")
        if key in seen:
            problems.append(f"level2 row {index} ({key}): duplicate")
        seen.add(key)
    if expected_ids is not None:
        actual_ids = {(r.get("bill_id"), r.get("question_id")) for r in rows}
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        if missing:
            problems.append(f"level2 missing template rows: {sorted(missing)[:5]} ...")
        if extra:
            problems.append(f"level2 has extra rows: {sorted(extra)[:5]} ...")
    if not problems:
        print(f"output/{path.name}: OK - {len(rows)} rows, no empty answers")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated CSVs")
    parser.add_argument("--output", default="output")
    parser.add_argument("--level1-template", default=None)
    parser.add_argument("--level2-template", default=None)
    args = parser.parse_args(argv)

    out = Path(args.output)
    problems: list[str] = []
    level1 = out / "level1.csv"
    level2 = out / "level2.csv"
    if level1.exists():
        problems += check_level1(level1)
    else:
        problems.append(f"{level1} missing")
    if level2.exists():
        problems += check_level2(level2, Path(args.level2_template) if args.level2_template else None)
    else:
        print(f"output/level2.csv - not present (Level 2 skipped)")

    if problems:
        print("\nPROBLEMS FOUND:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())