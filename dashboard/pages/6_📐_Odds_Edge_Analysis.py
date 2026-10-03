"""
FTS xG Portfolio — Odds Edge Analysis
Compares the average market odds taken against the implied win probability
of each qualifying league within each live system, vs actual results.
"""
import streamlit as st
import pandas as pd
import numpy as np
import json, os
import plotly.graph_objects as go

st.set_page_config(page_title="Odds Edge Analysis", page_icon="📐", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0d1117; }
[data-testid="stHeader"] { background-color: #0d1117; }
h1, h2, h3, p, span, label { color: #e6edf3 !important; }
[data-testid="stSidebar"],
[data-testid="stSidebar"] *,
[data-testid="stSidebarNav"],
[data-testid="stSidebarNav"] *,
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavLink"] *,
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarNavSeparator"] *,
section[data-testid="stSidebar"] a,
section[data-testid="stSidebar"] a *,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] li *,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div { color: #ffffff !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div > div > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div > div > div *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[class*="ValueContainer"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[class*="singleValue"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[class*="placeholder"],
[data-testid="stSidebar"] div[data-baseweb="select"] div,
[data-testid="stSidebar"] div[data-baseweb="select"] div *,
[data-testid="stSidebar"] div[data-baseweb="select"] span { color: #1a1a1a !important; background-color: #ffffff !important; }
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-baseweb="popover"] li,
[data-baseweb="menu"] [role="option"],
[data-baseweb="menu"] li { color: #1a1a1a !important; background-color: #ffffff !important; }
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover { background-color: #f0f4f8 !important; }
</style>
""", unsafe_allow_html=True)

st.title("📐 Odds Edge Analysis")
st.caption("Average odds taken vs. market-implied win probability, compared against actual results — per league, per live system.")

MKT = {"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00"}
BET_TYPE = {"Lay U1.5":"LAY","Back O2.5":"BACK","Lay O3.5":"LAY","FHG Lay U0.5":"LAY"}

@st.cache_data
def load_data():
    # pages/ -> dashboard/ -> repo root -> data/
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets = pd.DataFrame(json.load(open(os.path.join(base, "data", "portfolio_master_sheet.json"))))
    bets["date"] = pd.to_datetime(bets["date"], errors="coerce")
    return bets

bets = load_data()
LIVE = list(MKT.keys())
live_bets = bets[bets["system"].isin(LIVE)].copy()

def implied_win_pct(row):
    if row["bet_type"] == "LAY":
        return (1 - 1 / row["odds"])
    return 1 / row["odds"]

rows = []
for sys in LIVE:
    bt = BET_TYPE[sys]
    sub = live_bets[live_bets["system"] == sys]
    for lg, g in sub.groupby("league"):
        n = len(g)
        avg_odds = g["odds"].mean()
        implied = (1 - 1/g["odds"]).mean()*100 if bt == "LAY" else (1/g["odds"]).mean()*100
        actual = g["won"].mean()*100
        roi = g["pl"].sum()/n*100
        rows.append({
            "System": sys, "Bet Type": bt, "League": lg, "Bets": n,
            "Avg Odds": round(avg_odds, 3), "Implied Win %": round(implied, 2),
            "Actual Win %": round(actual, 2), "Edge (pp)": round(actual - implied, 2),
            "ROI %": round(roi, 2),
        })
edge_df = pd.DataFrame(rows)

with st.sidebar:
    st.header("Filter")
    sel_sys = st.multiselect("System", LIVE, default=LIVE)

show = edge_df[edge_df["System"].isin(sel_sys)].sort_values("Edge (pp)", ascending=False)

# ── KPI row ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Leagues analysed", len(show))
c2.metric("All positive edge?", "✅ Yes" if (show["Edge (pp)"] > 0).all() else "⚠️ No")
c3.metric("Average edge", f"{show['Edge (pp)'].mean():+.2f}pp")
weakest = show.loc[show["Edge (pp)"].idxmin()] if len(show) else None
if weakest is not None:
    c4.metric("Weakest edge", f"{weakest['Edge (pp)']:+.2f}pp", f"{weakest['System']} · {weakest['League']}")

st.divider()

# ── Table ─────────────────────────────────────────────────────────────────
st.subheader("Full breakdown")

def edge_color(v):
    if v >= 8: return "background-color:#D6EFE1;color:#155C2E;font-weight:bold"
    if v >= 4: return "background-color:#EAF7EE;color:#1E7E34"
    if v > 0:  return "background-color:#FEF9E7;color:#B7770D"
    return "background-color:#FDECEA;color:#C0392B;font-weight:bold"

def sys_color(v):
    return {"Lay U1.5":"background-color:#D4EEF2;color:#0B5E6B;font-weight:bold",
            "Back O2.5":"background-color:#D6EFE1;color:#217346;font-weight:bold",
            "Lay O3.5":"background-color:#EBE0F0;color:#4A235A;font-weight:bold",
            "FHG Lay U0.5":"background-color:#FFF0DC;color:#B35C00;font-weight:bold"}.get(v,"")

st.dataframe(
    show.style
        .format({"Avg Odds":"{:.3f}","Implied Win %":"{:.2f}%","Actual Win %":"{:.2f}%",
                 "Edge (pp)":"{:+.2f}","ROI %":"{:+.2f}%"})
        .map(sys_color, subset=["System"])
        .map(edge_color, subset=["Edge (pp)"]),
    use_container_width=True, hide_index=True, height=520,
)

st.divider()

# ── Chart: edge by league, coloured by system ────────────────────────────────
st.subheader("Edge by league")
show_sorted = show.sort_values("Edge (pp)")
fig = go.Figure(go.Bar(
    x=show_sorted["Edge (pp)"], y=show_sorted["League"] + " — " + show_sorted["System"],
    orientation="h",
    marker_color=[MKT[s] for s in show_sorted["System"]],
    text=[f"{v:+.2f}pp" for v in show_sorted["Edge (pp)"]],
    textposition="outside",
))
fig.update_layout(
    height=max(400, len(show_sorted)*24),
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#e6edf3"),
    margin=dict(l=0, r=40, t=10, b=20),
    xaxis=dict(title="Edge (percentage points)", gridcolor="rgba(48,54,61,0.4)"),
    yaxis=dict(gridcolor="rgba(0,0,0,0)"),
)
fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)")
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Edge = actual win rate minus the market-implied win rate from average odds taken. "
    "For LAY bets, implied win % = 1 − 1/odds (the lay holds when the event doesn't happen). "
    "For BACK bets, implied win % = 1/odds."
)
