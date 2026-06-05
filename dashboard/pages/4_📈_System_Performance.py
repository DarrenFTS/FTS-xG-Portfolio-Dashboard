"""Page 3: System Performance"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
st.set_page_config(page_title="System Performance", page_icon="📈", layout="wide")
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

MKT = {"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00","Back the Draw":"#1A5276"}

@st.cache_data(ttl=300)
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bets = pd.DataFrame(json.load(open(os.path.join(base,'data','portfolio_master_sheet.json'))))
    bets['date'] = pd.to_datetime(bets['date'], errors='coerce')
    return bets

bets = load_data()
st.title("📈 System Performance")

tab_perf, tab_mc = st.tabs(["📊 Performance", "🎲 Monte Carlo"])
with tab_perf:

    with st.sidebar:
        st.header("Select System")
        sc = st.radio("System", list(MKT.keys()), index=0)
        if sc == "Back the Draw":
            st.warning("🧪 **TEST mode** — Back the Draw is paper tracking only for 2026-27. Not for live betting.")

    col = MKT[sc]
    sb  = bets[bets['system'] == sc].sort_values('date').copy()

    n   = len(sb); pl = sb['pl'].sum(); roi = pl/n*100 if n else 0
    sr  = sb['won'].mean()*100 if n else 0
    cum = sb['pl'].cumsum()
    dd  = float((cum - cum.cummax()).min()) if len(cum) else 0

    st.markdown(f"## {sc}")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Bets",  f"{n:,}")
    c2.metric("P/L",         f"{pl:+.2f} pts")
    c3.metric("ROI",         f"{roi:+.2f}%")
    c4.metric("Strike Rate", f"{sr:.2f}%")
    c5.metric("Max Drawdown",f"{dd:.2f} pts")
    c6.metric("Leagues",     sb['league'].nunique())
    st.divider()

    # Cumulative P/L + Drawdown
    cl2, cr2 = st.columns([3, 2])
    with cl2:
        st.subheader("Cumulative P/L")
        fig = go.Figure()
        for lg in sb['league'].unique():
            lb = sb[sb['league'] == lg].sort_values('date')
            fig.add_trace(go.Scatter(x=lb['date'], y=lb['pl'].cumsum(), name=lg, mode='lines',
                line=dict(width=1.5),
                visible='legendonly' if sb['league'].nunique() > 8 else True,
                hovertemplate=f'<b>{lg}</b><br>%{{x|%d %b %Y}}<br>P/L: %{{y:+.2f}}<extra></extra>'))
        fig.add_trace(go.Scatter(x=sb['date'], y=sb['pl'].cumsum(), name='TOTAL', mode='lines',
            line=dict(color=col, width=3),
            hovertemplate='<b>TOTAL</b><br>%{x|%d %b %Y}<br>P/L: %{y:+.2f}<extra></extra>'))
        fig.update_layout(height=310, template='plotly_white',
            margin=dict(l=0,r=0,t=5,b=50),
            legend=dict(orientation='h', y=-0.30, font=dict(size=10)),
            yaxis_title="P/L (pts)")
        st.plotly_chart(fig, use_container_width=True)

    with cr2:
        st.subheader("Drawdown")
        ss2 = sb.sort_values('date'); cp = ss2['pl'].cumsum(); dds = cp - cp.cummax()
        fdd = go.Figure(go.Scatter(x=ss2['date'], y=dds.values, fill='tozeroy',
            line=dict(color='#9B1C1C', width=1.5), fillcolor='rgba(155,28,28,0.15)',
            hovertemplate='%{x|%d %b %Y}<br>DD: %{y:.2f}<extra></extra>'))
        fdd.update_layout(height=310, plot_bgcolor='#0d1117', paper_bgcolor='#0d1117', font=dict(color='#e6edf3'),
            margin=dict(l=0,r=0,t=5,b=50), yaxis_title='Drawdown (pts)')
        st.plotly_chart(fdd, use_container_width=True)

    st.divider()

    # League breakdown
    st.subheader("League Breakdown")
    lg = sb.groupby('league').agg(
        Bets=('pl','count'), PL=('pl','sum'), Won=('won','sum'), AvgOdds=('odds','mean')
    ).reset_index()
    lg['ROI%'] = lg['PL']/lg['Bets']*100; lg['SR%'] = lg['Won']/lg['Bets']*100

    def ldd(l):
        s2 = sb[sb['league'] == l].sort_values('date'); c2 = s2['pl'].cumsum()
        return float((c2 - c2.cummax()).min()) if len(c2) else 0

    lg['MaxDD'] = lg['league'].apply(ldd)
    lg = lg.rename(columns={'league':'League'})[['League','Bets','PL','ROI%','SR%','AvgOdds','MaxDD']].sort_values('ROI%', ascending=False)

    def rc(v):
        if v >= 30: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
        if v >= 15: return 'background-color:#D4EEF2;color:#0B5E6B;font-weight:bold'
        if v >= 10: return 'background-color:#DCE9F7;color:#1A5C9E'
        if v >  0:  return ''
        return 'background-color:#FDE8E8;color:#9B1C1C'

    ct, cb = st.columns([2, 3])
    with ct:
        st.dataframe(
            lg.style.format({'PL':'{:+.2f}','ROI%':'{:+.2f}%','SR%':'{:.2f}%',
                             'AvgOdds':'{:.2f}','MaxDD':'{:.2f}'})
              .map(rc, subset=['ROI%']),
            use_container_width=True, hide_index=True)
    with cb:
        flg = go.Figure(go.Bar(x=lg['League'], y=lg['ROI%'].round(2),
            marker_color=[col if v > 0 else '#9B1C1C' for v in lg['ROI%']],
            text=[f"{r:+.2f}%" for r in lg['ROI%']], textposition='outside'))
        flg.update_layout(height=290, template='plotly_white',
            margin=dict(l=0,r=0,t=10,b=80),
            xaxis_tickangle=-35, yaxis_title="ROI %", showlegend=False)
        st.plotly_chart(flg, use_container_width=True)

    st.divider()

    # Season heatmap
    st.subheader("Season-by-Season Heatmap")
    def sl(d):
        if pd.isna(d): return 'Unknown'
        y = d.year; m = d.month
        return f"{y}-{y+1}" if m >= 7 else f"{y-1}-{y}"

    sb2 = sb.copy(); sb2['sl'] = sb2['date'].apply(sl)
    sg = sb2.groupby(['sl','league']).agg(Bets=('pl','count'),PL=('pl','sum')).reset_index()
    sg['ROI%'] = sg['PL']/sg['Bets']*100
    pv = sg.rename(columns={'league':'League','sl':'Season'}).pivot_table(
        index='League', columns='Season', values='ROI%', aggfunc='first')

    def hc(v):
        if pd.isna(v): return 'background-color:#F5F5F5;color:#BBB'
        if v >= 30: return 'background-color:#D6EFE1;color:#155C2E;font-weight:bold'
        if v >= 10: return 'background-color:#DCE9F7;color:#1A5C9E'
        if v >  0:  return 'background-color:#FEF3C7;color:#92580B'
        return 'background-color:#FDE8E8;color:#9B1C1C'

    st.dataframe(pv.style.format('{:+.2f}%', na_rep='—').map(hc),
                 use_container_width=True)

    st.divider()

    # xG distribution
    st.subheader("xG Distribution")
    lbl = "6G FH xGTot (Col J)" if sc == "FHG Lay U0.5" else "6G Match xG (Col N)"
    fx = px.histogram(sb, x='xg_value', nbins=40, color='system',
                      color_discrete_map=MKT, labels={'xg_value': lbl})
    fx.update_layout(height=270, template='plotly_white',
        margin=dict(l=0,r=0,t=10,b=10), showlegend=False)
    st.plotly_chart(fx, use_container_width=True)

# ── MONTE CARLO TAB ───────────────────────────────────────────────────────────
with tab_mc:

    MC_DATA = {"Lay U1.5":{"meta":{"mu":0.2359,"sigma":1.65,"sr":0.8279,"avg_win":0.968,"avg_loss":-3.286,"n_hist":895},"horizons":{"500":{"pProfit":99.9,"pRuin":0.0,"pRoi10":96.4,"pRoi20":69.9,"ev":118.07,"evSd":36.6,"p5":56.7,"p10":68.2,"p25":94.4,"p50":118.7,"p75":142.8,"p90":163.1,"p95":177.7,"ddMed":-20.76,"ddP95":-36.7,"ddPct":20.8,"runMed":3,"run95":5,"run99":6},"1000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":99.6,"pRoi20":75.1,"ev":235.25,"evSd":51.9,"p5":148.3,"p10":167.4,"p25":200.3,"p50":236.3,"p75":270.7,"p90":299.1,"p95":320.0,"ddMed":-25.06,"ddP95":-41.5,"ddPct":25.1,"runMed":4,"run95":5,"run99":6},"2000":{"pProfit":100.0,"pRuin":0.01,"pRoi10":100.0,"pRoi20":82.9,"ev":470.72,"evSd":73.8,"p5":347.9,"p10":378.3,"p25":421.2,"p50":471.1,"p75":520.7,"p90":557.9,"p95":591.3,"ddMed":-29.69,"ddP95":-47.1,"ddPct":29.7,"runMed":4,"run95":5,"run99":6},"5000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":99.6,"ev":1180.09,"evSd":117.2,"p5":983.4,"p10":1028.7,"p25":1100.5,"p50":1178.3,"p75":1258.2,"p90":1330.1,"p95":1374.8,"ddMed":-35.68,"ddP95":-55.2,"ddPct":35.7,"runMed":4,"run95":6,"run99":7},"10000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":100.0,"ev":2354.81,"evSd":165.4,"p5":2079.2,"p10":2144.8,"p25":2240.6,"p50":2354.7,"p75":2468.2,"p90":2563.5,"p95":2626.1,"ddMed":-40.0,"ddP95":-60.8,"ddPct":40.0,"runMed":5,"run95":6,"run99":7}}},"Back O2.5":{"meta":{"mu":0.1626,"sigma":0.8805,"sr":0.6444,"avg_win":0.804,"avg_loss":-1.0,"n_hist":540},"horizons":{"500":{"pProfit":99.99,"pRuin":0.0,"pRoi10":94.7,"pRoi20":17.4,"ev":81.29,"evSd":19.6,"p5":49.3,"p10":56.8,"p25":68.5,"p50":81.7,"p75":94.6,"p90":107.1,"p95":114.4,"ddMed":-8.95,"ddP95":-15.0,"ddPct":8.9,"runMed":5,"run95":8,"run99":9},"1000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":98.9,"pRoi20":9.2,"ev":162.4,"evSd":27.7,"p5":117.5,"p10":127.8,"p25":144.1,"p50":162.8,"p75":181.2,"p90":198.2,"p95":208.5,"ddMed":-10.58,"ddP95":-16.6,"ddPct":10.6,"runMed":6,"run95":9,"run99":10},"2000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":99.9,"pRoi20":2.8,"ev":326.38,"evSd":39.6,"p5":260.5,"p10":275.0,"p25":298.6,"p50":325.8,"p75":352.2,"p90":376.1,"p95":390.6,"ddMed":-12.22,"ddP95":-18.5,"ddPct":12.2,"runMed":7,"run95":9,"run99":11},"5000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":61.3,"ev":813.43,"evSd":63.1,"p5":708.4,"p10":733.7,"p25":771.6,"p50":812.9,"p75":854.3,"p90":892.4,"p95":916.2,"ddMed":-14.42,"ddP95":-21.8,"ddPct":14.4,"runMed":8,"run95":10,"run99":12},"10000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":100.0,"ev":1628.2,"evSd":89.4,"p5":1476.2,"p10":1510.5,"p25":1566.3,"p50":1628.2,"p75":1690.1,"p90":1741.8,"p95":1773.5,"ddMed":-16.15,"ddP95":-24.2,"ddPct":16.2,"runMed":8,"run95":11,"run99":13}}},"Lay O3.5":{"meta":{"mu":0.1639,"sigma":1.4579,"sr":0.7431,"avg_win":0.98,"avg_loss":-2.196,"n_hist":938},"horizons":{"500":{"pProfit":99.25,"pRuin":0.0,"pRoi10":84.3,"pRoi20":28.5,"ev":82.08,"evSd":32.2,"p5":28.7,"p10":38.5,"p25":60.3,"p50":82.4,"p75":103.5,"p90":123.8,"p95":134.6,"ddMed":-19.87,"ddP95":-35.3,"ddPct":19.8,"runMed":4,"run95":6,"run99":7},"1000":{"pProfit":99.98,"pRuin":0.0,"pRoi10":91.6,"pRoi20":22.2,"ev":163.6,"evSd":46.4,"p5":87.5,"p10":103.6,"p25":132.7,"p50":164.7,"p75":196.0,"p90":222.5,"p95":239.9,"ddMed":-24.23,"ddP95":-41.3,"ddPct":24.1,"runMed":5,"run95":7,"run99":8},"2000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":97.8,"pRoi20":13.6,"ev":327.08,"evSd":65.1,"p5":220.8,"p10":247.2,"p25":283.5,"p50":327.2,"p75":372.0,"p90":409.2,"p95":433.3,"ddMed":-28.81,"ddP95":-46.8,"ddPct":29.0,"runMed":5,"run95":7,"run99":8},"5000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":96.8,"ev":817.89,"evSd":103.4,"p5":647.1,"p10":683.2,"p25":745.8,"p50":818.7,"p75":889.2,"p90":945.3,"p95":985.6,"ddMed":-35.43,"ddP95":-56.1,"ddPct":35.4,"runMed":6,"run95":8,"run99":9},"10000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":100.0,"ev":1639.58,"evSd":145.8,"p5":1398.3,"p10":1449.7,"p25":1542.1,"p50":1638.4,"p75":1736.2,"p90":1820.5,"p95":1877.3,"ddMed":-39.88,"ddP95":-62.1,"ddPct":39.9,"runMed":6,"run95":9,"run99":10}}},"FHG Lay U0.5":{"meta":{"mu":0.2312,"sigma":1.5346,"sr":0.8006,"avg_win":0.98,"avg_loss":-2.775,"n_hist":722},"horizons":{"500":{"pProfit":99.96,"pRuin":0.0,"pRoi10":97.0,"pRoi20":67.9,"ev":115.34,"evSd":34.5,"p5":58.6,"p10":70.1,"p25":92.5,"p50":116.6,"p75":139.4,"p90":160.1,"p95":172.1,"ddMed":-18.61,"ddP95":-32.8,"ddPct":18.7,"runMed":3,"run95":5,"run99":6},"1000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":99.6,"pRoi20":74.6,"ev":231.41,"evSd":48.4,"p5":152.2,"p10":169.1,"p25":199.5,"p50":231.8,"p75":265.0,"p90":294.2,"p95":311.0,"ddMed":-22.49,"ddP95":-36.5,"ddPct":22.5,"runMed":4,"run95":5,"run99":7},"2000":{"pProfit":100.0,"pRuin":0.01,"pRoi10":100.0,"pRoi20":81.4,"ev":461.56,"evSd":69.2,"p5":346.3,"p10":374.1,"p25":415.4,"p50":463.3,"p75":509.4,"p90":547.5,"p95":573.5,"ddMed":-26.46,"ddP95":-41.1,"ddPct":26.3,"runMed":4,"run95":6,"run99":7},"5000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":99.4,"ev":1156.81,"evSd":110.1,"p5":969.2,"p10":1013.5,"p25":1082.1,"p50":1156.4,"p75":1230.8,"p90":1297.3,"p95":1340.1,"ddMed":-31.69,"ddP95":-48.2,"ddPct":31.7,"runMed":5,"run95":6,"run99":8},"10000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":100.0,"ev":2312.58,"evSd":156.2,"p5":2053.1,"p10":2107.4,"p25":2206.3,"p50":2311.8,"p75":2418.4,"p90":2509.2,"p95":2568.7,"ddMed":-35.69,"ddP95":-53.8,"ddPct":35.7,"runMed":5,"run95":7,"run99":9}}},"Back the Draw":{"meta":{"mu":0.2609,"sigma":1.8416,"sr":0.3227,"avg_win":2.907,"avg_loss":-1.0,"n_hist":629},"horizons":{"500":{"pProfit":99.96,"pRuin":0.0,"pRoi10":97.7,"pRoi20":77.1,"ev":130.88,"evSd":41.1,"p5":64.5,"p10":78.3,"p25":102.9,"p50":131.2,"p75":159.1,"p90":183.7,"p95":199.2,"ddMed":-19.4,"ddP95":-33.0,"ddPct":19.4,"runMed":14,"run95":20,"run99":24},"1000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":99.6,"pRoi20":84.9,"ev":261.14,"evSd":58.9,"p5":163.5,"p10":184.7,"p25":221.1,"p50":260.4,"p75":299.8,"p90":334.2,"p95":356.5,"ddMed":-23.21,"ddP95":-38.1,"ddPct":23.4,"runMed":15,"run95":22,"run99":26},"2000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":93.1,"ev":522.52,"evSd":82.2,"p5":387.0,"p10":416.4,"p25":466.1,"p50":521.2,"p75":576.9,"p90":623.7,"p95":656.2,"ddMed":-27.28,"ddP95":-41.7,"ddPct":27.2,"runMed":17,"run95":24,"run99":29},"5000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":99.8,"ev":1305.18,"evSd":131.4,"p5":1086.3,"p10":1134.2,"p25":1214.8,"p50":1304.7,"p75":1394.6,"p90":1471.3,"p95":1519.8,"ddMed":-32.26,"ddP95":-49.1,"ddPct":32.3,"runMed":19,"run95":27,"run99":32},"10000":{"pProfit":100.0,"pRuin":0.0,"pRoi10":100.0,"pRoi20":100.0,"ev":2604.77,"evSd":185.8,"p5":2293.4,"p10":2366.1,"p25":2479.3,"p50":2603.8,"p75":2729.1,"p90":2837.2,"p95":2912.6,"ddMed":-36.81,"ddP95":-54.6,"ddPct":36.8,"runMed":21,"run95":30,"run99":36}}}}

    st.caption("Bootstrap simulations (10k for ≤2,000 bets · 5k for 5,000 bets · 2k for 10,000 bets) · flat 1-unit staking · 100-unit starting bank · resampled from full historical P/L distribution")

    mc_sys = sc
    mc_hor = st.radio("Horizon", [500, 1000, 2000, 5000, 10000],
                      format_func=lambda x: f"{x:,} bets", horizontal=True, key="mc_hor")

    d    = MC_DATA[mc_sys]["horizons"][str(mc_hor)]
    meta = MC_DATA[mc_sys]["meta"]

    if mc_sys == "Back the Draw":
        st.warning("🧪 Back the Draw is in TEST mode — these simulations are based on historical performance for research purposes.")

    st.divider()

    # ── KPI row 1 ─────────────────────────────────────────────────────────────
    st.subheader("Probability & Expected Value")
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Prob in profit",  f"{d['pProfit']:.1f}%",  "of 10,000 sims")
    k2.metric("Ruin probability",f"{d['pRuin']:.2f}%",    "bank hits zero")
    k3.metric("Prob ROI ≥ 10%", f"{d['pRoi10']:.1f}%",   "of sims")
    k4.metric("Prob ROI ≥ 20%", f"{d['pRoi20']:.1f}%",   "of sims")
    k5.metric("Expected P/L",   f"+{d['ev']:.1f} pts",    f"± {d['evSd']:.1f} σ")

    # ── KPI row 2 ─────────────────────────────────────────────────────────────
    st.subheader("Drawdown & Losing Runs")
    d1,d2,d3,d4 = st.columns(4)
    d1.metric("Max DD — median",    f"{d['ddMed']:.1f} pts",  f"{d['ddPct']:.1f}% of 100u bank")
    d2.metric("Max DD — worst 5%",  f"{d['ddP95']:.1f} pts",  "stress scenario")
    d3.metric("Losing run — median",f"{d['runMed']} bets",     f"95th: {d['run95']}  ·  99th: {d['run99']}")
    d4.metric("Historical basis",   f"{meta['n_hist']:,} bets",f"SR {meta['sr']*100:.1f}%  ·  avg {meta['mu']:+.4f} pts/bet")

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    ch_left, ch_right = st.columns(2)

    with ch_left:
        st.subheader("P/L distribution — percentiles")
        pcts  = ["5th","10th","25th","Median","75th","90th","95th"]
        pvals = [d["p5"],d["p10"],d["p25"],d["p50"],d["p75"],d["p90"],d["p95"]]
        fig_dist = go.Figure(go.Bar(
            x=pcts, y=pvals,
            marker_color=[col if v >= 0 else "#C0392B" for v in pvals],
            text=[f"{v:+.1f}" for v in pvals],
            textposition="outside",
        ))
        fig_dist.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), margin=dict(l=0,r=0,t=10,b=40),
            yaxis=dict(title="P/L (pts)", gridcolor="rgba(48,54,61,0.4)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            showlegend=False,
        )
        fig_dist.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.25)")
        st.plotly_chart(fig_dist, use_container_width=True)

    with ch_right:
        st.subheader("Probability summary")
        prob_labels = ["Any profit","ROI ≥ 10%","ROI ≥ 20%","Bank survives"]
        prob_vals   = [d["pProfit"], d["pRoi10"], d["pRoi20"], 100 - d["pRuin"]]
        prob_cols   = [col, col, col, "#16A34A"]
        fig_prob = go.Figure(go.Bar(
            x=prob_labels, y=prob_vals,
            marker_color=prob_cols,
            text=[f"{v:.1f}%" for v in prob_vals],
            textposition="outside",
        ))
        fig_prob.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), margin=dict(l=0,r=0,t=10,b=40),
            yaxis=dict(title="% of simulations", range=[0,105], gridcolor="rgba(48,54,61,0.4)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            showlegend=False,
        )
        st.plotly_chart(fig_prob, use_container_width=True)

    ch_left2, ch_right2 = st.columns(2)

    with ch_left2:
        st.subheader("Max drawdown scenarios")
        dd_labels = ["Typical (median)", "Bad (worst 10%)", "Very bad (worst 5%)"]
        dd_vals   = [d["ddMed"], round((d["ddMed"]+d["ddP95"])/2, 2), d["ddP95"]]
        dd_cols   = ["#16A34A","#B35C00","#C0392B"]
        fig_dd = go.Figure(go.Bar(
            x=dd_labels, y=dd_vals,
            marker_color=dd_cols,
            text=[f"{v:.1f} pts" for v in dd_vals],
            textposition="outside",
        ))
        fig_dd.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), margin=dict(l=0,r=0,t=10,b=40),
            yaxis=dict(title="Drawdown (pts)", gridcolor="rgba(48,54,61,0.4)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            showlegend=False,
        )
        fig_dd.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.25)")
        st.plotly_chart(fig_dd, use_container_width=True)

    with ch_right2:
        st.subheader("Longest losing run distribution")
        run_90 = round((d["runMed"] + d["run95"]) / 2)
        run_labels = ["Median","~90th pct","95th pct","99th pct"]
        run_vals   = [d["runMed"], run_90, d["run95"], d["run99"]]
        run_cols   = ["#16A34A","#0B5E6B","#B35C00","#C0392B"]
        fig_run = go.Figure(go.Bar(
            x=run_labels, y=run_vals,
            marker_color=run_cols,
            text=[f"{v} bets" for v in run_vals],
            textposition="outside",
        ))
        fig_run.update_layout(
            height=300, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#e6edf3"), margin=dict(l=0,r=0,t=10,b=40),
            yaxis=dict(title="Consecutive losses", gridcolor="rgba(48,54,61,0.4)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            showlegend=False,
        )
        st.plotly_chart(fig_run, use_container_width=True)

