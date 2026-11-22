"""
FTS xG Dashboard — shared look, colours and data loading.

Every page calls:
    import fts_ui as ui
    ui.apply_theme()
right after st.set_page_config(...). Change colours here once and every page follows.
"""
from __future__ import annotations

import json
import os

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, "data", "portfolio_master_sheet.json")
INFO_PATH = os.path.join(ROOT, "data", "build_info.json")

# ── Palette ───────────────────────────────────────────────────────────────────
BG = "#0B1220"
SURFACE = "#121B2E"
SURFACE_2 = "#18233A"
BORDER = "#25324D"
TEXT = "#E6EDF7"
MUTED = "#8FA3BF"
ACCENT = "#4F8CFF"
GREEN = "#22C55E"
RED = "#EF4444"
AMBER = "#F59E0B"

SYSTEM_COLORS = {
    "Lay U1.5": "#38BDF8",
    "Back O2.5": "#34D399",
    "Lay O3.5": "#A78BFA",
    "FHG Lay U0.5": "#FB923C",
    "Back the Draw": "#F472B6",
}
SYSTEM_ORDER = list(SYSTEM_COLORS.keys())
LIVE_SYSTEMS = SYSTEM_ORDER[:4]
STATUS = {s: "LIVE" for s in LIVE_SYSTEMS} | {"Back the Draw": "TEST"}
BET_TYPE = {"Lay U1.5": "LAY", "Back O2.5": "BACK", "Lay O3.5": "LAY",
            "FHG Lay U0.5": "LAY", "Back the Draw": "BACK"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ── Plotly template: every chart picks this up automatically ─────────────────
_tpl = go.layout.Template(pio.templates["plotly_dark"])
_tpl.layout.update(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
    colorway=list(SYSTEM_COLORS.values()) + [ACCENT, AMBER, GREEN, RED],
    xaxis=dict(gridcolor="rgba(143,163,191,0.12)", zerolinecolor="rgba(143,163,191,0.25)",
               linecolor=BORDER),
    yaxis=dict(gridcolor="rgba(143,163,191,0.12)", zerolinecolor="rgba(143,163,191,0.25)",
               linecolor=BORDER),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
    hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER, font=dict(color=TEXT)),
    margin=dict(l=10, r=10, t=30, b=10),
)
pio.templates["fts"] = _tpl
pio.templates.default = "fts"
TEMPLATE = "fts"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}}
.stApp {{ background: radial-gradient(1200px 600px at 85% -10%, rgba(79,140,255,0.10), transparent 60%), {BG}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px; }}

/* text */
h1, h2, h3, h4, h5, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{ color: {TEXT} !important; letter-spacing: -0.02em; }}
h1 {{ font-weight: 800 !important; }}
h2, h3 {{ font-weight: 700 !important; }}
p, li, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {TEXT}; }}
[data-testid="stCaptionContainer"], .stCaption, small {{ color: {MUTED} !important; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #0F1A33 0%, #0A1326 100%) !important;
  border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] * {{ color: {TEXT}; }}
[data-testid="stSidebarNav"] a {{ border-radius: 8px; margin: 1px 6px; }}
[data-testid="stSidebarNav"] a:hover {{ background: rgba(79,140,255,0.12); }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: rgba(79,140,255,0.20); }}
[data-testid="stSidebarNav"] span {{ color: {TEXT} !important; font-weight: 500; }}

[data-testid="stSidebarNav"] span[label="app"] p {{ font-size: 0 !important; }}
[data-testid="stSidebarNav"] span[label="app"] p::after {{ content: "🏠  Home"; font-size: 0.875rem; }}

/* metrics as cards */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset; }}
[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; font-size: 0.78rem !important;
  text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }}
[data-testid="stMetricValue"] {{ color: {TEXT} !important; font-weight: 700; font-size: 1.55rem !important; }}
[data-testid="stMetricValue"] p, [data-testid="stMetricValue"] div {{ font-size: 1.55rem !important; overflow: visible !important;
  text-overflow: clip !important; white-space: nowrap; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 10px 10px 0 0; padding: 8px 16px;
  color: {MUTED}; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ color: {TEXT} !important; background: {SURFACE}; }}

/* inputs — explicit dark backgrounds + light text so they read whatever the base theme is */
[data-baseweb="select"] > div, [data-baseweb="select"] > div > div, [data-baseweb="input"],
[data-baseweb="input"] > div, [data-baseweb="base-input"], .stNumberInput input, .stDateInput input,
.stTextInput input, .stNumberInput [data-baseweb="input"] {{
  background-color: {SURFACE_2} !important; border-color: {BORDER} !important; color: {TEXT} !important; }}
[data-baseweb="select"] *, [data-baseweb="input"] input, [data-baseweb="base-input"] input {{
  color: {TEXT} !important; -webkit-text-fill-color: {TEXT} !important; }}
