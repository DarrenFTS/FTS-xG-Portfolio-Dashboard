"""
FTS xG Portfolio Dashboard  —  Main entry point
Run: streamlit run dashboard/app.py --server.port 8502
"""
import streamlit as st

st.set_page_config(
    page_title="FTS xG Systems",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #DCE9F7 !important; }
.metric-card {
    background: #F2F6FB; border-radius: 8px; padding: 16px 20px;
    border-left: 4px solid #1A5C9E; margin-bottom: 8px;
}
.metric-value { font-size: 28px; font-weight: 700; color: #0D2B55; }
.metric-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
.system-teal   { border-left-color: #0B5E6B !important; }
.system-green  { border-left-color: #217346 !important; }
.system-purple { border-left-color: #4A235A !important; }
.system-orange { border-left-color: #B35C00 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
# ⚽ FTS xG Systems Dashboard
**4 systems  ·  32 league-system combinations  ·  6,783 historical bets  ·  +16.0% blended ROI**

---
""")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Bets", "6,783", "2021–2026")
with col2:
    st.metric("Total P/L", "+1,083.2 pts", "+16.0% ROI")
with col3:
    st.metric("Lay U1.5", "+19.4% ROI", "6 leagues")
with col4:
    st.metric("FHG Lay U0.5", "+18.7% ROI", "10 leagues")
with col5:
    st.metric("Back O2.5", "+13.1% ROI", "6 leagues")

st.markdown("""
---
### Navigate using the sidebar
- **📊 Portfolio Overview** — Full performance breakdown with charts
- **🎯 Daily Selector** — Upload fixtures, generate & download selections
- **📈 System Performance** — Detailed per-system and per-league analysis
- **🔬 Analytics** — Edge analysis, seasonality, distributions
""")
