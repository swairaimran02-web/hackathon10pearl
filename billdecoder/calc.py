"""Deterministic calculations over an extracted bill.

The guide recommends using code for arithmetic, so all averages, differences,
counts, percentages and estimates are computed here rather than by the LLM.
"""
from __future__ import annotations


def _round(value, digits: int = 2):
    return None if value is None else round(value, digits)


def _pct(part, whole):
    if part is None or whole in (None, 0):
        return None
    return round(100.0 * part / whole, 2)


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def compute_facts(bill: dict, history: list[dict] | None = None) -> dict:
    """Return a dictionary of derived figures used to ground the answers."""
    charges = bill.get("charges") or []
    taxes = bill.get("taxes") or []
    history = history or []

    total_charges = bill.get("total_charges")
    if total_charges is None and charges:
        total_charges = round(sum(c["amount"] for c in charges), 2)
    total_taxes = bill.get("total_taxes")
    if total_taxes is None and taxes:
        total_taxes = round(sum(t["amount"] for t in taxes), 2)

    current_bill = bill.get("current_bill")
    units = bill.get("units_consumed")
    history_units = [h["units"] for h in history]

    return {
        "units_consumed": units,
        "total_charges": total_charges,
        "total_taxes": total_taxes,
        "current_bill": current_bill,
        "arrears": bill.get("arrears"),
        "payable_within_due_date": bill.get("payable_within_due_date"),
        "payable_after_due_date": bill.get("payable_after_due_date"),
        "charges_share_percent": _pct(total_charges, current_bill),
        "tax_share_percent": _pct(total_taxes, current_bill),
        "effective_cost_per_unit": (
            round(current_bill / units, 2) if current_bill and units else None
        ),
        "charge_lines": charges,
        "tax_lines": taxes,
        "monthly_history": history,
        "history_months": len(history),
        "history_total_units": sum(history_units) if history_units else None,
        "history_average_units": _average(history_units),
        "history_max_units": max(history_units) if history_units else None,
        "history_min_units": min(history_units) if history_units else None,
    }


def count_above(values: list[float], threshold: float) -> int:
    return sum(1 for v in values if v > threshold)
