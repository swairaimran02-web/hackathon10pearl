"""Reusable UI building blocks: headers, cards, badges, empty states, tables.

Every value shown is real data from the backend / generated files. Missing
values are rendered as "Not available" — nothing is ever invented or faked.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

NAVY = "#0D1B3E"
ACCENT = "#4F46E5"
ACCENT2 = "#7C3AED"
GREEN = "#12805C"
AMBER = "#B45309"
RED = "#C0392B"


def esc(value) -> str:
    """Escape a value for safe embedding in innerHTML."""
    return html.escape(str(value))


# ------------------------------------------------------------- formatting ---
def fmt_num(value) -> str | None:
    """Thousand-separated number, or None."""
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    try:
        return f"{value:,}"
    except (TypeError, ValueError):
        return str(value)


def fmt_money(value) -> str | None:
    if value is None:
        return None
    return f"PKR {fmt_num(value)}"


def _display(value) -> str:
    """Turn a raw value into its display string; None -> 'Not available'."""
    if value is None:
        return 'Not available <span class="w-na">(not on the bill)</span>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = fmt_num(value)
    return esc(value)


# ------------------------------------------------------------- layout ------
def page_header(icon: str, title: str, subtitle: str = "") -> None:
    """Big page title with icon tile and optional subtitle."""
    st.markdown(
        f"<div class='w-titlebar'><span class='w-ico-tile'>{icon}</span>"
        f"<span class='w-title'>{esc(title)}</span></div>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f"<div class='w-subtitle'>{esc(subtitle)}</div>", unsafe_allow_html=True)


def hero(title: str, subtitle: str, chips: list[str] | None = None) -> None:
    """A gradient hero banner for the top of a page (Dashboard).

    ``chips`` are small translucent pills (static facts such as capability
    notes) — never statistics, those are always computed from real data.
    """
    chips_html = "".join(f"<span class='w-chip'>{esc(c)}</span>" for c in (chips or []))
    st.markdown(
        f"<div class='w-hero'><div class='w-hero-title'>{esc(title)}</div>"
        f"<div class='w-hero-sub'>{esc(subtitle)}</div>"
        f"<div class='w-hero-chips'>{chips_html}</div></div>",
        unsafe_allow_html=True,
    )


def stat_card(icon: str, value, label: str, accent: str = ACCENT) -> None:
    """Renders one dashboard stat card (call inside a st.columns slot)."""
    st.markdown(
        f"<div class='w-card w-stat'>"
        f"<div class='w-stat-icon' "
        f"style='background:{accent}1A;color:{accent};border:1px solid {accent}33'>{icon}</div>"
        f"<div><div class='w-stat-value'>{esc(value)}</div>"
        f"<div class='w-stat-label'>{esc(label)}</div></div></div>",
        unsafe_allow_html=True,
    )


def info_card(title: str, items: list[tuple[str, object]], icon: str = "🧾") -> None:
    """Card with a title and key/value rows. A None value -> 'Not available'."""
    rows = "".join(
        f"<div class='w-row'><span class='w-row-label'>{esc(label)}</span>"
        f"<span class='w-row-value'>{_display(value)}</span></div>"
        for label, value in items
    )
    st.markdown(
        f"<div class='w-card'><div class='w-section'>{icon} {esc(title)}</div>{rows}</div>",
        unsafe_allow_html=True,
    )


def badge(kind: str, text: str) -> str:
    """Return an HTML badge: kind is ok|warn|err|info."""
    return f"<span class='w-badge w-badge-{kind}'>{esc(text)}</span>"


def chip(text: str) -> str:
    return f"<span class='w-chip'>{esc(text)}</span>"


def empty_state(icon: str, title: str, body: str) -> None:
    """Friendly empty-state block with a hint about what to do next."""
    st.markdown(
        f"<div class='w-card'><div class='w-empty'>"
        f"<div class='w-empty-ico'>{icon}</div>"
        f"<div class='w-title'>{esc(title)}</div>"
        f"<div>{esc(body)}</div></div></div>",
        unsafe_allow_html=True,
    )


def render_df(df: pd.DataFrame, key: str = "") -> None:
    """Standard dataframe rendering with the app's rounded style."""
    st.dataframe(df, use_container_width=True, hide_index=True, key=key or None)


def render_log(entries: list[dict]) -> None:
    """Render the processing log as a monospace block with level colors."""
    if not entries:
        st.info("No processing activity yet.")
        return
    lines = []
    for e in entries:
        level = e.get("level", "info")
        lines.append(
            f"<span class='w-log-{level}'>[{e.get('t', '')}] "
            f"({level.upper():<4})</span> {esc(e.get('msg', ''))}"
        )
    st.markdown(f"<div class='w-log'><pre>{''.join(lines)}</pre></div>", unsafe_allow_html=True)