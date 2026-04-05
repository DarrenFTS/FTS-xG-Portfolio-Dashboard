"""
FTS xG Betting Systems — CONFIRMED REAL DATABASE RULES
Built and verified against FTS_Advanced_Results_xG_21-26.xlsx (35,412 rows)

4 systems · 41 league combinations · 2,517 historical bets
Total P/L: +571.03 pts · Blended ROI: +22.69% · Max DD: -31.23 pts

All leagues pass:
  ① ROI >= 10%
  ② Max 1 negative season across full history
  ③ Max drawdown >= -30 pts per league

No Poisson value filter on any system.
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


# ── FTS PreMatch column index mapping ─────────────────────────────────────────
COL_MAP = {
    'date':         0,
    'time':         1,
    'league':       3,
    'home':         4,
    'away':         5,
    'g6_fh_xg':    28,   # 6G 1st Half xGTot
    'g6_match_xg': 32,   # 6G Match xG
    'u15_lay':     70,   # U1.5 Lay Odds
    'o25_back':    63,   # O2.5 Back Odds
    'o35_lay':     79,   # O3.5 Lay Odds
    'fhu05_lay':   84,   # FHGU0.5 Lay Odds
}

# ── Historical ROI per (league, system_key) — verified from real database ─────
HIST_ROI = {
    # Lay U1.5
    ("Dutch Eredivisie",          "Lay_U15"): 61.13,
    ("Polish Ekstraklasa",        "Lay_U15"): 57.33,
    ("Swedish Allsvenskan",       "Lay_U15"): 51.70,
    ("Danish Superligaen",        "Lay_U15"): 40.43,
    ("Austrian Bundesliga",       "Lay_U15"): 33.48,
    ("Scottish Premiership",      "Lay_U15"): 32.77,
    ("Belgian Premier League",    "Lay_U15"): 11.90,
    ("Spanish Segunda Division",  "Lay_U15"): 11.46,
    ("English Premier League",    "Lay_U15"): 10.68,
    # Back O2.5
    ("English Championship",      "Back_O25"): 36.08,
    ("Portuguese Primeira Liga",  "Back_O25"): 22.60,
    ("Swiss Super League",        "Back_O25"): 14.11,
    ("Dutch Eredivisie",          "Back_O25"): 13.05,
    ("French Ligue 1",            "Back_O25"): 13.02,
    ("Irish Premier League",      "Back_O25"): 11.14,
    # Lay O3.5
    ("Dutch Eredivisie",          "Lay_O35"): 68.56,
    ("Belgian Premier League",    "Lay_O35"): 48.50,
    ("Italian Serie A",           "Lay_O35"): 43.31,
    ("Irish Premier League",      "Lay_O35"): 40.36,
    ("Danish Superligaen",        "Lay_O35"): 29.03,
    ("English Championship",      "Lay_O35"): 26.91,
    ("Scottish Premiership",      "Lay_O35"): 23.56,
    ("English League One",        "Lay_O35"): 22.20,
    ("Norwegian Tippeligaen",     "Lay_O35"): 21.58,
    ("English Premier League",    "Lay_O35"): 19.10,
    ("Swiss Super League",        "Lay_O35"): 14.58,
    ("Austrian Bundesliga",       "Lay_O35"): 14.36,
    ("Dutch Eerste Divisie",      "Lay_O35"): 13.92,
    ("German Bundesliga 2",       "Lay_O35"): 11.09,
    # FHG Lay U0.5
    ("Polish Ekstraklasa",        "Lay_FHU05"): 98.00,
    ("Swiss Super League",        "Lay_FHU05"): 55.15,
    ("German Bundesliga",         "Lay_FHU05"): 46.48,
    ("Belgian Premier League",    "Lay_FHU05"): 41.00,
    ("French Ligue 1",            "Lay_FHU05"): 40.04,
    ("German Bundesliga 2",       "Lay_FHU05"): 30.68,
    ("Scottish Premiership",      "Lay_FHU05"): 29.00,
    ("English Premier League",    "Lay_FHU05"): 24.80,
    ("Swedish Allsvenskan",       "Lay_FHU05"): 19.69,
    ("Dutch Eredivisie",          "Lay_FHU05"): 18.49,
    ("Norwegian Tippeligaen",     "Lay_FHU05"): 17.35,
    ("Spanish Segunda Division",  "Lay_FHU05"): 12.20,
}


def load_fixture_file(filepath: str) -> pd.DataFrame:
    """Load and normalise an FTS Advanced PreMatch Excel file."""
    raw = pd.read_excel(filepath, sheet_name='Sheet1', header=None)
    df  = raw.iloc[2:].copy().reset_index(drop=True)
    df  = df.rename(columns={v: k for k, v in COL_MAP.items()})
    for c in ['g6_fh_xg','g6_match_xg','u15_lay','o25_back','o35_lay','fhu05_lay']:
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
    # leagues: Dict of league_name -> (op, threshold)
    # op = '>' (xG above threshold) or '<' (xG below threshold)
    leagues: Dict = {}

    def check_odds(self, odds) -> bool:
        try:
            o = float(odds)
        except (TypeError, ValueError):
            return False
        return not np.isnan(o) and self.odds_min < o <= self.odds_max

    def check_xg(self, xg, league: str) -> Tuple[bool, str]:
        rule_val = self.leagues.get(league)
        if rule_val is None:
            return False, ''
        op, thresh = rule_val
        try:
            xg_f = float(xg)
        except (TypeError, ValueError):
            return False, ''
        if np.isnan(xg_f):
            return False, ''
        if op == '>' and xg_f > thresh:
            return True, f">= {thresh:.2f}"
        if op == '<' and xg_f < thresh:
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
    9 leagues | +23.34% ROI | 609 bets | Match xG filter | Lay odds <= 6.00
    """
    system_key   = 'Lay_U15'
    system_label = 'Lay U1.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'u15_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        "Dutch Eredivisie":         ('>', 3.90),  # +61.13% ROI  5/5 seasons
        "Polish Ekstraklasa":       ('>', 4.00),  # +57.33% ROI  4/5 seasons
        "Swedish Allsvenskan":      ('>', 3.50),  # +51.70% ROI  4/4 seasons
        "Danish Superligaen":       ('>', 4.05),  # +40.43% ROI  3/4 seasons
        "Austrian Bundesliga":      ('>', 4.00),  # +33.48% ROI  4/5 seasons
        "Scottish Premiership":     ('>', 3.40),  # +32.77% ROI  4/5 seasons
        "Belgian Premier League":   ('>', 3.65),  # +11.90% ROI  4/5 seasons
        "Spanish Segunda Division": ('>', 2.80),  # +11.46% ROI  4/5 seasons
        "English Premier League":   ('>', 3.50),  # +10.68% ROI  4/5 seasons
    }


