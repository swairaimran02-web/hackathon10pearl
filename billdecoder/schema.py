"""The Level 1 target schema and its controlled vocabularies.

See sections 5.1-5.4 of the participant guide. Numeric fields are numbers, not
quoted strings, and every required field must be present even when it is null.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

CHARGE_TYPES = [
    "energy",
    "fixed",
    "fpa",
    "quarterly_adjustment",
    "surcharge",
    "meter_rent",
    "subsidy",
    "other",
]

TAX_TYPES = [
    "gst",
    "electricity_duty",
    "income_tax",
    "municipal_tax",
    "other_tax",
]

# Order matters: it is the order used in the JSON output.
LEVEL1_FIELDS = [
    "provider",
    "tariff",
    "sanctioned_load_kw",
    "bill_month",
    "reading_date",
    "issue_date",
    "due_date",
    "previous_reading",
    "current_reading",
    "units_consumed",
    "charges",
    "total_charges",
    "taxes",
    "total_taxes",
    "current_bill",
    "arrears",
    "payable_within_due_date",
    "payable_after_due_date",
]


def empty_bill() -> dict:
    """Return a fully-populated Level 1 skeleton with nulls and empty lists."""
    bill: dict = {key: None for key in LEVEL1_FIELDS}
    bill["charges"] = []
    bill["taxes"] = []
    return bill


class LineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    amount: float | None = None


class Bill(BaseModel):
    """Validation model for a normalised Level 1 object."""

    model_config = ConfigDict(extra="ignore")

    provider: Optional[str] = None
    tariff: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    bill_month: Optional[str] = None
    reading_date: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    previous_reading: Optional[float] = None
    current_reading: Optional[float] = None
    units_consumed: Optional[float] = None
    charges: list[LineItem] = []
    total_charges: Optional[float] = None
    taxes: list[LineItem] = []
    total_taxes: Optional[float] = None
    current_bill: Optional[float] = None
    arrears: Optional[float] = None
    payable_within_due_date: Optional[float] = None
    payable_after_due_date: Optional[float] = None
