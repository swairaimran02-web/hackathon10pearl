"""End-to-end CLI for the WTQ Utility Bill Decoder.

Usage:
    python run.py --bills test/bills --out output/ \
        --level1-template test/csv/level1.csv \
        --level2-template test/csv/level2.csv

It extracts every bill image once, writes output/level1.csv, then answers the
questions from the level2 template into output/level2.csv.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from billdecoder.config import Settings
from billdecoder.extract import extract_bill
from billdecoder.io_utils import dump_json, write_csv
from billdecoder.level1 import build_level1_rows
from billdecoder.level2 import build_level2_rows
from billdecoder.llm import LLMClient
from billdecoder.preprocess import list_bill_images

logger = logging.getLogger("billdecoder")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WTQ 2026 Utility Bill Decoder")
    parser.add_argument("--bills", required=True, help="folder containing bill images")
    parser.add_argument("--out", default="output", help="output folder (default: output)")
    parser.add_argument(
        "--level1-template",
        default=None,
        help="optional level1.csv template to preserve row order",
    )
    parser.add_argument(
        "--level2-template",
        default=None,
        help="optional level2.csv template with the questions",
    )
    parser.add_argument(
        "--no-questions",
        action="store_true",
        help="only produce level1.csv (skip Level 2 answers)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="process only the first N bills (for quick testing)",
    )
    parser.add_argument("--verbose", action="store_true", help="verbose logging")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    settings = Settings.from_env()
    settings.validate()
    logger.info("using provider=%s model=%s", settings.provider, settings.model)
    client = LLMClient(settings)

    images = list_bill_images(args.bills)
    if args.limit:
        images = images[: args.limit]
    if not images:
        print(f"No bill images found in {args.bills}", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: dict[str, dict] = {}
    total = len(images)
    for index, image_path in enumerate(images, start=1):
        bill_id = image_path.stem
        try:
            record = extract_bill(client, image_path)
        except Exception as err:  # noqa: BLE001 - keep going on a single bad bill
            logger.error("failed to extract %s: %s", bill_id, err)
            record = {"bill_id": bill_id, "bill": None, "history": [], "raw": {}}
        if record.get("bill"):
            records[bill_id] = record
            print(
                f"[{index}/{total}] {bill_id}: provider={record['bill']['provider']} "
                f"units={record['bill']['units_consumed']} "
                f"bill={record['bill']['current_bill']}"
            )
        else:
            print(f"[{index}/{total}] {bill_id}: extraction failed")

    # ---- Level 1 ---------------------------------------------------------
    fieldnames, rows = build_level1_rows(records, args.level1_template)
    write_csv(out_dir / "level1.csv", fieldnames, rows)
    print(f"wrote {out_dir / 'level1.csv'} ({len(rows)} rows)")

    # ---- Level 2 ---------------------------------------------------------
    if not args.no_questions:
        template = args.level2_template
        if template and Path(template).exists():
            q_fields, q_rows = build_level2_rows(records, client, template)
            write_csv(out_dir / "level2.csv", q_fields, q_rows)
            print(f"wrote {out_dir / 'level2.csv'} ({len(q_rows)} rows)")
        else:
            print("No level2 template supplied; skipping Level 2.")

    # ---- Debug artefacts -------------------------------------------------
    artefacts = {
        bill_id: {"history": rec["history"], "raw": rec.get("raw", {})}
        for bill_id, rec in records.items()
    }
    (out_dir / "extraction_raw.json").write_text(
        json.dumps(artefacts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
