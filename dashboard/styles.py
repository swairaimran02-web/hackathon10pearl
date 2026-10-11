"""Visual theme: a calm, premium fintech look.

Deep-navy sidebar with aurora glows, soft layered light canvas, Inter/Sora
typography, gradient accents (indigo -> violet with a cyan spark), rounded
cards with a gentle hover lift, pill tabs/radios, and a glassy log terminal.

Injected once per run via ``inject()``. Card / badge / log classes are reused
by dashboard/components.py. Degrades gracefully offline (system font
fallbacks). No JS — pure CSS, so it survives Streamlit reruns untouched.
"""
from __future__ import annotations

import streamlit as st

NAVY = "#0D1B3E"
ACCENT = "#4F46E5"
ACCENT2 = "#7C3AED"
ACCENT3 = "#06B6D4"
LIGHT = "#F5F7FC"
INK = "#0F172A"
MUTED = "#64748B"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {{
  --navy: {NAVY}; --accent: {ACCENT}; --accent2: {ACCENT2}; --accent3: {ACCENT3};
  --light: {LIGHT}; --ink: {INK}; --muted: {MUTED};
  --card: #FFFFFF; --line: #E6EAF3; --shadow-soft: rgba(16,24,40,.05);
  --shadow-mid: rgba(16,24,40,.09);
}}

/* ------------------------------ base ------------------------------ */
html, body, [class*="css"], .stApp {{
  font-family: "Inter", "Segoe UI", Roboto, -apple-system, sans-serif;
  color: var(--ink);
}}
.stApp {{
  background:
    radial-gradient(1100px 520px at 88% -12%, rgba(124,58,237,.07), transparent 58%),
    radial-gradient(900px 480px at -8% 18%, rgba(79,70,229,.05), transparent 55%),
    var(--light);
}}
h1, h2, h3, h4 {{ font-family: "Sora", "Inter", sans-serif; letter-spacing: -.01em; color: var(--ink); }}

/* ------------------------------ scrollbars ------------------------------ */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
  background: #C6D0E0; border-radius: 8px; border: 2px solid transparent;
  background-clip: content-box;
}}
::-webkit-scrollbar-thumb:hover {{ background: #94A3B8; background-clip: content-box; }}

/* ------------------------------ sidebar ------------------------------ */
[data-testid="stSidebar"] {{
  background:
    radial-gradient(520px 300px at 20% -10%, rgba(124,58,237,.35), transparent 60%),
    radial-gradient(420px 340px at 110% 30%, rgba(6,182,212,.16), transparent 60%),
    linear-gradient(180deg, #081226 0%, #0D1B3E 45%, #10264F 100%);
  border-right: 1px solid rgba(255,255,255,.07);
}}
[data-testid="stSidebar"] * {{ color: #C9D7F2; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p {{ color: #FFFFFF; }}
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {{
  text-transform: uppercase; font-size: .68rem; letter-spacing: .12em;
  color: #6E82B8 !important; font-weight: 700;
}}
[data-testid="stSidebar"] .stRadio > div {{ gap: 3px; }}
[data-testid="stSidebar"] .stRadio label {{
  padding: .48rem .8rem; border-radius: 11px; margin: 1px 0;
  font-size: .94rem; cursor: pointer; display: block; position: relative;
  border: 1px solid transparent; transition: all .15s ease;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
  background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.04);
}}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {{
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  color: #FFFFFF; font-weight: 600;
  box-shadow: 0 6px 18px rgba(79,70,229,.45), inset 0 1px 0 rgba(255,255,255,.25);
}}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked)::after {{
  content: ""; position: absolute; right: 12px; top: 50%; width: 6px; height: 6px;
  border-radius: 50%; background: #fff; transform: translateY(-50%);
  opacity: .85;
}}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.08); }}

/* ------------------------------ buttons ------------------------------ */
.stButton > button {{
  border-radius: 12px; font-weight: 600; font-size: .92rem;
  padding: .55rem 1.05rem; border: 1px solid var(--line); background: #fff;
  color: #334155; transition: all .18s ease;
  box-shadow: 0 1px 2px var(--shadow-soft);
}}
.stButton > button:hover {{
  border-color: #818CF8; color: var(--accent); transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(79,70,229,.16);
}}
.stButton > button:active {{ transform: translateY(0); }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border: none; color: #fff;
  box-shadow: 0 6px 16px rgba(79,70,229,.35), inset 0 1px 0 rgba(255,255,255,.25);
}}
.stButton > button[kind="primary"]:hover {{
  box-shadow: 0 12px 26px rgba(79,70,229,.45); transform: translateY(-1px);
  color: #fff; border: none;
}}
.stButton > button:focus-visible, [data-testid="stSidebar"] label:focus-visible,
.stTextInput input:focus-visible, .stTextArea textarea:focus-visible {{
  outline: 2px solid var(--accent); outline-offset: 2px;
}}

