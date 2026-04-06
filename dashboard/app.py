"""FTS xG Portfolio Dashboard"""
import streamlit as st
st.set_page_config(page_title="FTS xG Systems", page_icon="⚽", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""<style>
[data-testid="stSidebar"]{background:#0D2B55;}
[data-testid="stSidebar"]*{color:white!important;}
</style>""", unsafe_allow_html=True)

st.markdown("# ⚽ FTS xG Systems Dashboard")
st.markdown("**4 systems · 30 leagues · 3,080 bets · +20.39% blended ROI**")
st.markdown("*All leagues verified: ROI ≥10% · max 1 negative season · DD ≥-30 pts · min 50 bets*")
st.divider()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Bets",    "3,080",       "2021–2026")
c2.metric("Total P/L",     "+628.10 pts", "+20.39% ROI")
c3.metric("Lay U1.5",      "+25.12% ROI", "7 leagues")
c4.metric("FHG Lay U0.5",  "+25.12% ROI", "7 leagues")
c5.metric("Lay O3.5",      "+15.36% ROI", "8 leagues")

st.markdown("""
---
### Navigate using the sidebar
- **📊 Portfolio** — Full performance breakdown with charts
- **🎯 Daily Selector** — Upload PreMatch fixture file, generate & download selections
- **📈 System Performance** — Detailed per-system and per-league analysis
- **🔬 Analytics** — Edge analysis, distributions, rolling ROI
- **🔄 Update Database** — Upload new results file to refresh all data
""")
