"""Page 5: Results Dashboard — Historical performance with cumulative P&L curves"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def hex_alpha(hex_color, alpha=0.67):
    """Convert #rrggbb hex + alpha float to rgba() string."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


st.set_page_config(page_title="Results Dashboard", page_icon="📉", layout="wide")
st.markdown("""<style>
/* Sidebar background */
[data-testid="stSidebar"] { background: #0D2B55 !important; }

/* Nuclear option — every element inside sidebar = white */
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

/* Page headings */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stHeadingWithActionElements"] h3,
div[class*="stHeading"] h1,
div[class*="stHeading"] h2,
div[class*="stHeading"] h3 { color: #ffffff !important; }
</style>""", unsafe_allow_html=True)

# ── Embedded historical data ──────────────────────────────────────────────────
SYSTEM_DATA = {
    "Lay U1.5": {
        "total_pl": 211.17, "total_bets": 881, "max_dd": -17.44,
        "dd_start": "2021-07-31", "dd_end": "2021-10-02",
        "avg_xg": 4.184, "avg_odds": 4.63,
        "color": "#58a6ff",
        "seasons": [
            {"Season":"2021-2022","pl":18.32,"bets":159,"avg_xg":4.221,"avg_odds":4.545},
            {"Season":"2022",     "pl":13.72,"bets":14, "avg_xg":4.674,"avg_odds":4.768},
            {"Season":"2022-2023","pl":57.25,"bets":166,"avg_xg":4.152,"avg_odds":4.472},
            {"Season":"2023",     "pl":-0.70,"bets":13, "avg_xg":4.562,"avg_odds":4.658},
            {"Season":"2023-2024","pl":58.92,"bets":154,"avg_xg":4.118,"avg_odds":4.604},
            {"Season":"2024",     "pl": 8.00,"bets":23, "avg_xg":4.529,"avg_odds":4.793},
            {"Season":"2024-2025","pl":43.15,"bets":192,"avg_xg":4.164,"avg_odds":4.698},
            {"Season":"2025",     "pl": 8.82,"bets":9,  "avg_xg":4.534,"avg_odds":5.089},
            {"Season":"2025-2026","pl": 8.05,"bets":128,"avg_xg":4.112,"avg_odds":4.791},
        ],
        "competitions": [
            {"Competition":"Scottish Premiership",   "pl":38.12,"bets":324,"avg_xg":3.499,"avg_odds":4.173},
            {"Competition":"Danish Superligaen",     "pl":36.32,"bets":104,"avg_xg":4.366,"avg_odds":4.835},
            {"Competition":"Belgian Premier League", "pl":36.04,"bets":164,"avg_xg":4.343,"avg_odds":4.985},
            {"Competition":"German Bundesliga 2",    "pl":33.20,"bets":85, "avg_xg":4.823,"avg_odds":5.174},
            {"Competition":"Polish Ekstraklasa",     "pl":30.89,"bets":65, "avg_xg":5.005,"avg_odds":4.655},
            {"Competition":"Swedish Allsvenskan",    "pl":29.84,"bets":59, "avg_xg":4.572,"avg_odds":4.803},
            {"Competition":"Italian Serie A",        "pl":11.12,"bets":57, "avg_xg":5.002,"avg_odds":4.820},
        ],
    },
    "Back O2.5": {
        "total_pl": 88.21, "total_bets": 529, "max_dd": -8.47,
        "dd_start": "2023-10-28", "dd_end": "2023-11-25",
        "avg_xg": 4.844, "avg_odds": 1.818,
        "color": "#3fb950",
        "seasons": [
            {"Season":"2021-2022","pl":15.00,"bets":112,"avg_xg":4.915,"avg_odds":1.833},
            {"Season":"2022",     "pl": 2.58,"bets":10, "avg_xg":4.216,"avg_odds":1.816},
            {"Season":"2022-2023","pl":10.59,"bets":85, "avg_xg":4.832,"avg_odds":1.816},
            {"Season":"2023",     "pl":12.20,"bets":16, "avg_xg":4.721,"avg_odds":2.004},
            {"Season":"2023-2024","pl":10.08,"bets":98, "avg_xg":4.895,"avg_odds":1.782},
            {"Season":"2024",     "pl": 4.07,"bets":12, "avg_xg":4.519,"avg_odds":1.962},
            {"Season":"2024-2025","pl":22.79,"bets":96, "avg_xg":4.898,"avg_odds":1.823},
            {"Season":"2025",     "pl":-0.04,"bets":13, "avg_xg":4.507,"avg_odds":1.918},
            {"Season":"2025-2026","pl": 9.84,"bets":77, "avg_xg":4.808,"avg_odds":1.769},
        ],
        "competitions": [
            {"Competition":"Spanish Primera Division","pl":19.82,"bets":151,"avg_xg":4.400,"avg_odds":1.870},
            {"Competition":"Irish Premier League",    "pl":18.81,"bets":51, "avg_xg":4.520,"avg_odds":1.935},
            {"Competition":"English Championship",   "pl":10.85,"bets":52, "avg_xg":5.254,"avg_odds":1.917},
            {"Competition":"Polish Ekstraklasa",     "pl":10.82,"bets":73, "avg_xg":5.026,"avg_odds":1.832},
            {"Competition":"Italian Serie A",        "pl": 9.84,"bets":66, "avg_xg":5.003,"avg_odds":1.781},
            {"Competition":"Portuguese Primeira Liga","pl": 9.17,"bets":56, "avg_xg":4.926,"avg_odds":1.825},
            {"Competition":"Dutch Eredivisie",       "pl": 7.80,"bets":70, "avg_xg":5.108,"avg_odds":1.697},
        ],
    },
    "Lay O3.5": {
        "total_pl": 143.80, "total_bets": 915, "max_dd": -21.14,
        "dd_start": "2022-03-14", "dd_end": "2022-05-08",
        "avg_xg": 2.385, "avg_odds": 3.556,
        "color": "#ffa657",
        "seasons": [
            {"Season":"2021-2022","pl":  1.15,"bets":188,"avg_xg":2.300,"avg_odds":3.682},
            {"Season":"2022-2023","pl": 42.40,"bets":176,"avg_xg":2.562,"avg_odds":3.510},
            {"Season":"2023-2024","pl":  7.36,"bets":144,"avg_xg":2.733,"avg_odds":3.301},
            {"Season":"2024-2025","pl": 38.03,"bets":219,"avg_xg":2.591,"avg_odds":3.439},
            {"Season":"2025-2026","pl": 49.04,"bets":162,"avg_xg":2.809,"avg_odds":3.432},
        ],
        "competitions": [
            {"Competition":"Belgian Premier League",  "pl":41.82,"bets":309,"avg_xg":1.571,"avg_odds":3.505},
            {"Competition":"Spanish Segunda Division","pl":26.42,"bets":55, "avg_xg":4.769,"avg_odds":3.813},
            {"Competition":"German Bundesliga 2",     "pl":19.76,"bets":122,"avg_xg":1.457,"avg_odds":3.277},
            {"Competition":"Dutch Eerste Divisie",   "pl":15.66,"bets":119,"avg_xg":5.464,"avg_odds":2.337},
            {"Competition":"English Championship",   "pl":15.05,"bets":144,"avg_xg":1.012,"avg_odds":4.507},
            {"Competition":"Spanish Primera Division","pl":12.62,"bets":79, "avg_xg":0.948,"avg_odds":4.690},
            {"Competition":"French Ligue 1",         "pl": 6.65,"bets":61, "avg_xg":5.352,"avg_odds":2.841},
        ],
    },
    "FHG Lay U0.5": {
        "total_pl": 163.84, "total_bets": 714, "max_dd": -12.37,
        "dd_start": "2024-12-06", "dd_end": "2025-04-06",
        "avg_xg": 2.811, "avg_odds": 4.018,
        "color": "#bc8cff",
        "seasons": [
            {"Season":"2021-2022","pl":19.43,"bets":130,"avg_xg":2.816,"avg_odds":3.837},
            {"Season":"2022-2023","pl":54.50,"bets":148,"avg_xg":2.783,"avg_odds":3.932},
            {"Season":"2023-2024","pl":33.31,"bets":129,"avg_xg":2.818,"avg_odds":4.006},
            {"Season":"2024-2025","pl":37.08,"bets":163,"avg_xg":2.819,"avg_odds":4.092},
            {"Season":"2025-2026","pl":30.01,"bets":124,"avg_xg":2.824,"avg_odds":4.228},
        ],
        "competitions": [
            {"Competition":"Dutch Eredivisie",       "pl":37.70,"bets":172,"avg_xg":2.524,"avg_odds":4.393},
            {"Competition":"Portuguese Primeira Liga","pl":31.55,"bets":107,"avg_xg":2.787,"avg_odds":3.984},
            {"Competition":"Polish Ekstraklasa",     "pl":31.06,"bets":101,"avg_xg":2.720,"avg_odds":3.670},
            {"Competition":"Danish Superligaen",     "pl":27.38,"bets":53, "avg_xg":3.109,"avg_odds":3.892},
            {"Competition":"German Bundesliga",      "pl":20.18,"bets":108,"avg_xg":2.987,"avg_odds":4.304},
            {"Competition":"French Ligue 1",         "pl":14.95,"bets":65, "avg_xg":2.926,"avg_odds":3.950},
            {"Competition":"English Championship",   "pl":11.51,"bets":88, "avg_xg":3.028,"avg_odds":3.504},
        ],
    },
    "Back the Draw": {
        "total_pl": 173.56, "total_bets": 604, "max_dd": -26.04,
        "dd_start": "2023-09-03", "dd_end": "2023-09-15",
        "avg_xg": 0.387, "avg_odds": 3.992,
        "color": "#4A90D9",
        "seasons": [
            {"Season":"2022-2023","pl": 39.86,"bets":175,"avg_xg":0.391,"avg_odds":3.988},
            {"Season":"2023-2024","pl": 59.17,"bets":152,"avg_xg":0.388,"avg_odds":3.991},
            {"Season":"2024-2025","pl": 74.14,"bets":153,"avg_xg":0.385,"avg_odds":3.994},
            {"Season":"2025-2026","pl":  5.60,"bets":115,"avg_xg":0.383,"avg_odds":3.997},
        ],
        "competitions": [
            {"Competition":"Scottish Premiership",   "pl":16.29,"bets":13, "avg_xg":0.412,"avg_odds":4.102},
            {"Competition":"Italian Serie A",        "pl":24.73,"bets":27, "avg_xg":0.398,"avg_odds":4.210},
            {"Competition":"Dutch Eredivisie",       "pl":40.73,"bets":51, "avg_xg":0.401,"avg_odds":4.185},
            {"Competition":"Swiss Super League",     "pl":33.92,"bets":76, "avg_xg":0.389,"avg_odds":3.942},
            {"Competition":"German Bundesliga",      "pl":16.40,"bets":61, "avg_xg":0.385,"avg_odds":3.972},
            {"Competition":"German Bundesliga 2",    "pl":16.89,"bets":60, "avg_xg":0.382,"avg_odds":3.961},
            {"Competition":"Dutch Eerste Divisie",   "pl":23.79,"bets":103,"avg_xg":0.378,"avg_odds":3.874},
            {"Competition":"Belgian Premier League", "pl":13.96,"bets":73, "avg_xg":0.381,"avg_odds":3.891},
            {"Competition":"English Premier League", "pl": 2.80,"bets":83, "avg_xg":0.376,"avg_odds":3.823},
            {"Competition":"Polish Ekstraklasa",     "pl": 1.03,"bets":21, "avg_xg":0.373,"avg_odds":3.812},
            {"Competition":"French Ligue 1",         "pl":-4.37,"bets":16, "avg_xg":0.368,"avg_odds":3.798},
            {"Competition":"Spanish Primera Division","pl":-7.40,"bets":11,"avg_xg":0.362,"avg_odds":3.781},
        ],
    },
}

