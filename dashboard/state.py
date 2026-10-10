"""Session-state helpers for the dashboard.

All state lives in ``st.session_state`` so it survives Streamlit reruns:
  * records   - bill_id -> extraction record (bill, history, warnings, source)
  * failures  - list of {bill_id, error} for bills that failed extraction
  * log       - processing log entries {t, level, msg}
  * output_dir - where generated CSV files are written
  * upload_dir - session-scoped temp folder for uploaded bill images
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import streamlit as st

from billdecoder.config import PROJECT_ROOT

DEFAULT_OUTPUT_DIR = str(PROJECT_ROOT / "output")


def init() -> None:
    ss = st.session_state
    ss.setdefault("records", {})
    ss.setdefault("failures", [])
    ss.setdefault("log", [])
    ss.setdefault("output_dir", DEFAULT_OUTPUT_DIR)
    ss.setdefault("page", "Dashboard")
    ss.setdefault(
        "upload_dir",
        str(Path(tempfile.gettempdir()) / f"wtq_uploads_{os.urandom(6).hex()}"),
    )


def upload_dir() -> Path:
    """Session-scoped folder for uploaded images (persists across reruns)."""
    return Path(st.session_state.get("upload_dir") or str(Path(tempfile.gettempdir()) / "wtq_uploads"))


def add_log(level: str, message: str) -> None:
    """Append a processing-log entry: level is ok|warn|err|info."""
    st.session_state["log"].append(
        {"t": time.strftime("%H:%M:%S"), "level": level, "msg": message}
    )
    # Keep only the most recent entries so the log cannot grow forever.
    if len(st.session_state["log"]) > 300:
        st.session_state["log"] = st.session_state["log"][-300:]


def clear_log() -> None:
    st.session_state["log"] = []


def recent_log(n: int = 60) -> list[dict]:
    return st.session_state["log"][-n:]