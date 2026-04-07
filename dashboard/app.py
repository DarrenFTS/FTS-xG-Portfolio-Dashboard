"""FTS xG Portfolio Dashboard — Home"""
import streamlit as st

st.set_page_config(page_title="FTS xG Systems", page_icon="⚽", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"]{background:#0D2B55;}
[data-testid="stSidebar"]*{color:white!important;}
h1, h2, h3 { color: #ffffff !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ── Header with logo ──────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1f6feb,#0D2B55);
                border-radius:16px;padding:14px;text-align:center;
                font-size:2.4rem;line-height:1;margin-top:4px">
        ⚽
    </div>""", unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <div style="padding-left:8px">
        <div style="color:#ffffff;font-size:2rem;font-weight:800;
                    letter-spacing:-0.5px;line-height:1.1">
            FTS xG Systems Dashboard
        </div>
        <div style="color:#8b949e;font-size:0.9rem;margin-top:4px">
            4 systems · 30 leagues · 3,080 bets · +20.39% blended ROI
        </div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── KPI metrics ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Bets",    "3,080",       "2021–2026")
c2.metric("Total P/L",     "+628.10 pts", "+20.39% ROI")
c3.metric("Lay U1.5",      "+25.12% ROI", "7 leagues")
c4.metric("FHG Lay U0.5",  "+25.12% ROI", "7 leagues")
c5.metric("Lay O3.5",      "+15.36% ROI", "8 leagues")

st.divider()

# ── Navigation cards ──────────────────────────────────────────────────────────
st.markdown("<h3 style='color:#ffffff;margin-bottom:16px'>Navigate</h3>",
            unsafe_allow_html=True)

nav_items = [
    ("🎯", "Daily Selector",     "#1f6feb", "Upload today's PreMatch file to generate qualifying selections"),
    ("📊", "Portfolio",          "#0B5E6B", "Full performance breakdown with season & league charts"),
    ("📉", "Results Dashboard",  "#4A235A", "Cumulative P&L curves, drawdown analysis, competition breakdown"),
    ("📈", "System Performance", "#155C2E", "Detailed per-system and per-league edge analysis"),
    ("🔬", "Analytics",          "#92580B", "Distributions, rolling ROI, and deep-dive analytics"),
    ("🔄", "Update Database",    "#333333", "Upload a new results file to refresh all data"),
]

cols = st.columns(3)
for i, (icon, title, color, desc) in enumerate(nav_items):
    with cols[i % 3]:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;
                    border-top:3px solid {color};border-radius:10px;
                    padding:18px;margin-bottom:16px;height:110px">
            <div style="font-size:1.4rem;margin-bottom:6px">{icon}
                <span style="color:#ffffff;font-weight:700;font-size:1rem;
                             vertical-align:middle;margin-left:6px">{title}</span>
            </div>
            <div style="color:#8b949e;font-size:0.78rem;line-height:1.4">{desc}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;
            padding:14px 18px;margin-top:8px;color:#8b949e;font-size:0.8rem">
    <span style="color:#58a6ff;font-weight:600">ℹ️ How to use:</span>
    Select a page from the sidebar to navigate. Start with
    <strong style="color:#ffffff">Daily Selector</strong> to generate today's bets,
    or <strong style="color:#ffffff">Results Dashboard</strong> to review historical performance.
</div>""", unsafe_allow_html=True)
