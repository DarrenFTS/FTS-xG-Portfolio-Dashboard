"""
Page 4: Analytics
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(page_title="Analytics", page_icon="🔬", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets = pd.DataFrame(json.load(open(os.path.join(base, 'data', 'portfolio_master_sheet.json'))))
    bets['date'] = pd.to_datetime(bets['date'], errors='coerce')
    return bets

bets = load_data()

MKT_COLOURS = {
    "Lay U1.5":    "#0B5E6B",
    "Back O2.5":   "#217346",
    "Lay O3.5":    "#4A235A",
    "FHG Lay U0.5":"#B35C00",
}

st.title("🔬 Analytics")

# ── ROI by odds band ──────────────────────────────────────────────────────────
st.subheader("ROI by Odds Band")

def odds_bucket(o):
    if o < 1.5:  return "1.00–1.49"
    if o < 2.0:  return "1.50–1.99"
    if o < 2.5:  return "2.00–2.49"
    if o < 3.0:  return "2.50–2.99"
    if o < 4.0:  return "3.00–3.99"
    if o < 5.0:  return "4.00–4.99"
    return "5.00+"

odds_order = ["1.00–1.49","1.50–1.99","2.00–2.49","2.50–2.99","3.00–3.99","4.00–4.99","5.00+"]
bets2 = bets.copy()
bets2['odds_band'] = bets2['odds'].apply(odds_bucket)

odds_grp = bets2.groupby(['system', 'odds_band']).agg(
    Bets=('pl', 'count'), PL=('pl', 'sum')
).reset_index()
odds_grp['ROI%'] = odds_grp['PL'] / odds_grp['Bets'] * 100

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(odds_grp, x='odds_band', y='ROI%', color='system',
                 barmode='group', category_orders={'odds_band': odds_order},
                 color_discrete_map=MKT_COLOURS,
                 labels={'odds_band': 'Odds Band', 'ROI%': 'ROI %'})
    fig.update_layout(height=350, template='plotly_white',
                      margin=dict(l=0, r=0, t=10, b=10),
                      legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    odds_vol = bets2.groupby('odds_band')['pl'].agg(['count', 'sum']).reset_index()
    odds_vol.columns = ['Odds Band', 'Bets', 'PL']
    odds_vol['ROI%'] = odds_vol['PL'] / odds_vol['Bets'] * 100
    odds_vol = odds_vol.set_index('Odds Band').reindex(odds_order).dropna()
    st.dataframe(
        odds_vol.style.format({'PL': '{:+.2f}', 'ROI%': '{:+.2f}%'}),
        use_container_width=True
    )

st.divider()

# ── Monthly P/L ───────────────────────────────────────────────────────────────
st.subheader("Monthly Performance")
bets2['year_month'] = bets2['date'].dt.to_period('M').astype(str)
monthly = bets2.groupby('year_month').agg(
    Bets=('pl', 'count'), PL=('pl', 'sum')
).reset_index()
monthly['ROI%']  = monthly['PL'] / monthly['Bets'] * 100
monthly['Color'] = monthly['PL'].apply(lambda x: '#217346' if x > 0 else '#9B1C1C')

fig_m = go.Figure(go.Bar(
    x=monthly['year_month'], y=monthly['PL'].round(2),
    marker_color=monthly['Color'],
    text=[f"{p:+.2f}" for p in monthly['PL']], textposition='outside',
    hovertemplate='%{x}<br>P/L: %{y:+.2f}<extra></extra>'
))
fig_m.update_layout(height=320, template='plotly_white',
                    margin=dict(l=0, r=0, t=10, b=60),
                    xaxis_tickangle=-45, yaxis_title="P/L (pts)")
st.plotly_chart(fig_m, use_container_width=True)

st.divider()

# ── Win/Loss distribution + SR ────────────────────────────────────────────────
st.subheader("Win/Loss Distribution")
col3, col4 = st.columns(2)

with col3:
    fig_hist = px.histogram(bets2, x='pl', color='system', nbins=50,
                            color_discrete_map=MKT_COLOURS,
                            labels={'pl': 'P/L per bet'})
    fig_hist.update_layout(height=300, template='plotly_white',
                           margin=dict(l=0, r=0, t=10, b=10),
                           legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig_hist, use_container_width=True)

with col4:
    win_rate = bets2.groupby('system').agg(
        Bets=('pl', 'count'), Won=('won', 'sum')
    ).reset_index()
    win_rate['SR%'] = win_rate['Won'] / win_rate['Bets'] * 100
    fig_sr = go.Figure(go.Bar(
        x=win_rate['system'], y=win_rate['SR%'].round(2),
        marker_color=[MKT_COLOURS.get(s, '#888') for s in win_rate['system']],
        text=[f"{r:.2f}%" for r in win_rate['SR%']], textposition='outside',
    ))
    fig_sr.update_layout(height=300, template='plotly_white',
                         margin=dict(l=0, r=0, t=10, b=10),
                         yaxis_title="Strike Rate %", showlegend=False,
                         title="Strike Rate by System")
    st.plotly_chart(fig_sr, use_container_width=True)

st.divider()

# ── xG vs P/L scatter ────────────────────────────────────────────────────────
st.subheader("xG Value vs P/L (per bet)")
league_sel = st.selectbox("Select league", ["All"] + sorted(bets2['league'].unique()))
scatter_data = bets2 if league_sel == "All" else bets2[bets2['league'] == league_sel]
if league_sel == "All":
    scatter_data = scatter_data.sample(min(2000, len(scatter_data)), random_state=42)

fig_sc = px.scatter(scatter_data, x='xg_value', y='pl', color='system',
                    color_discrete_map=MKT_COLOURS,
                    labels={'xg_value': '6G xG Value', 'pl': 'P/L'},
                    opacity=0.5)
fig_sc.add_hline(y=0, line_dash='dash', line_color='grey', opacity=0.5)
fig_sc.update_layout(height=380, template='plotly_white',
                     margin=dict(l=0, r=0, t=10, b=10),
                     legend=dict(orientation='h', y=-0.15))
st.plotly_chart(fig_sc, use_container_width=True)

st.divider()

# ── Rolling ROI ───────────────────────────────────────────────────────────────
st.subheader("Rolling 50-Bet ROI")
roll_system = st.selectbox("System", list(MKT_COLOURS.keys()))
sub = bets2[bets2['system'] == roll_system].sort_values('date').copy()
sub['rolling_roi'] = sub['pl'].rolling(50, min_periods=20).mean() * 100

fig_r = go.Figure(go.Scatter(
    x=sub['date'], y=sub['rolling_roi'].round(2),
    mode='lines', line=dict(color=MKT_COLOURS[roll_system], width=2),
    hovertemplate='%{x|%d %b %Y}<br>ROI: %{y:+.2f}%<extra></extra>'
))
fig_r.add_hline(y=0, line_dash='dash', line_color='grey', opacity=0.5)
fig_r.update_layout(height=300, template='plotly_white',
                    margin=dict(l=0, r=0, t=10, b=10),
                    yaxis_title="Rolling ROI per bet (%)")
st.plotly_chart(fig_r, use_container_width=True)

st.divider()

# ── Full stats table ──────────────────────────────────────────────────────────
st.subheader("Full Stats by System + League")
full = bets2.groupby(['system', 'league']).agg(
    Bets=('pl', 'count'), PL=('pl', 'sum'), Won=('won', 'sum'), AvgOdds=('odds', 'mean')
).reset_index()
full['ROI%'] = full['PL'] / full['Bets'] * 100
full['SR%']  = full['Won'] / full['Bets'] * 100
full = full.rename(columns={'system': 'System', 'league': 'League'})
full = full[['System', 'League', 'Bets', 'PL', 'ROI%', 'SR%', 'AvgOdds']]\
    .sort_values(['System', 'ROI%'], ascending=[True, False])

st.dataframe(
    full.style.format({
        'PL':      '{:+.2f}',
        'ROI%':    '{:+.2f}%',
        'SR%':     '{:.2f}%',
        'AvgOdds': '{:.2f}',
    }),
    use_container_width=True, hide_index=True, height=500
)
