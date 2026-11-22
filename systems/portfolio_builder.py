"""
FTS xG Portfolio — rebuild engine (single source of truth)
==========================================================

Turns an "FTS Advanced Results" Excel file (sheet FTSAdvanced) into
data/portfolio_master_sheet.json — the file every dashboard page reads.

Used by:
  * dashboard/pages/9_🔄_Update_Database.py  (upload in the browser)
  * scripts/update_dashboard.py               (run on your own computer)

Columns are found by their header names (first occurrence = 6 Game Model),
so the rebuild still works if FTS add or move columns.

System rules below are the confirmed rules from the FTS xG Portfolio
Overview document. To add/remove a league or change a threshold, edit
RULES / BTD_LEAGUES here — every page picks it up on the next rebuild.
"""
from __future__ import annotations

import io
import json
from datetime import datetime

import pandas as pd

# ── System rules ──────────────────────────────────────────────────────────────
# (op, threshold) — op ">=" means xG at or above the threshold, "<=" at or below
RULES = {
    "Lay U1.5": {
        "Polish Ekstraklasa": (">=", 4.25), "Swedish Allsvenskan": (">=", 4.00),
        "German Bundesliga 2": (">=", 4.25), "Danish Superligaen": (">=", 3.75),
        "Belgian Premier League": (">=", 3.75), "Italian Serie A": (">=", 4.50),
        "Scottish Premiership": (">=", 2.75),
    },
    "Back O2.5": {
        "Irish Premier League": (">=", 3.75), "English Championship": (">=", 4.75),
        "Italian Serie A": (">=", 4.50), "Portuguese Primeira Liga": (">=", 4.50),
        "Dutch Eredivisie": (">=", 4.50), "Spanish Primera Division": (">=", 3.75),
        "Polish Ekstraklasa": (">=", 4.25),
    },
    "Lay O3.5": {
        "Spanish Segunda Division": (">=", 4.25), "Spanish Primera Division": ("<=", 1.25),
        "German Bundesliga 2": ("<=", 1.75), "English Championship": ("<=", 1.25),
        "Belgian Premier League": ("<=", 2.00), "Dutch Eerste Divisie": (">=", 4.75),
        "French Ligue 1": (">=", 4.75),
    },
    "FHG Lay U0.5": {
        "Danish Superligaen": (">=", 2.50), "Portuguese Primeira Liga": (">=", 2.25),
        "French Ligue 1": (">=", 2.50), "Dutch Eredivisie": (">=", 2.00),
        "Polish Ekstraklasa": (">=", 2.25), "German Bundesliga": (">=", 2.50),
        "English Championship": (">=", 2.50),
    },
}

# system -> (xG field, odds field, P/L field, bet type, odds min, odds max, key)
MARKETS = {
    "Lay U1.5":     ("match_xg", "u15_odds", "u15_pl", "LAY",  1.00, 6.00, "lay_u1_5"),
    "Back O2.5":    ("match_xg", "o25_odds", "o25_pl", "BACK", 1.50, 2.50, "back_o2_5"),
    "Lay O3.5":     ("match_xg", "o35_odds", "o35_pl", "LAY",  1.00, 6.00, "lay_o3_5"),
    "FHG Lay U0.5": ("fh_xg",    "fhu_odds", "fhu_pl", "LAY",  1.00, 6.00, "fhg_lay_u0_5"),
}

# Back the Draw (TEST): league must be in this list AND its previous season's
# 0-0 rate must be below BTD_00_MAX. Then Season Home Supremacy 0.25-0.55 and
# draw odds >= 3.60. Verified to reproduce all 629 historical BTD bets.
BTD_LEAGUES = [
    "Belgian Premier League", "Dutch Eerste Divisie", "Dutch Eredivisie",
    "English Premier League", "French Ligue 1", "German Bundesliga",
    "German Bundesliga 2", "Italian Serie A", "Polish Ekstraklasa",
    "Scottish Premiership", "Spanish Primera Division", "Swiss Super League",
]
BTD_00_MAX = 6.0
BTD_SUP = (0.25, 0.55)
BTD_MIN_ODDS = 3.60

