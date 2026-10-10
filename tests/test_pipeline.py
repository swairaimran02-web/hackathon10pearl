"""Offline end-to-end pipeline test with a fake model client (no API key)."""
from __future__ import annotations

import json

from PIL import Image

from billdecoder.extract import extract_bill
from billdecoder.io_utils import read_csv_rows, write_csv
from billdecoder.level1 import build_level1_rows
from billdecoder.level2 import build_level2_rows

CANNED_EXTRACT = {
    "provider": "KESC",
    "tariff": "A1-R",
    "sanctioned_load_kw": 3,
    "bill_month": "2026-04",
    "reading_date": "03-Apr-2026",
    "issue_date": "07-Apr-2026",
    "due_date": "21-Apr-2026",
    "previous_reading": 8819,
    "current_reading": 8970,
    "units_consumed": 151,
    "charges": [
        {"type": "fixed", "amount": 900},
        {"type": "energy", "amount": 1054},
        {"type": "energy", "amount": 663.51},
        {"type": "quarterly_adjustment", "amount": 52.91},
        {"type": "fpa", "amount": 125.27},
        {"type": "surcharge", "amount": 64.93},
    ],
    "total_charges": 2860.62,
    "taxes": [
        {"type": "electricity_duty", "amount": 29.41},
        {"type": "gst", "amount": 520.21},
        {"type": "municipal_tax", "amount": 20},
    ],
    "total_taxes": 569.62,
    "current_bill": 3430.24,
    "arrears": "-0.53",
    "payable_within_due_date": 3430,
    "payable_after_due_date": 3716,
    "monthly_history": [{"month": "July 2025", "units": 239}],
}


class FakeClient:
    def generate(
        self, prompt, image_bytes=None, mime_type=None, json_mode=False, tag=""
    ):
        if tag.startswith("extract"):
            return json.dumps(CANNED_EXTRACT)
        if tag == "qa":
            return json.dumps(
                {
                    "answers": [
                        {"question_id": "Q1", "answer": "Taxes total PKR 569.62."},
                        {"question_id": "Q2", "answer": "151 units."},
                    ]
                }
            )
        return "{}"


def test_pipeline_end_to_end_offline(tmp_path):
    image = Image.new("RGB", (400, 600), "white")
    image_path = tmp_path / "KESC_0008.png"
    image.save(image_path)

    client = FakeClient()
    record = extract_bill(client, image_path)

    assert record["bill_id"] == "KESC_0008"
    assert record["bill"]["provider"] == "KE"
    assert record["history"] == [{"month": "2025-07", "units": 239}]

    # Level 1 CSV
    fieldnames, rows = build_level1_rows({"KESC_0008": record})
    assert fieldnames == ["bill_id", "json"]
    parsed = json.loads(rows[0]["json"])
    assert parsed["units_consumed"] == 151
    assert parsed["current_bill"] == 3430.24

    # Level 2 CSV from a template
    template = tmp_path / "level2.csv"
    template.write_text(
        "bill_id,question_id,question,answer\n"
        "KESC_0008,Q1,How much of my bill is taxes?,\n"
        "KESC_0008,Q2,How many units did I use?,\n",
        encoding="utf-8",
    )
    q_fields, q_rows = build_level2_rows({"KESC_0008": record}, client, template)
    assert q_fields == ["bill_id", "question_id", "question", "answer"]
    assert len(q_rows) == 2
    assert q_rows[0]["answer"] == "Taxes total PKR 569.62."
    assert q_rows[1]["answer"] == "151 units."

    # Round-trip through the CSV writer (quoting rules must survive)
    out = tmp_path / "out_level2.csv"
    write_csv(out, q_fields, q_rows)
    fields, reread = read_csv_rows(out)
    assert reread[0]["answer"] == "Taxes total PKR 569.62."