# ── System 2: Back O2.5 ───────────────────────────────────────────────────────
class BackO25System(BaseSystem):
    """
    Back Over 2.5 Goals
    6 leagues | +16.57% ROI | 359 bets | Match xG filter | Back odds 1.50-2.50
    """
    system_key   = 'Back_O25'
    system_label = 'Back O2.5'
    bet_type     = 'BACK'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o25_back'
    odds_min, odds_max = 1.5, 2.5
    leagues = {
        "English Championship":     ('>', 3.70),  # +36.08% ROI  4/5 seasons
        "Portuguese Primeira Liga": ('>', 3.40),  # +22.60% ROI  4/5 seasons
        "Swiss Super League":       ('>', 3.90),  # +14.11% ROI  5/5 seasons
        "Dutch Eredivisie":         ('>', 4.20),  # +13.05% ROI  4/5 seasons
        "French Ligue 1":           ('>', 3.80),  # +13.02% ROI  5/5 seasons
        "Irish Premier League":     ('>', 2.80),  # +11.14% ROI  4/5 seasons
    }


# ── System 3: Lay O3.5 ────────────────────────────────────────────────────────
class LayO35System(BaseSystem):
    """
    Lay Over 3.5 Goals
    14 leagues | +22.15% ROI | 922 bets | Match xG filter | Lay odds <= 6.00
    No Poisson value filter.
    Mix of LOW xG (<=) and HIGH xG (>=) rules depending on league.
    """
    system_key   = 'Lay_O35'
    system_label = 'Lay O3.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o35_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        # LOW xG — lay the over when few goals expected
        "Dutch Eredivisie":         ('<', 1.80),  # +68.56% ROI  3/4 seasons
        "Belgian Premier League":   ('<', 1.80),  # +48.50% ROI  4/5 seasons
        "Irish Premier League":     ('<', 1.70),  # +40.36% ROI  4/5 seasons
        "Swiss Super League":       ('<', 2.20),  # +14.58% ROI  4/5 seasons
        # HIGH xG — lay the over when both teams attack freely
        "Italian Serie A":          ('>', 4.00),  # +43.31% ROI  4/4 seasons
        "Danish Superligaen":       ('>', 3.80),  # +29.03% ROI  4/5 seasons
        "English Championship":     ('>', 3.60),  # +26.91% ROI  4/5 seasons
        "Scottish Premiership":     ('>', 3.80),  # +23.56% ROI  5/5 seasons
        "English League One":       ('>', 3.85),  # +22.20% ROI  4/5 seasons
        "Norwegian Tippeligaen":    ('>', 4.20),  # +21.58% ROI  3/4 seasons
        "English Premier League":   ('>', 4.50),  # +19.10% ROI  4/5 seasons
        "Austrian Bundesliga":      ('>', 3.20),  # +14.36% ROI  4/5 seasons
        "Dutch Eerste Divisie":     ('>', 4.00),  # +13.92% ROI  4/5 seasons
        "German Bundesliga 2":      ('>', 3.50),  # +11.09% ROI  4/5 seasons
    }


