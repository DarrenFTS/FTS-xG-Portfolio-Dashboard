"""
Page 0: Database Update
Upload a fresh FTS Advanced Results Excel file to rebuild the entire portfolio dataset.
All other tabs update automatically once the upload is processed.
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

# ── System rules (identical to all_systems.py) ────────────────────────────────
RULES = {
    'Lay_U15': {
        "German Bundesliga 2":    (">", 4.10),
        "Danish Superligaen":     (">", 3.65),
        "Belgian Premier League": (">", 3.75),
        "Scottish Premiership":   (">", 3.25),
        "French Ligue 1":         (">", 4.05),
        "Swedish Allsvenskan":    (">", 2.20),
    },
    'Back_O25': {
        "English Championship":    (">", 4.25),
        "Spanish Primera Division":(">", 3.70),
        "Portuguese Primeira Liga":(">", 3.55),
        "English Premier League":  (">", 4.30),
        "Polish Ekstraklasa":      (">", 3.95),
        "Norwegian Tippeligaen":   (">", 3.60),
    },
    'Lay_O35': {
        "Spanish Primera Division":  [("<", 1.50)],
        "German Bundesliga 2":       [("<", 2.00)],
        "Belgian Premier League":    [("<", 2.00)],
        "Irish Premier League":      [("<", 2.85)],
        "Dutch Eredivisie":          [("<", 2.05)],
        "Italian Serie A":           [("<", 1.40)],
        "Spanish Segunda Division":  [(">", 3.60)],
        "Austrian Bundesliga":       [(">", 2.35)],
        "English Championship":      [(">", 3.85)],
        "Dutch Eerste Divisie":      [(">", 4.70)],
    },
    'Lay_FHU05': {
        "Polish Ekstraklasa":      (">", 1.90),
        "Belgian Premier League":  (">", 1.95),
        "Portuguese Primeira Liga":(">", 2.20),
        "Danish Superligaen":      (">", 1.95),
        "German Bundesliga":       (">", 2.40),
        "Dutch Eredivisie":        (">", 2.00),
        "English Championship":    (">", 2.35),
        "Scottish Premiership":    (">", 0.85),
        "Swiss Super League":      (">", 2.10),
        "English League One":      (">", 1.50),
    },
}

MARKET_COLS = {
    'Lay_U15':   ('U15_Lay_PL',    'U15_Lay_Odds'),
    'Back_O25':  ('O25_Back_PL',   'O25_Back_Odds'),
    'Lay_O35':   ('O35_Lay_PL',    'O35_Lay_Odds'),
    'Lay_FHU05': ('FHGU05_Lay_PL', 'FHGU05_Lay_Odds'),
}
ODDS_FILTER = {
    'Lay_U15':   lambda d: d[(d['U15_Lay_Odds'] > 1.0)   & (d['U15_Lay_Odds'] <= 6.0)],
    'Back_O25':  lambda d: d[(d['O25_Back_Odds'] >= 1.5)  & (d['O25_Back_Odds'] <= 2.5)],
    'Lay_O35':   lambda d: d[(d['O35_Lay_Odds'] > 1.0)   & (d['O35_Lay_Odds'] <= 6.0)],
    'Lay_FHU05': lambda d: d[(d['FHGU05_Lay_Odds'] > 1.0) & (d['FHGU05_Lay_Odds'] <= 6.0)],
}
XG_COL    = {'Lay_U15':'G6_MatchxG','Back_O25':'G6_MatchxG','Lay_O35':'G6_MatchxG','Lay_FHU05':'G6_FH_xG'}
MKT_LABEL = {'Lay_U15':'Lay U1.5','Back_O25':'Back O2.5','Lay_O35':'Lay O3.5','Lay_FHU05':'FHG Lay U0.5'}
BET_TYPE  = {'Lay_U15':'LAY','Back_O25':'BACK','Lay_O35':'LAY','Lay_FHU05':'LAY'}

HIST_ROI = {
    ("German Bundesliga 2","Lay_U15"):37.9,   ("Danish Superligaen","Lay_U15"):35.6,
    ("Belgian Premier League","Lay_U15"):25.5, ("Scottish Premiership","Lay_U15"):16.1,
    ("French Ligue 1","Lay_U15"):12.1,         ("Swedish Allsvenskan","Lay_U15"):12.0,
    ("English Championship","Back_O25"):18.2,  ("Spanish Primera Division","Back_O25"):14.0,
    ("Portuguese Primeira Liga","Back_O25"):12.6,("English Premier League","Back_O25"):12.3,
    ("Polish Ekstraklasa","Back_O25"):11.9,    ("Norwegian Tippeligaen","Back_O25"):10.6,
    ("Spanish Primera Division","Lay_O35"):16.2,("German Bundesliga 2","Lay_O35"):16.1,
    ("Belgian Premier League","Lay_O35"):15.2, ("Spanish Segunda Division","Lay_O35"):14.6,
    ("Austrian Bundesliga","Lay_O35"):12.6,    ("Irish Premier League","Lay_O35"):11.6,
    ("English Championship","Lay_O35"):11.5,   ("Dutch Eerste Divisie","Lay_O35"):11.0,
    ("Dutch Eredivisie","Lay_O35"):10.4,       ("Italian Serie A","Lay_O35"):10.1,
    ("Polish Ekstraklasa","Lay_FHU05"):34.8,   ("Belgian Premier League","Lay_FHU05"):29.4,
    ("Portuguese Primeira Liga","Lay_FHU05"):28.3,("Danish Superligaen","Lay_FHU05"):26.9,
    ("German Bundesliga","Lay_FHU05"):25.8,    ("Dutch Eredivisie","Lay_FHU05"):20.1,
    ("English Championship","Lay_FHU05"):18.1, ("Scottish Premiership","Lay_FHU05"):14.5,
    ("Swiss Super League","Lay_FHU05"):13.0,   ("English League One","Lay_FHU05"):10.2,
}

# ── Column mapping for FTS Advanced Results Excel (FTSAdvanced sheet) ─────────
RESULTS_COL_MAP = {
    0:  'Date',       1:  'Time',     3:  'League',
    4:  'Home',       5:  'Away',     6:  'Season',
    9:  'G6_FH_xG',   13: 'G6_MatchxG',
    70: 'U15_Lay_Odds',  71: 'U15_Lay_PL',
    63: 'O25_Back_Odds', 64: 'O25_Back_PL',
    79: 'O35_Lay_Odds',  80: 'O35_Lay_PL',
    84: 'FHGU05_Lay_Odds', 85: 'FHGU05_Lay_PL',
}


def load_results_excel(filepath: str) -> pd.DataFrame:
    """Load the FTS Advanced Results Excel file (FTSAdvanced sheet)."""
    raw = pd.read_excel(filepath, sheet_name='FTSAdvanced', header=None)
    df  = raw.iloc[1:].copy().reset_index(drop=True)  # skip header row
    df  = df.rename(columns=RESULTS_COL_MAP)
    numeric_cols = ['G6_FH_xG','G6_MatchxG',
                    'U15_Lay_Odds','U15_Lay_PL',
                    'O25_Back_Odds','O25_Back_PL',
                    'O35_Lay_Odds','O35_Lay_PL',
                    'FHGU05_Lay_Odds','FHGU05_Lay_PL']
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df


def build_portfolio(df: pd.DataFrame):
    """Run all 4 systems against the results dataframe. Returns (bets_list, stats_list)."""
    all_bets   = []
    stats_list = []

    for mkt, (pl_col, odds_col) in MARKET_COLS.items():
        if pl_col not in df.columns or odds_col not in df.columns:
            continue

        for lg, rule_val in RULES[mkt].items():
            lgdf = ODDS_FILTER[mkt](df[df['League'] == lg])
            rule_list = rule_val if isinstance(rule_val, list) else [rule_val]
            xg = XG_COL[mkt]

            if xg not in lgdf.columns:
                continue

            mask = pd.Series(False, index=lgdf.index)
            for (op, thresh) in rule_list:
                mask = mask | (lgdf[xg] > thresh if op == '>' else lgdf[xg] < thresh)
            filt = lgdf[mask]
            filt = filt[filt[pl_col].notna() & filt[odds_col].notna()].copy()

            if len(filt) < 1:
                continue

            rule_str = " OR ".join(
                f">={t:.2f}" if o == '>' else f"<={t:.2f}" for o, t in rule_list
            )

            # ── Per-bet rows ──────────────────────────────────────────────────
            for _, row in filt.iterrows():
                all_bets.append({
                    'date':       str(row.get('Date', ''))[:10],
                    'season':     str(row.get('Season', '')),
                    'league':     lg,
                    'home':       str(row.get('Home', '')),
                    'away':       str(row.get('Away', '')),
                    'system':     MKT_LABEL[mkt],
                    'system_key': mkt,
                    'bet_type':   BET_TYPE[mkt],
                    'xg_col':     xg,
                    'xg_value':   round(float(row.get(xg, 0) or 0), 2),
                    'rule':       rule_str,
                    'odds':       round(float(row.get(odds_col, 0) or 0), 2),
                    'pl':         round(float(row.get(pl_col, 0) or 0), 2),
                    'won':        int(row.get(pl_col, 0) > 0),
                    'hist_roi':   round(HIST_ROI.get((lg, mkt), 0), 2),
                })

            # ── Aggregate stats ───────────────────────────────────────────────
            n    = len(filt)
            pl_t = filt[pl_col].sum()
            cum  = filt[pl_col].cumsum()
            dd   = float((cum - cum.cummax()).min())
            ssn  = {}
            for s in filt['Season'].dropna().unique():
                sf = filt[filt['Season'] == s]
                if len(sf) >= 3:
                    sp = sf[pl_col].sum()
                    ssn[str(s)] = {
                        'n':   int(len(sf)),
                        'pl':  round(float(sp), 2),
                        'roi': round(float(sp / len(sf) * 100), 2),
                        'sr':  round(float((sf[pl_col] > 0).mean() * 100), 2),
                    }
            stats_list.append({
                'system':     MKT_LABEL[mkt], 'system_key': mkt, 'league': lg,
                'bet_type':   BET_TYPE[mkt],  'xg_col': xg,
                'xg_rules':   rule_list,       'poisson_value_filter': False,
                'odds_min':   {'Lay_U15':1.0,'Back_O25':1.5,'Lay_O35':1.0,'Lay_FHU05':1.0}[mkt],
                'odds_max':   {'Lay_U15':6.0,'Back_O25':2.5,'Lay_O35':6.0,'Lay_FHU05':6.0}[mkt],
                'n':          n,
                'wins':       int((filt[pl_col] > 0).sum()),
                'sr':         round(float((filt[pl_col] > 0).mean() * 100), 2),
                'pl':         round(float(pl_t), 2),
                'roi':        round(float(pl_t / n * 100), 2),
                'avg_odds':   round(float(filt[odds_col].mean()), 2),
                'max_dd':     round(dd, 2),
                'hist_roi':   round(HIST_ROI.get((lg, mkt), 0), 2),
                'seasons':    ssn,
                'bets_per_season': round(n / max(len(ssn), 1), 1),
            })

    return all_bets, stats_list


def save_data(all_bets, stats_list, base_path):
    """Save both JSON files to the data/config folders."""
    bets_path  = os.path.join(base_path, 'data',   'portfolio_master_sheet.json')
    stats_path = os.path.join(base_path, 'config', 'portfolio_stats.json')
    with open(bets_path,  'w') as f: json.dump(all_bets,    f, indent=2)
    with open(stats_path, 'w') as f: json.dump(stats_list,  f, indent=2)
    return bets_path, stats_path


# ── PAGE LAYOUT ───────────────────────────────────────────────────────────────
st.title("🔄 Database Update")
st.markdown("Upload a fresh **FTS Advanced Results Excel** file to rebuild the entire portfolio. "
            "All other tabs update automatically once processing completes.")

st.divider()

# ── Current database summary ─────────────────────────────────────────────────
base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bets_path = os.path.join(base, 'data', 'portfolio_master_sheet.json')

if os.path.exists(bets_path):
    current = pd.DataFrame(json.load(open(bets_path)))
    current['date'] = pd.to_datetime(current['date'], errors='coerce')
    last_date = current['date'].max()

    st.subheader("📊 Current Database")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Bets",    f"{len(current):,}")
    c2.metric("Total P/L",     f"{current['pl'].sum():+.2f} pts")
    c3.metric("Date Range",    f"{current['date'].min().strftime('%b %Y')} – {last_date.strftime('%b %Y')}")
    c4.metric("Last Updated",  last_date.strftime('%d %b %Y'))
else:
    st.info("No database found yet. Upload a file below to create one.")

st.divider()

# ── Upload section ────────────────────────────────────────────────────────────
st.subheader("📁 Upload Updated Results File")
st.markdown("""
**File required:** The main FTS Advanced Results Excel file  
**Sheet required:** Must contain a sheet named **`FTSAdvanced`**  
**What it contains:** All historical match results with xG values and market P/L columns
""")

uploaded = st.file_uploader(
    "Drop your FTS Advanced Results Excel file here",
    type=['xlsx', 'xls'],
    help="Must be the FTS Advanced Results file containing the FTSAdvanced sheet"
)

if uploaded:
    st.info(f"📄 File received: **{uploaded.name}** ({uploaded.size / 1024:.0f} KB)")

    # Preview before processing
    col_prev, col_proc = st.columns([1, 1])

    with col_prev:
        if st.button("👀 Preview file first", use_container_width=True):
            with st.spinner("Reading file..."):
                try:
                    tmp = "/tmp/results_upload.xlsx"
                    with open(tmp, 'wb') as f: f.write(uploaded.getvalue())
                    df_prev = load_results_excel(tmp)
                    st.success(f"✅ File readable — {len(df_prev):,} rows found")
                    st.markdown(f"**Date range:** {df_prev['Date'].min().strftime('%d %b %Y')} → {df_prev['Date'].max().strftime('%d %b %Y')}")
                    st.markdown(f"**Leagues:** {', '.join(sorted(df_prev['League'].dropna().unique()[:8]))}{'...' if len(df_prev['League'].dropna().unique()) > 8 else ''}")
                    st.dataframe(df_prev[['Date','League','Home','Away']].head(5), hide_index=True)
                except Exception as e:
                    st.error(f"Could not read file: {e}")
                    st.markdown("Make sure the file has a sheet named **FTSAdvanced**")

    with col_proc:
        process = st.button("⚡ Process & Update Dashboard", type="primary", use_container_width=True)

    if process:
        progress = st.progress(0, text="Starting...")
        status   = st.empty()

        try:
            # Step 1 — Save upload
            progress.progress(10, text="Saving uploaded file...")
            tmp = "/tmp/results_upload.xlsx"
            with open(tmp, 'wb') as f:
                f.write(uploaded.getvalue())

            # Step 2 — Load
            progress.progress(25, text="Loading results file...")
            status.info("📖 Reading FTSAdvanced sheet...")
            df = load_results_excel(tmp)
            n_rows = len(df)
            status.info(f"📖 Loaded {n_rows:,} rows from {df['Date'].min().strftime('%d %b %Y')} to {df['Date'].max().strftime('%d %b %Y')}")

            # Step 3 — Run systems
            progress.progress(50, text="Running all 4 systems...")
            status.info("⚙️  Qualifying bets through Lay U1.5, Back O2.5, Lay O3.5, FHG Lay U0.5...")
            all_bets, stats_list = build_portfolio(df)

            # Step 4 — Save
            progress.progress(80, text="Saving updated data files...")
            status.info("💾 Writing portfolio_master_sheet.json and portfolio_stats.json...")
            bets_path, stats_path = save_data(all_bets, stats_list, base)

            # Step 5 — Clear cache so all pages reload
            progress.progress(95, text="Clearing cache...")
            st.cache_data.clear()

            progress.progress(100, text="Complete!")

            # ── Results summary ───────────────────────────────────────────────
            st.success("✅ Database updated successfully!")
            st.balloons()

            new_df = pd.DataFrame(all_bets)
            st.subheader("📊 Updated Database Summary")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Total Bets",    f"{len(new_df):,}")
            r2.metric("Total P/L",     f"{new_df['pl'].sum():+.2f} pts")
            r3.metric("Blended ROI",   f"{new_df['pl'].sum()/len(new_df)*100:+.2f}%")
            r4.metric("System combos", len(stats_list))

            st.markdown("**Bets per system:**")
            from collections import Counter
            mc = Counter(b['system'] for b in all_bets)
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Lay U1.5",     mc.get('Lay U1.5', 0))
            sc2.metric("Back O2.5",    mc.get('Back O2.5', 0))
            sc3.metric("Lay O3.5",     mc.get('Lay O3.5', 0))
            sc4.metric("FHG Lay U0.5", mc.get('FHG Lay U0.5', 0))

            st.divider()
            st.markdown("### ✅ All tabs updated — click any tab in the sidebar to see the new data")
            st.markdown("*The Portfolio, System Performance and Analytics tabs will all reflect the new results.*")

        except Exception as e:
            progress.empty()
            st.error(f"❌ Error processing file: {e}")
            st.markdown("""