LIVE_SYSTEMS = list(RULES.keys())
ALL_SYSTEMS = LIVE_SYSTEMS + ["Back the Draw"]
BET_TYPE = {**{s: m[3] for s, m in MARKETS.items()}, "Back the Draw": "BACK"}

# Calendar-year leagues are folded into the matching cross-season bucket.
SEASON_MERGE = {
    "2022": "2022-2023", "2023": "2023-2024", "2024": "2024-2025",
    "2025": "2025-2026", "2026": "2025-2026",
}

# header name -> field; the FIRST matching column is used (6 Game Model block)
HEADERS = {
    "Date": "date", "Time": "time", "Season": "season", "Competition": "league",
    "Home Team": "home", "Away Team": "away",
    "1st Half xGTot": "fh_xg", "Match xG": "match_xg",
    "Season xG Home Supremacy": "sup",
    "Draw Back Odds": "draw_odds", "Draw BackPL": "draw_pl",
    "O2.5 Back Odds": "o25_odds", "O2.5 Back PL": "o25_pl",
    "U1.5 Lay Odds": "u15_odds", "U1.5 Lay PL": "u15_pl",
    "O3.5 Lay Odds": "o35_odds", "O3.5 Lay PL": "o35_pl",
    "FHGU0.5 Lay Odds": "fhu_odds", "FHGU0.5 Lay PL": "fhu_pl",
    "FT Home": "ft_home", "FT Away": "ft_away",
}
# fallback positions (Nov 2026 layout) if a header name ever changes
FALLBACK_IDX = {
    "date": 0, "time": 1, "season": 2, "league": 3, "home": 4, "away": 5,
    "fh_xg": 6, "match_xg": 10, "sup": 30, "draw_odds": 53, "draw_pl": 54,
    "o25_odds": 60, "o25_pl": 61, "u15_odds": 67, "u15_pl": 68,
    "o35_odds": 76, "o35_pl": 77, "fhu_odds": 81, "fhu_pl": 82,
    "ft_home": 97, "ft_away": 98,
}
NUMERIC = ["fh_xg", "match_xg", "sup", "draw_odds", "draw_pl", "o25_odds", "o25_pl",
           "u15_odds", "u15_pl", "o35_odds", "o35_pl", "fhu_odds", "fhu_pl",
           "ft_home", "ft_away"]


def load_results(src) -> tuple[pd.DataFrame, list[str]]:
    """Read the FTSAdvanced sheet (path, bytes or file-like). Returns (df, notes)."""
    if isinstance(src, (bytes, bytearray)):
        src = io.BytesIO(src)
    xl = pd.ExcelFile(src)
    sheet = "FTSAdvanced" if "FTSAdvanced" in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    names = [str(x).strip() if pd.notna(x) else "" for x in raw.iloc[1]]
    notes, cols = [], {}
    for name, field in HEADERS.items():
        if field in cols:
            continue
        if name in names:
            cols[field] = names.index(name)
        else:
            cols[field] = FALLBACK_IDX[field]
            notes.append(f"Header '{name}' not found — using column {FALLBACK_IDX[field] + 1}")
    data = raw.iloc[2:]
    df = pd.DataFrame({f: data.iloc[:, i].values for f, i in cols.items()})
    df = df[df["date"].notna()].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df = df[df["date"].notna()]
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["season"] = df["season"].astype(str).str.strip().map(lambda s: SEASON_MERGE.get(s, s))
    df["time"] = df["time"].map(_fmt_time)
    return df.reset_index(drop=True), notes


def _fmt_time(t):
    if pd.isna(t):
        return None
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    s = str(t)
    return s[:5] if len(s) >= 5 and s[2] == ":" else s


def _passes(op, thr, v):
    return v >= thr if op == ">=" else v <= thr


def zero_zero_rates(df: pd.DataFrame) -> pd.Series:
    """0-0 rate % per (league, season)."""
    played = df[df["ft_home"].notna() & df["ft_away"].notna()]
    nil = (played["ft_home"] == 0) & (played["ft_away"] == 0)
    return nil.groupby([played["league"], played["season"]]).mean() * 100


