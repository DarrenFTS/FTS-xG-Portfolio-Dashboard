"""
FTS xG Betting Systems — CONFIRMED FINAL PORTFOLIO
Verified against FTS_Advanced_Results_xG_21-26.xlsx (35,412 rows)

Column mapping (confirmed by user):
  xG filter : Col N  (idx 13) — Match xG (6 Game Model)
  FH xG     : Col J  (idx  9) — 1st Half xGTot (6 Game Model)
  U1.5 Lay  : Col BS (idx 70) odds / Col BT (idx 71) P/L
  O2.5 Back : Col BL (idx 63) odds / Col BM (idx 64) P/L
  O3.5 Lay  : Col CB (idx 79) odds / Col CC (idx 80) P/L
  FHG Lay   : Col CG (idx 84) odds / Col CH (idx 85) P/L

4 systems · 30 leagues · 3,080 bets · +628.10 pts · +20.39% ROI
All leagues: ROI>=10%, max 1 neg season, DD>=-30 pts, min 50 bets
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class BetSignal:
    date: str
    time: str
    league: str
    home: str
    away: str
    system: str
    system_key: str
    bet_type: str
    xg_col: str
    xg_value: float
    rule: str
    odds: float
    hist_roi: float


# ── PreMatch file column mapping (Sheet1, skip first 2 header rows) ───────────
# These match the confirmed column positions in the FTS Advanced PreMatch file
COL_MAP = {
    'date':         0,
    'time':         1,
    'league':       3,
    'home':         4,
    'away':         5,
    'g6_fh_xg':     9,   # Col J — 1st Half xGTot (6 Game Model)
    'g6_match_xg': 13,   # Col N — Match xG (6 Game Model)
    'o25_back':    63,   # Col BL — O2.5 Back Odds
    'u15_lay':     70,   # Col BS — U1.5 Lay Odds
    'o35_lay':     79,   # Col CB — O3.5 Lay Odds
    'fhu05_lay':   84,   # Col CG — FHGU0.5 Lay Odds
}


# ── Historical ROI per (league, system_key) from real database ────────────────
HIST_ROI = {
    # Lay U1.5
    ("Swedish Allsvenskan",      "Lay_U15"): 50.58,
    ("Polish Ekstraklasa",       "Lay_U15"): 47.52,
    ("German Bundesliga 2",      "Lay_U15"): 39.06,
    ("Danish Superligaen",       "Lay_U15"): 34.92,
    ("Belgian Premier League",   "Lay_U15"): 21.98,
    ("Italian Serie A",          "Lay_U15"): 19.51,
    ("Scottish Premiership",     "Lay_U15"): 11.77,
    # Back O2.5
    ("Irish Premier League",     "Back_O25"): 36.88,
    ("English Championship",     "Back_O25"): 20.87,
    ("Polish Ekstraklasa",       "Back_O25"): 16.42,
    ("Portuguese Primeira Liga", "Back_O25"): 16.38,
    ("Italian Serie A",          "Back_O25"): 14.91,
    ("Spanish Primera Division", "Back_O25"): 12.40,
    ("Dutch Eredivisie",         "Back_O25"): 10.52,
    ("English Premier League",   "Back_O25"): 10.31,
    # Lay O3.5
    ("Spanish Segunda Division", "Lay_O35"): 48.04,
    ("German Bundesliga 2",      "Lay_O35"): 16.20,
    ("Spanish Primera Division", "Lay_O35"): 15.97,
    ("Belgian Premier League",   "Lay_O35"): 13.53,
    ("Dutch Eerste Divisie",     "Lay_O35"): 13.16,
    ("German Bundesliga",        "Lay_O35"): 12.69,
    ("French Ligue 1",           "Lay_O35"): 10.90,
    ("English Championship",     "Lay_O35"): 10.45,
    # FHG Lay U0.5
    ("Danish Superligaen",       "Lay_FHU05"): 51.66,
    ("Polish Ekstraklasa",       "Lay_FHU05"): 30.75,
    ("Portuguese Primeira Liga", "Lay_FHU05"): 29.49,
    ("French Ligue 1",           "Lay_FHU05"): 23.00,
    ("Dutch Eredivisie",         "Lay_FHU05"): 21.92,
    ("German Bundesliga",        "Lay_FHU05"): 18.69,
    ("English Championship",     "Lay_FHU05"): 13.08,
}


def load_fixture_file(filepath: str) -> pd.DataFrame:
    """Load and normalise an FTS Advanced PreMatch Excel file."""
    raw = pd.read_excel(filepath, sheet_name='Sheet1', header=None)
    df  = raw.iloc[2:].copy().reset_index(drop=True)
    df  = df.rename(columns={v: k for k, v in COL_MAP.items()})
    for c in ['g6_fh_xg', 'g6_match_xg', 'u15_lay', 'o25_back', 'o35_lay', 'fhu05_lay']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df


class BaseSystem:
    system_key:   str   = ''
    system_label: str   = ''
    bet_type:     str   = 'LAY'
    xg_col:       str   = 'g6_match_xg'
    odds_col:     str   = ''
    odds_min:     float = 1.0
    odds_max:     float = 6.0
    # leagues: {name: (op, threshold)}  op = '>=' or '<='
    leagues: Dict = {}

    def check_odds(self, odds) -> bool:
        try:
            o = float(odds)
        except (TypeError, ValueError):
            return False
        return not np.isnan(o) and self.odds_min < o <= self.odds_max

    def check_xg(self, xg, league: str) -> Tuple[bool, str]:
        rule = self.leagues.get(league)
        if rule is None:
            return False, ''
        op, thresh = rule
        try:
            xg_f = float(xg)
        except (TypeError, ValueError):
            return False, ''
        if np.isnan(xg_f):
            return False, ''
        if op == '>=' and xg_f >= thresh:
            return True, f">= {thresh:.2f}"
        if op == '<=' and xg_f <= thresh:
            return True, f"<= {thresh:.2f}"
        return False, ''

    def scan(self, fixtures: pd.DataFrame) -> List[BetSignal]:
        signals = []
        for _, row in fixtures.iterrows():
            league = str(row.get('league', '') or '')
            if league not in self.leagues:
                continue
            xg   = row.get(self.xg_col, np.nan)
            odds = row.get(self.odds_col, np.nan)
            xg_ok, rule_str = self.check_xg(xg, league)
            if not xg_ok or not self.check_odds(odds):
                continue
            signals.append(BetSignal(
                date=str(row.get('date', ''))[:10],
                time=str(row.get('time', '')),
                league=league,
                home=str(row.get('home', '')),
                away=str(row.get('away', '')),
                system=self.system_label,
                system_key=self.system_key,
                bet_type=self.bet_type,
                xg_col=self.xg_col,
                xg_value=round(float(xg), 2),
                rule=rule_str,
                odds=round(float(odds), 2),
                hist_roi=HIST_ROI.get((league, self.system_key), 0.0),
            ))
        return signals


# ── System 1: Lay U1.5 ────────────────────────────────────────────────────────
class LayU15System(BaseSystem):
    """
    Lay Under 1.5 Goals
    7 leagues · 858 bets · +215.53 pts · +25.12% ROI
    Filter: Match xG (Col N) >= threshold · Lay odds (Col BS) 1.00–6.00
    """
    system_key   = 'Lay_U15'
    system_label = 'Lay U1.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'u15_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        "Swedish Allsvenskan":    ('>=', 4.00),  # +50.58% ROI  3/4 seasons
        "Polish Ekstraklasa":     ('>=', 4.25),  # +47.52% ROI  4/5 seasons
        "German Bundesliga 2":    ('>=', 4.25),  # +39.06% ROI  4/5 seasons
        "Danish Superligaen":     ('>=', 3.75),  # +34.92% ROI  4/5 seasons
        "Belgian Premier League": ('>=', 3.75),  # +21.98% ROI  4/5 seasons
        "Italian Serie A":        ('>=', 4.50),  # +19.51% ROI  4/5 seasons
        "Scottish Premiership":   ('>=', 2.75),  # +11.77% ROI  4/5 seasons
    }


# ── System 2: Back O2.5 ───────────────────────────────────────────────────────
class BackO25System(BaseSystem):
    """
    Back Over 2.5 Goals
    8 leagues · 585 bets · +93.41 pts · +15.97% ROI
    Filter: Match xG (Col N) >= threshold · Back odds (Col BL) 1.50–2.50
    """
    system_key   = 'Back_O25'
    system_label = 'Back O2.5'
    bet_type     = 'BACK'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o25_back'
    odds_min, odds_max = 1.5, 2.5
    leagues = {
        "Irish Premier League":    ('>=', 3.75),  # +36.88% ROI  3/4 seasons
        "English Championship":    ('>=', 4.75),  # +20.87% ROI  4/5 seasons
        "Polish Ekstraklasa":      ('>=', 4.25),  # +16.42% ROI  4/5 seasons
        "Portuguese Primeira Liga":('>=', 4.50),  # +16.38% ROI  4/5 seasons
        "Italian Serie A":         ('>=', 4.50),  # +14.91% ROI  4/5 seasons
        "Spanish Primera Division":('>=', 3.75),  # +12.40% ROI  4/5 seasons
        "Dutch Eredivisie":        ('>=', 4.50),  # +10.52% ROI  4/5 seasons
        "English Premier League":  ('>=', 4.50),  # +10.31% ROI  4/5 seasons
    }


# ── System 3: Lay O3.5 ────────────────────────────────────────────────────────
class LayO35System(BaseSystem):
    """
    Lay Over 3.5 Goals
    8 leagues · 943 bets · +144.83 pts · +15.36% ROI
    Filter: Match xG (Col N) >= or <= threshold · Lay odds (Col CB) 1.00–6.00
    LOW xG (<=): lay when few goals expected
    HIGH xG (>=): lay when both teams attack freely
    No Poisson value filter.
    """
    system_key   = 'Lay_O35'
    system_label = 'Lay O3.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o35_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        # HIGH xG
        "Spanish Segunda Division": ('>=', 4.25),  # +48.04% ROI  5/5 seasons
        "Dutch Eerste Divisie":     ('>=', 4.75),  # +13.16% ROI  4/5 seasons
        "German Bundesliga":        ('>=', 5.25),  # +12.69% ROI  4/5 seasons
        "French Ligue 1":           ('>=', 4.75),  # +10.90% ROI  4/5 seasons
        # LOW xG
        "German Bundesliga 2":      ('<=', 1.75),  # +16.20% ROI  4/5 seasons
        "Spanish Primera Division": ('<=', 1.25),  # +15.97% ROI  4/5 seasons
        "Belgian Premier League":   ('<=', 2.00),  # +13.53% ROI  5/5 seasons
        "English Championship":     ('<=', 1.25),  # +10.45% ROI  4/5 seasons
    }


# ── System 4: FHG Lay U0.5 ───────────────────────────────────────────────────
class LayFHU05System(BaseSystem):
    """
    First Half Goals — Lay Under 0.5
    7 leagues · 694 bets · +174.33 pts · +25.12% ROI
    Filter: FH xGTot (Col J) >= threshold · Lay odds (Col CG) 1.00–6.00
    """
    system_key   = 'Lay_FHU05'
    system_label = 'FHG Lay U0.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_fh_xg'
    odds_col     = 'fhu05_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        "Danish Superligaen":      ('>=', 2.50),  # +51.66% ROI  4/5 seasons
        "Polish Ekstraklasa":      ('>=', 2.25),  # +30.75% ROI  4/5 seasons
        "Portuguese Primeira Liga":('>=', 2.25),  # +29.49% ROI  5/5 seasons
        "French Ligue 1":          ('>=', 2.50),  # +23.00% ROI  4/5 seasons
        "Dutch Eredivisie":        ('>=', 2.00),  # +21.92% ROI  4/5 seasons
        "German Bundesliga":       ('>=', 2.50),  # +18.69% ROI  5/5 seasons
        "English Championship":    ('>=', 2.50),  # +13.08% ROI  4/5 seasons
    }


# ── Registry ──────────────────────────────────────────────────────────────────
ALL_SYSTEMS = [
    LayU15System(),
    BackO25System(),
    LayO35System(),
    LayFHU05System(),
]


def scan_all_systems(fixtures: pd.DataFrame) -> List[BetSignal]:
    """Run all 4 systems against a fixture DataFrame. Returns sorted signal list."""
    signals = []
    for system in ALL_SYSTEMS:
        signals.extend(system.scan(fixtures))
    signals.sort(key=lambda s: (s.date, s.time, s.league, s.home, s.system))
    return signals


def signals_to_dataframe(signals: List[BetSignal]) -> pd.DataFrame:
    """Convert BetSignal list to a display DataFrame."""
    if not signals:
        return pd.DataFrame()
    return pd.DataFrame([{
        'Date':          s.date,
        'Time':          s.time,
        'League':        s.league,
        'Home':          s.home,
        'Away':          s.away,
        'Market':        s.system,
        '6G xG':         s.xg_value,
        'Rule':          s.rule,
        'Odds':          s.odds,
        'Hist ROI':      f"+{s.hist_roi:.2f}%",
        'Bet Type':      s.bet_type,
        '_system_key':   s.system_key,
        '_hist_roi_raw': s.hist_roi,
    } for s in signals])
