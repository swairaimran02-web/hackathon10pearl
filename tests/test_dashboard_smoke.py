"""Smoke tests for the Streamlit dashboard (uses streamlit's AppTest runner).

These tests execute app.py headlessly and check that every page renders without
exceptions — including the empty states (nothing processed yet). No API calls
are made: the dashboard only calls the Gemini API on user action.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGES = [
    "Dashboard",
    "Upload Bills",
    "Bill Analysis",
    "Questions & Answers",
    "Generated Reports",
    "Settings",
]


def _app() -> AppTest:
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_starts_and_sidebar_has_six_pages() -> None:
    at = _app()
    # The navigation radio lives in the sidebar and exposes all six pages
    # (labels may carry an icon prefix, e.g. "📊 Dashboard").
    radios = at.sidebar.radio
    assert len(radios) == 1
    options = list(radios[0].options)
    assert len(options) == len(PAGES)
    assert all(page in opt for opt, page in zip(options, PAGES))


def test_every_page_renders_without_exception() -> None:
    at = _app()
    for page in PAGES:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, f"page {page} raised: {at.exception}"
        # Every page must show some content, not a blank screen.
        assert len(at.get("markdown")) + len(at.get("dataframe")) + len(at.get("metric")) > 0


def test_dashboard_shows_empty_state_when_nothing_processed() -> None:
    at = _app()
    # Point the app at an empty output folder so there is genuinely no data —
    # regardless of what previous CLI runs may have written to output/.
    empty_dir = Path(tempfile.mkdtemp())
    at.session_state["output_dir"] = str(empty_dir)
    at.session_state["records"] = {}
    at.session_state["failures"] = []
    at.run()
    texts = [m.value for m in at.markdown]
    assert any("Nothing processed yet" in t for t in texts)


def test_upload_page_has_process_button_and_template_uploaders() -> None:
    at = _app()
    at.sidebar.radio[0].set_value("Upload Bills").run()
    buttons = [b.label for b in at.button]
    assert any("Process bills" in b for b in buttons)
    labels = [u.label for u in at.get("file_uploader")]
    assert any("Level 2 CSV template" in u for u in labels)


def test_settings_page_shows_model_configuration() -> None:
    at = _app()
    at.sidebar.radio[0].set_value("Settings").run()
    texts = [m.value for m in at.markdown]
    assert any("Model configuration" in t for t in texts)
    assert any("API key status" in t for t in texts)