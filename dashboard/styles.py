"""Visual theme: clean light background, deep-navy sidebar, blue/purple accents.

Injected once per run via ``inject()``. Card / badge / log classes are reused
by dashboard/components.py.
"""
from __future__ import annotations

import streamlit as st

NAVY = "#0D1B3E"
ACCENT = "#4F46E5"
ACCENT2 = "#7C3AED"
LIGHT = "#F4F6FB"
INK = "#1E293B"
MUTED = "#8896AB"

CSS = f"""
<style>
:root {{
  --navy: {NAVY}; --accent: {ACCENT}; --accent2: {ACCENT2};
  --light: {LIGHT}; --ink: {INK}; --muted: {MUTED};
}}

html, body, [class*="css"], .stApp {{
  font-family: "Segoe UI", "Inter", Roboto, -apple-system, sans-serif;
  color: var(--ink);
}}
.stApp {{ background: var(--light); }}

/* ---------- Deep navy sidebar ---------- */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0B1A3A 0%, #122952 100%);
  border-right: 1px solid rgba(255,255,255,.06);
}}
[data-testid="stSidebar"] * {{ color: #D7E2F5; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p {{ color: #FFFFFF; }}
[data-testid="stSidebar"] .stRadio > div {{ gap: 2px; }}
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {{
  text-transform: uppercase; font-size: .72rem; letter-spacing: .08em;
  color: #8FA3D4 !important; font-weight: 700;
}}
[data-testid="stSidebar"] .stRadio label {{
  padding: .42rem .7rem; border-radius: 10px; margin: 1px 0;
  font-size: .95rem; cursor: pointer; display: block;
}}
[data-testid="stSidebar"] .stRadio label:hover {{ background: rgba(255,255,255,.07); }}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {{
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  color: #FFFFFF; font-weight: 600;
  box-shadow: 0 4px 12px rgba(79,70,229,.35);
}}

/* ---------- Buttons ---------- */
.stButton > button {{
  border-radius: 10px; font-weight: 600; border: 1px solid #E2E8F0;
  padding: .5rem 1rem; transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: var(--accent); color: var(--accent); }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border: none; color: #fff;
}}
.stButton > button[kind="primary"]:hover {{ box-shadow: 0 6px 16px rgba(79,70,229,.4); color:#fff; }}

/* ---------- Generic card ---------- */
.w-card {{
  background: #FFFFFF; border: 1px solid #E7EBF3; border-radius: 14px;
  padding: 1.05rem 1.2rem; margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(16,24,40,.06), 0 6px 18px rgba(16,24,40,.05);
}}
.w-section {{ font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: .2rem 0 .6rem; }}
.w-sub {{ color: var(--muted); font-size: .85rem; margin-bottom: .4rem; }}

/* ---------- Stat cards (dashboard) ---------- */
.w-stat {{ display: flex; align-items: center; gap: .9rem; }}
.w-stat-icon {{
  width: 46px; height: 46px; border-radius: 12px; flex: 0 0 46px;
  display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
}}
.w-stat-value {{ font-size: 1.65rem; font-weight: 800; color: #0F172A; line-height: 1.1; }}
.w-stat-label {{ font-size: .82rem; color: var(--muted); font-weight: 600; }}

/* ---------- Key/value rows ---------- */
.w-row {{ display: flex; justify-content: space-between; gap: 1rem;
  padding: .42rem 0; border-bottom: 1px dashed #EDF1F8; font-size: .93rem; }}
.w-row:last-child {{ border-bottom: none; }}
.w-row-label {{ color: var(--muted); }}
.w-row-value {{ font-weight: 600; color: #0F172A; text-align: right; }}
.w-na {{ color: #A5B0C3; font-style: italic; font-weight: 400; }}

/* ---------- Badges ---------- */
.w-badge {{ display: inline-block; border-radius: 999px; padding: .16rem .6rem;
  font-size: .76rem; font-weight: 700; letter-spacing: .02em; }}
.w-badge-ok {{ background: #E7F7EE; color: #12805C; }}
.w-badge-warn {{ background: #FFF4E5; color: #B45309; }}
.w-badge-err {{ background: #FDEBEC; color: #C0392B; }}
.w-badge-info {{ background: #EEF2FF; color: #4338CA; }}
.w-chip {{ display: inline-block; background: #EEF2FF; color: #4338CA;
  border-radius: 999px; padding: .16rem .6rem; font-size: .78rem; font-weight: 600; }}

/* ---------- Page header ---------- */
.w-title {{ font-size: 1.45rem; font-weight: 800; color: #0F172A; margin: .4rem 0 .1rem; }}
.w-titlebar {{ display:flex; align-items:center; gap:.6rem; margin-bottom:.15rem; }}
.w-titlebar .w-ico {{ font-size:1.5rem; }}
.w-subtitle {{ color: var(--muted); margin-bottom: 1.1rem; font-size:.92rem; }}

/* ---------- Empty states ---------- */
.w-empty {{ text-align: center; padding: 2.8rem 1rem 2.2rem; color: #94A3B8; }}
.w-empty .w-ico {{ font-size: 2.6rem; display:block; margin-bottom:.5rem; }}
.w-empty .w-title {{ font-size: 1.1rem; color:#475569; font-weight:700; margin-bottom:.3rem;}}

/* ---------- Processing log ---------- */
.w-log pre {{
  background: #0F172A; color: #A5F3FC; border-radius: 10px;
  padding: .85rem 1rem; font-family: Consolas, "Cascadia Code", monospace;
  font-size: .82rem; line-height: 1.55; max-height: 360px; overflow-y: auto;
  white-space: pre-wrap;
}}
.w-log-ok {{ color:#86EFAC; }} .w-log-warn {{ color:#FCD34D; }}
.w-log-err {{ color:#FCA5A5; }} .w-log-info {{ color:#93C5FD; }}

/* ---------- Tables ---------- */
[data-testid="stDataFrame"] {{
  border-radius: 12px; overflow: hidden; border: 1px solid #E7EBF3;
  box-shadow: 0 2px 10px rgba(16,24,40,.04);
}}

/* ---------- Misc ---------- */
[data-testid="stExpander"] {{ border: 1px solid #E7EBF3; border-radius: 12px;
  background:#fff; box-shadow: 0 2px 8px rgba(16,24,40,.03); }}
div[data-testid="stMetric"] {{
  background:#fff; border:1px solid #E7EBF3; border-radius:14px;
  padding:.8rem 1rem; box-shadow: 0 2px 10px rgba(16,24,40,.04);
}}
div[data-testid="stMetric"] label {{ color: var(--muted); }}
hr {{ border-color: #E7EBF3; }}
</style>
"""


def inject() -> None:
    """A helper that injects the CSS into the running app."""
    st.markdown(CSS, unsafe_allow_html=True)