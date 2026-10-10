"""Unit tests for the consistency validator."""
from __future__ import annotations

from billdecoder.validate import validate_bill


def test_no_warnings_for_consistent_bill():
    bill = {
        "charges": [{"type": "energy", "amount": 100}, {"type": "fixed", "amount": 50}],
        "total_charges": 150,
        "taxes": [{"type": "gst", "amount": 30}],
        "total_taxes": 30,
        "current_bill": 180,
        "previous_reading": 1000,
        "current_reading": 1100,
        "units_consumed": 100,
    }
    assert validate_bill(bill) == []


def test_missing_charges_subtotal_is_flagged():
    bill = {
        "charges": [{"type": "energy", "amount": 100}, {"type": "fixed", "amount": 50}],
        "total_charges": 170,  # should be 150
        "current_bill": 200,
    }
    warnings = validate_bill(bill)
    assert any("total_charges" in w for w in warnings)


def test_combined_tax_with_empty_list_is_allowed():
    bill = {
        "taxes": [],
        "total_taxes": 3358.23,
        "current_bill": 20726,
    }
    assert validate_bill(bill) == []


def test_bad_units_reading_check():
    bill = {
        "previous_reading": 1000,
        "current_reading": 1100,
        "units_consumed": 150,  # should be 100
    }
    warnings = validate_bill(bill)
    assert any("units_consumed" in w for w in warnings)