[data-baseweb="select"] svg {{ fill: {MUTED} !important; }}
input::placeholder {{ color: {MUTED} !important; -webkit-text-fill-color: {MUTED} !important; }}
[data-baseweb="tag"] {{ background: rgba(79,140,255,0.22) !important; }}
[data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background-color: {SURFACE_2} !important; }}
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [data-baseweb="popover"] li * {{
  background-color: {SURFACE_2}; color: {TEXT} !important; }}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {{ background-color: rgba(79,140,255,0.22) !important; }}
[data-baseweb="calendar"], [data-baseweb="calendar"] * {{ background-color: {SURFACE_2} !important; color: {TEXT} !important; }}
.stNumberInput button {{ background-color: {SURFACE_2} !important; color: {TEXT} !important; border-color: {BORDER} !important; }}

/* newer Streamlit dropdowns / date pickers (react-aria) */
[data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"],
[data-testid="stMultiSelect"] [data-baseweb="select"] > div, [data-testid="stDateInputField"],
[data-testid="stDateInput"] [role="group"], [data-testid="stTimeInput"] [role="group"] {{
  background-color: {SURFACE_2} !important; border-color: {BORDER} !important; color: {TEXT} !important; }}
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [role="group"] *, [data-testid="stMultiSelect"] [role="group"] *,
[data-testid="stDateInputField"] * {{
  color: {TEXT} !important; -webkit-text-fill-color: {TEXT} !important; background-color: transparent !important; }}
[data-testid="stMultiSelect"] [data-baseweb="tag"], [data-testid="stMultiSelect"] [role="group"] [role="row"],
[data-testid="stMultiSelect"] [role="group"] [role="gridcell"] {{ background-color: rgba(79,140,255,0.25) !important; }}
[role="listbox"], [role="listbox"] [role="option"], .react-aria-Popover, .react-aria-ListBox,
[role="dialog"] [role="grid"], .react-aria-Calendar {{ background-color: {SURFACE_2} !important; color: {TEXT} !important; }}
[role="listbox"] [role="option"] * {{ color: {TEXT} !important; }}
[role="listbox"] [role="option"][data-focused], [role="listbox"] [role="option"]:hover,
[role="listbox"] [role="option"][aria-selected="true"] {{ background-color: rgba(79,140,255,0.25) !important; }}

/* file uploader */
[data-testid="stFileUploaderDropzone"] {{ background-color: {SURFACE_2} !important; border: 1px dashed {BORDER} !important; }}
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploaderFile"] * {{ color: {TEXT} !important; }}
[data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzoneInstructions"] span {{ color: {MUTED} !important; }}
[data-testid="stFileUploaderDropzone"] button {{ background-color: {SURFACE} !important; border: 1px solid {BORDER} !important; }}

/* metric deltas */
[data-testid="stMetricDelta"] {{ background-color: transparent !important; }}
[data-testid="stMetricDelta"] div, [data-testid="stMetricDelta"] p {{ color: {MUTED} !important; }}
[data-testid="stMetricDelta"] svg {{ fill: {GREEN} !important; color: {GREEN} !important; }}

/* radio / checkbox / toggle labels */
.stRadio label p, .stCheckbox label p, [data-testid="stWidgetLabel"] p {{ color: {TEXT} !important; }}

/* buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"] {{
  border-radius: 10px; font-weight: 600; border: 1px solid {BORDER} !important;
  background-color: {SURFACE_2} !important; color: {TEXT} !important; }}
.stButton > button *, .stDownloadButton > button * {{ color: inherit !important; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: {ACCENT} !important; color: white !important; }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: linear-gradient(135deg, {ACCENT}, #3B6FE0) !important; border: 0 !important; color: white !important; }}

/* expander header */
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color: {TEXT} !important; }}
[data-testid="stExpander"] details {{ background-color: {SURFACE} !important; }}

/* containers */
[data-testid="stExpander"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 12px; overflow: hidden; }}
hr {{ border-color: {BORDER} !important; opacity: 0.6; }}
[data-testid="stPlotlyChart"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; padding: 6px; }}

/* custom components */
.fts-hero {{ display:flex; align-items:center; gap:16px; margin: 0 0 18px 0; }}
.fts-hero .ico {{ width:52px; height:52px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:1.6rem; background: linear-gradient(135deg, rgba(79,140,255,0.35), rgba(79,140,255,0.08));
  border:1px solid rgba(79,140,255,0.35); }}
.fts-hero h1 {{ margin:0; padding:0; font-size:1.9rem; line-height:1.1; }}
.fts-hero .sub {{ color:{MUTED}; font-size:0.92rem; margin-top:4px; }}
.fts-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px; height:100%; }}
.fts-card .lbl {{ color:{MUTED}; font-size:0.74rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; }}
.fts-card .val {{ color:{TEXT}; font-size:1.55rem; font-weight:700; margin-top:4px; }}
.fts-card .sub {{ color:{MUTED}; font-size:0.8rem; margin-top:2px; }}
.fts-pill {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:0.7rem; font-weight:700;
  letter-spacing:0.05em; }}
