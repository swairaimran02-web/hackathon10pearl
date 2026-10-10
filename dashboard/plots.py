"""Plotly charts built only from real extracted data.

If there is nothing to plot (missing history, empty line items, …) the helper
returns None and the caller shows a text note instead — no fake charts.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ACCENT = "#4F46E5"
ACCENT2 = "#7C3AED"

_LAYOUT = dict(
    template="plotly_white",
    height=300,
    margin=dict(l=10, r=10, t=40, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)


def history_bar(history: list[dict]):
    """Bar chart of previous monthly consumption (units) when history exists."""
    months = [h.get("month") for h in history]
    units = [h.get("units") for h in history]
    if not months or all(u is None for u in units):
        return None
    df = pd.DataFrame({"Month": months, "Units": units})
    fig = px.bar(
        df,
        x="Month",
        y="Units",
        title="Monthly consumption history (as printed on the bill)",
        color="Units",
        color_continuous_scale=["#C7D2FE", ACCENT],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**_LAYOUT, coloraxis_showscale=False)
    fig.update_yaxes(zeroline=False)
    return fig


def charges_tax_donut(total_charges: float | None, total_taxes: float | None):
    """Share of charges vs taxes inside the current bill."""
    values = [total_charges, total_taxes]
    if total_charges is None or total_taxes is None or sum(v for v in values if v) <= 0:
        return None
    fig = go.Figure(
        go.Pie(
            labels=["Charges", "Taxes & duties"],
            values=[v or 0 for v in values],
            hole=0.55,
            marker=dict(colors=[ACCENT, ACCENT2]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(**{**_LAYOUT, "height": 260, "title": "Bill composition"},
                      showlegend=False)
    return fig


def line_items_hbar(titled_rows: list[tuple[str, float]]):
    """Horizontal bars for a list of (title, amount) line items."""
    if not titled_rows:
        return None
    df = pd.DataFrame(titled_rows, columns=["Item", "Amount"])
    fig = px.bar(df, x="Amount", y="Item", orientation="h", color="Amount",
                 color_continuous_scale=["#E0E7FF", ACCENT])
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**_LAYOUT, height=max(220, 60 * len(df) + 80),
                      coloraxis_showscale=False, xaxis_title="PKR",
                      yaxis_title="")
    fig.update_xaxes(zeroline=False)
    return fig


def render(fig, key: str = "") -> None:
    """Render a plotly figure if one exists; no-op otherwise."""
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, key=key or None)