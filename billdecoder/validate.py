"""Deterministic sanity checks over an extracted bill.

These checks are warnings only. The guide says values must be extracted "as
printed" and never recalculated, so warnings are surfaced for a human (or a
second model pass) to adjudicate - they never overwrite printed values.
"""
from __future__ import annotations


def _round2(value):
    return round(float(value), 2) if value is not None else None


def validate_bill(bill: dict) -> list[str]:
    """Return a list of human-readable consistency warnings for a bill."""
    warnings: list[str] = []

    charges = bill.get("charges") or []
    taxes = bill.get("taxes") or []
    total_charges = bill.get("total_charges")
    total_taxes = bill.get("total_taxes")
    current_bill = bill.get("current_bill")

    if charges and total_charges is not None:
        total = _round2(sum(item["amount"] for item in charges))
        if abs(total - total_charges) > 1.01:
            warnings.append(
                f"total_charges ({total_charges}) != sum of charge lines ({total})"
            )

    # A combined tax amount is allowed with an empty taxes list (guide 5.3).
    if taxes and total_taxes is not None:
        total = _round2(sum(item["amount"] for item in taxes))
        if abs(total - total_taxes) > 1.01:
            warnings.append(
                f"total_taxes ({total_taxes}) != sum of tax lines ({total})"
            )

    if (
        current_bill is not None
        and total_charges is not None
        and total_taxes is not None
        and abs(current_bill - (total_charges + total_taxes)) > 1.01
    ):
        warnings.append(
            f"current_bill ({current_bill}) != total_charges + total_taxes "
            f"({_round2(total_charges + total_taxes)})"
        )

    prev = bill.get("previous_reading")
    curr = bill.get("current_reading")
    units = bill.get("units_consumed")
    if (
        prev is not None
        and curr is not None
        and units is not None
        and abs((curr - prev) - units) > 1.01
    ):
        warnings.append(
            f"units_consumed ({units}) != current - previous reading ({curr - prev})"
        )

    return warnings