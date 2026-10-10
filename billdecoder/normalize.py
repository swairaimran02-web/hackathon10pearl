"""Normalise raw model output into the exact Level 1 schema.

Handles currency labels, commas, credit suffixes, parentheses and the required
date formats. Values that cannot be read are returned as ``None`` (null).
"""
from __future__ import annotations

import re
from datetime import date, datetime

from dateutil import parser as date_parser

from .schema import CHARGE_TYPES, TAX_TYPES, empty_bill

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_PROVIDER_MAP = {
    "ke": "KE",
    "kesc": "KE",
    "k-electric": "KE",
    "k electric": "KE",
    "k-electric (kesc)": "KE",
    "lesco": "LESCO",
    "iesco": "IESCO",
}


def _clean_number(value: float):
    return int(value) if float(value).is_integer() else float(value)


def parse_number(value) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return _clean_number(value)
    text = str(value).strip()
    if not text:
        return None
    low = text.lower()
    negative = (
        "cr" in low.replace(" ", "")[-3:]
        or "credit" in low
        or (text.startswith("(") and text.endswith(")"))
        or text.lstrip().startswith("-")
    )
    text = text.replace(",", "")
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    number = float(match.group(0))
    if negative:
        number = -abs(number)
    return _clean_number(number)


def parse_date(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)
    try:
        return date_parser.parse(text, fuzzy=True, dayfirst=False).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def parse_month(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return text
    try:
        return date_parser.parse(text, fuzzy=True, dayfirst=False).strftime("%Y-%m")
    except (ValueError, OverflowError, TypeError):
        return None


def _normalise_provider(value) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower()
    if key in _PROVIDER_MAP:
        return _PROVIDER_MAP[key]
    for needle, provider in _PROVIDER_MAP.items():
        if needle and needle in key:
            return provider
    upper = str(value).strip().upper()
    return upper if upper in {"KE", "LESCO", "IESCO"} else None


def _normalise_items(items, allowed: list[str], default: str, subsidy: bool):
    if items is None:
        return []
    # Accept a dict of {type: amount} as well as a list of {type, amount}.
    if isinstance(items, dict):
        items = [{"type": k, "amount": v} for k, v in items.items()]
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        amount = parse_number(item.get("amount"))
        if amount is None:
            continue
        entry_type = str(item.get("type") or default).strip().lower().replace(" ", "_")
        if entry_type not in allowed:
            entry_type = default
        if subsidy and entry_type == "subsidy":
            amount = -abs(amount)
        # Section 5.3: skip lines printed as 0.
        if amount == 0:
            continue
        result.append({"type": entry_type, "amount": amount})
    return result


def normalize_bill(raw: dict | None) -> dict:
    raw = raw or {}
    bill = empty_bill()
    bill["provider"] = _normalise_provider(raw.get("provider"))
    tariff = raw.get("tariff")
    bill["tariff"] = str(tariff).strip() if tariff not in (None, "") else None
    bill["sanctioned_load_kw"] = parse_number(raw.get("sanctioned_load_kw"))
    bill["bill_month"] = parse_month(raw.get("bill_month"))
    for key in ("reading_date", "issue_date", "due_date"):
        bill[key] = parse_date(raw.get(key))
    for key in (
        "previous_reading",
        "current_reading",
        "units_consumed",
        "total_charges",
        "total_taxes",
        "current_bill",
        "arrears",
        "payable_within_due_date",
        "payable_after_due_date",
    ):
        bill[key] = parse_number(raw.get(key))
    bill["charges"] = _normalise_items(
        raw.get("charges"), CHARGE_TYPES, "other", subsidy=True
    )
    bill["taxes"] = _normalise_items(
        raw.get("taxes"), TAX_TYPES, "other_tax", subsidy=False
    )
    return bill


def normalize_history(raw) -> list[dict]:
    if not raw:
        return []
    history = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        month = parse_month(entry.get("month"))
        units = parse_number(entry.get("units"))
        if month and units is not None:
            history.append({"month": month, "units": units})
    return history
