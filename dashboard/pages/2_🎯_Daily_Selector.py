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
