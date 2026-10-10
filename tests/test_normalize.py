"""Unit tests for normalization. These do not call any API."""
from __future__ import annotations

from billdecoder.calc import compute_facts, count_above
from billdecoder.normalize import (
    normalize_bill,
    normalize_history,
    parse_date,
    parse_month,
    parse_number,
)


def test_parse_number_handles_currency_and_commas():
    assert parse_number("Rs. 19,964") == 19964
    assert parse_number("PKR 2,860.62") == 2860.62
    assert parse_number(151) == 151


def test_parse_number_handles_credits():
    assert parse_number("38209CR") == -38209
    assert parse_number("(500)") == -500
    assert parse_number("-0.53") == -0.53


def test_parse_dates():
    assert parse_date("22nd Sep 2026") == "2026-09-22"
    assert parse_date("2026-04-03") == "2026-04-03"
    assert parse_date("") is None


def test_parse_month():
    assert parse_month("MAR 2026") == "2026-03"
    assert parse_month("2026-04") == "2026-04"


def test_normalize_bill_full_example():
    raw = {
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
    }
    bill = normalize_bill(raw)
    assert bill["provider"] == "KE"
    assert bill["charges"][0] == {"type": "fixed", "amount": 900}
    assert len(bill["charges"]) == 6
    assert bill["arrears"] == -0.53
    assert bill["current_bill"] == 3430.24


def test_normalize_matches_guide_example_json():
    """Round-trip the exact KESC_0008 answer from section 5.7 of the guide."""
    raw = {
        "provider": "KESC", "tariff": "A1-R", "sanctioned_load_kw": 3,
        "bill_month": "2026-04", "reading_date": "03-Apr-2026",
        "issue_date": "07-Apr-2026", "due_date": "21-Apr-2026",
        "previous_reading": 8819, "current_reading": 8970,
        "units_consumed": 151,
        "charges": [
            {"type": "fixed", "amount": 900}, {"type": "energy", "amount": 1054},
            {"type": "energy", "amount": 663.51},
            {"type": "quarterly_adjustment", "amount": 52.91},
            {"type": "fpa", "amount": 125.27}, {"type": "surcharge", "amount": 64.93},
        ],
        "total_charges": 2860.62,
        "taxes": [
            {"type": "electricity_duty", "amount": 29.41},
            {"type": "gst", "amount": 520.21}, {"type": "municipal_tax", "amount": 20},
        ],
        "total_taxes": 569.62, "current_bill": 3430.24, "arrears": "-0.53",
        "payable_within_due_date": 3430, "payable_after_due_date": 3716,
    }
    expected = {
        "provider": "KE", "tariff": "A1-R", "sanctioned_load_kw": 3,
        "bill_month": "2026-04", "reading_date": "2026-04-03",
        "issue_date": "2026-04-07", "due_date": "2026-04-21",
        "previous_reading": 8819, "current_reading": 8970, "units_consumed": 151,
        "charges": [
            {"type": "fixed", "amount": 900}, {"type": "energy", "amount": 1054},
            {"type": "energy", "amount": 663.51},
            {"type": "quarterly_adjustment", "amount": 52.91},
            {"type": "fpa", "amount": 125.27}, {"type": "surcharge", "amount": 64.93},
        ],
        "total_charges": 2860.62,
        "taxes": [
            {"type": "electricity_duty", "amount": 29.41},
            {"type": "gst", "amount": 520.21}, {"type": "municipal_tax", "amount": 20},
        ],
        "total_taxes": 569.62, "current_bill": 3430.24, "arrears": -0.53,
        "payable_within_due_date": 3430, "payable_after_due_date": 3716,
    }
    assert normalize_bill(raw) == expected


def test_subsidy_is_negative_and_zero_lines_dropped():
    bill = normalize_bill(
        {
            "charges": [
                {"type": "subsidy", "amount": 500},
                {"type": "other", "amount": 0},
            ]
        }
    )
    assert bill["charges"] == [{"type": "subsidy", "amount": -500}]


def test_normalize_history():
    history = normalize_history(
        [{"month": "July 2025", "units": 239}, {"month": "2025-08", "units": "203"}]
    )
    assert history == [
        {"month": "2025-07", "units": 239},
        {"month": "2025-08", "units": 203},
    ]


def test_compute_facts():
    bill = normalize_bill(
        {"current_bill": 3430.24, "total_charges": 2860.62, "total_taxes": 569.62,
         "units_consumed": 151}
    )
    facts = compute_facts(bill, [{"month": "2025-07", "units": 239},
                                 {"month": "2025-08", "units": 203}])
    assert facts["tax_share_percent"] == 16.61
    assert facts["history_max_units"] == 239
    assert count_above([239, 203, 151], 200) == 2
