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

    # ── Simulation engine ─────────────────────────────────────────────────────
    @st.cache_data(show_spinner=False)
    def run_mc(sys_name: str, horizon: int, n_sims: int = 5000,
               bank: float = 100.0, ruin_threshold: float = 20.0, seed: int = 42):
        import json as _json, os as _os
        base = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        path = _os.path.join(base, "data", "portfolio_master_sheet.json")
        records = _json.load(open(path))
        df_mc = pd.DataFrame(records)
        sub = df_mc[df_mc["system"] == sys_name]["pl"].values.astype(float)
        if len(sub) < 10:
            return None

        win_rate  = float((sub > 0).mean())
        avg_bet   = float(sub.mean())

        np.random.seed(seed)
        bets_arr  = np.random.choice(sub, size=(n_sims, horizon), replace=True)
        cum       = np.cumsum(bets_arr, axis=1)
        bank_path = bank + cum
        terminal  = cum[:, -1]
        pk        = np.maximum.accumulate(cum, axis=1)
        dd_all    = (cum - pk).min(axis=1)

        pct_ruin   = (bank_path < ruin_threshold).any(axis=1).mean() * 100
        pct_profit = (terminal > 0).mean() * 100

        # Losing runs (sample 1000)
        idx  = np.random.choice(n_sims, min(1000, n_sims), replace=False)
        llrs = []
        for i in idx:
            mx = cr = 0
            for v in bets_arr[i]:
                if v < 0: cr += 1; mx = max(mx, cr)
                else: cr = 0
            llrs.append(mx)
        llrs = np.array(llrs)

        # P&L histogram (dynamic range)
        t_min = max(-200, int(np.floor(np.percentile(terminal, 1) / 25) * 25))
        t_max = min(1500, int(np.ceil(np.percentile(terminal, 99) / 25) * 25) + 25)
        edges = list(range(t_min, t_max + 1, 25))
        hist, _ = np.histogram(terminal, bins=edges)
        hist_pct = (hist / n_sims * 100).tolist()

        # DD histogram
        dd_min   = max(-200, int(np.floor(np.percentile(dd_all, 1) / 5) * 5))
        dd_edges = list(range(dd_min, 5, 2))
        dd_hist, _ = np.histogram(dd_all, bins=dd_edges)
        dd_pct = (dd_hist / n_sims * 100).tolist()

        return {
            "n_sims":    n_sims, "horizon": horizon, "bank": bank,
            "win_rate":  round(win_rate * 100, 1),
            "avg_bet":   round(avg_bet, 4),
            "n_hist":    len(sub),
            "pl_mean":   round(float(terminal.mean()), 2),
            "pl_p5":     round(float(np.percentile(terminal,  5)), 2),
            "pl_p25":    round(float(np.percentile(terminal, 25)), 2),
            "pl_p50":    round(float(np.percentile(terminal, 50)), 2),
            "pl_p75":    round(float(np.percentile(terminal, 75)), 2),
            "pl_p95":    round(float(np.percentile(terminal, 95)), 2),
            "pct_profit": round(pct_profit, 1),
            "pct_ruin":  round(pct_ruin, 2),
            "dd_med":    round(float(np.median(dd_all)), 2),
            "dd_p5":     round(float(np.percentile(dd_all, 5)), 2),
            "dd_pct_med": round(float(abs(np.median(dd_all)) / bank * 100), 1),
            "dd_pct_p5":  round(float(abs(np.percentile(dd_all, 5)) / bank * 100), 1),
            "llr_med":   int(np.median(llrs)),
            "llr_p75":   int(np.percentile(llrs, 75)),
            "llr_p90":   int(np.percentile(llrs, 90)),
            "llr_p95":   int(np.percentile(llrs, 95)),
            "llr_max":   int(llrs.max()),
            "hist_edges": edges[:-1],
            "hist_pct":  [round(v, 2) for v in hist_pct],
            "dd_edges":  dd_edges[:-1],
            "dd_pct":    [round(v, 2) for v in dd_pct],
            "cum_paths": cum[:50],
        }

    # ── Header banner ─────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:#0d1f0f;border:1px solid #1a4a20;border-left:3px solid #2ecc71;'
        'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:0.85rem;color:#81c784">'
        'Bootstrap resampling from historical bet returns &nbsp;·&nbsp; '
        '5,000 simulations per run &nbsp;·&nbsp; Starting bank: <strong style="color:#fff">100u</strong>'
        ' &nbsp;·&nbsp; Ruin threshold: bank falls below <strong style="color:#fff">20u</strong> (80% drawdown)'
        '</div>', unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
    with ctrl1:
        mc_sys = sc   # inherits system radio from sidebar
        st.info(f"System: **{mc_sys}**  ·  selected in sidebar")
    with ctrl2:
        mc_hor = st.select_slider(
            "Bet horizon",
            options=[250, 500, 750, 1000, 1500, 2000, 5000, 10000],
            value=1000,
            format_func=lambda x: f"{x:,} bets",
            key="mc_slider"
        )
    with ctrl3:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        run_btn = st.button("▶  Run simulation", type="primary",
                            use_container_width=True, key="mc_run")
        st.markdown("</div>", unsafe_allow_html=True)

    if mc_sys == "Back the Draw":
        st.warning("🧪 Back the Draw is in TEST mode — simulations are for research purposes only.")

    # ── Run / retrieve ────────────────────────────────────────────────────────
    _key = f"mc_{mc_sys}_{mc_hor}"
    if run_btn or _key not in st.session_state:
        with st.spinner(f"Running 5,000 simulations for {mc_sys} over {mc_hor:,} bets…"):
            st.session_state[_key] = run_mc(mc_sys, mc_hor)

    R = st.session_state.get(_key)
    if R is None:
        st.error("Insufficient data."); st.stop()

    _col = MKT[mc_sys]

    def _rgb(hex_col):
        return int(hex_col[1:3],16), int(hex_col[3:5],16), int(hex_col[5:7],16)
    r0, g0, b0 = _rgb(_col)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Historical bets", f"{R['n_hist']:,}",     delta=f"Win rate {R['win_rate']}%")
    k2.metric("Expected P/L",    f"+{R['pl_mean']:.1f}u",delta=f"Median {R['pl_p50']:+.1f}u")
    k3.metric("% in profit",     f"{R['pct_profit']:.1f}%", delta=f"of {R['n_sims']:,} sims")
    k4.metric("Ruin probability",f"{R['pct_ruin']:.2f}%",   delta="bank < 20u ever")
    k5.metric("DD median",       f"{R['dd_med']:.1f}u",     delta=f"{R['dd_pct_med']:.1f}% of bank")
    k6.metric("DD worst 5%",     f"{R['dd_p5']:.1f}u",      delta=f"{R['dd_pct_p5']:.1f}% of bank")

    st.divider()

    # ── Row 1: Fan chart + P&L histogram ─────────────────────────────────────
    col_fan, col_dist = st.columns([3, 2])

    with col_fan:
        st.subheader("Simulation paths — first 50 runs")
        all_paths = R["cum_paths"]
        x_ax  = list(range(1, mc_hor + 1))
        p5p   = np.percentile(all_paths, 5,  axis=0)
        p25p  = np.percentile(all_paths, 25, axis=0)
        p50p  = np.percentile(all_paths, 50, axis=0)
        p75p  = np.percentile(all_paths, 75, axis=0)
        p95p  = np.percentile(all_paths, 95, axis=0)

        fig_fan = go.Figure()
        for path in all_paths:
            fig_fan.add_trace(go.Scatter(
                x=x_ax, y=path.tolist(), mode="lines",
                line=dict(width=0.5, color=_col), opacity=0.18,
                showlegend=False, hoverinfo="skip"))
        # Shaded band P5–P95
        fig_fan.add_trace(go.Scatter(
            x=x_ax + x_ax[::-1],
            y=p95p.tolist() + p5p.tolist()[::-1],
            fill="toself",
            fillcolor=f"rgba({r0},{g0},{b0},0.10)",
            line=dict(width=0), showlegend=False, hoverinfo="skip"))
        # Median
        fig_fan.add_trace(go.Scatter(
            x=x_ax, y=p50p.tolist(), mode="lines",
            line=dict(width=2.5, color=_col), name="Median path"))
        # P5
        fig_fan.add_trace(go.Scatter(
            x=x_ax, y=p5p.tolist(), mode="lines",
            line=dict(width=1.2, color="#e74c3c", dash="dash"), name="P5 — worst 5%"))
        # P95
        fig_fan.add_trace(go.Scatter(
            x=x_ax, y=p95p.tolist(), mode="lines",
            line=dict(width=1.2, color=_col, dash="dash"), name="P95 — best 5%"))
        fig_fan.add_hline(y=0, line_width=1, line_dash="dot", line_color="#555")
        fig_fan.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=320,
            font=dict(color="#e6edf3", size=11),
            xaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)", title="Bets"),
            yaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)",
                       title="Cumulative P/L (u)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.18, font=dict(size=10)),
        )
        st.plotly_chart(fig_fan, use_container_width=True)

    with col_dist:
        st.subheader("P/L distribution")
        edges = R["hist_edges"]
        pcts  = R["hist_pct"]
        bar_colors = ["#e74c3c" if e < 0 else "#f39c12" if e < 50 else _col for e in edges]
        fig_dist = go.Figure(go.Bar(
            x=[f"{e:+d}" for e in edges], y=pcts,
            marker_color=bar_colors, marker_line_width=0))
        mean_idx = min(range(len(edges)), key=lambda i: abs(edges[i] - R["pl_mean"]))
        fig_dist.add_vline(
            x=mean_idx, line_width=2, line_dash="dash", line_color=_col,
            annotation_text=f"Mean {R['pl_mean']:+.0f}u",
            annotation_position="top right", annotation_font_color=_col)
        fig_dist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=320,
            font=dict(color="#e6edf3", size=10),
            xaxis=dict(showgrid=False, title="Terminal P/L (u)",
                       tickmode="array",
                       tickvals=list(range(0, len(edges), 4)),
                       ticktext=[f"{edges[i]:+d}" for i in range(0, len(edges), 4)]),
            yaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)",
                       title="% of simulations"),
            bargap=0.05)
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Row 2: Drawdown histogram + Percentile table ──────────────────────────
    col_dd, col_pctl = st.columns([3, 2])

    with col_dd:
        st.subheader("Drawdown distribution")
        dd_edges = R["dd_edges"]
        dd_pct   = R["dd_pct"]
        dd_colors = ["#e74c3c" if e < -30 else "#f39c12" if e < -15 else "#2ecc71"
                     for e in dd_edges]
        fig_dd = go.Figure(go.Bar(
            x=[f"{e}" for e in dd_edges], y=dd_pct,
            marker_color=dd_colors, marker_line_width=0))
        med_idx = min(range(len(dd_edges)), key=lambda i: abs(dd_edges[i] - R["dd_med"]))
        fig_dd.add_vline(
            x=med_idx, line_width=2, line_dash="dash", line_color="#f39c12",
            annotation_text=f"Median {R['dd_med']:.1f}u",
            annotation_position="top right", annotation_font_color="#f39c12")
        fig_dd.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=280,
            font=dict(color="#e6edf3", size=10),
            xaxis=dict(showgrid=False, title="Max drawdown from peak (u)",
                       tickmode="array",
                       tickvals=list(range(0, len(dd_edges), 5)),
                       ticktext=[f"{dd_edges[i]}" for i in range(0, len(dd_edges), 5)]),
            yaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)",
                       title="% of simulations"),
            bargap=0.05)
        st.plotly_chart(fig_dd, use_container_width=True)

    with col_pctl:
        st.subheader("P/L percentiles")
        pctl_df = pd.DataFrame([
            {"Percentile": "5th  — worst 5%",  "P/L": f"{R['pl_p5']:+.1f}u",
             "vs Bank": f"{R['pl_p5']/100*100:+.1f}%"},
            {"Percentile": "25th",              "P/L": f"{R['pl_p25']:+.1f}u",
             "vs Bank": f"{R['pl_p25']/100*100:+.1f}%"},
            {"Percentile": "50th — median",     "P/L": f"{R['pl_p50']:+.1f}u",
             "vs Bank": f"{R['pl_p50']/100*100:+.1f}%"},
            {"Percentile": "75th",              "P/L": f"{R['pl_p75']:+.1f}u",
             "vs Bank": f"{R['pl_p75']/100*100:+.1f}%"},
            {"Percentile": "95th — best 5%",    "P/L": f"{R['pl_p95']:+.1f}u",
             "vs Bank": f"{R['pl_p95']/100*100:+.1f}%"},
            {"Percentile": "Mean",              "P/L": f"{R['pl_mean']:+.1f}u",
             "vs Bank": f"{R['pl_mean']/100*100:+.1f}%"},
        ])
        st.dataframe(pctl_df, use_container_width=True, hide_index=True, height=240)
        ruin_col = "#2ecc71" if R["pct_ruin"] <= 0.01 else "#f39c12" if R["pct_ruin"] <= 1 else "#e74c3c"
        st.markdown(
            f'<div style="background:#0d1f0f;border:1px solid #1a4a20;border-left:3px solid '
            f'{ruin_col};border-radius:6px;padding:10px 14px;font-size:0.82rem;'
            f'color:#81c784;margin-top:8px">'
            f'<strong style="color:#fff">Ruin probability:</strong> {R["pct_ruin"]:.2f}%'
            f' &nbsp;|&nbsp; '
            f'<strong style="color:#fff">% in profit:</strong> {R["pct_profit"]:.1f}%'
            f'</div>', unsafe_allow_html=True)

    st.divider()

    # ── Row 3: Losing run analysis ────────────────────────────────────────────
    st.subheader("Longest losing run analysis")
    st.markdown(
        f'<div style="font-size:0.82rem;color:#81c784;margin-bottom:12px">'
        f'How many consecutive losing bets should you expect over {mc_hor:,} bets? '
        f'Figures below show the distribution across 1,000 simulated sequences. '
        f'Plan your bank size and staking to withstand the 95th percentile run without panic.</div>',
        unsafe_allow_html=True)

    llr_cols = st.columns(5)
    llr_data = [
        ("Median",     R["llr_med"],  "#2ecc71"),
        ("75th pct — 1 in 4", R["llr_p75"],  "#2ecc71" if R["llr_p75"] < 8  else "#f39c12"),
        ("90th pct — 1 in 10",R["llr_p90"],  "#2ecc71" if R["llr_p90"] < 12 else "#f39c12"),
        ("95th pct — 1 in 20",R["llr_p95"],  "#f39c12" if R["llr_p95"] < 20 else "#e74c3c"),
        ("Worst seen", R["llr_max"],  "#e74c3c"),
    ]
    for lcol, (label, val, lcolor) in zip(llr_cols, llr_data):
        lcol.markdown(
            f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;'
            f'padding:14px 10px;text-align:center">'
            f'<div style="font-size:30px;font-weight:500;color:{lcolor}">{val}</div>'
            f'<div style="font-size:11px;color:#8b949e;margin-top:4px">{label}</div>'
            f'</div>', unsafe_allow_html=True)

    # ── Row 4: All-system comparison ──────────────────────────────────────────
    st.divider()
    with st.expander("📊  Compare all systems at selected horizon", expanded=False):
        st.markdown(f"Running comparison across all 5 systems at **{mc_hor:,} bets**…")
        cmp_rows = []
        prog = st.progress(0)
        sys_list = list(MKT.keys())
        status_map = {"Back the Draw": "🧪 TEST"}
        for i, sn in enumerate(sys_list):
            r2 = run_mc(sn, mc_hor)
            prog.progress((i + 1) / len(sys_list))
            if r2:
                cmp_rows.append({
                    "System":      sn,
                    "Status":      status_map.get(sn, "🟢 LIVE"),
                    "Win rate":    f"{r2['win_rate']:.1f}%",
                    "Exp P/L":     f"{r2['pl_mean']:+.1f}u",
                    "Median P/L":  f"{r2['pl_p50']:+.1f}u",
                    "P5 P/L":      f"{r2['pl_p5']:+.1f}u",
                    "P95 P/L":     f"{r2['pl_p95']:+.1f}u",
                    "% profit":    f"{r2['pct_profit']:.1f}%",
                    "Ruin %":      f"{r2['pct_ruin']:.2f}%",
                    "DD median":   f"{r2['dd_med']:.1f}u",
                    "DD worst 5%": f"{r2['dd_p5']:.1f}u",
                    "LLR median":  r2["llr_med"],
                    "LLR P95":     r2["llr_p95"],
                })
        prog.empty()
        if cmp_rows:
            st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)