SYSTEMS = list(SYSTEM_DATA.keys())
TOTAL_PL   = sum(d["total_pl"]   for d in SYSTEM_DATA.values())
TOTAL_BETS = sum(d["total_bets"] for d in SYSTEM_DATA.values())
WORST_DD   = min(d["max_dd"]     for d in SYSTEM_DATA.values())

# ── Cumulative P&L series (from embedded HTML data) ───────────────────────────
# Key points only — enough to draw accurate curves
CUM_ENDPOINTS = {
    "Lay U1.5":    {"start":"2021-07-23","end":"2026-04-30","final":211.17},
    "Back O2.5":   {"start":"2021-08-16","end":"2026-04-30","final": 87.11},
    "Lay O3.5":    {"start":"2021-07-27","end":"2026-04-30","final":143.80},
    "FHG Lay U0.5":{"start":"2021-08-08","end":"2026-04-30","final":163.84},
    "Back the Draw":{"start":"2022-08-07","end":"2026-04-30","final":173.56},
}

# ── Load full bet-by-bet master sheet for accurate cum + drawdown ─────────────
@st.cache_data
def load_master_sheet():
    import json, os
    # pages/ -> dashboard/ -> repo root -> data/
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(repo_root, "data", "portfolio_master_sheet.json")
    with open(path) as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

