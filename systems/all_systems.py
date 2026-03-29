"""
FTS xG Betting Systems — FINAL (from FTS_Final_Systems_xG.docx)
4 systems, 32 league combinations, 6,783 historical bets, +16.0% blended ROI.
No Poisson value filter on any system.
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


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


# FTS PreMatch column index mapping
COL_MAP = {
    'date':         0,
    'time':         1,
    'league':       3,
    'home':         4,
    'away':         5,
    'g6_fh_xg':    30,
    'g6_match_xg': 34,
    'u15_lay':     88,
    'o25_back':    84,
    'o35_lay':     95,
    'fhu05_lay':  108,
}

HIST_ROI = {
    ("German Bundesliga 2",    "Lay_U15"): 37.9,
    ("Danish Superligaen",     "Lay_U15"): 35.6,
    ("Belgian Premier League", "Lay_U15"): 25.5,
    ("Scottish Premiership",   "Lay_U15"): 16.1,
    ("French Ligue 1",         "Lay_U15"): 12.1,
    ("Swedish Allsvenskan",    "Lay_U15"): 12.0,
    ("English Championship",    "Back_O25"): 18.2,
    ("Spanish Primera Division","Back_O25"): 14.0,
    ("Portuguese Primeira Liga","Back_O25"): 12.6,
    ("English Premier League",  "Back_O25"): 12.3,
    ("Polish Ekstraklasa",      "Back_O25"): 11.9,
    ("Norwegian Tippeligaen",   "Back_O25"): 10.6,
    ("Spanish Primera Division",  "Lay_O35"): 16.2,
    ("German Bundesliga 2",       "Lay_O35"): 16.1,
    ("Belgian Premier League",    "Lay_O35"): 15.2,
    ("Spanish Segunda Division",  "Lay_O35"): 14.6,
    ("Austrian Bundesliga",       "Lay_O35"): 12.6,
    ("Irish Premier League",      "Lay_O35"): 11.6,
    ("English Championship",      "Lay_O35"): 11.5,
    ("Dutch Eerste Divisie",      "Lay_O35"): 11.0,
    ("Dutch Eredivisie",          "Lay_O35"): 10.4,
    ("Italian Serie A",           "Lay_O35"): 10.1,
    ("Polish Ekstraklasa",      "Lay_FHU05"): 34.8,
    ("Belgian Premier League",  "Lay_FHU05"): 29.4,
    ("Portuguese Primeira Liga","Lay_FHU05"): 28.3,
    ("Danish Superligaen",      "Lay_FHU05"): 26.9,
    ("German Bundesliga",       "Lay_FHU05"): 25.8,
    ("Dutch Eredivisie",        "Lay_FHU05"): 20.1,
    ("English Championship",    "Lay_FHU05"): 18.1,
    ("Scottish Premiership",    "Lay_FHU05"): 14.5,
    ("Swiss Super League",      "Lay_FHU05"): 13.0,
    ("English League One",      "Lay_FHU05"): 10.2,
}


def load_fixture_file(filepath: str) -> pd.DataFrame:
    raw = pd.read_excel(filepath, sheet_name='Sheet1', header=None)
    df = raw.iloc[2:].copy().reset_index(drop=True)
    rename = {v: k for k, v in COL_MAP.items()}
    df = df.rename(columns=rename)
    for c in ['g6_fh_xg','g6_match_xg','u15_lay','o25_back','o35_lay','fhu05_lay']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df


class BaseSystem:
    system_key: str = ''
    system_label: str = ''
    bet_type: str = 'LAY'
    xg_col: str = 'g6_match_xg'
    odds_col: str = ''
    odds_min: float = 1.0
    odds_max: float = 6.0
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
        rule_list = rule_val if isinstance(rule_val, list) else [rule_val]
        try:
            xg_f = float(xg)
        except (TypeError, ValueError):
            return False, ''
        if np.isnan(xg_f):
            return False, ''
        for (op, thresh) in rule_list:
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
            if not xg_ok:
                continue
            if not self.check_odds(odds):
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


class LayU15System(BaseSystem):
    """Lay U1.5 | 6 leagues | +19.4% ROI | Match xG >= threshold | Lay odds <= 6.00"""
    system_key   = 'Lay_U15'
    system_label = 'Lay U1.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'u15_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
        "German Bundesliga 2":    (">", 4.10),
        "Danish Superligaen":     (">", 3.65),
        "Belgian Premier League": (">", 3.75),
        "Scottish Premiership":   (">", 3.25),
        "French Ligue 1":         (">", 4.05),
        "Swedish Allsvenskan":    (">", 2.20),
    }


class BackO25System(BaseSystem):
    """Back O2.5 | 6 leagues | +13.1% ROI | Match xG >= threshold | Back odds 1.50-2.50"""
    system_key   = 'Back_O25'
    system_label = 'Back O2.5'
    bet_type     = 'BACK'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o25_back'
    odds_min, odds_max = 1.5, 2.5
    leagues = {
        "English Championship":    (">", 4.25),
        "Spanish Primera Division":(">", 3.70),
        "Portuguese Primeira Liga":(">", 3.55),
        "English Premier League":  (">", 4.30),
        "Polish Ekstraklasa":      (">", 3.95),
        "Norwegian Tippeligaen":   (">", 3.60),
    }


class LayO35System(BaseSystem):
    """
    Lay O3.5 | 10 leagues | +12.9% ROI | Match xG filter | Lay odds <= 6.00
    NO Poisson value filter — pure xG only.
    LOW xG (<=) leagues: lay when few goals expected.
    HIGH xG (>=) leagues: lay when both teams attack freely.
    """
    system_key   = 'Lay_O35'
    system_label = 'Lay O3.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_match_xg'
    odds_col     = 'o35_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
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
    }


class LayFHU05System(BaseSystem):
    """FHG Lay U0.5 | 10 leagues | +18.7% ROI | FH xG >= threshold | Lay odds <= 6.00"""
    system_key   = 'Lay_FHU05'
    system_label = 'FHG Lay U0.5'
    bet_type     = 'LAY'
    xg_col       = 'g6_fh_xg'
    odds_col     = 'fhu05_lay'
    odds_min, odds_max = 1.0, 6.0
    leagues = {
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
    }


ALL_SYSTEMS = [LayU15System(), BackO25System(), LayO35System(), LayFHU05System()]


def scan_all_systems(fixtures: pd.DataFrame) -> List[BetSignal]:
    signals = []
    for system in ALL_SYSTEMS:
        signals.extend(system.scan(fixtures))
    signals.sort(key=lambda s: (s.date, s.time, s.league, s.home, s.system))
    return signals


def signals_to_dataframe(signals: List[BetSignal]) -> pd.DataFrame:
    if not signals:
        return pd.DataFrame()
    return pd.DataFrame([{
        'Date':           s.date,
        'Time':           s.time,
        'League':         s.league,
        'Home':           s.home,
        'Away':           s.away,
        'Market':         s.system,
        '6G xG':          s.xg_value,
        'Rule':           s.rule,
        'Odds':           s.odds,
        'Hist ROI':       f"+{s.hist_roi:.1f}%",
        'Bet Type':       s.bet_type,
        '_system_key':    s.system_key,
        '_hist_roi_raw':  s.hist_roi,
    } for s in signals])