def btd_gate(df: pd.DataFrame) -> dict[str, set]:
    """season -> set of BTD leagues that qualify (prior-season 0-0 rate < 6%)."""
    rates = zero_zero_rates(df)
    seasons = sorted(df["season"].dropna().unique())
    gate = {}
    for i, s in enumerate(seasons):
        if i == 0:
            gate[s] = set()
            continue
        prev = seasons[i - 1]
        gate[s] = {lg for lg in BTD_LEAGUES
                   if (lg, prev) in rates.index and rates[(lg, prev)] < BTD_00_MAX}
    return gate


def build_bets(df: pd.DataFrame) -> list[dict]:
    """Run every system over the results and return one record per qualifying bet."""
    out = []

    def rec(r, system, key, xg, odds, pl):
        return {
            "date": r.date.strftime("%Y-%m-%d"), "time": r.time, "season": r.season,
            "league": r.league, "home": r.home, "away": r.away,
            "system": system, "system_key": key,
            "pl": round(float(pl), 2), "won": bool(pl > 0),
            "odds": round(float(odds), 2),
            "xg_value": None if pd.isna(xg) else round(float(xg), 2),
        }

    for system, rules in RULES.items():
        xg_f, o_f, pl_f, _, o_min, o_max, key = MARKETS[system]
        sub = df[df["league"].isin(rules.keys()) & df[o_f].notna() & df[pl_f].notna()
                 & df[xg_f].notna() & (df[o_f] >= o_min) & (df[o_f] <= o_max)]
        for r in sub.itertuples(index=False):
            op, thr = rules[r.league]
            xg = getattr(r, xg_f)
            if _passes(op, thr, xg):
                out.append(rec(r, system, key, xg, getattr(r, o_f), getattr(r, pl_f)))

    gate = btd_gate(df)
    lo, hi = BTD_SUP
    sub = df[df["league"].isin(BTD_LEAGUES) & df["sup"].between(lo, hi)
             & (df["draw_odds"] >= BTD_MIN_ODDS) & df["draw_pl"].notna()]
    for r in sub.itertuples(index=False):
        if r.league in gate.get(r.season, set()):
            out.append(rec(r, "Back the Draw", "Back_Draw", r.sup, r.draw_odds, r.draw_pl))

    out.sort(key=lambda b: (b["date"], b["time"] or "", b["system"]))
    return out


def gate_table(df: pd.DataFrame) -> pd.DataFrame:
    """BTD league status for the latest season (for display)."""
    rates = zero_zero_rates(df)
    seasons = sorted(df["season"].dropna().unique())
    if len(seasons) < 2:
        return pd.DataFrame()
    cur, prev = seasons[-1], seasons[-2]
    rows = []
    for lg in BTD_LEAGUES:
        r = rates.get((lg, prev))
        rows.append({"League": lg, f"{prev} 0-0 %": None if r is None else round(r, 2),
                     f"{cur} status": "Qualifies" if r is not None and r < BTD_00_MAX else "Excluded"})
    return pd.DataFrame(rows)


def summarise(bets: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(bets)
    if d.empty:
        return d
    g = d.groupby("system").agg(Bets=("pl", "size"), PL=("pl", "sum"), Won=("won", "mean"))
    g["ROI %"] = g["PL"] / g["Bets"] * 100
    g["SR %"] = g["Won"] * 100
    g = g.drop(columns="Won").reindex([s for s in ALL_SYSTEMS if s in g.index])
    g.loc["TOTAL"] = [g["Bets"].sum(), g["PL"].sum(), g["PL"].sum() / g["Bets"].sum() * 100, d["won"].mean() * 100]
    return g.round(2)


def rebuild(src) -> tuple[list[dict], pd.DataFrame, list[str]]:
    df, notes = load_results(src)
    bets = build_bets(df)
    return bets, df, notes


def to_json_bytes(bets: list[dict]) -> bytes:
    return json.dumps(bets, separators=(",", ":")).encode()


def build_info(bets: list[dict], df: pd.DataFrame) -> dict:
    return {
        "built": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "results_to": df["date"].max().strftime("%Y-%m-%d"),
        "source_rows": int(len(df)),
        "bets": len(bets),
    }
