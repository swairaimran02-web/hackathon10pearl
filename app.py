"""Streamlit demo for the WTQ Utility Bill Decoder.

Run with:  streamlit run app.py

Upload a bill image to see the Level 1 extraction and ask Level 2 questions
about that bill, all grounded in the bill data.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from billdecoder.config import Settings
from billdecoder.extract import extract_bill
from billdecoder.level2 import answer_bill
from billdecoder.llm import LLMClient

st.set_page_config(page_title="Utility Bill Decoder", page_icon="🧾", layout="wide")
st.title("🧾 Utility Bill Decoder")
st.caption("Reads K-Electric, LESCO and IESCO bills and explains them in plain English.")

DEFAULT_QUESTIONS = [
    "How much of my bill is taxes?",
    "How many units did I use this month?",
    "What is my effective cost per unit?",
    "How much do I pay after the due date?",
]


@st.cache_resource
def get_client(provider: str, model: str) -> LLMClient:
    settings = Settings.from_env()
    settings.provider = provider
    settings.model = model
    return LLMClient(settings)


def read_settings() -> tuple[str, str]:
    try:
        settings = Settings.from_env()
        return settings.provider, settings.model
    except Exception:  # noqa: BLE001 - show a friendly message instead
        return "google", "gemini-3.5-flash-lite"


provider, model = read_settings()
st.sidebar.write(f"**Provider:** {provider}")
st.sidebar.write(f"**Model:** {model}")

uploaded = st.file_uploader("Upload a bill image", type=["png", "jpg", "jpeg", "webp"])

if uploaded is not None:
    col_image, col_data = st.columns([1, 1])
    with col_image:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

    try:
        settings = Settings.from_env()
        settings.validate()
        client = get_client(settings.provider, settings.model)
    except Exception as err:  # noqa: BLE001
        st.error(f"Configuration error: {err}")
        st.stop()

    with st.spinner("Reading the bill..."):
        with tempfile.NamedTemporaryFile(
            suffix=Path(uploaded.name).suffix, delete=False
        ) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name
        record = extract_bill(client, tmp_path)

    with col_data:
        st.subheader("Level 1 - extracted fields")
        st.json(record["bill"])

    if record.get("history"):
        st.subheader("Consumption history")
        st.dataframe(record["history"], use_container_width=True)

    st.subheader("Level 2 - ask a question")
    question = st.text_input("Your question", value=DEFAULT_QUESTIONS[0])
    if st.button("Answer") and question.strip():
        with st.spinner("Thinking..."):
            answers, facts = answer_bill(
                client,
                record["bill"],
                record["history"],
                [{"question_id": "Q1", "question": question}],
            )
        st.success(answers.get("Q1", ""))
        with st.expander("Computed figures used for the answer"):
            st.json(facts)
else:
    st.info("Upload a bill image to get started.")
