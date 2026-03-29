"""
Page 2: Daily Bet Selector
"""
import streamlit as st
import pandas as pd
import io, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from systems.all_systems import load_fixture_file, scan_all_systems, signals_to_dataframe
from models.enhanced_daily_selector import export_to_excel

st.set_page_config(page_title="Daily Selector", page_icon="🎯", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

MKT_COLOURS_HEX = {
    "Lay U1.5":    "#0B5E6B",
    "Back O2.5":   "#217346",
    "Lay O3.5":    "#4A235A",
    "FHG Lay U0.5":"#B35C00",
}

st.title("🎯 Daily Bet Selector")
st.markdown("Upload the **FTS Advanced PreMatch Excel** file to generate today's qualifying selections.")

uploaded = st.file_uploader("Upload FTS PreMatch file (Excel)", type=['xlsx', 'xls'])

if uploaded:
    with st.spinner("Loading fixtures and running systems..."):
        try:
            tmp_path = f"/tmp/fixtures_{date.today()}.xlsx"
            with open(tmp_path, 'wb') as f:
                f.write(uploaded.read())
            fixtures = load_fixture_file(tmp_path)
            signals  = scan_all_systems(fixtures)
            df_sel   = signals_to_dataframe(signals)
            n_fixtures = len(fixtures)
            fixture_date = fixtures['date'].dropna().iloc[0] if len(fixtures) > 0 else None
            date_str = fixture_date.strftime('%A %d %B %Y') if fixture_date is not None else str(date.today())
        except Exception as e:
            st.error(f"Error loading file: {e}")
            st.stop()

    st.success(f"✅ Loaded **{n_fixtures} fixtures** for **{date_str}**")

    from collections import Counter
    mc = Counter(s.system for s in signals)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Selections", len(signals))
    c2.metric("Lay U1.5",         mc.get('Lay U1.5', 0))
    c3.metric("Back O2.5",        mc.get('Back O2.5', 0))
    c4.metric("Lay O3.5",         mc.get('Lay O3.5', 0))
    c5.metric("FHG Lay U0.5",     mc.get('FHG Lay U0.5', 0))

    st.divider()

    if not df_sel.empty:
        st.subheader("📋 Qualifying Selections")

        filter_cols = st.columns(2)
        with filter_cols[0]:
            system_filter = st.multiselect("Filter by Market",
                options=sorted(df_sel['Market'].unique()),
                default=sorted(df_sel['Market'].unique()))
        with filter_cols[1]:
            league_filter = st.multiselect("Filter by League",
                options=sorted(df_sel['League'].unique()),
                default=sorted(df_sel['League'].unique()))

        display_df = df_sel[
            df_sel['Market'].isin(system_filter) &
            df_sel['League'].isin(league_filter)
        ].copy()

        display_cols = ['Date', 'Time', 'League', 'Home', 'Away', 'Market', '6G xG', 'Rule', 'Odds', 'Hist ROI']
        available_cols = [c for c in display_cols if c in display_df.columns]
        show_df = display_df[available_cols].copy()

        def style_market(val):
            colors = {
                "Lay U1.5":    "background-color:#D4EEF2;color:#0B5E6B;font-weight:bold",
                "Back O2.5":   "background-color:#D6EFE1;color:#217346;font-weight:bold",
                "Lay O3.5":    "background-color:#EBE0F0;color:#4A235A;font-weight:bold",
                "FHG Lay U0.5":"background-color:#FFF0DC;color:#B35C00;font-weight:bold",
            }
            return colors.get(val, '')

        def style_roi(val):
            try:
                r = float(str(val).replace('%', '').replace('+', ''))
                if r >= 20: return 'color:#155C2E;font-weight:bold'
                if r >= 10: return 'color:#0B5E6B;font-weight:bold'
                return 'color:#1A5C9E'
            except:
                return ''

        # Format numeric columns to 2dp before display
        fmt = {}
        if '6G xG' in show_df.columns:
            fmt['6G xG'] = '{:.2f}'
        if 'Odds' in show_df.columns:
            fmt['Odds'] = '{:.2f}'

        styled = show_df.style.format(fmt)\
            .applymap(style_market, subset=['Market'])\
            .applymap(style_roi, subset=['Hist ROI'])

        st.dataframe(styled, use_container_width=True, hide_index=True,
                     height=min(600, 60 + len(display_df) * 35))

        st.divider()
        st.subheader("📥 Download Selections")

        excel_path = f"/tmp/FTS_Selections_{date.today().strftime('%Y%m%d')}.xlsx"
        export_to_excel(signals, excel_path, date_str)
        with open(excel_path, 'rb') as f:
            excel_bytes = f.read()

        col_dl, col_info = st.columns([1, 3])
        with col_dl:
            st.download_button(
                label="⬇️ Download Excel",
                data=excel_bytes,
                file_name=f"FTS_Selections_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary", use_container_width=True,
            )
        with col_info:
            st.info("Colour-coded Excel with date, time, league, home, away, market, "
                    "6G xG, rule, odds, hist ROI — plus result entry columns with live running totals.")
    else:
        st.warning("⚠️ No qualifying selections found in today's fixtures.")
        leagues_in_file = sorted(fixtures['league'].dropna().unique()) if 'league' in fixtures.columns else []
        if leagues_in_file:
            st.markdown(f"**Leagues in this file:** {', '.join(leagues_in_file)}")

    with st.expander("📖 System Rules Reference"):
        st.markdown("""
| System | xG Column | Leagues & Thresholds | Odds Filter |
|--------|-----------|----------------------|-------------|
| **Lay U1.5** | 6G Match xG | German BL2 ≥4.10, Danish SL ≥3.65, Belgian PL ≥3.75, Scottish Prem ≥3.25, French L1 ≥4.05, Swedish AS ≥2.20 | Lay 1.00–6.00 |
| **Back O2.5** | 6G Match xG | Eng Champ ≥4.25, Spanish La Liga ≥3.70, Portuguese PL ≥3.55, EPL ≥4.30, Polish EK ≥3.95, Norwegian TL ≥3.60 | Back 1.50–2.50 |
| **Lay O3.5** | 6G Match xG (no value filter) | Spanish La Liga ≤1.50, German BL2 ≤2.00, Belgian PL ≤2.00, Irish PL ≤2.85, Dutch Eredivisie ≤2.05, Italian SA ≤1.40, Spanish Segunda ≥3.60, Austrian BL ≥2.35, Eng Champ ≥3.85, Dutch Eerste ≥4.70 | Lay 1.00–6.00 |
| **FHG Lay U0.5** | 6G FH xG | Polish EK ≥1.90, Belgian PL ≥1.95, Portuguese PL ≥2.20, Danish SL ≥1.95, German BL ≥2.40, Dutch Eredivisie ≥2.00, Eng Champ ≥2.35, Scottish Prem ≥0.85, Swiss SL ≥2.10, Eng L1 ≥1.50 | Lay 1.00–6.00 |
        """)