/* ------------------------------ inputs ------------------------------ */
.stTextInput input, .stTextArea textarea, [data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
  border-radius: 10px !important; border-color: var(--line) !important;
  background: #fff !important; transition: all .15s ease;
}}
.stTextInput input:focus, .stTextArea textarea:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(79,70,229,.15) !important;
}}
[data-testid="stFileUploader"] {{
  border: 1.5px dashed #BFC7EE; border-radius: 14px;
  background: rgba(79,70,229,.035); padding: .35rem .5rem;
  transition: all .18s ease;
}}
[data-testid="stFileUploader"]:hover {{
  border-color: var(--accent); background: rgba(79,70,229,.06);
}}
[data-testid="stImage"] img {{ border-radius: 10px; box-shadow: 0 2px 8px var(--shadow-soft); }}

/* ------------------------------ radios (main area) ------------------------------ */
[data-testid="stRadio"] [role="radiogroup"] label {{
  background: #fff; border: 1px solid var(--line); border-radius: 999px;
  padding: .42rem .95rem; margin-right: .45rem; font-weight: 600;
  transition: all .15s ease;
}}
[data-testid="stRadio"] [role="radiogroup"] label:hover {{ border-color: #A5B4FC; }}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border-color: transparent; color: #fff;
  box-shadow: 0 4px 14px rgba(79,70,229,.35);
}}

