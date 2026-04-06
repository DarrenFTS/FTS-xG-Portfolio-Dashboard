"""Page 4: Analytics"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
st.set_page_config(page_title="Analytics", page_icon="🔬", layout="wide")
st.markdown("""<style>
[data-testid="stSidebar"]{background:#0D2B55;}
[data-testid="stSidebar"]*{color:white!important;}
</style>""", unsafe_allow_html=True)

MKT = {"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00"}

@st.cache_data(ttl=300)
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets = pd.DataFrame(json.load(open(os.path.join(base,'data','portfolio_master_sheet.json'))))
    bets['date'] = pd.to_datetime(bets['date'], errors='coerce')
    return bets

bets = load_data()
st.title("🔬 Analytics")

def ob(o):
    if o < 1.5:  return "1.00–1.49"
    if o < 2.0:  return "1.50–1.99"
    if o < 2.5:  return "2.00–2.49"
    if o < 3.0:  return "2.50–2.99"
    if o < 4.0:  return "3.00–3.99"
    if o < 5.0:  return "4.00–4.99"
    return "5.00+"

OO = ["1.00–1.49","1.50–1.99","2.00–2.49","2.50–2.99","3.00–3.99","4.00–4.99","5.00+"]
b2 = bets.copy(); b2['ob'] = b2['odds'].apply(ob)

# ROI by Odds Band
st.subheader("ROI by Odds Band")
og = b2.groupby(['system','ob']).agg(Bets=('pl','count'),PL=('pl','sum')).reset_index()
og['ROI%'] = og['PL']/og['Bets']*100
c1, c2 = st.columns(2)
with c1:
    fo = px.bar(og, x='ob', y='ROI%', color='system', barmode='group',
                category_orders={'ob':OO}, color_discrete_map=MKT,
                labels={'ob':'Odds Band','ROI%':'ROI %'})
    fo.update_layout(height=330, template='plotly_white',
        margin=dict(l=0,r=0,t=10,b=10), legend=dict(orientation='h', y=-0.25))
    st.plotly_chart(fo, use_container_width=True)
with c2:
    ov = b2.groupby('ob')['pl'].agg(['count','sum']).reset_index()
    ov.columns = ['Odds Band','Bets','PL']; ov['ROI%'] = ov['PL']/ov['Bets']*100
    ov = ov.set_index('Odds Band').reindex(OO).dropna()
    st.dataframe(ov.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%'}),
                 use_container_width=True)

st.divider()

# Monthly P/L
st.subheader("Monthly Performance")
b2['ym'] = b2['date'].dt.to_period('M').astype(str)
mn = b2.groupby('ym').agg(Bets=('pl','count'),PL=('pl','sum')).reset_index()
mn['ROI%'] = mn['PL']/mn['Bets']*100
mn['clr']  = mn['PL'].apply(lambda x: '#217346' if x > 0 else '#9B1C1C')
fm = go.Figure(go.Bar(x=mn['ym'], y=mn['PL'].round(2), marker_color=mn['clr'],
    text=[f"{p:+.2f}" for p in mn['PL']], textposition='outside',
    hovertemplate='%{x}<br>P/L: %{y:+.2f}<extra></extra>'))
fm.update_layout(height=300, template='plotly_white',
    margin=dict(l=0,r=0,t=10,b=60), xaxis_tickangle=-45, yaxis_title="P/L (pts)")
st.plotly_chart(fm, use_container_width=True)

st.divider()

# Win/Loss + Strike Rate
st.subheader("Distribution & Strike Rates")
c3, c4 = st.columns(2)
with c3:
    fh = px.histogram(b2, x='pl', color='system', nbins=50,
                      color_discrete_map=MKT, labels={'pl':'P/L per bet'})
    fh.update_layout(height=280, template='plotly_white',
        margin=dict(l=0,r=0,t=10,b=10), legend=dict(orientation='h', y=-0.25))
    st.plotly_chart(fh, use_container_width=True)
with c4:
    wr = b2.groupby('system').agg(Bets=('pl','count'),Won=('won','sum')).reset_index()
    wr['SR%'] = wr['Won']/wr['Bets']*100
    fsr = go.Figure(go.Bar(x=wr['system'], y=wr['SR%'].round(2),
        marker_color=[MKT.get(s,'#888') for s in wr['system']],
        text=[f"{r:.2f}%" for r in wr['SR%']], textposition='outside'))
    fsr.update_layout(height=280, template='plotly_white',
        margin=dict(l=0,r=0,t=10,b=10),
        yaxis_title="Strike Rate %", showlegend=False, title="Strike Rate by System")
    st.plotly_chart(fsr, use_container_width=True)

st.divider()

# Rolling 50-Bet ROI
st.subheader("Rolling 50-Bet ROI")
rs = st.selectbox("System", list(MKT.keys()))
rs_d = b2[b2['system'] == rs].sort_values('date').copy()
rs_d['rr'] = rs_d['pl'].rolling(50, min_periods=20).mean() * 100
fr = go.Figure(go.Scatter(x=rs_d['date'], y=rs_d['rr'].round(2), mode='lines',
    line=dict(color=MKT[rs], width=2),
    hovertemplate='%{x|%d %b %Y}<br>ROI: %{y:+.2f}%<extra></extra>'))
fr.add_hline(y=0, line_dash='dash', line_color='grey', opacity=0.5)
fr.update_layout(height=280, template='plotly_white',
    margin=dict(l=0,r=0,t=10,b=10), yaxis_title="Rolling ROI per bet (%)")
st.plotly_chart(fr, use_container_width=True)

st.divider()

# Full stats table
st.subheader("Full Stats — All Systems & Leagues")
fs = b2.groupby(['system','league']).agg(
    Bets=('pl','count'), PL=('pl','sum'), Won=('won','sum'), AvgOdds=('odds','mean')
).reset_index()
fs['ROI%'] = fs['PL']/fs['Bets']*100; fs['SR%'] = fs['Won']/fs['Bets']*100
fs = fs.rename(columns={'system':'System','league':'League'})
fs = fs[['System','League','Bets','PL','ROI%','SR%','AvgOdds']].sort_values(
    ['System','ROI%'], ascending=[True,False])
st.dataframe(
    fs.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%','SR%':'{:.2f}%','AvgOdds':'{:.2f}'}),
    use_container_width=True, hide_index=True, height=500)
