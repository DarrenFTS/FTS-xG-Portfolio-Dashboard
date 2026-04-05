"""Page 2: Daily Bet Selector"""
import streamlit as st
import pandas as pd
import os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from systems.all_systems import load_fixture_file, scan_all_systems, signals_to_dataframe
from models.enhanced_daily_selector import export_to_excel

st.set_page_config(page_title="Daily Selector", page_icon="🎯", layout="wide")
st.markdown("""<style>
[data-testid="stSidebar"]{background:#0D2B55;}
[data-testid="stSidebar"]*{color:white!important;}
</style>""", unsafe_allow_html=True)

MKT_C={"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00"}

st.title("🎯 Daily Bet Selector")
st.markdown("Upload the **FTS Advanced PreMatch Excel** file to generate today's qualifying selections.")

uploaded = st.file_uploader("Upload FTS PreMatch file (Excel)", type=['xlsx','xls'])

if uploaded:
    with st.spinner("Running all systems..."):
        try:
            tmp=f"/tmp/fixtures_{date.today()}.xlsx"
            with open(tmp,'wb') as f: f.write(uploaded.read())
            fixtures = load_fixture_file(tmp)
            signals  = scan_all_systems(fixtures)
            df_sel   = signals_to_dataframe(signals)
            fd = fixtures['date'].dropna().iloc[0] if len(fixtures) else None
            date_str = fd.strftime('%A %d %B %Y') if fd is not None else str(date.today())
        except Exception as e:
            st.error(f"Error: {e}"); st.stop()

    st.success(f"✅ {len(fixtures)} fixtures loaded — **{date_str}**")

    from collections import Counter
    mc=Counter(s.system for s in signals)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Selections",    len(signals))
    c2.metric("Lay U1.5",      mc.get('Lay U1.5',0))
    c3.metric("Back O2.5",     mc.get('Back O2.5',0))
    c4.metric("Lay O3.5",      mc.get('Lay O3.5',0))
    c5.metric("FHG Lay U0.5",  mc.get('FHG Lay U0.5',0))
    st.divider()

    if not df_sel.empty:
        st.subheader("📋 Qualifying Selections")
        fc=st.columns(2)
        with fc[0]: sf=st.multiselect("Market",sorted(df_sel['Market'].unique()),default=sorted(df_sel['Market'].unique()))
        with fc[1]: lf=st.multiselect("League",sorted(df_sel['League'].unique()),default=sorted(df_sel['League'].unique()))

        show=df_sel[df_sel['Market'].isin(sf)&df_sel['League'].isin(lf)].copy()
        cols=['Date','Time','League','Home','Away','Market','6G xG','Rule','Odds','Hist ROI']
        show=show[[c for c in cols if c in show.columns]]

        fmt={}
        if '6G xG' in show.columns: fmt['6G xG']='{:.2f}'
        if 'Odds'  in show.columns: fmt['Odds'] ='{:.2f}'

        def sm(v):
            return {"Lay U1.5":"background-color:#D4EEF2;color:#0B5E6B;font-weight:bold",
                    "Back O2.5":"background-color:#D6EFE1;color:#217346;font-weight:bold",
                    "Lay O3.5":"background-color:#EBE0F0;color:#4A235A;font-weight:bold",
                    "FHG Lay U0.5":"background-color:#FFF0DC;color:#B35C00;font-weight:bold"}.get(v,'')
        def sr2(v):
            try:
                r=float(str(v).replace('%','').replace('+',''))
                return 'color:#155C2E;font-weight:bold' if r>=20 else ('color:#0B5E6B;font-weight:bold' if r>=10 else 'color:#1A5C9E')
            except: return ''

        st.dataframe(show.style.format(fmt).map(sm,subset=['Market']).map(sr2,subset=['Hist ROI']),
                     use_container_width=True,hide_index=True,height=min(580,60+len(show)*35))
        st.divider()

        xp=f"/tmp/FTS_{date.today().strftime('%Y%m%d')}.xlsx"
        export_to_excel(signals,xp,date_str)
        with open(xp,'rb') as f2: xb=f2.read()

        cd,ci=st.columns([1,3])
        with cd:
            st.download_button("⬇️ Download Excel",xb,
                file_name=f"FTS_Selections_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",use_container_width=True)
        with ci:
            st.info("Colour-coded Excel with date, time, league, home, away, market, xG, rule, odds, hist ROI — plus result columns with running totals.")
    else:
        st.warning("⚠️ No qualifying selections in today's fixtures.")
        lgs=sorted(fixtures['league'].dropna().unique()) if 'league' in fixtures.columns else []
        if lgs: st.markdown(f"**Leagues in file:** {', '.join(lgs)}")

    with st.expander("📖 System Rules Reference"):
        st.markdown("""
| System | xG Col | Leagues & Thresholds | Odds |
|--------|--------|---------------------|------|
| **Lay U1.5** | 6G Match xG | German BL2 ≥4.10 · Danish SL ≥3.65 · Belgian PL ≥3.75 · Scottish Prem ≥3.25 · French L1 ≥4.05 · Swedish AS ≥2.20 | Lay 1.00–6.00 |
| **Back O2.5** | 6G Match xG | Eng Champ ≥4.25 · Spanish La Liga ≥3.70 · Portuguese PL ≥3.55 · EPL ≥4.30 · Polish EK ≥3.95 · Norwegian TL ≥3.60 | Back 1.50–2.50 |
| **Lay O3.5** | 6G Match xG | Spanish La Liga ≤1.50 · German BL2 ≤2.00 · Belgian PL ≤2.00 · Irish PL ≤2.85 · Dutch Eredivisie ≤2.05 · Italian SA ≤1.40 · Spanish Segunda ≥3.60 · Austrian BL ≥2.35 · Eng Champ ≥3.85 · Dutch Eerste ≥4.70 | Lay 1.00–6.00 |
| **FHG Lay U0.5** | 6G FH xG | Polish EK ≥1.90 · Belgian PL ≥1.95 · Portuguese PL ≥2.20 · Danish SL ≥1.95 · German BL ≥2.40 · Dutch Eredivisie ≥2.00 · Eng Champ ≥2.35 · Scottish Prem ≥0.85 · Swiss SL ≥2.10 · Eng L1 ≥1.50 | Lay 1.00–6.00 |
        """)
