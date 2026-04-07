"""Page 1: Portfolio Overview"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
st.set_page_config(page_title="Portfolio Overview", page_icon="📊", layout="wide")
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

MKT = {"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00"}

@st.cache_data(ttl=300)
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets = pd.DataFrame(json.load(open(os.path.join(base,'data','portfolio_master_sheet.json'))))
    bets['date'] = pd.to_datetime(bets['date'], errors='coerce')
    return bets

bets = load_data()
st.title("📊 Portfolio Overview")

with st.sidebar:
    st.header("Filters")
    sel_sys = st.selectbox("System", ["All"] + sorted(bets['system'].unique()))
    sel_lg  = st.selectbox("League", ["All"] + sorted(bets['league'].unique()))
    dr = st.date_input("Date Range",
                       value=(bets['date'].min().date(), bets['date'].max().date()))

f = bets.copy()
if sel_sys != "All": f = f[f['system'] == sel_sys]
if sel_lg  != "All": f = f[f['league'] == sel_lg]
if len(dr) == 2:
    f = f[(f['date'].dt.date >= dr[0]) & (f['date'].dt.date <= dr[1])]

n = len(f); pl = f['pl'].sum(); roi = pl/n*100 if n else 0
sr = f['won'].mean()*100 if n else 0
cum = f.sort_values('date')['pl'].cumsum()
dd  = float((cum - cum.cummax()).min()) if len(cum) else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Bets",  f"{n:,}")
c2.metric("Total P/L",   f"{pl:+.2f} pts")
c3.metric("ROI",         f"{roi:+.2f}%")
c4.metric("Strike Rate", f"{sr:.2f}%")
c5.metric("Max Drawdown",f"{dd:.2f} pts")
st.divider()

# Cumulative P/L chart
st.subheader("📈 Cumulative P/L")
cd = f.sort_values('date').copy(); cd['cumpl'] = cd['pl'].cumsum()
fig = go.Figure()
for mkt, col in MKT.items():
    sub = cd[cd['system'] == mkt].sort_values('date')
    if len(sub):
        fig.add_trace(go.Scatter(x=sub['date'], y=sub['pl'].cumsum(), name=mkt,
            line=dict(color=col, width=2), mode='lines',
            hovertemplate=f'<b>{mkt}</b><br>%{{x|%d %b %Y}}<br>P/L: %{{y:+.2f}}<extra></extra>'))
fig.add_trace(go.Scatter(x=cd['date'], y=cd['cumpl'], name='Combined',
    line=dict(color='#0D2B55', width=3, dash='dot'), mode='lines',
    hovertemplate='<b>Combined</b><br>%{x|%d %b %Y}<br>P/L: %{y:+.2f}<extra></extra>'))
fig.update_layout(height=360, template='plotly_white',
    legend=dict(orientation='h', y=-0.18),
    margin=dict(l=0,r=0,t=10,b=50), yaxis_title="P/L (pts)")
st.plotly_chart(fig, use_container_width=True)

# System table + bar
cl, cr = st.columns([3, 2])
with cl:
    st.subheader("System Breakdown")
    sg = f.groupby('system').agg(Bets=('pl','count'),PL=('pl','sum'),Won=('won','sum')).reset_index()
    sg['ROI%'] = sg['PL']/sg['Bets']*100; sg['SR%'] = sg['Won']/sg['Bets']*100
    sg = sg.rename(columns={'system':'System'})[['System','Bets','PL','ROI%','SR%']].sort_values('ROI%', ascending=False)
    st.dataframe(sg.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%','SR%':'{:.2f}%'}),
                 use_container_width=True, hide_index=True)
with cr:
    st.subheader("ROI by System")
    fig2 = go.Figure(go.Bar(x=sg['System'], y=sg['ROI%'].round(2),
        marker_color=[MKT.get(m,'#888') for m in sg['System']],
        text=[f"{r:+.2f}%" for r in sg['ROI%']], textposition='outside'))
    fig2.update_layout(height=270, template='plotly_white',
        margin=dict(l=0,r=0,t=10,b=10), yaxis_title="ROI %", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# League table
st.subheader("League Breakdown")
lg = f.groupby(['system','league']).agg(Bets=('pl','count'),PL=('pl','sum'),Won=('won','sum')).reset_index()
lg['ROI%'] = lg['PL']/lg['Bets']*100; lg['SR%'] = lg['Won']/lg['Bets']*100
lg = lg.rename(columns={'system':'System','league':'League'})
lg = lg[['System','League','Bets','PL','ROI%','SR%']].sort_values(['System','ROI%'], ascending=[True,False])

def croi(v):
    if v >= 30: return 'background-color:#D6EFE1;color:#155C2E'
    if v >= 15: return 'background-color:#DCE9F7;color:#0B5E6B'
    if v >  0:  return 'background-color:#FEF3C7'
    return 'background-color:#FDE8E8;color:#9B1C1C'

st.dataframe(
    lg.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%','SR%':'{:.2f}%'})
      .map(croi, subset=['ROI%']),
    use_container_width=True, hide_index=True, height=520)

st.divider()

# Season chart
st.subheader("📅 Season Performance")
def ssn(d):
    if pd.isna(d): return 'Unknown'
    y = d.year; m = d.month
    return f"{y}-{y+1}" if m >= 7 else f"{y-1}-{y}"

f2 = f.copy(); f2['sl'] = f2['date'].apply(ssn)
sg2 = f2.groupby(['sl','system']).agg(Bets=('pl','count'),PL=('pl','sum')).reset_index()
sg2['ROI%'] = sg2['PL']/sg2['Bets']*100
fig3 = go.Figure()
for mkt, col in MKT.items():
    sub = sg2[sg2['system'] == mkt]
    if len(sub):
        fig3.add_trace(go.Bar(x=sub['sl'], y=sub['ROI%'].round(2), name=mkt, marker_color=col,
            hovertemplate=f'<b>{mkt}</b><br>%{{x}}<br>ROI: %{{y:+.2f}}%<extra></extra>'))
fig3.update_layout(height=300, template='plotly_white', barmode='group',
    legend=dict(orientation='h', y=-0.22), margin=dict(l=0,r=0,t=10,b=60),
    yaxis_title="ROI %", xaxis_title="Season")
st.plotly_chart(fig3, use_container_width=True)