/* ------------------------------ tabs ------------------------------ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 6px; background: transparent; }}
[data-testid="stTabs"] [data-baseweb="tab"] {{
  background: #EEF1F8; border-radius: 999px; padding: .3rem 1rem;
  font-weight: 600; color: #475569; border: 1px solid transparent;
  transition: all .15s ease;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {{ background: #E4E9F5; color: var(--ink); }}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{
  background: #fff; color: var(--accent); border-color: #C7D2FE;
  box-shadow: 0 4px 12px rgba(79,70,229,.14);
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] {{ display: none; }}

/* ------------------------------ progress ------------------------------ */
[data-testid="stProgress"] > div {{ background: #E8EDF6; border-radius: 999px; }}
[data-testid="stProgress"] > div > div > div {{
  background: linear-gradient(90deg, var(--accent), var(--accent2), var(--accent3));
  border-radius: 999px;
}}

/* ------------------------------ alerts ------------------------------ */
[data-testid="stAlert"] {{ border-radius: 12px; border-left-width: 4px; }}

/* ------------------------------ generic card ------------------------------ */
.w-card {{
  background: linear-gradient(180deg, #FFFFFF, #FBFCFE);
  border: 1px solid var(--line); border-radius: 16px;
  padding: 1.05rem 1.25rem; margin-bottom: 1rem;
  box-shadow: 0 1px 2px var(--shadow-soft), 0 8px 24px var(--shadow-mid);
  transition: transform .18s ease, box-shadow .18s ease;
}}
.w-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 2px 4px var(--shadow-soft), 0 14px 34px rgba(16,24,40,.11);
}}
.w-section {{ font-family: "Sora", sans-serif; font-size: 1rem; font-weight: 700;
  color: #0F172A; margin: .2rem 0 .65rem; }}
.w-sub {{ color: var(--muted); font-size: .85rem; margin-bottom: .4rem; }}

/* ------------------------------ stat cards ------------------------------ */
.w-stat {{ display: flex; align-items: center; gap: .95rem; }}
.w-stat-icon {{
  width: 48px; height: 48px; border-radius: 13px; flex: 0 0 48px;
  display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.6);
}}
.w-stat-value {{ font-size: 1.7rem; font-weight: 800; color: #0F172A;
  line-height: 1.1; font-variant-numeric: tabular-nums; }}
.w-stat-label {{ font-size: .8rem; color: var(--muted); font-weight: 600; }}

/* ------------------------------ key/value rows ------------------------------ */
.w-row {{ display: flex; justify-content: space-between; gap: 1rem;
  padding: .46rem 0; border-bottom: 1px dashed #EDF1F8; font-size: .92rem; }}
.w-row:last-child {{ border-bottom: none; }}
.w-row-label {{ color: var(--muted); }}
.w-row-value {{ font-weight: 600; color: #0F172A; text-align: right; }}
.w-na {{ color: #A5B0C3; font-style: italic; font-weight: 400; }}

/* ------------------------------ badges ------------------------------ */
.w-badge {{ display: inline-block; border-radius: 999px; padding: .18rem .62rem;
  font-size: .75rem; font-weight: 700; letter-spacing: .02em; }}
.w-badge-ok {{ background: #E7F7EE; color: #0E8A5F; }}
.w-badge-warn {{ background: #FFF4E5; color: #B45309; }}
.w-badge-err {{ background: #FDEBEC; color: #C0392B; }}
.w-badge-info {{ background: #EEF2FF; color: #4338CA; }}
.w-chip {{ display: inline-block; background: rgba(255,255,255,.14);
  color: #E6EBFF; border: 1px solid rgba(255,255,255,.16);
  border-radius: 999px; padding: .22rem .7rem; font-size: .76rem; font-weight: 600;
  backdrop-filter: blur(4px); }}

/* ------------------------------ page header ------------------------------ */
.w-titlebar {{ display: flex; align-items: center; gap: .7rem; margin: .45rem 0 .15rem; }}
.w-ico-tile {{
  width: 46px; height: 46px; border-radius: 14px; flex: 0 0 46px;
  display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
  background: linear-gradient(135deg, rgba(79,70,229,.12), rgba(124,58,237,.14));
  border: 1px solid rgba(79,70,229,.18);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.7), 0 4px 12px rgba(79,70,229,.12);
}}
.w-title {{ font-family: "Sora", sans-serif; font-size: 1.5rem; font-weight: 800;
  color: #0F172A; letter-spacing: -.015em; }}
.w-subtitle {{ color: var(--muted); margin: .1rem 0 1.15rem; font-size: .92rem; }}

/* ------------------------------ hero banner ------------------------------ */
.w-hero {{
  border-radius: 20px; padding: 1.5rem 1.7rem; margin-bottom: 1.2rem;
  color: #fff; position: relative; overflow: hidden;
  background: linear-gradient(120deg, #0D1B3E 0%, #22306B 55%, #3A2D8F 100%);
  box-shadow: 0 12px 34px rgba(13,27,62,.28), inset 0 1px 0 rgba(255,255,255,.15);
}}
.w-hero::before, .w-hero::after {{
  content: ""; position: absolute; border-radius: 50%; filter: blur(2px);
}}
.w-hero::before {{ width: 320px; height: 320px; right: -80px; top: -140px;
  background: radial-gradient(circle, rgba(124,58,237,.55), transparent 65%); }}
.w-hero::after {{ width: 240px; height: 240px; left: 34%; bottom: -150px;
  background: radial-gradient(circle, rgba(6,182,212,.35), transparent 65%); }}
.w-hero-title {{ position: relative; font-family: "Sora", sans-serif;
  font-size: 1.55rem; font-weight: 800; letter-spacing: -.01em; }}
.w-hero-sub {{ position: relative; margin-top: .35rem; font-size: .95rem;
  color: #C9D7F2; max-width: 62rem; line-height: 1.5; }}
.w-hero-chips {{ position: relative; margin-top: .85rem; display: flex;
  flex-wrap: wrap; gap: .45rem; }}
.w-hero-chips .w-chip {{
  background: rgba(255,255,255,.12); color: #E6EBFF;
  border-color: rgba(255,255,255,.18);
}}

/* ------------------------------ empty states ------------------------------ */
.w-empty {{ text-align: center; padding: 2.6rem 1rem 2.2rem; color: #94A3B8; }}
.w-empty-ico {{
  width: 64px; height: 64px; margin: 0 auto .85rem; border-radius: 20px;
  display: flex; align-items: center; justify-content: center; font-size: 1.7rem;
  background: linear-gradient(135deg, rgba(79,70,229,.08), rgba(124,58,237,.12));
  border: 1.5px dashed #BFC7EE;
}}
.w-empty .w-title {{ font-size: 1.08rem; color: #475569; font-weight: 700; margin-bottom: .3rem; }}

/* ------------------------------ processing log ------------------------------ */
.w-log pre {{
  background: linear-gradient(180deg, #0A142F, #0E2145);
  border: 1px solid rgba(255,255,255,.08); border-radius: 14px;
  padding: 1rem 1.1rem;
  font-family: Consolas, "Cascadia Code", "JetBrains Mono", monospace;
  font-size: .82rem; line-height: 1.6; max-height: 380px; overflow-y: auto;
  white-space: pre-wrap; color: #D7E4FF;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.07), 0 12px 30px rgba(11,15,32,.28);
}}
.w-log-ok {{ color: #4ADE80; }} .w-log-warn {{ color: #FBBF24; }}
.w-log-err {{ color: #F87171; }} .w-log-info {{ color: #93C5FD; }}

/* ------------------------------ metrics ------------------------------ */
div[data-testid="stMetric"] {{
  background: linear-gradient(180deg, #fff, #FBFCFE);
  border: 1px solid var(--line); border-radius: 14px;
  padding: .85rem 1.05rem; position: relative; overflow: hidden;
  box-shadow: 0 1px 2px var(--shadow-soft), 0 6px 18px var(--shadow-mid);
  font-variant-numeric: tabular-nums;
}}
div[data-testid="stMetric"]::before {{
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--accent), var(--accent2));
  border-radius: 0 3px 3px 0;
}}
div[data-testid="stMetric"] label {{ color: var(--muted); font-weight: 600; font-size: .8rem; }}

/* ------------------------------ tables / expander ------------------------------ */
[data-testid="stDataFrame"] {{
  border-radius: 14px; overflow: hidden; border: 1px solid var(--line);
  box-shadow: 0 2px 10px rgba(16,24,40,.05);
}}
[data-testid="stExpander"] {{
  border: 1px solid var(--line); border-radius: 14px; background: #fff;
  box-shadow: 0 2px 10px rgba(16,24,40,.04);
}}
hr {{ border-color: var(--line); }}

/* ------------------------------ footer / misc ------------------------------ */
[data-testid="stSidebar"] .w-side-foot {{
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.09);
  border-radius: 12px; padding: .55rem .75rem; font-size: .8rem;
}}
</style>
"""


def inject() -> None:
    """A helper that injects the CSS into the running app."""
    st.markdown(CSS, unsafe_allow_html=True)