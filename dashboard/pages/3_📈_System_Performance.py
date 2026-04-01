"""Page 3: System Performance"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(page_title="System Performance", page_icon="📈", layout="wide")
st.markdown("""<style>
[data-testid="stSidebar"]{background:#0D2B55;}
[data-testid="stSidebar"]*{color:white!important;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets=pd.DataFrame(json.load(open(os.path.join(base,'data','portfolio_master_sheet.json'))))
    bets['date']=pd.to_datetime(bets['date'],errors='coerce')
    return bets

bets=load_data()
MKT={"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00"}

st.title("📈 System Performance")

with st.sidebar:
    st.header("Select System")
    sc=st.radio("System",list(MKT.keys()),index=0)

col=MKT[sc]; sb=bets[bets['system']==sc].sort_values('date').copy()

n=len(sb); pl=sb['pl'].sum(); roi=pl/n*100 if n else 0
sr=sb['won'].mean()*100 if n else 0
cum=sb['pl'].cumsum(); dd=float((cum-cum.cummax()).min()) if len(cum) else 0

st.markdown(f"## {sc}")
c1,c2,c3,c4,c5,c6=st.columns(6)
c1.metric("Total Bets",  f"{n:,}")
c2.metric("P/L",         f"{pl:+.2f} pts")
c3.metric("ROI",         f"{roi:+.2f}%")
c4.metric("Strike Rate", f"{sr:.2f}%")
c5.metric("Max Drawdown",f"{dd:.2f} pts")
c6.metric("Leagues",     sb['league'].nunique())
st.divider()

cl2,cr2=st.columns([3,2])
with cl2:
    st.subheader("Cumulative P/L")
    fig=go.Figure()
    for lg in sb['league'].unique():
        lb=sb[sb['league']==lg].sort_values('date')
        fig.add_trace(go.Scatter(x=lb['date'],y=lb['pl'].cumsum(),name=lg,mode='lines',
            line=dict(width=1.5),
            visible='legendonly' if sb['league'].nunique()>6 else True,
            hovertemplate=f'<b>{lg}</b><br>%{{x|%d %b %Y}}<br>P/L: %{{y:+.2f}}<extra></extra>'))
    fig.add_trace(go.Scatter(x=sb['date'],y=sb['pl'].cumsum(),name='TOTAL',mode='lines',
        line=dict(color=col,width=3),
        hovertemplate='<b>TOTAL</b><br>%{x|%d %b %Y}<br>P/L: %{y:+.2f}<extra></extra>'))
    fig.update_layout(height=310,template='plotly_white',
        margin=dict(l=0,r=0,t=5,b=50),
        legend=dict(orientation='h',y=-0.28,font=dict(size=10)),yaxis_title="P/L (pts)")
    st.plotly_chart(fig,use_container_width=True)

with cr2:
    st.subheader("Drawdown")
    ss2=sb.sort_values('date'); cp=ss2['pl'].cumsum(); dds=cp-cp.cummax()
    fdd=go.Figure(go.Scatter(x=ss2['date'],y=dds.values,fill='tozeroy',
        line=dict(color='#9B1C1C',width=1.5),fillcolor='rgba(155,28,28,0.15)',
        hovertemplate='%{x|%d %b %Y}<br>DD: %{y:.2f}<extra></extra>'))
    fdd.update_layout(height=310,template='plotly_white',
        margin=dict(l=0,r=0,t=5,b=50),yaxis_title="Drawdown (pts)")
    st.plotly_chart(fdd,use_container_width=True)

st.divider()

# League breakdown
st.subheader("League Breakdown")
lg=sb.groupby('league').agg(Bets=('pl','count'),PL=('pl','sum'),Won=('won','sum'),AvgOdds=('odds','mean')).reset_index()
lg['ROI%']=lg['PL']/lg['Bets']*100; lg['SR%']=lg['Won']/lg['Bets']*100
def ldd(l):
    s2=sb[sb['league']==l].sort_values('date'); c2=s2['pl'].cumsum()
    return float((c2-c2.cummax()).min()) if len(c2) else 0
lg['MaxDD']=lg['league'].apply(ldd)
lg=lg.rename(columns={'league':'League'})[['League','Bets','PL','ROI%','SR%','AvgOdds','MaxDD']].sort_values('ROI%',ascending=False)

def rc(v):
    if v>=25: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
    if v>=15: return 'background-color:#D4EEF2;color:#0B5E6B;font-weight:bold'
    if v>=10: return 'background-color:#DCE9F7;color:#1A5C9E'
    if v>0:   return ''
    return 'background-color:#FDE8E8;color:#9B1C1C'

ct,cb=st.columns([2,3])
with ct:
    st.dataframe(lg.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%','SR%':'{:.2f}%','AvgOdds':'{:.2f}','MaxDD':'{:.2f}'})
                   .map(rc,subset=['ROI%']),
                 use_container_width=True,hide_index=True)
with cb:
    flg=go.Figure(go.Bar(x=lg['League'],y=lg['ROI%'].round(2),
        marker_color=[col if v>0 else '#9B1C1C' for v in lg['ROI%']],
        text=[f"{r:+.2f}%" for r in lg['ROI%']],textposition='outside'))
    flg.update_layout(height=290,template='plotly_white',margin=dict(l=0,r=0,t=10,b=80),
        xaxis_tickangle=-35,yaxis_title="ROI %",showlegend=False)
    st.plotly_chart(flg,use_container_width=True)

st.divider()

# Season heatmap
st.subheader("Season-by-Season")
def sl(d):
    if pd.isna(d): return 'Unknown'
    y=d.year; m=d.month
    return f"{y}-{y+1}" if m>=7 else f"{y-1}-{y}"
sb2=sb.copy(); sb2['sl']=sb2['date'].apply(sl)
sg=sb2.groupby(['sl','league']).agg(Bets=('pl','count'),PL=('pl','sum')).reset_index()
sg['ROI%']=sg['PL']/sg['Bets']*100
pv=sg.rename(columns={'league':'League','sl':'Season'}).pivot_table(index='League',columns='Season',values='ROI%',aggfunc='first')

def hc(v):
    if pd.isna(v): return 'background-color:#F5F5F5;color:#BBB'
    if v>=30: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
    if v>=10: return 'background-color:#DCE9F7;color:#1A5C9E'
    if v>0:   return 'background-color:#FEF3C7;color:#92580B'
    return 'background-color:#FDE8E8;color:#9B1C1C'

st.dataframe(pv.style.format('{:+.2f}%',na_rep='—').map(hc),use_container_width=True)

st.divider()

# xG distribution
st.subheader("xG Distribution")
lbl="6G FH xG" if sc=="FHG Lay U0.5" else "6G Match xG"
fx=px.histogram(sb,x='xg_value',nbins=40,color='system',color_discrete_map=MKT,
                labels={'xg_value':lbl,'count':'Frequency'})
fx.update_layout(height=280,template='plotly_white',margin=dict(l=0,r=0,t=10,b=10),showlegend=False)
st.plotly_chart(fx,use_container_width=True)
