# FTS xG Systems Dashboard

A Streamlit dashboard for the FTS xG betting portfolio —
4 systems, 34 system-league combinations, 5,386 historical bets, +17.7% blended ROI.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run dashboard (port 8502 to avoid conflict with other portfolios)
streamlit run dashboard/app.py --server.port 8502
```

Open: http://localhost:8502

---

## File Structure

```
fts_dashboard/
├── dashboard/
│   ├── app.py                          # Home page
│   └── pages/
│       ├── 1_📊_Portfolio.py           # Portfolio overview
│       ├── 2_🎯_Daily_Selector.py      # Daily bet generator
│       ├── 3_📈_System_Performance.py  # Per-system analysis
│       └── 4_🔬_Analytics.py          # Edge & distribution analysis
├── models/
│   └── enhanced_daily_selector.py      # Selection engine + Excel export
├── systems/
│   └── all_systems.py                  # All 4 system classes
├── config/
│   └── portfolio_stats.json            # Pre-calculated stats per system+league
├── data/
│   └── portfolio_master_sheet.json     # Full historical bet dataset
├── requirements.txt
└── README.md
```

---

## Dashboard Pages

### 1. 📊 Portfolio Overview
- KPI metrics: bets, P/L, ROI, SR, max drawdown
- Cumulative P/L chart (all systems + combined)
- System breakdown table and ROI bar chart
- League breakdown with colour-coded ROI
- Season-by-season grouped bar chart
- Filters: system, league, date range

### 2. 🎯 Daily Selector
1. Upload the **FTS Advanced PreMatch Excel** file
2. Dashboard runs all 4 systems automatically
3. Filter results by market/league
4. Download colour-coded Excel in the standard format

**Excel output format:**
- Columns: Date | Time | League | Home | Away | Market | 6G xG | Rule | Odds | Hist ROI
- Result columns: Lay U1.5 | Back O2.5 | Lay O3.5 | FHG Lay U0.5
- Live totals: Row Total | Cumulative running P/L

### 3. 📈 System Performance
- Select any of the 4 systems
- Cumulative P/L chart (per league + combined)
- Drawdown chart
- League breakdown table + ROI bar chart
- Season-by-season heatmap
- xG value distribution histogram

### 4. 🔬 Analytics
- ROI by odds band
- Monthly P/L bar chart
- P/L distribution histogram
- Win rate by system
- xG vs P/L scatter plot
- Rolling 50-bet ROI chart

---

## The 4 Systems

### ① Lay U1.5 — 9 leagues | +23.1% ROI
xG: 6G Match xG | Odds: Lay 1.00–6.00

| League | Threshold |
|--------|-----------|
| Belgian Premier League | >= 3.75 |
| Danish Superligaen | >= 3.65 |
| Dutch Eerste Divisie | >= 3.95 |
| English League One | >= 4.20 |
| French Ligue 1 | >= 4.05 |
| German Bundesliga 2 | >= 4.10 |
| Polish Ekstraklasa | >= 3.90 |
| Scottish Premiership | >= 3.25 |
| Swedish Allsvenskan | >= 3.35 |

### ② Back O2.5 — 8 leagues | +13.1% ROI
xG: 6G Match xG | Odds: Back 1.50–2.50

| League | Threshold |
|--------|-----------|
| English Championship | >= 4.25 |
| English Premier League | >= 4.30 |
| Irish Premier League | >= 2.85 |
| Italian Serie A | >= 3.90 |
| Norwegian Tippeligaen | >= 3.60 |
| Polish Ekstraklasa | >= 3.95 |
| Portuguese Primeira Liga | >= 3.70 |
| Spanish Primera Division | >= 3.70 |

### ③ Lay O3.5 — 5 leagues | +13.2% ROI
xG: 6G Match xG + Poisson O3.5 Value < 0 | Odds: Lay 1.00–6.00

| League | Rule |
|--------|------|
| Belgian Premier League | Match xG <= 2.00 |
| Dutch Eerste Divisie | Match xG >= 4.70 |
| Dutch Eredivisie | Match xG <= 2.05 |
| English Championship | Match xG >= 3.85 OR <= 1.30 |
| Spanish Primera Division | Match xG >= 4.30 OR <= 1.50 |

**Note:** Also requires Poisson 6G O3.5 value column (G6_O35Val) to be negative.

### ④ FHG Lay U0.5 — 12 leagues | +18.9% ROI
xG: 6G FH xG | Odds: Lay 1.00–6.00

| League | Threshold |
|--------|-----------|
| Belgian Premier League | >= 1.95 |
| Danish Superligaen | >= 2.05 |
| Dutch Eredivisie | >= 2.00 |
| English Championship | >= 2.35 |
| English League One | >= 1.50 |
| German Bundesliga | >= 2.40 |
| Irish Premier League | >= 1.60 |
| Polish Ekstraklasa | >= 1.90 |
| Portuguese Primeira Liga | >= 2.20 |
| Scottish Premiership | >= 1.30 |
| Swiss Super League | >= 2.10 |
| Turkish Super Lig | >= 2.25 |

---

## FTS PreMatch File Format

The fixture file must be the standard **FTS Advanced PreMatch Excel** with:
- Row 1: Section headers
- Row 2: Column headers
- Rows 3+: Fixture data

Key columns used (by index):
| Col | Content |
|-----|---------|
| 0 | Date |
| 1 | Time |
| 3 | Competition/League |
| 4 | Home Team |
| 5 | Away Team |
| 27 | Poisson O3.5 Value (6G) |
| 30 | 6G 1st Half xGTot |
| 34 | 6G Match xG |
| 84 | O2.5 Back Odds |
| 88 | U1.5 Lay Odds |
| 95 | O3.5 Lay Odds |
| 108 | FHG U0.5 Lay Odds |

---

## Running Alongside Another Dashboard

```bash
# Terminal 1 – Other portfolio (port 8501)
cd ~/other_portfolio
streamlit run dashboard/app.py

# Terminal 2 – This dashboard (port 8502)
cd ~/fts_dashboard
streamlit run dashboard/app.py --server.port 8502
```

---

## Command-Line Usage

Generate selections without the dashboard:

```bash
python models/enhanced_daily_selector.py fixtures.xlsx output.xlsx
```

---

## Bet Calculation Notes

**BACK bets (Back O2.5):**
- Win: Profit = Stake × (Odds - 1)
- Lose: Loss = -Stake
- P/L shown at 1pt flat stake

**LAY bets (Lay U1.5, Lay O3.5, FHG Lay U0.5):**
- Win (laid outcome does NOT happen): Profit = +1pt (1pt liability)
- Lose (laid outcome DOES happen): Loss = -(Odds - 1) pts
- P/L shown at 1pt liability per bet

**Historical ROI:** Pre-calculated from 2021–2026 data, league-specific (not system-wide averages).
