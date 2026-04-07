"""
Page 0: Database Update
Upload a fresh FTS Advanced Results Excel file to rebuild the entire portfolio dataset.
All other tabs update automatically once the upload is processed.

CONFIRMED COLUMN MAPPING (FTS Advanced Results, FTSAdvanced sheet, header row 1):
  Date:              col 0  (A)
  League:            col 3  (D) — Competition
  Home:              col 4  (E)
  Away:              col 5  (F)
  Season:            col 2  (C)
  Match xG (6G):     col 13 (N)  — 6 Game Model
  FH xGTot (6G):     col 9  (J)  — 6 Game Model
  O2.5 Back Odds:    col 63 (BL)
  O2.5 Back PL:      col 64 (BM)
  U1.5 Lay Odds:     col 70 (BS)
  U1.5 Lay PL:       col 71 (BT)
  O3.5 Lay Odds:     col 79 (CB)
  O3.5 Lay PL:       col 80 (CC)
  FHG U0.5 Lay Odds: col 84 (CG)
  FHG U0.5 Lay PL:   col 85 (CH)
"""
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(page_title="Database Update", page_icon="🔄", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0D2B55; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# ── CONFIRMED RULES (must match all_systems.py exactly) ───────────────────────
# Format: {system_key: {league: (op, threshold)}}
# op = '>=' (xG above threshold) or '<=' (xG below threshold)
RULES = {
    'Lay_U15': {
        "Swedish Allsvenskan":    ('>=', 4.00),
        "Polish Ekstraklasa":     ('>=', 4.25),
        "German Bundesliga 2":    ('>=', 4.25),
        "Danish Superligaen":     ('>=', 3.75),
        "Belgian Premier League": ('>=', 3.75),
        "Italian Serie A":        ('>=', 4.50),
        "Scottish Premiership":   ('>=', 2.75),
    },
    'Back_O25': {
        "Irish Premier League":    ('>=', 3.75),
        "English Championship":    ('>=', 4.75),
        "Polish Ekstraklasa":      ('>=', 4.25),
        "Portuguese Primeira Liga":('>=', 4.50),
        "Italian Serie A":         ('>=', 4.50),
        "Spanish Primera Division":('>=', 3.75),
        "Dutch Eredivisie":        ('>=', 4.50),
        "English Premier League":  ('>=', 4.50),
    },
    'Lay_O35': {
        "Spanish Segunda Division":('>=', 4.25),
        "Dutch Eerste Divisie":    ('>=', 4.75),
        "German Bundesliga":       ('>=', 5.25),
        "French Ligue 1":          ('>=', 4.75),
        "German Bundesliga 2":     ('<=', 1.75),
        "Spanish Primera Division":('<=', 1.25),
        "Belgian Premier League":  ('<=', 2.00),
        "English Championship":    ('<=', 1.25),
    },
    'Lay_FHU05': {
        "Danish Superligaen":      ('>=', 2.50),
        "Polish Ekstraklasa":      ('>=', 2.25),
        "Portuguese Primeira Liga":('>=', 2.25),
        "French Ligue 1":          ('>=', 2.50),
        "Dutch Eredivisie":        ('>=', 2.00),
        "German Bundesliga":       ('>=', 2.50),
        "English Championship":    ('>=', 2.50),
    },
}

# Column index positions (0-based, after reading header row 1)
COL_IDX = {
    'date':     0,   'league':  3,   'home':    4,
    'away':     5,   'season':  2,
    'match_xg': 13,  'fh_xg':   9,
    'o25_o':    63,  'o25_pl':  64,
    'u15_o':    70,  'u15_pl':  71,
    'o35_o':    79,  'o35_pl':  80,
    'fhu_o':    84,  'fhu_pl':  85,
}

MARKET = {
    'Lay_U15':   ('match_xg', 'u15_o',  'u15_pl',  'LAY',  'Lay U1.5',     1.0, 6.0),
    'Back_O25':  ('match_xg', 'o25_o',  'o25_pl',  'BACK', 'Back O2.5',    1.5, 2.5),
    'Lay_O35':   ('match_xg', 'o35_o',  'o35_pl',  'LAY',  'Lay O3.5',     1.0, 6.0),
    'Lay_FHU05': ('fh_xg',    'fhu_o',  'fhu_pl',  'LAY',  'FHG Lay U0.5', 1.0, 6.0),
}

HIST_ROI = {
    ("Swedish Allsvenskan","Lay_U15"):50.58,    ("Polish Ekstraklasa","Lay_U15"):47.52,
    ("German Bundesliga 2","Lay_U15"):39.06,    ("Danish Superligaen","Lay_U15"):34.92,
    ("Belgian Premier League","Lay_U15"):21.98, ("Italian Serie A","Lay_U15"):19.51,
    ("Scottish Premiership","Lay_U15"):11.77,
    ("Irish Premier League","Back_O25"):36.88,  ("English Championship","Back_O25"):20.87,
    ("Polish Ekstraklasa","Back_O25"):16.42,    ("Portuguese Primeira Liga","Back_O25"):16.38,
    ("Italian Serie A","Back_O25"):14.91,       ("Spanish Primera Division","Back_O25"):12.40,
    ("Dutch Eredivisie","Back_O25"):10.52,      ("English Premier League","Back_O25"):10.31,
    ("Spanish Segunda Division","Lay_O35"):48.04,("German Bundesliga 2","Lay_O35"):16.20,
    ("Spanish Primera Division","Lay_O35"):15.97,("Belgian Premier League","Lay_O35"):13.53,
    ("Dutch Eerste Divisie","Lay_O35"):13.16,   ("German Bundesliga","Lay_O35"):12.69,
    ("French Ligue 1","Lay_O35"):10.90,         ("English Championship","Lay_O35"):10.45,
    ("Danish Superligaen","Lay_FHU05"):51.66,   ("Polish Ekstraklasa","Lay_FHU05"):30.75,
    ("Portuguese Primeira Liga","Lay_FHU05"):29.49,("French Ligue 1","Lay_FHU05"):23.00,
    ("Dutch Eredivisie","Lay_FHU05"):21.92,     ("German Bundesliga","Lay_FHU05"):18.69,
    ("English Championship","Lay_FHU05"):13.08,
}


def load_results_excel(filepath: str) -> pd.DataFrame:
    """Load FTS Advanced Results file using confirmed column positions."""
    raw = pd.read_excel(filepath, sheet_name='FTSAdvanced', header=None)
    df  = raw.iloc[2:].copy().reset_index(drop=True)  # row 0=merged headers, row 1=col names
    # Rename by index position
    rename = {v: k for k, v in COL_IDX.items()}
    df = df.rename(columns=rename)
    for c in ['match_xg','fh_xg','o25_o','o25_pl','u15_o','u15_pl',
              'o35_o','o35_pl','fhu_o','fhu_pl']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df


def build_portfolio(df: pd.DataFrame):
    """Run all 4 systems against the results dataframe."""
    all_bets   = []
    stats_list = []

    for mkt, (xg_key, odds_key, pl_key, bet_type, label, o_min, o_max) in MARKET.items():
        if xg_key not in df.columns or pl_key not in df.columns:
            continue

        for lg, (op, thresh) in RULES[mkt].items():
            lgdf = df[df['league'] == lg].copy()
            lgdf = lgdf[(lgdf[odds_key] > o_min) & (lgdf[odds_key] <= o_max)
                        & lgdf[pl_key].notna() & lgdf[xg_key].notna()]

            mask = (lgdf[xg_key] >= thresh) if op == '>=' else (lgdf[xg_key] <= thresh)
            filt = lgdf[mask].copy()
            if len(filt) < 1:
                continue

            rule_str = f"{op}{thresh:.2f}"
            n    = len(filt)
            pl_t = float(filt[pl_key].sum())
            roi  = pl_t / n * 100
            cum  = filt[pl_key].cumsum()
            dd   = float((cum - cum.cummax()).min())

            ssn_data = {}
            for s in filt['season'].dropna().unique():
                sf = filt[filt['season'] == s]
                if len(sf) >= 3:
                    sp = float(sf[pl_key].sum())
                    ssn_data[str(s)] = {
                        'n':   int(len(sf)),
                        'pl':  round(sp, 2),
                        'roi': round(sp / len(sf) * 100, 2),
                        'sr':  round(float((sf[pl_key] > 0).mean() * 100), 2),
                    }

            for _, row in filt.iterrows():
                all_bets.append({
                    'date':       str(row.get('date',''))[:10],
                    'season':     str(row.get('season','')),
                    'league':     lg,
                    'home':       str(row.get('home','')),
                    'away':       str(row.get('away','')),
                    'system':     label,
                    'system_key': mkt,
                    'bet_type':   bet_type,
                    'xg_col':     xg_key,
                    'xg_value':   round(float(row.get(xg_key, 0) or 0), 2),
                    'rule':       rule_str,
                    'odds':       round(float(row.get(odds_key, 0) or 0), 2),
                    'pl':         round(float(row.get(pl_key, 0) or 0), 2),
                    'won':        int(row.get(pl_key, 0) > 0),
                    'hist_roi':   round(HIST_ROI.get((lg, mkt), 0), 2),
                })

            stats_list.append({
                'system': label, 'system_key': mkt, 'league': lg,
                'bet_type': bet_type, 'xg_col': xg_key,
                'xg_op': op, 'xg_thresh': thresh,
                'odds_min': o_min, 'odds_max': o_max,
                'n': n, 'pl': round(pl_t, 2), 'roi': round(roi, 2),
                'sr':  round(float((filt[pl_key] > 0).mean() * 100), 2),
                'avg_odds': round(float(filt[odds_key].mean()), 2),
                'max_dd': round(dd, 2),
                'hist_roi': round(HIST_ROI.get((lg, mkt), 0), 2),
                'seasons': ssn_data,
            })

    return all_bets, stats_list


def save_data(all_bets, stats_list, base_path):
    bets_path  = os.path.join(base_path, 'data',   'portfolio_master_sheet.json')
    stats_path = os.path.join(base_path, 'config', 'portfolio_stats.json')
    with open(bets_path,  'w') as f: json.dump(all_bets,   f, indent=2)
    with open(stats_path, 'w') as f: json.dump(stats_list, f, indent=2)
    return bets_path, stats_path


# ── PAGE ──────────────────────────────────────────────────────────────────────
st.title("🔄 Database Update")
st.markdown("Upload a fresh **FTS Advanced Results Excel** file to rebuild the entire portfolio. "
            "All other tabs update automatically once processing completes.")
st.divider()

base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bets_path = os.path.join(base, 'data', 'portfolio_master_sheet.json')

if os.path.exists(bets_path):
    current = pd.DataFrame(json.load(open(bets_path)))
    current['date'] = pd.to_datetime(current['date'], errors='coerce')
    st.subheader("📊 Current Database")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Bets",   f"{len(current):,}")
    c2.metric("Total P/L",    f"{current['pl'].sum():+.2f} pts")
    c3.metric("Date Range",   f"{current['date'].min().strftime('%b %Y')} – {current['date'].max().strftime('%b %Y')}")
    c4.metric("Last Updated", current['date'].max().strftime('%d %b %Y'))
else:
    st.info("No database found. Upload a file below to create one.")

st.divider()
st.subheader("📁 Upload Updated Results File")
st.markdown("""
**File required:** FTS Advanced Results Excel  
**Sheet required:** Must be named **`FTSAdvanced`**  
**Header:** Row 1 is column names (row 0 is merged group headers)
""")

uploaded = st.file_uploader(
    "Drop your FTS Advanced Results Excel file here",
    type=['xlsx','xls'],
    help="Must contain the FTSAdvanced sheet with correct column layout"
)

if uploaded:
    st.info(f"📄 File received: **{uploaded.name}** ({uploaded.size/1024:.0f} KB)")
    col_prev, col_proc = st.columns([1,1])

    with col_prev:
        if st.button("👀 Preview file first", use_container_width=True):
            with st.spinner("Reading file..."):
                try:
                    tmp = "/tmp/results_upload.xlsx"
                    with open(tmp,'wb') as f: f.write(uploaded.getvalue())
                    df_prev = load_results_excel(tmp)
                    st.success(f"✅ {len(df_prev):,} rows found")
                    st.markdown(f"**Date range:** {df_prev['date'].min().strftime('%d %b %Y')} → {df_prev['date'].max().strftime('%d %b %Y')}")
                    lgs = sorted(df_prev['league'].dropna().unique())
                    st.markdown(f"**Leagues:** {', '.join(lgs[:8])}{'...' if len(lgs)>8 else ''}")
                    st.dataframe(df_prev[['date','league','home','away']].head(5), hide_index=True)
                except Exception as e:
                    st.error(f"Could not read file: {e}")

    with col_proc:
        process = st.button("⚡ Process & Update Dashboard", type="primary", use_container_width=True)

    if process:
        progress = st.progress(0, text="Starting...")
        status   = st.empty()
        try:
            progress.progress(10, text="Saving file...")
            tmp = "/tmp/results_upload.xlsx"
            with open(tmp,'wb') as f: f.write(uploaded.getvalue())

            progress.progress(25, text="Loading results...")
            status.info("📖 Reading FTSAdvanced sheet...")
            df = load_results_excel(tmp)
            status.info(f"📖 Loaded {len(df):,} rows — {df['date'].min().strftime('%d %b %Y')} to {df['date'].max().strftime('%d %b %Y')}")

            progress.progress(50, text="Running all 4 systems...")
            status.info("⚙️ Qualifying bets through all systems...")
            all_bets, stats_list = build_portfolio(df)

            progress.progress(80, text="Saving data files...")
            status.info("💾 Writing JSON data files...")
            save_data(all_bets, stats_list, base)

            progress.progress(95, text="Clearing cache...")
            st.cache_data.clear()
            progress.progress(100, text="Complete!")

            st.success("✅ Database updated successfully!")
            st.balloons()

            new_df = pd.DataFrame(all_bets)
            st.subheader("📊 Updated Database Summary")
            r1,r2,r3,r4 = st.columns(4)
            r1.metric("Total Bets",    f"{len(new_df):,}")
            r2.metric("Total P/L",     f"{new_df['pl'].sum():+.2f} pts")
            r3.metric("Blended ROI",   f"{new_df['pl'].sum()/len(new_df)*100:+.2f}%")
            r4.metric("System combos", len(stats_list))

            from collections import Counter
            mc = Counter(b['system'] for b in all_bets)
            sc1,sc2,sc3,sc4 = st.columns(4)
            sc1.metric("Lay U1.5",     mc.get('Lay U1.5',0))
            sc2.metric("Back O2.5",    mc.get('Back O2.5',0))
            sc3.metric("Lay O3.5",     mc.get('Lay O3.5',0))
            sc4.metric("FHG Lay U0.5", mc.get('FHG Lay U0.5',0))

            st.divider()
            st.markdown("### ✅ All tabs updated — click any tab in the sidebar to see the new data")

        except Exception as e:
            progress.empty()
            st.error(f"❌ Error: {e}")
            st.markdown("""
**Common causes:**
- Sheet is not named `FTSAdvanced`
- Column layout differs from standard FTS Advanced Results format
- File is corrupted or password protected
            """)

st.divider()
with st.expander("📋 Expected file format & column mapping"):
    st.markdown("""
**File:** FTS Advanced Results Excel — the main historical results file (not the PreMatch fixture file)

**Sheet name:** `FTSAdvanced`

**Header structure:** Row 0 = merged group headers, Row 1 = column names, Row 2+ = data

| Excel Col | Index | Column Name | Used for |
|-----------|-------|-------------|---------|
| A | 0 | Date | Match date |
| C | 2 | Season | Season label |
| D | 3 | Competition | League filter |
| E | 4 | Home Team | Home team name |
| F | 5 | Away Team | Away team name |
| J | 9 | 1st Half xGTot | FHG system xG filter |
| N | 13 | Match xG | Lay U1.5 / Back O2.5 / Lay O3.5 xG filter |
| BL | 63 | O2.5 Back Odds | Back O2.5 odds |
| BM | 64 | O2.5 Back PL | Back O2.5 P/L |
| BS | 70 | U1.5 Lay Odds | Lay U1.5 odds |
| BT | 71 | U1.5 Lay PL | Lay U1.5 P/L |
| CB | 79 | O3.5 Lay Odds | Lay O3.5 odds |
| CC | 80 | O3.5 Lay PL | Lay O3.5 P/L |
| CG | 84 | FHGU0.5 Lay Odds | FHG Lay U0.5 odds |
| CH | 85 | FHGU0.5 Lay PL | FHG Lay U0.5 P/L |
    """)
