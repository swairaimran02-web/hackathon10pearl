"""Prompt templates for extraction (Level 1) and question answering (Level 2).

These prompts encode the rules from sections 5 and 6 of the participant guide.
They are kept in one module so they can be reviewed and versioned easily.
"""
from __future__ import annotations

import json

# Bump this when a prompt changes so cached outputs are invalidated.
PROMPT_VERSION = "v1"

EXTRACTION_PROMPT = """\
You are an expert at reading Pakistani electricity bills issued by K-Electric \
(shown as KESC in file names), LESCO and IESCO. The image may be a scan, a photo \
or a screenshot. It may be tilted and may contain Urdu text. Personal identifiers \
(names, addresses, CNIC, account, consumer, meter and reference numbers) are \
covered with grey boxes.

Read the attached bill image and return ONE JSON object with the billing details.

GENERAL RULES
- Extract values exactly as printed. Do NOT recalculate, round or correct them.
- Amounts are numbers in PKR: remove "Rs.", "PKR" and commas ("Rs. 19,964" -> 19964).
- Credits and subsidies are negative ("38209CR" -> -38209). A subsidy is a deduction.
- Dates must use YYYY-MM-DD (for example "22nd Sep 2026" -> "2026-09-22").
- The billing month must use YYYY-MM ("MAR 2026" -> "2026-03").
- Use null for any value that is not printed, blank, covered by a grey box or \
unreadable. A correct null is better than a guess. Do not invent values.
- Never return personal identifiers (names, addresses, CNIC, account, consumer, \
meter or reference numbers). If such a value appears, omit it and use null where a \
field would otherwise hold it.
- Output numbers as JSON numbers, not quoted strings.

FIELD DEFINITIONS
- provider: one of "KE", "LESCO" or "IESCO". K-Electric / KESC maps to "KE".
- tariff: the tariff code exactly as printed, e.g. "A1-R" or "A-1a(01)".
- sanctioned_load_kw: sanctioned load in kW (labels: Sanc Load, S.Load, San Load).
- bill_month: the billing month, YYYY-MM.
- reading_date, issue_date, due_date: printed dates, YYYY-MM-DD. due_date is the \
last date to pay without a late-payment surcharge.
- previous_reading, current_reading: the printed meter readings.
- units_consumed: units billed for the current month, as printed.
- charges: one entry per line in the charges / electricity section. Skip blank \
lines and lines printed as 0. Keep separate entries when the same type appears \
more than once. Each entry is {"type": <one charge type>, "amount": <number>}.
- total_charges: the printed charges subtotal, or null if none is printed.
- taxes: one entry per line in the tax / government section. Classify a line by \
its section, not its name. Each entry is {"type": <one tax type>, "amount": <number>}.
- total_taxes: the printed tax subtotal, or null if none is printed. If only a \
combined tax amount is printed, return an empty taxes list and put the amount here.
- current_bill: the printed amount for this month's bill.
- arrears: previous dues carried forward, keeping the printed sign; null if blank.
- payable_within_due_date: the amount payable by the due date.
- payable_after_due_date: the amount payable after the due date. If several \
late-payment amounts are shown, use the highest.

CHARGE TYPES (choose one per charge entry; the printed section decides charges vs taxes)
- energy: cost of units used (e.g. "Variable Upto ... Units", "Cost of Electricity", "Energy Charges").
- fixed: fixed charges.
- fpa: fuel price adjustment. Use fpa for both FPA and FCA.
- quarterly_adjustment: quarterly tariff adjustment (QTA, Uniform Quarterly Adjustment).
- surcharge: surcharges such as Additional Surcharge (PHL) or F.C Surcharge.
- meter_rent: meter rent or service rent.
- subsidy: government subsidy or relief lines (amount negative).
- other: any other charge line.

TAX TYPES (choose one per tax entry)
- gst: sales tax / GST, including GST on FPA.
- electricity_duty: electricity duty (often labelled ED).
- income_tax: income tax.
- municipal_tax: municipal / local charges under taxes (e.g. KE MUCT / KMC).
- other_tax: any other tax line (extra tax, further tax, TV fee, ...).

ALSO EXTRACT (for later questions)
- monthly_history: the consumption history table if the bill prints one, as a list \
of {"month": "YYYY-MM", "units": <number>} oldest first. Empty list if none.

Return ONLY the JSON object, with exactly these keys:
{
  "provider": "KE | LESCO | IESCO",
  "tariff": "string or null",
  "sanctioned_load_kw": number or null,
  "bill_month": "YYYY-MM or null",
  "reading_date": "YYYY-MM-DD or null",
  "issue_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "previous_reading": number or null,
  "current_reading": number or null,
  "units_consumed": number or null,
  "charges": [{"type": "...", "amount": number}],
  "total_charges": number or null,
  "taxes": [{"type": "...", "amount": number}],
  "total_taxes": number or null,
  "current_bill": number or null,
  "arrears": number or null,
  "payable_within_due_date": number or null,
  "payable_after_due_date": number or null,
  "monthly_history": [{"month": "YYYY-MM", "units": number}]
}
"""


QA_SYSTEM = (
    "You explain a customer's electricity bill in plain English. Use ONLY the bill "
    "data and computed figures provided. Never use outside tariff or rate "
    "information and never invent numbers. Label any estimate clearly and show how "
    "you calculated it. If the bill does not show a needed value, say so instead of "
    "guessing. Exclude personal identifiers. Always answer in English, even when "
    "part of the bill is in Urdu."
)


def build_qa_prompt(bill: dict, facts: dict, questions: list[dict]) -> str:
    """Build the Level 2 prompt: one batched call per bill for all questions."""
    return (
        f"{QA_SYSTEM}\n\n"
        "BILL DATA (Level 1 JSON):\n"
        f"{json.dumps(bill, ensure_ascii=False)}\n\n"
        "COMPUTED FIGURES (already calculated from the bill, use these numbers):\n"
        f"{json.dumps(facts, ensure_ascii=False)}\n\n"
        "QUESTIONS:\n"
        f"{json.dumps(questions, ensure_ascii=False)}\n\n"
        "Answer every question. Keep each answer specific and grounded in the bill, "
        "quote the relevant amounts, and state percentages to one decimal place. "
        'Return ONLY JSON of the form {"answers": [{"question_id": "...", '
        '"answer": "..."}]} with one entry per question and answer in English.'
    )