def build_cum_curve(sys_name):
    """Return (dates, cum_pl, drawdown) from full bet-by-bet data."""
    df = load_master_sheet()
    sub = df[df["system"] == sys_name].sort_values("date").reset_index(drop=True)
    cum  = sub["pl"].cumsum().values
    peak = np.maximum.accumulate(cum)
    dd   = cum - peak
    dates = sub["date"].dt.strftime("%Y-%m-%d").tolist()
    return (
        dates,
        [round(float(x), 2) for x in cum],
        [round(float(x), 2) for x in dd],
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📉 Results Dashboard")
st.markdown("Historical performance across all 4 systems · 5 seasons · 2021–2026")
st.divider()

# ── Tab navigation ────────────────────────────────────────────────────────────
tab_overview, tab_lay15, tab_back25, tab_lay35, tab_fhg, tab_btd = st.tabs([
    "📊 Portfolio Overview", "Lay U1.5", "Back O2.5", "Lay O3.5", "FHG Lay U0.5", "Back the Draw"
])

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Portfolio P&L", f"+{TOTAL_PL:.2f} pts", "All 4 systems combined")
    c2.metric("🎯 Total Bets",           f"{TOTAL_BETS:,}",      "Across 5 seasons")
    c3.metric("📉 Worst System DD",       f"{WORST_DD:.2f} pts",  "FHG Lay U0.5 Dec–Apr 2026")
    c4.metric("✅ Systems Profitable",    "5 / 5",               "100% of systems in profit")
    st.divider()

    # System summary cards
    st.subheader("System Summary")
    cols = st.columns(5)
    for i, sys in enumerate(SYSTEMS):
        d = SYSTEM_DATA[sys]
        with cols[i]:
            roi = (d["total_pl"] / d["total_bets"]) * 100
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid {d['color']}44;
                        border-top:3px solid {d['color']};border-radius:10px;
                        padding:16px;margin-bottom:8px">
                <div style="color:{d['color']};font-weight:700;font-size:1rem;margin-bottom:8px">{sys}</div>
                <div style="font-size:1.8rem;font-weight:800;color:#3fb950">+{d['total_pl']:.2f}</div>
                <div style="color:#8b949e;font-size:0.75rem;margin-top:6px">
                    {d['total_bets']} bets · ROI: +{roi:.1f}%<br>
                    DD: <span style="color:#f85149">{d['max_dd']:.2f}</span> · 
                    Avg odds: {d['avg_odds']}
                </div>
            </div>""", unsafe_allow_html=True)
    st.divider()

    # Cumulative P&L — all systems on one chart
    st.subheader("Cumulative P&L — All Systems")
    fig_all = go.Figure()
    for sys in SYSTEMS:
        d = SYSTEM_DATA[sys]
        dates, values, _ = build_cum_curve(sys)
        fig_all.add_trace(go.Scatter(
            x=dates, y=values,
            name=sys,
            line=dict(color=d["color"], width=2.5),
            mode="lines",
            hovertemplate=f"<b>{sys}</b><br>Date: %{{x}}<br>P&L: %{{y:.2f}} pts<extra></extra>",
        ))
    fig_all.add_hline(y=0, line_dash="dot", line_color="#30363d")
    fig_all.update_layout(
        height=380, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#e6edf3", size=12),
        xaxis=dict(gridcolor="rgba(48,54,61,0.27)", showgrid=True),
        yaxis=dict(gridcolor="rgba(48,54,61,0.27)", showgrid=True, title="Cumulative P&L (pts)"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        hovermode="x unified", margin=dict(t=20, b=40, l=60, r=20),
    )
    st.plotly_chart(fig_all, use_container_width=True)
    st.divider()

    # Side-by-side bar charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("P&L by System")
        fig_bar = go.Figure(go.Bar(
            x=SYSTEMS,
            y=[SYSTEM_DATA[s]["total_pl"] for s in SYSTEMS],
            marker_color=[SYSTEM_DATA[s]["color"] for s in SYSTEMS],
            text=[f"+{SYSTEM_DATA[s]['total_pl']:.1f}" for s in SYSTEMS],
            textposition="outside",
        ))
        fig_bar.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="P&L (pts)"),
            margin=dict(t=20, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Max Drawdown by System")
        fig_dd = go.Figure(go.Bar(
            x=[SYSTEM_DATA[s]["max_dd"] for s in SYSTEMS],
            y=SYSTEMS,
            orientation="h",
            marker_color='rgba(248,81,73,0.67)',
            marker_line_color="#f85149",
            marker_line_width=1.5,
            text=[f"{SYSTEM_DATA[s]['max_dd']:.2f}" for s in SYSTEMS],
            textposition="outside",
        ))
        fig_dd.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="Max Drawdown (pts)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            margin=dict(t=20, b=40, l=160, r=60),
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    # Bet distribution doughnut
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("Bet Volume by System")
        fig_pie = go.Figure(go.Pie(
            labels=SYSTEMS,
            values=[SYSTEM_DATA[s]["total_bets"] for s in SYSTEMS],
            marker=dict(colors=[SYSTEM_DATA[s]["color"] for s in SYSTEMS]),
            hole=0.5,
            textinfo="label+percent",
        ))
        fig_pie.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_d2:
        st.subheader("Avg Odds by System")
        fig_odds = go.Figure(go.Bar(
            x=SYSTEMS,
            y=[SYSTEM_DATA[s]["avg_odds"] for s in SYSTEMS],
            marker_color=[hex_alpha(SYSTEM_DATA[s]["color"]) for s in SYSTEMS],
            marker_line_color=[SYSTEM_DATA[s]["color"] for s in SYSTEMS],
            marker_line_width=1.5,
            text=[str(SYSTEM_DATA[s]["avg_odds"]) for s in SYSTEMS],
            textposition="outside",
        ))
        fig_odds.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="Avg Odds", range=[0, 6]),
            margin=dict(t=20, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_odds, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM TAB RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def render_system_tab(tab, sys_name):
    d = SYSTEM_DATA[sys_name]
    color = d["color"]
    roi = (d["total_pl"] / d["total_bets"]) * 100

    with tab:
        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total P&L",   f"+{d['total_pl']:.2f} pts")
        c2.metric("🎯 Total Bets",  f"{d['total_bets']:,}")
        c3.metric("📈 ROI",         f"+{roi:.2f}%")
        c4.metric("📉 Max Drawdown",f"{d['max_dd']:.2f} pts")

        # DD highlight
        st.markdown(f"""
        <div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.3);
                    border-radius:8px;padding:14px 20px;margin:12px 0;
                    display:flex;gap:40px;flex-wrap:wrap">
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Max Drawdown</div>
                 <div style="color:#f85149;font-weight:700;font-size:1.1rem">{d['max_dd']:.2f} pts</div></div>
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Peak Before DD</div>
                 <div style="font-weight:600">{d['dd_start']}</div></div>
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">DD Trough Date</div>
                 <div style="font-weight:600">{d['dd_end']}</div></div>
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Recovery Status</div>
                 <div style="color:#3fb950;font-weight:700">✓ Recovered</div></div>
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Avg Match xG</div>
                 <div style="font-weight:600">{d['avg_xg']}</div></div>
            <div><div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Avg Odds</div>
                 <div style="font-weight:600">{d['avg_odds']}</div></div>
        </div>""", unsafe_allow_html=True)

        # Cumulative P&L + Drawdown — dual-axis single chart
        st.subheader("Cumulative P&L & Drawdown")
        dates, values, dd_arr = build_cum_curve(sys_name)

        fig_cum = go.Figure()

        # P&L line — left y-axis (y1)
        fig_cum.add_trace(go.Scatter(
            x=dates, y=values,
            fill="tozeroy",
            line=dict(color=color, width=2.5),
            fillcolor=hex_alpha(color, 0.13),
            mode="lines",
            name=sys_name,
            yaxis="y1",
            hovertemplate="P&L: %{y:.2f} pts<extra></extra>",
        ))

        # Drawdown line — right y-axis (y2)
        fig_cum.add_trace(go.Scatter(
            x=dates, y=dd_arr,
            line=dict(color="#f85149", width=1.5),
            mode="lines",
            name="Drawdown",
            yaxis="y2",
            hovertemplate="DD: %{y:.2f} pts<extra></extra>",
        ))

        fig_cum.update_layout(
            height=380,
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"),
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="v", x=1.08, y=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(t=20, b=40, l=65, r=75),
            xaxis=dict(
                gridcolor="rgba(48,54,61,0.27)", showgrid=True,
            ),
            yaxis=dict(
                title=dict(text="Cumulative P&L (units)", font=dict(color=color)),
                tickfont=dict(color=color),
                gridcolor="rgba(48,54,61,0.27)", showgrid=True,
                side="left",
            ),
            yaxis2=dict(
                title=dict(text="Drawdown (u)", font=dict(color="#f85149")),
                tickfont=dict(color="#f85149"),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=True,
                zerolinecolor="rgba(248,81,73,0.25)",
                zerolinewidth=1,
            ),
        )
        st.plotly_chart(fig_cum, use_container_width=True)

        # Season + Competition charts
        col_s, col_c = st.columns(2)

        with col_s:
            st.subheader("Results by Season")
            season_metric = st.selectbox("Metric", ["P&L (pts)","Bets","Avg xG","Avg Odds"],
                                          key=f"sm_{sys_name}")
            metric_map = {"P&L (pts)":"pl","Bets":"bets","Avg xG":"avg_xg","Avg Odds":"avg_odds"}
            m = metric_map[season_metric]

            # Merge calendar-year seasons into adjacent winter seasons
            # '2022'→'2022-2023', '2023'→'2023-2024', '2024'→'2024-2025', '2025'→'2025-2026'
            CAL_MERGE = {"2022":"2022-2023","2023":"2023-2024","2024":"2024-2025","2025":"2025-2026"}
            merged = {}
            for s in d["seasons"]:
                lbl = CAL_MERGE.get(s["Season"], s["Season"])
                if lbl not in merged:
                    merged[lbl] = {"Season":lbl,"pl":0,"bets":0,"avg_xg":[],"avg_odds":[]}
                merged[lbl]["pl"]    += s["pl"]
                merged[lbl]["bets"]  += s["bets"]
                merged[lbl]["avg_xg"].append(s.get("avg_xg",0))
                merged[lbl]["avg_odds"].append(s.get("avg_odds",0))
            for lbl in merged:
                xgs   = [v for v in merged[lbl]["avg_xg"]   if v]
                odds  = [v for v in merged[lbl]["avg_odds"]  if v]
                merged[lbl]["avg_xg"]   = round(sum(xgs)/len(xgs),3)   if xgs   else 0
                merged[lbl]["avg_odds"] = round(sum(odds)/len(odds),3)  if odds  else 0
            season_order = ["2021-2022","2022-2023","2023-2024","2024-2025","2025-2026"]
            seasons_merged = [merged[k] for k in season_order if k in merged]

            s_labels = [s["Season"] for s in seasons_merged]
            s_vals   = [s[m] for s in seasons_merged]
            s_colors = ['rgba(63,185,80,0.67)' if v >= 0 else 'rgba(248,81,73,0.53)' for v in s_vals] if m == "pl" else [hex_alpha(color)]*len(s_vals)
            s_borders= ["#3fb950" if v >= 0 else "#f85149" for v in s_vals] if m == "pl" else [color]*len(s_vals)

            fig_s = go.Figure(go.Bar(
                x=s_labels, y=s_vals,
                marker_color=s_colors,
                marker_line_color=s_borders,
                marker_line_width=1.5,
                text=[f"{v:+.2f}" if m=="pl" else f"{v:.3f}" for v in s_vals],
                textposition="outside",
            ))
            fig_s.update_layout(
                height=320, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#e6edf3"), showlegend=False,
                xaxis=dict(gridcolor="rgba(48,54,61,0.27)", tickangle=0),
                yaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
                margin=dict(t=30, b=60, l=60, r=20),
            )
            st.plotly_chart(fig_s, use_container_width=True)

        with col_c:
            st.subheader("Results by Competition")
            comp_metric = st.selectbox("Metric", ["P&L (pts)","Bets","Avg xG","Avg Odds"],
                                        key=f"cm_{sys_name}")
            m2 = metric_map[comp_metric]
            comps = sorted(d["competitions"], key=lambda x: x[m2], reverse=True)
            c_labels = [c["Competition"] for c in comps]
            c_vals   = [c[m2] for c in comps]
            c_colors = ['rgba(63,185,80,0.67)' if v >= 0 else 'rgba(248,81,73,0.53)' for v in c_vals] if m2=="pl" else [hex_alpha(color)]*len(c_vals)
            c_borders= ["#3fb950" if v >= 0 else "#f85149" for v in c_vals] if m2=="pl" else [color]*len(c_vals)

            fig_c = go.Figure(go.Bar(
                x=c_vals, y=c_labels,
                orientation="h",
                marker_color=c_colors,
                marker_line_color=c_borders,
                marker_line_width=1.5,
                text=[f"{v:+.2f}" if m2=="pl" else f"{v:.3f}" for v in c_vals],
                textposition="outside",
            ))
            fig_c.update_layout(
                height=320, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#e6edf3", size=11), showlegend=False,
                xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                margin=dict(t=30, b=40, l=180, r=60),
            )
            st.plotly_chart(fig_c, use_container_width=True)

        # Breakdowns tables
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader("Season Breakdown")
            sort_s = st.selectbox("Sort by", ["Chronological","P&L (desc)","Bets (desc)"],
                                   key=f"sort_s_{sys_name}")
            df_s = pd.DataFrame(d["seasons"])
            if sort_s == "P&L (desc)":   df_s = df_s.sort_values("pl", ascending=False)
            elif sort_s == "Bets (desc)": df_s = df_s.sort_values("bets", ascending=False)
            df_s_disp = df_s.rename(columns={"Season":"Season","pl":"P&L","bets":"Bets",
                                               "avg_xg":"Avg xG","avg_odds":"Avg Odds"})
            df_s_disp["P&L"] = df_s_disp["P&L"].apply(lambda x: f"+{x:.2f}" if x>=0 else f"{x:.2f}")
            st.dataframe(df_s_disp, use_container_width=True, hide_index=True)

        with col_t2:
            st.subheader("Competition Breakdown")
            sort_c = st.selectbox("Sort by", ["P&L (desc)","Bets (desc)","Avg xG","Avg Odds"],
                                   key=f"sort_c_{sys_name}")
            df_c = pd.DataFrame(d["competitions"])
            sort_col_map = {"P&L (desc)":"pl","Bets (desc)":"bets","Avg xG":"avg_xg","Avg Odds":"avg_odds"}
            df_c = df_c.sort_values(sort_col_map[sort_c], ascending=False)
            df_c_disp = df_c.rename(columns={"Competition":"League","pl":"P&L","bets":"Bets",
                                              "avg_xg":"Avg xG","avg_odds":"Avg Odds"})
            df_c_disp["P&L"] = df_c_disp["P&L"].apply(lambda x: f"+{x:.2f}" if x>=0 else f"{x:.2f}")
            st.dataframe(df_c_disp, use_container_width=True, hide_index=True)


# ── Render each system tab ────────────────────────────────────────────────────
render_system_tab(tab_lay15,  "Lay U1.5")
render_system_tab(tab_back25, "Back O2.5")
render_system_tab(tab_lay35,  "Lay O3.5")
render_system_tab(tab_fhg,    "FHG Lay U0.5")
render_system_tab(tab_btd,    "Back the Draw")
