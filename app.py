"""Utility Bill Decoder — WTQ 2026 competition dashboard.

A beginner-friendly Streamlit app that drives the existing ``billdecoder``
backend:

* **Upload Bills** — drag & drop bill images (or point at a folder), run real
  AI extraction, and generate the official ``output/level1.csv`` /
  ``output/level2.csv`` files with the exact competition format.
* **Bill Analysis** — browse every extracted bill: dates, meter readings,
  units, charges, taxes and the printed monthly history. Missing values are
  shown as "Not available", never invented.
* **Questions & Answers** — every supplied question with its answer, searchable,
  with unanswered questions clearly marked.
* **Generated Reports** — working download buttons for the actual CSV files.
* **Settings** — model configuration read from the root ``.env`` (the API key
  is never shown or logged).

This file contains ONLY orchestration + Streamlit UI. Extraction, normalisation,
validation and CSV building live in ``billdecoder/`` and are untouched.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from billdecoder.calc import compute_facts
from billdecoder.config import PROJECT_ROOT, Settings
from billdecoder.llm import LLMClient
from billdecoder.preprocess import list_bill_images

from dashboard import components as ui
from dashboard import io as ui_io
from dashboard import pipeline_ui
from dashboard import plots
from dashboard import state as app_state
from dashboard import styles

# ------------------------------------------------------------------ setup --
st.set_page_config(
    page_title="Utility Bill Decoder · WTQ 2026",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

styles.inject()          # navy sidebar + light background + cards
app_state.init()         # session_state defaults (records, log, output_dir…)

PAGES = [
    "Dashboard",
    "Upload Bills",
    "Bill Analysis",
    "Questions & Answers",
    "Generated Reports",
    "Settings",
]

# Human readable names for the charge / tax line types (schema.py vocabularies).
CHARGES_LABELS = {
    "energy": "Energy charges",
    "fixed": "Fixed charges",
    "fpa": "Fuel price adjustment",
    "quarterly_adjustment": "Quarterly adjustment",
    "surcharge": "Surcharge",
    "meter_rent": "Meter rent",
    "subsidy": "Subsidy (credit)",
    "other": "Other charges",
}
TAX_LABELS = {
    "gst": "GST",
    "electricity_duty": "Electricity duty",
    "income_tax": "Income tax",
    "municipal_tax": "Municipal tax",
    "other_tax": "Other taxes",
}


# ------------------------------------------------------------ shared state --
def _output_dir() -> Path:
    """The folder where generated CSVs are written (session-overridable)."""
    return Path(st.session_state.get("output_dir") or str(PROJECT_ROOT / "output"))


def _resolve_records() -> dict:
    """Records from this session, falling back to previously generated artefacts."""
    records = st.session_state.get("records") or {}
    if not records:
        loaded = ui_io.load_records_from_artefacts(_output_dir() / "extraction_raw.json")
        if loaded:
            st.session_state["records"] = loaded
        records = loaded
    return records


def _load_level2_df() -> pd.DataFrame | None:
    return ui_io.load_level2_df(_output_dir() / "level2.csv")


def _stats() -> dict:
    """Real, live statistics — never hardcoded."""
    records = _resolve_records()
    failures = st.session_state.get("failures") or []
    ok_count = sum(1 for rec in records.values() if rec.get("bill"))
    total = len(records) + len(failures)
    level2 = _load_level2_df()
    questions = int(len(level2)) if level2 is not None else 0
    if level2 is not None and questions:
        answered = int((level2["answer"].fillna("").astype(str).str.strip() != "").sum())
    else:
        answered = 0
    return {
        "total": total,
        "ok": ok_count,
        "failed": total - ok_count,
        "questions": questions,
        "answered": answered,
        "records": records,
        "failures": failures,
    }


def _template_path(uploaded, key_name: str) -> Path | None:
    """Persist an uploaded template CSV to a temp file (or return None)."""
    if uploaded is None:
        return None
    path = ui_io.uploaded_to_temp(uploaded, key_name)
    return path


def _run_processing(paths: list[Path], tpl1: Path | None, tpl2: Path | None) -> None:
    """Run real extraction + CSV generation, updating session state and logs."""
    try:
        settings = Settings.from_env()
        settings.validate()                       # allowed model + API key present
    except ValueError as err:
        st.error(f"❌ **Configuration error:** {err}")
        st.info(
            "Fix the root `.env` file (see `.env.example`), then click "
            "**Process bills** again — no need to restart the app."
        )
        return

    client = LLMClient(settings)
    progress = st.progress(0.0, text="Starting extraction…")
    records, failures = pipeline_ui.process_paths(
        client, paths, log=app_state.add_log, progress=progress
    )
    progress.empty()

    # Merge with anything already processed in this session.
    merged = dict(st.session_state.get("records") or {})
    merged.update(records)
    st.session_state["records"] = merged
    st.session_state["failures"] = failures

    result = pipeline_ui.build_outputs(
        merged, client, tpl1, tpl2, _output_dir(), log=app_state.add_log
    )

    if records:
        st.success(
            f"✅ Extracted **{len(records)}** bill(s) "
            f"({len(failures)} failed). "
            f"Level 1: **{result['level1_rows']}** row(s). "
            f"Level 2: **{result['level2_rows']}** row(s), "
            f"**{result['answered']}** answered."
        )
    elif failures:
        st.error("❌ Every bill failed to extract — see the processing log below.")
    else:
        st.warning("Nothing to process.")


# -------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.markdown(
        "<div style='padding:.2rem 0 1rem 0'>"
        "<span style='font-size:1.35rem;font-weight:800;color:#fff'>🧾 Utility "
        "Bill</span><br/>"
        "<span style='font-size:.95rem;font-weight:600;color:#8FA3D4'>Decoder · "
        "WTQ 2026</span></div>",
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        PAGES,
        key="page_nav",
        label_visibility="collapsed",
        index=PAGES.index(st.session_state.get("page", "Dashboard")),
    )
    st.session_state["page"] = page

    # Small live footer: model provider + whether a key is configured.
    st.markdown("---")
    try:
        settings = Settings.from_env()
        key_ready = bool(settings.api_key())
        st.markdown(
            f"**Model:** `{settings.model}`  \n"
            f"**Provider:** {settings.provider}  \n"
            f"**API key:** {'✅ configured' if key_ready else '❌ missing'}"
        )
    except ValueError as err:
        st.markdown(f"⚠️ {err}")

    with st.expander("🪵 Processing log"):
        ui.render_log(app_state.recent_log(20))


# ---------------------------------------------------------------- pages -----
def page_dashboard() -> None:
    ui.page_header(
        "📊", "Dashboard",
        "Live overview based on the real files in this session and in the output folder.",
    )
    stats = _stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.stat_card("🗂️", stats["total"], "Bills processed", ui.ACCENT)
    with col2:
        ui.stat_card("✅", stats["ok"], "Successful extractions", ui.GREEN)
    with col3:
        ui.stat_card("❌", stats["failed"], "Failed bills", ui.RED)
    with col4:
        ui.stat_card(
            "💬", f"{stats['answered']}/{stats['questions']}",
            "Questions answered", ui.ACCENT2,
        )

    if st.button("↻ Refresh from output folder", key="btn_refresh_dash"):
        st.session_state.pop("records", None)
        st.rerun()

    if stats["total"] == 0:
        ui.empty_state(
            "📭", "Nothing processed yet",
            "Head to **Upload Bills** to process bill images, or process a "
            "bills folder with the CLI (`python run.py --bills … --out output`).",
        )
        return

    if stats["questions"]:
        answered, questions = stats["answered"], stats["questions"]
        pct = int(100 * answered / questions)
        st.markdown("### 💬 Level 2 progress")
        st.progress(answered / questions, text=f"{answered} of {questions} questions answered ({pct}%)")

    if stats["failures"]:
        with st.container(border=True):
            st.error("Bills that failed to extract")
            for item in stats["failures"][:10]:
                st.markdown(f"- **{item['bill_id']}**: {item['error']}")

    if app_state.recent_log(1):
        st.markdown("### 🪵 Recent activity")
        ui.render_log(app_state.recent_log(8))


def page_upload() -> None:
    ui.page_header(
        "📤", "Upload Bills",
        "Drop bill images or choose a folder, then process them with the AI backend.",
    )

    mode = st.radio(
        "Input source",
        ["folder", "upload"],
        horizontal=True,
        format_func=lambda m: "📁 Process a folder" if m == "folder" else "🖼️ Upload images",
        key="upload_mode",
    )

    # Default to the test folder on hackathon day, else the training folder.
    default_folder = ""
    for candidate in (PROJECT_ROOT / "data" / "test" / "bills", PROJECT_ROOT / "data" / "train" / "bills"):
        if candidate.exists():
            default_folder = str(candidate)
            break

    paths: list[Path] = []
    folder_error = ""

    if mode == "folder":
        folder = st.text_input("Bills folder path", value=default_folder, key="folder_path")
        if folder.strip():
            folder_path = Path(folder.strip())
            if not folder_path.exists():
                folder_error = f"Folder not found: **{folder_path}**"
                st.error(folder_error)
            else:
                images = list_bill_images(folder_path)
                all_files = [p for p in folder_path.iterdir() if p.is_file()]
                skipped = len(all_files) - len(images)
                st.caption(
                    f"📂 Found **{len(images)}** image(s) in `{folder_path}`"
                    + (f" — {skipped} non-image file(s) skipped" if skipped else "")
                )
                paths = images
    else:
        uploaded = st.file_uploader(
            "Bill images (PNG / JPG / WEBP / BMP)",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            accept_multiple_files=True,
            key="bill_files",
        )
        # Small preview grid so the user can confirm what they selected.
        if uploaded:
            st.caption(f"🖼️ {len(uploaded)} file(s) selected — preview:")
            cols = st.columns(min(4, len(uploaded)))
            for i, file in enumerate(uploaded[:8]):
                with cols[i % 4]:
                    st.image(file, width=130)
                    st.caption(f"{file.name} · {file.size / 1024:.0f} KB" if file.size else file.name)
        paths = [ui_io.uploaded_to_temp(f) for f in uploaded] if uploaded else []

    st.markdown("### 🗂️ Optional CSV templates")
    tpl1 = st.file_uploader(
        "Level 1 CSV template (preserves official bill order)", type=["csv"], key="tpl1"
    )
    tpl2 = st.file_uploader(
        "Level 2 CSV template (required to generate answers)", type=["csv"], key="tpl2"
    )
    tpl1_path = _template_path(tpl1, "level1_template")
    tpl2_path = _template_path(tpl2, "level2_template")
    if tpl1 is None and tpl2 is None:
        st.caption(
            "No template → only `level1.csv` is written (alphabetical bill order). "
            "Provide the Level 2 template for answers."
        )

    process = st.button("🚀 Process bills", type="primary", key="btn_process")
    if process:
        if folder_error:
            st.error("Fix the folder path above before processing.")
        elif not paths:
            st.warning("No bill images to process — add images or pick a valid folder.")
        else:
            _run_processing(paths, tpl1_path, tpl2_path)

    if app_state.recent_log(1):
        st.markdown("### 🪵 Processing log")
        ui.render_log(app_state.recent_log(60))


def _line_df(bill: dict, key: str, labels: dict, total_field: str):
    """DataFrame for charge/tax line items; None when there is nothing to show."""
    rows = []
    for item in bill.get(key) or []:
        amount = item.get("amount")
        if amount is None:
            continue
        rows.append(
            {
                "Line item": labels.get(item.get("type") or "other", (item.get("type") or "other").replace("_", " ").title()),
                "Amount (PKR)": amount,
            }
        )
    if not rows and bill.get(total_field) is None:
        return None
    if bill.get(total_field) is not None:
        rows.append({"Line item": "**Total**", "Amount (PKR)": bill.get(total_field)})
    df = pd.DataFrame(rows)
    df["Amount (PKR)"] = df["Amount (PKR)"].map(ui.fmt_num)
    return df


def page_analysis() -> None:
    ui.page_header(
        "🔍", "Bill Analysis",
        "Browse each extracted bill: dates, meter readings, units, charges, "
        "taxes and the printed monthly history.",
    )
    records = _resolve_records()
    valid = {bid: rec for bid, rec in records.items() if rec.get("bill")}
    if not valid:
        ui.empty_state(
            "🗂️", "No bills analysed yet",
            "Process bills on the **Upload Bills** page first (or via the CLI), "
            "then come back here.",
        )
        return

    labels = {
        bid: f"{bid} · {rec['bill'].get('provider')} · {rec['bill'].get('bill_month')} · "
        f"{ui.fmt_num(rec['bill'].get('units_consumed')) or '—'} units"
        for bid, rec in sorted(valid.items())
    }
    chosen = st.selectbox("Select a bill", sorted(labels, key=lambda b: labels[b]),
                          format_func=lambda b: labels[b], key="bill_selector")
    rec = valid[chosen]
    bill, history, warnings = rec["bill"], rec.get("history", []), rec.get("warnings") or []
    facts = compute_facts(bill, history)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Units consumed", ui.fmt_num(bill.get("units_consumed")) or "—")
    m2.metric("Current bill", ui.fmt_money(bill.get("current_bill")) or "—")
    m3.metric("Payable (on time)", ui.fmt_money(bill.get("payable_within_due_date")) or "—")
    m4.metric("Due date", bill.get("due_date") or "—")

    tab_snap, tab_charges, tab_history = st.tabs(["Snapshot", "Charges & taxes", "History"])

    with tab_snap:
        left, right = st.columns(2)
        with left:
            ui.info_card("Billing", [
                ("Provider", bill.get("provider")),
                ("Tariff", bill.get("tariff")),
                ("Billing month", bill.get("bill_month")),
                ("Period / reading date", bill.get("reading_date")),
                ("Issue date", bill.get("issue_date")),
                ("Due date", bill.get("due_date")),
                ("Reference number", None),  # PII — deliberately not extracted
            ])
            st.caption(
                "⚠️ Personal identifiers (names, addresses, reference / meter "
                "serial numbers) are deliberately excluded from outputs per the "
                "competition rules."
            )
            ui.info_card("Meter information", [
                ("Sanctioned load (kW)", bill.get("sanctioned_load_kw")),
                ("Previous reading", bill.get("previous_reading")),
                ("Current reading", bill.get("current_reading")),
            ], icon="🔢")
        with right:
            ui.info_card("Amounts (PKR)", [
                ("Total charges", bill.get("total_charges")),
                ("Total taxes & duties", bill.get("total_taxes")),
                ("Current bill", bill.get("current_bill")),
                ("Arrears (previous dues)", bill.get("arrears")),
                ("Payable within due date", bill.get("payable_within_due_date")),
                ("Payable after due date", bill.get("payable_after_due_date")),
            ], icon="💰")
            ui.info_card("Derived figures", [
                ("Effective cost per unit", ui.fmt_money(facts.get("effective_cost_per_unit"))),
                ("Charges share of bill", f"{ui.fmt_num(facts.get('charges_share_percent'))}%" if facts.get("charges_share_percent") is not None else None),
                ("Tax share of bill", f"{ui.fmt_num(facts.get('tax_share_percent'))}%" if facts.get("tax_share_percent") is not None else None),
                ("History available", f"{facts.get('history_months')} month(s)" if facts.get("history_months") else None),
            ], icon="🧮")
        if warnings:
            with st.container(border=True):
                st.warning("Advisory consistency warnings (values are printed as-is)")
                for w in warnings:
                    st.markdown(f"- {w}")

    with tab_charges:
        st.markdown("### Charges")
        df_charges = _line_df(bill, "charges", CHARGES_LABELS, "total_charges")
        if df_charges is None:
            st.info("No charge line items printed on this bill.")
        else:
            ui.render_df(df_charges, key="df_charges")

        st.markdown("### Taxes & duties")
        df_taxes = _line_df(bill, "taxes", TAX_LABELS, "total_taxes")
        if df_taxes is None:
            st.info("No tax line items printed on this bill.")
        else:
            ui.render_df(df_taxes, key="df_taxes")

        c1, c2 = st.columns(2)
        with c1:
            plots.render(plots.charges_tax_donut(bill.get("total_charges"), bill.get("total_taxes")), key="donut")
        with c2:
            charge_rows = [(CHARGES_LABELS.get(i.get("type") or "other", "Other"), i.get("amount"))
                           for i in (bill.get("charges") or []) if i.get("amount") is not None]
            plots.render(plots.line_items_hbar(charge_rows), key="hbar")

    with tab_history:
        if not history:
            st.info("The bill does not include any monthly history.")
        else:
            plots.render(plots.history_bar(history), key="hist_bar")
            ui.render_df(pd.DataFrame([{"Month": h.get("month"), "Units": h.get("units")} for h in history]), key="hist_df")


def page_qa() -> None:
    ui.page_header(
        "❓", "Questions & Answers",
        "Every supplied question with its answer, searchable, with unanswered "
        "questions clearly marked.",
    )
    level2 = _load_level2_df()

    if level2 is None or level2.empty:
        ui.empty_state(
            "🗒️", "No answers yet",
            "Provide the Level 2 CSV template on **Upload Bills** and process "
            "bills, or use the generator below.",
        )
        _qa_inline_generate(_output_dir())
        return

    df = level2.copy()
    df = df.rename(columns={"bill_id": "Bill", "question_id": "Q ID",
                            "question": "Question", "answer": "Answer"})
    df["Status"] = df["Answer"].fillna("").astype(str).str.strip().map(
        lambda s: "✓ Answered" if s else "— Not answered"
    )
    total_q = len(df)
    answered = int((df["Status"] == "✓ Answered").sum())

    c1, c2 = st.columns(2)
    c1.metric("Questions in template", total_q)
    c2.metric("Answered", f"{answered} ({total_q - answered} unanswered)")

    query = st.text_input("🔎 Search questions, answers or bill IDs", key="qa_filter")
    if query.strip():
        mask = df.astype(str).apply(lambda col: col.str.contains(query.strip(), case=False, na=False)).any(axis=1)
        df = df[mask]

    ui.render_df(df[["Bill", "Q ID", "Question", "Answer", "Status"]], key="qa_table")
    if answered < total_q:
        st.warning(
            f"{total_q - answered} question(s) have no answer yet — the answer "
            "may not be derivable from this bill (e.g. not printed on it)."
        )


def _qa_inline_generate(output_dir: Path) -> None:
    """Fallback generator so users can produce answers without leaving the page."""
    with st.expander("⚡ Generate answers now"):
        with st.form("qa_gen_form"):
            tpl2 = st.file_uploader("Level 2 CSV template", type=["csv"], key="tpl2_inline")
            go = st.form_submit_button("Generate answers", type="primary")
        if go and tpl2 is not None:
            records = _resolve_records()
            if not records:
                st.warning("Process bills first (Upload Bills page).")
            else:
                try:
                    settings = Settings.from_env()
                    settings.validate()
                except ValueError as err:
                    st.error(f"❌ {err}")
                else:
                    client = LLMClient(settings)
                    res = pipeline_ui.build_outputs(
                        records, client, None, _template_path(tpl2, "level2_inline"),
                        output_dir, log=app_state.add_log,
                    )
                    st.success(
                        f"Wrote **{res['level2_rows']}** answers "
                        f"({res['answered']} answered) → {output_dir / 'level2.csv'}"
                    )


def page_reports() -> None:
    ui.page_header(
        "📄", "Generated Reports",
        "Download the actual generated CSV files (exact competition format).",
    )
    out = _output_dir()
    required = [("level1.csv", "Level 1 — extracted bills"), ("level2.csv", "Level 2 — question answers")]
    generated = []
    missing = []

    for name, _desc in required:
        path = out / name
        info = ui_io.file_info(path)
        if info["exists"]:
            generated.append((name, path))
        else:
            missing.append(name)

    for name, path in generated:
        info = ui_io.file_info(path)
        st.markdown(f"### 📄 {name}")
        st.markdown(
            f"{ui.chip(info['size'])} {ui.chip(f'modified {info['modified']}')}",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            st.download_button(
                f"⬇️ Download {name}",
                data=path.read_bytes(),
                file_name=name,
                mime="text/csv",
                use_container_width=True,
                key=f"dl_{name}",
            )
        with c2:
            with st.expander("Preview (first 5 rows)"):
                ui.render_df(pd.read_csv(path).head(5), key=f"prev_{name}")

    if missing:
        ui.empty_state(
            "📭", "Some reports are not generated yet",
            "Process bills on **Upload Bills** (with the Level 2 template for "
            f"answers). Output folder: `{out}`. Missing: {', '.join(missing)}.",
        )

    st.markdown("---")
    st.markdown("### ♻️ Regenerate from processed bills")
    records = _resolve_records()
    if not records:
        st.info("No processed bills in this session — process some first.")
        return
    tpl2 = st.file_uploader("Level 2 CSV template (regenerates answers)", type=["csv"], key="tpl2_regen")
    if st.button("Regenerate reports", type="primary", key="btn_regen"):
        try:
            settings = Settings.from_env()
            settings.validate()
        except ValueError as err:
            st.error(f"❌ {err}")
        else:
            client = LLMClient(settings)
            res = pipeline_ui.build_outputs(
                records, client, None, _template_path(tpl2, "level2_regen"),
                out, log=app_state.add_log,
            )
            st.success(
                f"Regenerated level1.csv ({res['level1_rows']} rows) and "
                f"level2.csv ({res['level2_rows']} rows, {res['answered']} answered)."
            )
            st.rerun()


def page_settings() -> None:
    ui.page_header(
        "⚙️", "Settings",
        "Configuration is read from the root `.env` file — the API key is never "
        "displayed or logged.",
    )
    try:
        settings = Settings.from_env()
        configured, model, provider = True, settings.model, settings.provider
        key_state = "✅ configured" if settings.api_key() else "❌ missing"
    except ValueError as err:
        configured, key_state = False, f"⚠️ {err}"
        model = provider = "—"

    ui.info_card("Model configuration", [
        ("Provider", provider),
        ("Model", model),
        ("Fallback model", getattr(settings, "fallback_model", "—") if configured else None),
        ("Output folder", str(_output_dir())),
        ("Cache folder", str(getattr(settings, "cache_dir", PROJECT_ROOT / ".cache"))),
        (".env file", str(PROJECT_ROOT / ".env")),
        ("API key status", key_state),
    ], icon="🤖")

    if not configured:
        st.info("Create a `.env` file from `.env.example` and add your API key (e.g. `GEMINI_API_KEY=…`).")

    if st.button("🔌 Test API connection", key="btn_test_api"):
        try:
            settings = Settings.from_env()
            settings.validate()
            client = LLMClient(settings)
            reply = client.generate("Reply with exactly: OK", json_mode=False, tag="ping")
            st.success(f"✅ Connected! Model replied: {reply.strip()[:40]}")
        except ValueError as err:
            st.error(f"❌ Configuration: {err}")
        except Exception as err:
            st.error(f"❌ API call failed: {err}")
            st.info(
                "Check that the key in `.env` is valid and that the model ID is "
                "copied exactly from AI Studio (see the participant guide)."
            )

    st.markdown("### 📁 Output folder")
    new_out = st.text_input("Output directory", value=str(_output_dir()), key="outdir_input")
    if new_out.strip() and Path(new_out.strip()) != _output_dir():
        st.session_state["output_dir"] = new_out.strip()
        st.success(f"Output folder updated to `{new_out.strip()}` — "
                   "downloads and analysis now use this folder.")
        st.rerun()


# ------------------------------------------------------------------ render --
if page == "Dashboard":
    page_dashboard()
elif page == "Upload Bills":
    page_upload()
elif page == "Bill Analysis":
    page_analysis()
elif page == "Questions & Answers":
    page_qa()
elif page == "Generated Reports":
    page_reports()
elif page == "Settings":
    page_settings()