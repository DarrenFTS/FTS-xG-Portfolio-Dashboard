"""
Page 1: Portfolio Overview
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(page_title="Portfolio Overview", page_icon="📊", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets  = pd.DataFrame(json.load(open(os.path.join(base, 'data', 'portfolio_master_sheet.json'))))
    stats = json.load(open(os.path.join(base, 'config', 'portfolio_stats.json')))
    bets['date'] = pd.to_datetime(bets['date'], errors='coerce')
    return bets, stats

bets, stats = load_data()

MKT_COLOURS = {
    "Lay U1.5":    "#0B5E6B",
    "Back O2.5":   "#217346",
    "Lay O3.5":    "#4A235A",
    "FHG Lay U0.5":"#B35C00",
}

st.title("📊 Portfolio Overview")

# ── Filters ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    systems_avail = ["All"] + sorted(bets['system'].unique().tolist())
    sel_system = st.selectbox("System", systems_avail)
    leagues_avail = ["All"] + sorted(bets['league'].unique().tolist())
    sel_league = st.selectbox("League", leagues_avail)
    min_date = bets['date'].min().date()
    max_date = bets['date'].max().date()
    date_range = st.date_input("Date Range", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)

filtered = bets.copy()
if sel_system != "All": filtered = filtered[filtered['system'] == sel_system]
if sel_league != "All": filtered = filtered[filtered['league'] == sel_league]
if len(date_range) == 2:
    filtered = filtered[(filtered['date'].dt.date >= date_range[0]) &
                        (filtered['date'].dt.date <= date_range[1])]

# ── KPI Row ───────────────────────────────────────────────────────────────────
n   = len(filtered)
pl  = filtered['pl'].sum()
roi = pl / n * 100 if n > 0 else 0
sr  = filtered['won'].mean() * 100 if n > 0 else 0
cum = filtered.sort_values('date')['pl'].cumsum()
dd  = float((cum - cum.cummax()).min()) if len(cum) > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Bets",   f"{n:,}")
c2.metric("Total P/L",    f"{pl:+.2f} pts")
c3.metric("ROI",          f"{roi:+.2f}%")
c4.metric("Strike Rate",  f"{sr:.2f}%")
c5.metric("Max Drawdown", f"{dd:.2f} pts")

st.divider()

# ── Cumulative P/L chart ──────────────────────────────────────────────────────
st.subheader("📈 Cumulative P/L")
chart_data = filtered.sort_values('date').copy()
chart_data['cumpl'] = chart_data['pl'].cumsum()

fig = go.Figure()
for mkt, col in MKT_COLOURS.items():
    sub = chart_data[chart_data['system'] == mkt].sort_values('date')
    if len(sub) > 0:
        fig.add_trace(go.Scatter(
            x=sub['date'], y=sub['pl'].cumsum().values,
            name=mkt, line=dict(color=col, width=2), mode='lines',
            hovertemplate=f'<b>{mkt}</b><br>%{{x|%d %b %Y}}<br>P/L: %{{y:+.2f}}<extra></extra>'
        ))
fig.add_trace(go.Scatter(
    x=chart_data['date'], y=chart_data['cumpl'],
    name='Combined', line=dict(color='#0D2B55', width=3, dash='dot'), mode='lines',
    hovertemplate='<b>Combined</b><br>%{x|%d %b %Y}<br>P/L: %{y:+.2f}<extra></extra>'
))
fig.update_layout(height=380, template='plotly_white',
                  legend=dict(orientation='h', y=-0.15),
                  margin=dict(l=0, r=0, t=10, b=50),
                  yaxis_title="P/L (pts)", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)

# ── System table + ROI bar ────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("System Breakdown")
    sys_grp = filtered.groupby('system').agg(
        Bets=('pl', 'count'), PL=('pl', 'sum'), Won=('won', 'sum')
    ).reset_index()
    sys_grp['ROI%'] = sys_grp['PL'] / sys_grp['Bets'] * 100
    sys_grp['SR%']  = sys_grp['Won'] / sys_grp['Bets'] * 100
    sys_grp = sys_grp.rename(columns={'system': 'System'})
    sys_grp = sys_grp[['System', 'Bets', 'PL', 'ROI%', 'SR%']].sort_values('ROI%', ascending=False)

    st.dataframe(
        sys_grp.style.format({
            'PL':   '{:+.2f}',
            'ROI%': '{:+.2f}%',
            'SR%':  '{:.2f}%',
        }),
        use_container_width=True, hide_index=True
    )

with col_right:
    st.subheader("ROI by System")
    fig2 = go.Figure(go.Bar(
        x=sys_grp['System'], y=sys_grp['ROI%'].round(2),
        marker_color=[MKT_COLOURS.get(m, '#888') for m in sys_grp['System']],
        text=[f"{r:+.2f}%" for r in sys_grp['ROI%']], textposition='outside',
    ))
    fig2.update_layout(height=280, template='plotly_white',
                       margin=dict(l=0, r=0, t=10, b=10),
                       yaxis_title="ROI %", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── League table ──────────────────────────────────────────────────────────────
st.subheader("League Breakdown")
lg_grp = filtered.groupby(['system', 'league']).agg(
    Bets=('pl', 'count'), PL=('pl', 'sum'), Won=('won', 'sum')
).reset_index()
lg_grp['ROI%'] = lg_grp['PL'] / lg_grp['Bets'] * 100
lg_grp['SR%']  = lg_grp['Won'] / lg_grp['Bets'] * 100
lg_grp = lg_grp.rename(columns={'system': 'System', 'league': 'League'})
lg_grp = lg_grp[['System', 'League', 'Bets', 'PL', 'ROI%', 'SR%']]\
    .sort_values(['System', 'ROI%'], ascending=[True, False])

def colour_roi(val):
    if val >= 20: return 'background-color:#D6EFE1;color:#155C2E'
    if val >= 10: return 'background-color:#DCE9F7;color:#0B5E6B'
    if val >  0:  return 'background-color:#FEF3C7'
    return 'background-color:#FDE8E8;color:#9B1C1C'

st.dataframe(
    lg_grp.style
        .format({'PL': '{:+.2f}', 'ROI%': '{:+.2f}%', 'SR%': '{:.2f}%'})
        .applymap(colour_roi, subset=['ROI%']),
    use_container_width=True, hide_index=True, height=500
)

st.divider()

# ── Season trend chart ────────────────────────────────────────────────────────
st.subheader("📅 Season Performance")

def season_from_date(d):
    if pd.isna(d): return 'Unknown'
    y = d.year; m = d.month
    return f"{y}-{y+1}" if m >= 7 else f"{y-1}-{y}"

filtered2 = filtered.copy()
filtered2['season_label'] = filtered2['date'].apply(season_from_date)
ssn_grp = filtered2.groupby(['season_label', 'system']).agg(
    Bets=('pl', 'count'), PL=('pl', 'sum')
).reset_index()
ssn_grp['ROI%'] = ssn_grp['PL'] / ssn_grp['Bets'] * 100

fig3 = go.Figure()
for mkt, col in MKT_COLOURS.items():
    sub = ssn_grp[ssn_grp['system'] == mkt]
    if len(sub) > 0:
        fig3.add_trace(go.Bar(
            x=sub['season_label'], y=sub['ROI%'].round(2),
            name=mkt, marker_color=col,
            hovertemplate=f'<b>{mkt}</b><br>%{{x}}<br>ROI: %{{y:+.2f}}%<extra></extra>'
        ))
fig3.update_layout(
    height=320, template='plotly_white', barmode='group',
    legend=dict(orientation='h', y=-0.2),
    margin=dict(l=0, r=0, t=10, b=60),
    yaxis_title="ROI %", xaxis_title="Season"
)
st.plotly_chart(fig3, use_container_width=True)
