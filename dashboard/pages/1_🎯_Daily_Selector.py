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

MKT_C = {"Lay U1.5":"#0B5E6B","Back O2.5":"#217346","Lay O3.5":"#4A235A","FHG Lay U0.5":"#B35C00","Back the Draw":"#1A5276"}

st.title("🎯 Daily Bet Selector")
st.markdown("Upload today's **FTS Advanced PreMatch Excel** file to generate qualifying selections.")

uploaded = st.file_uploader("Upload FTS PreMatch file (Excel)", type=['xlsx','xls'])

if uploaded:
    with st.spinner("Running all 4 systems..."):
        try:
            tmp = f"/tmp/fixtures_{date.today()}.xlsx"
            with open(tmp, 'wb') as f:
                f.write(uploaded.read())
            fixtures = load_fixture_file(tmp)
            signals  = scan_all_systems(fixtures)
            df_sel   = signals_to_dataframe(signals)
            # Add extra BTD columns from fixtures for Back the Draw signals
            if 'supremacy' in fixtures.columns and 'draw_odds' in fixtures.columns:
                btd_mask = df_sel['Market'] == 'Back the Draw'
                if btd_mask.any():
                    # Match by home/away to get supremacy and draw_odds
                    fix_idx = fixtures.set_index(['home','away'])
                    for idx in df_sel[btd_mask].index:
                        h = df_sel.loc[idx,'Home']; a = df_sel.loc[idx,'Away']
                        try:
                            row = fix_idx.loc[(h,a)]
                            if hasattr(row,'iloc'): row = row.iloc[0]
                            df_sel.loc[idx,'Supremacy'] = round(float(row['supremacy']),3)
                            df_sel.loc[idx,'Draw Odds'] = round(float(row['draw_odds']),3)
                        except Exception:
                            pass
            fd       = fixtures['date'].dropna().iloc[0] if len(fixtures) else None
            date_str = fd.strftime('%A %d %B %Y') if fd is not None else str(date.today())
        except Exception as e:
            st.error(f"Error loading file: {e}"); st.stop()

    st.success(f"✅ {len(fixtures)} fixtures loaded — **{date_str}**")

    from collections import Counter
    mc = Counter(s.system for s in signals)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Selections",    len(signals))
    c2.metric("Lay U1.5",      mc.get('Lay U1.5', 0))
    c3.metric("Back O2.5",     mc.get('Back O2.5', 0))
    c4.metric("Lay O3.5",      mc.get('Lay O3.5', 0))
    c5.metric("FHG Lay U0.5",  mc.get('FHG Lay U0.5', 0))
    c6.metric("Back the Draw", mc.get('Back the Draw', 0))
    st.divider()

    if not df_sel.empty:
        st.subheader("📋 Qualifying Selections")
        fc = st.columns(2)
        with fc[0]:
            sf = st.multiselect("Market", sorted(df_sel['Market'].unique()),
                                default=sorted(df_sel['Market'].unique()))
        with fc[1]:
            lf = st.multiselect("League", sorted(df_sel['League'].unique()),
                                default=sorted(df_sel['League'].unique()))

        show = df_sel[df_sel['Market'].isin(sf) & df_sel['League'].isin(lf)].copy()
        # Reformat date to DD/MM/YYYY and clean time
        if 'Date' in show.columns:
            import re as _re
            def _fmt_d(v):
                s = str(v).strip()
                if _re.match(r'\d{4}-\d{2}-\d{2}', s):
                    parts = s[:10].split('-')
                    return f"{parts[2]}/{parts[1]}/{parts[0]}"
                return s.split(' ')[0].split('T')[0]
            show['Date'] = show['Date'].apply(_fmt_d)
        if 'Time' in show.columns:
            show['Time'] = show['Time'].apply(
                lambda v: str(v).strip().split(':')[:2] and ':'.join(str(v).strip().split(':')[:2]) or str(v))
        cols = ['Date','Time','League','Home','Away','Market','6G xG','Supremacy','Draw Odds','Rule','Odds','Hist ROI']
        show = show[[c for c in cols if c in show.columns]]

        fmt = {}
        if '6G xG' in show.columns: fmt['6G xG'] = '{:.2f}'
        if 'Odds'  in show.columns: fmt['Odds']  = '{:.2f}'

        def sm(v):
            return {"Lay U1.5":      "background-color:#D4EEF2;color:#0B5E6B;font-weight:bold",
                    "Back O2.5":     "background-color:#D6EFE1;color:#217346;font-weight:bold",
                    "Lay O3.5":      "background-color:#EBE0F0;color:#4A235A;font-weight:bold",
                    "FHG Lay U0.5":  "background-color:#FFF0DC;color:#B35C00;font-weight:bold",
                    "Back the Draw": "background-color:#D6EAF8;color:#1A5276;font-weight:bold"}.get(v, '')

        def sr2(v):
            try:
                r = float(str(v).replace('%','').replace('+',''))
                return ('color:#155C2E;font-weight:bold' if r >= 30
                        else 'color:#0B5E6B;font-weight:bold' if r >= 15
                        else 'color:#1A5C9E')
            except:
                return ''

        st.dataframe(
            show.style.format(fmt).map(sm, subset=['Market']).map(sr2, subset=['Hist ROI']),
            use_container_width=True, hide_index=True,
            height=min(580, 60 + len(show) * 35))

        st.divider()
        xp = f"/tmp/FTS_{date.today().strftime('%Y%m%d')}.xlsx"
        export_to_excel(signals, xp, date_str)
        with open(xp, 'rb') as f2:
            xb = f2.read()

        cd, ci = st.columns([1, 3])
        with cd:
            st.download_button("⬇️ Download Excel", xb,
                file_name=f"FTS_Selections_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary", use_container_width=True)
        with ci:
            st.info("Colour-coded Excel with result entry columns and running totals.")
    else:
        st.warning("⚠️ No qualifying selections found in today's fixtures.")
        lgs = sorted(fixtures['league'].dropna().unique()) if 'league' in fixtures.columns else []
        if lgs: st.markdown(f"**Leagues in file:** {', '.join(lgs)}")

    with st.expander("📖 System Rules Reference"):
        st.markdown("""
| System | xG Column (PreMatch) | Leagues & Rules | Odds Filter (PreMatch) |
|--------|---------------------|----------------|----------------------|
| **Lay U1.5** | Match xG — Col AI | Swedish AS ≥4.00 · Polish EK ≥4.25 · German BL2 ≥4.25 · Danish SL ≥3.75 · Belgian PL ≥3.75 · Italian SA ≥4.50 · Scottish Prem ≥2.75 | Lay 1.00–6.00 — Col CK |
| **Back O2.5** | Match xG — Col AI | Irish PL ≥3.75 · Eng Champ ≥4.75 · Polish EK ≥4.25 · Portuguese PL ≥4.50 · Italian SA ≥4.50 · Spanish La Liga ≥3.75 · Dutch Eredivisie ≥4.50 | Back 1.40–2.80 buffer / 1.50–2.50 qualifying — Col CG |
| **Lay O3.5** | Match xG — Col AI | HIGH xG: Spanish Segunda ≥4.25 · Dutch Eerste ≥4.75 · French L1 ≥4.75 · LOW xG: German BL2 ≤1.75 · Spanish La Liga ≤1.25 · Belgian PL ≤2.00 · Eng Champ ≤1.25 | Lay 1.00–6.00 — Col CR |
| **FHG Lay U0.5** | FH xGTot — Col AE | Danish SL ≥2.50 · Polish EK ≥2.25 · Portuguese PL ≥2.25 · French L1 ≥2.50 · Dutch Eredivisie ≥2.00 · German BL ≥2.50 · Eng Champ ≥2.50 | Lay 1.00–6.00 — Col DE |
| **Back the Draw** | Season Supremacy — Col BG | **(1)** 12 eligible leagues **(2)** Supremacy ≥0.25 & ≤0.55 **(3)** Prior season 0-0 rate <6% **(4)** Draw odds ≥3.60 (buffer ≥3.30 shown in amber) · **2025-26 active:** Dutch Eredivisie · EPL · French Ligue 1 · Polish EK · Scottish Prem · Spanish La Liga · Swiss SL | Back ≥3.60 — Col CB |
        """)
