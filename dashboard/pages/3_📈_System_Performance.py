"""
Page 3: System Performance
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(page_title="System Performance", page_icon="📈", layout="wide")
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

st.title("📈 System Performance")

with st.sidebar:
    st.header("Select System")
    system_choice = st.radio("System",
        options=["Lay U1.5", "Back O2.5", "Lay O3.5", "FHG Lay U0.5"], index=0)

colour   = MKT_COLOURS.get(system_choice, "#1A5C9E")
sys_bets = bets[bets['system'] == system_choice].sort_values('date').copy()

# ── KPIs ─────────────────────────────────────────────────────────────────────
n   = len(sys_bets)
pl  = sys_bets['pl'].sum()
roi = pl / n * 100 if n else 0
sr  = sys_bets['won'].mean() * 100 if n else 0
cum = sys_bets['pl'].cumsum()
dd  = float((cum - cum.cummax()).min()) if len(cum) > 0 else 0

st.markdown(f"## {system_choice}")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Bets",   f"{n:,}")
c2.metric("P/L",          f"{pl:+.2f} pts")
c3.metric("ROI",          f"{roi:+.2f}%")
c4.metric("Strike Rate",  f"{sr:.2f}%")
c5.metric("Max Drawdown", f"{dd:.2f} pts")
c6.metric("Leagues",      sys_bets['league'].nunique())

st.divider()

# ── Cumulative P/L + Drawdown ─────────────────────────────────────────────────
col_chart, col_dd = st.columns([3, 2])

with col_chart:
    st.subheader("Cumulative P/L")
    fig = go.Figure()
    for lg in sys_bets['league'].unique():
        lb = sys_bets[sys_bets['league'] == lg].sort_values('date')
        fig.add_trace(go.Scatter(
            x=lb['date'], y=lb['pl'].cumsum(),
            name=lg, mode='lines', line=dict(width=1.5),
            hovertemplate=f'<b>{lg}</b><br>%{{x|%d %b %Y}}<br>P/L: %{{y:+.2f}}<extra></extra>',
            visible='legendonly' if len(sys_bets['league'].unique()) > 6 else True,
        ))
    fig.add_trace(go.Scatter(
        x=sys_bets['date'], y=sys_bets['pl'].cumsum(),
        name='TOTAL', mode='lines', line=dict(color=colour, width=3),
        hovertemplate='<b>TOTAL</b><br>%{x|%d %b %Y}<br>P/L: %{y:+.2f}<extra></extra>'
    ))
    fig.update_layout(height=320, template='plotly_white',
                      margin=dict(l=0, r=0, t=5, b=50),
                      legend=dict(orientation='h', y=-0.25, font=dict(size=11)),
                      yaxis_title="P/L (pts)")
    st.plotly_chart(fig, use_container_width=True)

with col_dd:
    st.subheader("Drawdown")
    ss = sys_bets.sort_values('date')
    cum_pl    = ss['pl'].cumsum()
    dd_series = cum_pl - cum_pl.cummax()
    fig_dd = go.Figure(go.Scatter(
        x=ss['date'], y=dd_series.values,
        fill='tozeroy', line=dict(color='#9B1C1C', width=1.5),
        fillcolor='rgba(155,28,28,0.15)',
        hovertemplate='%{x|%d %b %Y}<br>DD: %{y:.2f}<extra></extra>'
    ))
    fig_dd.update_layout(height=320, template='plotly_white',
                         margin=dict(l=0, r=0, t=5, b=50),
                         yaxis_title="Drawdown (pts)")
    st.plotly_chart(fig_dd, use_container_width=True)

st.divider()

# ── Per-league breakdown ──────────────────────────────────────────────────────
st.subheader("League Breakdown")
lg_grp = sys_bets.groupby('league').agg(
    Bets=('pl', 'count'), PL=('pl', 'sum'), Won=('won', 'sum'), AvgOdds=('odds', 'mean')
).reset_index()
lg_grp['ROI%']    = lg_grp['PL'] / lg_grp['Bets'] * 100
lg_grp['SR%']     = lg_grp['Won'] / lg_grp['Bets'] * 100

def league_dd(lg):
    sub = sys_bets[sys_bets['league'] == lg].sort_values('date')
    c = sub['pl'].cumsum()
    return float((c - c.cummax()).min()) if len(c) > 0 else 0

lg_grp['MaxDD']   = lg_grp['league'].apply(league_dd)
lg_grp = lg_grp.rename(columns={'league': 'League'})
lg_grp = lg_grp[['League', 'Bets', 'PL', 'ROI%', 'SR%', 'AvgOdds', 'MaxDD']]\
    .sort_values('ROI%', ascending=False)

col_tbl, col_bar = st.columns([2, 3])
with col_tbl:
    def roi_color(val):
        if val >= 25: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
        if val >= 15: return 'background-color:#D4EEF2;color:#0B5E6B;font-weight:bold'
        if val >= 10: return 'background-color:#DCE9F7;color:#1A5C9E'
        if val >  0:  return ''
        return 'background-color:#FDE8E8;color:#9B1C1C'

    st.dataframe(
        lg_grp.style
            .format({
                'PL':       '{:+.2f}',
                'ROI%':     '{:+.2f}%',
                'SR%':      '{:.2f}%',
                'AvgOdds':  '{:.2f}',
                'MaxDD':    '{:.2f}',
            })
            .applymap(roi_color, subset=['ROI%']),
        use_container_width=True, hide_index=True
    )

with col_bar:
    fig_lg = go.Figure(go.Bar(
        x=lg_grp['League'], y=lg_grp['ROI%'].round(2),
        marker_color=[colour if v > 0 else '#9B1C1C' for v in lg_grp['ROI%']],
        text=[f"{r:+.2f}%" for r in lg_grp['ROI%']], textposition='outside',
    ))
    fig_lg.update_layout(height=300, template='plotly_white',
                         margin=dict(l=0, r=0, t=10, b=80),
                         xaxis_tickangle=-35, yaxis_title="ROI %", showlegend=False)
    st.plotly_chart(fig_lg, use_container_width=True)

st.divider()

# ── Season-by-season heatmap ──────────────────────────────────────────────────
st.subheader("Season-by-Season Performance")

def season_label(d):
    if pd.isna(d): return 'Unknown'
    y = d.year; m = d.month
    return f"{y}-{y+1}" if m >= 7 else f"{y-1}-{y}"

sys_bets2 = sys_bets.copy()
sys_bets2['season_label'] = sys_bets2['date'].apply(season_label)
ssn_grp = sys_bets2.groupby(['season_label', 'league']).agg(
    Bets=('pl', 'count'), PL=('pl', 'sum')
).reset_index()
ssn_grp['ROI%'] = ssn_grp['PL'] / ssn_grp['Bets'] * 100
ssn_grp = ssn_grp.rename(columns={'league': 'League', 'season_label': 'Season'})
pivot = ssn_grp.pivot_table(index='League', columns='Season', values='ROI%', aggfunc='first')

def heat_color(val):
    if pd.isna(val): return 'background-color:#F5F5F5;color:#BBB'
    if val >= 30: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
    if val >= 10: return 'background-color:#DCE9F7;color:#1A5C9E'
    if val >  0:  return 'background-color:#FEF3C7;color:#92580B'
    return 'background-color:#FDE8E8;color:#9B1C1C'

st.dataframe(
    pivot.style
        .format('{:+.2f}%', na_rep='—')
        .applymap(heat_color),
    use_container_width=True
)

st.divider()

# ── xG distribution ───────────────────────────────────────────────────────────
st.subheader("xG Distribution")
xg_label = "6G FH xG" if system_choice == "FHG Lay U0.5" else "6G Match xG"
fig_xg = px.histogram(sys_bets, x='xg_value', nbins=40, color='system',
                       color_discrete_map=MKT_COLOURS,
                       labels={'xg_value': xg_label, 'count': 'Frequency'})
fig_xg.update_layout(height=300, template='plotly_white',
                      margin=dict(l=0, r=0, t=10, b=10), showlegend=False)
st.plotly_chart(fig_xg, use_container_width=True)