.fts-banner {{ border-radius:14px; padding:16px 18px; border:1px solid {BORDER}; background:{SURFACE}; margin-bottom:14px; }}
.fts-banner b {{ color:{TEXT}; }}
.fts-section {{ display:flex; align-items:center; gap:10px; margin: 18px 0 8px 0; }}
.fts-section .bar {{ width:4px; height:20px; border-radius:4px; background:{ACCENT}; }}
.fts-section .t {{ font-size:1.12rem; font-weight:700; color:{TEXT}; }}
.fts-section .s {{ color:{MUTED}; font-size:0.85rem; }}
</style>
"""


def apply_theme():
    """Inject the shared CSS and sidebar brand. Call once per page after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)
    info = build_info()
    fresh = f"Results to {pd.to_datetime(info['results_to']).strftime('%d %b %Y')}" if info else ""
    st.sidebar.markdown(
        f'<div style="padding:4px 4px 14px 4px;border-bottom:1px solid {BORDER};margin-bottom:10px">'
        f'<div style="font-weight:800;font-size:1.05rem">⚽ FTS xG Dashboard</div>'
        f'<div style="color:{MUTED};font-size:0.78rem;margin-top:2px">{fresh}</div></div>',
        unsafe_allow_html=True)


def hero(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="fts-hero"><div class="ico">{icon}</div><div><h1>{title}</h1>'
        f'<div class="sub">{subtitle}</div></div></div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "", color: str = ACCENT):
    st.markdown(
        f'<div class="fts-section"><div class="bar" style="background:{color}"></div>'
        f'<div class="t">{title}</div><div class="s">{subtitle}</div></div>', unsafe_allow_html=True)


def card(label: str, value: str, sub: str = "", color: str | None = None):
    edge = f"border-left:4px solid {color};" if color else ""
    return (f'<div class="fts-card" style="{edge}"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div><div class="sub">{sub}</div></div>')


def pill(text: str, color: str):
    return (f'<span class="fts-pill" style="background:{color}22;color:{color};'
            f'border:1px solid {color}55">{text}</span>')


def status_pill(system: str):
    return pill(STATUS.get(system, ""), GREEN if STATUS.get(system) == "LIVE" else AMBER)


def hex_rgba(h: str, a: float):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load(path: str, mtime: float) -> pd.DataFrame:
    df = pd.DataFrame(json.load(open(path)))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["won"] = df["won"].astype(bool)
    df["month"] = df["date"].dt.to_period("M")
    df["bet_type"] = df["system"].map(BET_TYPE)
    return df.sort_values(["date", "system"]).reset_index(drop=True)


def load_bets() -> pd.DataFrame:
    """All bets. Re-reads automatically whenever the data file changes."""
    return _load(DATA_PATH, os.path.getmtime(DATA_PATH)).copy()


def build_info() -> dict | None:
    try:
        return json.load(open(INFO_PATH))
    except Exception:
        try:
            d = json.load(open(DATA_PATH))
            return {"results_to": max(r["date"] for r in d), "bets": len(d)}
        except Exception:
            return None


def summary(df: pd.DataFrame, by: str | list | None = None) -> pd.DataFrame:
    """Bets, P/L, ROI, strike rate, avg odds, max drawdown — optionally grouped."""
    def _one(g):
        g = g.sort_values("date")
        cum = g["pl"].cumsum()
        return pd.Series({
            "Bets": len(g), "Won": int(g["won"].sum()), "P/L": g["pl"].sum(),
            "ROI %": g["pl"].sum() / len(g) * 100 if len(g) else 0,
            "SR %": g["won"].mean() * 100 if len(g) else 0,
            "Avg Odds": g["odds"].mean(),
            "Max DD": float((cum - cum.cummax()).min()) if len(g) else 0,
        })
    if by is None:
        return _one(df).to_frame().T
    return df.groupby(by, observed=True).apply(_one, include_groups=False).reset_index()


# ── Table styling (dark-friendly) ────────────────────────────────────────────
def pl_style(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    if pd.isna(v):
        return f"color:{MUTED}"
    if v > 0:
        return f"color:{GREEN};font-weight:600"
    if v < 0:
        return f"color:{RED};font-weight:600"
    return ""


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    a, b = hex_a.lstrip("#"), hex_b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def heat_style(v, scale: float = 30):
    """Green/red cell shading by value (ROI %, P/L, edge). Solid colours + white text, readable on any theme."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    if pd.isna(v):
        return f"color:{MUTED}"
    t = min(abs(v) / scale, 1) * 0.65 + 0.25
    base = "#16A34A" if v > 0 else "#DC2626" if v < 0 else "#64748B"
    return f"background-color:{_mix(SURFACE_2, base, t)};color:#FFFFFF;font-weight:600"


def system_style(v):
    c = SYSTEM_COLORS.get(v)
    return f"color:{c};font-weight:700" if c else ""
