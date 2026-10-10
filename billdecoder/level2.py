"""Level 2: answer the customer questions for each bill.

All questions for a single bill are answered in one batched model call to keep
within the free-tier daily request limit. If the model call fails, a grounded
fallback answer is produced from the computed figures so no cell is ever empty.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from .calc import compute_facts
from .io_utils import parse_json, read_csv_rows
from .llm import LLMClient
from .prompts import build_qa_prompt
from .schema import empty_bill

logger = logging.getLogger(__name__)

LEVEL2_COLUMNS = ["bill_id", "question_id", "question", "answer"]


def _fmt(value, suffix: str = "") -> str:
    if value is None:
        return "not shown on the bill"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}{suffix}" if isinstance(value, (int, float)) else f"{value}{suffix}"


def fallback_answer(question: str, bill: dict, facts: dict) -> str:
    """A short, grounded answer used if the model response is unusable."""
    q = (question or "").lower()
    facts = facts or compute_facts(bill, [])

    if "tax" in q:
        return (
            f"Taxes and duties total PKR {_fmt(facts.get('total_taxes'))} out of a "
            f"current bill of PKR {_fmt(facts.get('current_bill'))}, about "
            f"{_fmt(facts.get('tax_share_percent'), '%')} of the bill."
        )
    if "unit" in q or "consum" in q or "used" in q:
        return (
            f"This bill is for {_fmt(facts.get('units_consumed'))} units, with an "
            f"effective cost of about PKR {_fmt(facts.get('effective_cost_per_unit'))} "
            "per unit."
        )
    if "due" in q or "pay" in q:
        return (
            f"The amount payable within the due date is PKR "
            f"{_fmt(facts.get('payable_within_due_date'))} and after the due date it is "
            f"PKR {_fmt(facts.get('payable_after_due_date'))}."
        )
    if "arrear" in q or "previous" in q:
        return f"Previous dues (arrears) on this bill are PKR {_fmt(facts.get('arrears'))}."
    if "average" in q and facts.get("history_average_units") is not None:
        return (
            f"The average of the {facts.get('history_months')} months of history is "
            f"{_fmt(facts.get('history_average_units'))} units per month."
        )
    return (
        "Based on the bill: units consumed "
        f"{_fmt(facts.get('units_consumed'))}, current bill PKR "
        f"{_fmt(facts.get('current_bill'))}, of which PKR "
        f"{_fmt(facts.get('total_charges'))} is charges and PKR "
        f"{_fmt(facts.get('total_taxes'))} is taxes."
    )


def answer_bill(
    client: LLMClient, bill: dict, history: list[dict], questions: list[dict]
) -> tuple[dict[str, str], dict]:
    """Answer all questions for one bill. Returns (answers_by_id, facts)."""
    facts = compute_facts(bill, history)
    answers: dict[str, str] = {}
    try:
        prompt = build_qa_prompt(bill, facts, questions)
        text = client.generate(prompt, json_mode=True, tag="qa")
        data = parse_json(text)
        for item in data.get("answers", []):
            qid = str(item.get("question_id", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if qid and answer:
                answers[qid] = answer
    except Exception as err:  # noqa: BLE001 - fall back to a grounded answer
        logger.warning("QA call failed, using fallback answers: %s", err)

    for question in questions:
        answers.setdefault(
            question["question_id"],
            fallback_answer(question.get("question", ""), bill, facts),
        )
    return answers, facts


def build_level2_rows(
    records: dict[str, dict], client: LLMClient, template_path: str | Path
) -> tuple[list[str], list[dict]]:
    """Return (fieldnames, rows) for output/level2.csv, preserving row order."""
    fieldnames, template_rows = read_csv_rows(template_path)

    questions_by_bill: dict[str, list[dict]] = defaultdict(list)
    for row in template_rows:
        questions_by_bill[(row.get("bill_id") or "").strip()].append(
            {
                "question_id": (row.get("question_id") or "").strip(),
                "question": row.get("question") or "",
            }
        )

    answers_by_bill: dict[str, dict[str, str]] = {}
    for bill_id, questions in questions_by_bill.items():
        record = records.get(bill_id)
        if not record:
            logger.warning("no extracted record for %s; using empty bill", bill_id)
            bill, history = empty_bill(), []
        else:
            bill, history = record["bill"], record["history"]
        answers, _ = answer_bill(client, bill, history, questions)
        answers_by_bill[bill_id] = answers

    rows = []
    for row in template_rows:
        bill_id = (row.get("bill_id") or "").strip()
        question_id = (row.get("question_id") or "").strip()
        rows.append(
            {
                "bill_id": bill_id,
                "question_id": question_id,
                "question": row.get("question") or "",
                "answer": answers_by_bill.get(bill_id, {}).get(question_id, ""),
            }
        )
    return (fieldnames or LEVEL2_COLUMNS), rows