**Common causes:**
- The sheet is not named `FTSAdvanced` (check in Excel — it must be exactly that)
- The file has a different column layout to the standard FTS Advanced Results format
- The file is corrupted or password protected
            """)

st.divider()

# ── Format guide ─────────────────────────────────────────────────────────────
with st.expander("📋 Expected file format"):
    st.markdown("""
**File:** FTS Advanced Results Excel (the main historical results file, not the PreMatch file)

**Sheet name:** `FTSAdvanced`

**Key columns used (by position):**

| Column | Index | Content |
|--------|-------|---------|
| Date | 0 | Match date |
| Time | 1 | Kick-off time |
| League | 3 | Competition name |
| Home | 4 | Home team |
| Away | 5 | Away team |
| Season | 6 | Season label |
| 6G FH xG | 9 | 6-game first half xG total |
| 6G Match xG | 13 | 6-game match xG total |
| O2.5 Back Odds | 63 | Over 2.5 back market odds |
| O2.5 Back P/L | 64 | Over 2.5 back P/L result |
| U1.5 Lay Odds | 70 | Under 1.5 lay market odds |
| U1.5 Lay P/L | 71 | Under 1.5 lay P/L result |
| O3.5 Lay Odds | 79 | Over 3.5 lay market odds |
| O3.5 Lay P/L | 80 | Over 3.5 lay P/L result |
| FHG U0.5 Lay Odds | 84 | First half goals U0.5 lay odds |
| FHG U0.5 Lay P/L | 85 | First half goals U0.5 lay P/L |
    """)
