"""
FTS xG Portfolio Dashboard — Home
4 systems · 41 league combinations · 2,517 bets · +22.69% blended ROI
Verified against real database: FTS_Advanced_Results_xG_21-26.xlsx
"""
import streamlit as st

st.set_page_config(
    page_title="FTS xG Systems",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ⚽ FTS xG Systems Dashboard")
st.markdown("**4 systems  ·  41 league combinations  ·  2,517 historical bets  ·  +22.69% blended ROI**")
st.markdown("*All leagues verified against real database — ROI ≥ 10%, max 1 negative season, DD ≤ -30 pts*")
st.divider()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Bets",    "2,517",       "2021–2026")
c2.metric("Total P/L",    "+571.03 pts",  "+22.69% ROI")
c3.metric("Lay U1.5",     "+23.34% ROI",  "9 leagues")
c4.metric("FHG Lay U0.5", "+26.34% ROI",  "12 leagues")
c5.metric("Lay O3.5",     "+22.15% ROI",  "14 leagues")

st.markdown("""
---
### Navigate using the sidebar
- **📊 Portfolio** — Full performance breakdown with charts
- **🎯 Daily Selector** — Upload fixtures, generate & download selections
- **📈 System Performance** — Detailed per-system and per-league analysis
- **🔬 Analytics** — Edge analysis, distributions, rolling ROI
""")