# ── System 4: FHG Lay U0.5 ───────────────────────────────────────────────────
class LayFHU05System(BaseSystem):
    """
    First Half Goals — Lay Under 0.5
    12 leagues | +26.34% ROI | 627 bets | 6G FH xG filter | Lay odds <= 6.00
    """
    system_key   = 'Lay_FHU05'
    system_label = 'FHG Lay U0.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_fh_xg'
    odds_col     = 'fhu05_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        "Polish Ekstraklasa":       ('>', 2.20),  # +98.00% ROI  5/5 seasons
        "Swiss Super League":       ('>', 2.00),  # +55.15% ROI  5/5 seasons
        "German Bundesliga":        ('>', 2.40),  # +46.48% ROI  4/5 seasons
        "Belgian Premier League":   ('>', 2.20),  # +41.00% ROI  4/5 seasons
        "French Ligue 1":           ('>', 2.10),  # +40.04% ROI  4/5 seasons
        "German Bundesliga 2":      ('>', 2.20),  # +30.68% ROI  5/5 seasons
        "Scottish Premiership":     ('>', 2.00),  # +29.00% ROI  4/5 seasons
        "English Premier League":   ('>', 2.00),  # +24.80% ROI  4/5 seasons
        "Swedish Allsvenskan":      ('>', 2.10),  # +19.69% ROI  3/4 seasons
        "Dutch Eredivisie":         ('>', 1.95),  # +18.49% ROI  4/5 seasons
        "Norwegian Tippeligaen":    ('>', 2.30),  # +17.35% ROI  3/4 seasons
        "Spanish Segunda Division": ('>', 1.20),  # +12.20% ROI  4/5 seasons
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
    """Convert BetSignal list to a clean display DataFrame."""
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
