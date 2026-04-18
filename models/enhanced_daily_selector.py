"""
FTS xG Portfolio — Enhanced Daily Selector Excel Export
Exact formatting per Claude_Results.xlsx inspection:

  B-F  : system light bg, system fg, size 10 | B/D/E/F=left, C=center, bold=False
  G    : system dark bg, white, bold=True, size 11, center
  H    : system light bg, system fg, bold=True, size 10, center
  I    : system light bg, system fg, bold=False, size 10, center
  J    : alternating F2F6FB/FFFFFF, fg=1A5C9E, bold=True, size 11, center
  K    : alternating F2F6FB/FFFFFF, fg=0B5E6B (positive ROI) or 155C2E, bold=True, size 11, center
  L-P  : inactive = F0F0F0 bg, CCCCCC fg | active = system light bg, 0D2B55 fg
  Q    : EEF4FF bg, 1A5C9E fg, bold=True, size 11, center
  R/S  : F2F6FB bg, 0D2B55 fg, bold=True, size 11, center
  T    : F2F6FB bg, 0D2B55 fg, bold=True, size 11, center
"""
import os, sys
from datetime import datetime
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.all_systems import BetSignal

SYS = {
    "Lay U1.5":      {"col": 12, "light": "D4EEF2", "dark": "0B5E6B", "fg": "0B5E6B"},
    "Back O2.5":     {"col": 13, "light": "D6EFE1", "dark": "217346", "fg": "217346"},
    "Lay O3.5":      {"col": 14, "light": "EBE0F0", "dark": "4A235A", "fg": "4A235A"},
    "FHG Lay U0.5":  {"col": 15, "light": "FFF0DC", "dark": "B35C00", "fg": "B35C00"},
    "Back the Draw": {"col": 16, "light": "D6EAF8", "dark": "1A5C9E", "fg": "1A5276"},
}
NAVY       = "0D2B55"
INACT_BG   = "F0F0F0"
INACT_FG   = "CCCCCC"
ACTIVE_FG  = "0D2B55"
JK_ODD_BG  = "F2F6FB"   # row index 1,3,5… (rows 3,5,7…)
JK_EVEN_BG = "FFFFFF"   # row index 2,4,6… (rows 4,6,8…)
J_FG       = "1A5C9E"
K_FG_POS   = "0B5E6B"

def _bdr():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def _c(ws, row, col, val, bg, fg, bold, size, align):
    c = ws.cell(row, col, val if val is not None else "")
    c.font      = Font(name="Arial", bold=bold, size=size, color=fg)
    c.fill      = PatternFill("solid", start_color=bg)
    c.alignment = Alignment(horizontal=align, vertical="center")
    c.border    = _bdr()

def _fmt_date(val):
    if not val or str(val).strip() in ('', 'nan', 'None'):
        return ''
    try:
        if isinstance(val, datetime):
            return val.strftime('%d/%m/%Y')
        s = str(val).strip().split(' ')[0].split('T')[0]
        if len(s) == 10 and s[2] == '/' and s[5] == '/':
            return s
        if len(s) == 10 and s[4] == '-':
            p = s.split('-')
            return f"{p[2]}/{p[1]}/{p[0]}"
        return s
    except Exception:
        return str(val)

def _fmt_time(val):
    if not val or str(val).strip() in ('', 'nan', 'None'):
        return ''
    s = str(val).strip()
    if ' ' in s:
        s = s.split(' ')[-1]
    parts = s.split(':')
    return f"{parts[0]}:{parts[1]}" if len(parts) >= 2 else s


def export_to_excel(signals: List[BetSignal], filepath: str, date_str: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Selections"
    ws.sheet_view.showGridLines = False

    for col, w in {'A':2,'B':12,'C':8,'D':25,'E':20,'F':13,'G':17,
                   'H':8,'I':21.5,'J':8,'K':10,'L':14.8,'M':13,'N':13,
                   'O':13,'P':13,'Q':10,'R':13,'S':12,'T':8.7}.items():
        ws.column_dimensions[col].width = w

    # ── Row 1: Title + system total formulas ──────────────────────────────────
    ws.row_dimensions[1].height = 21.75
    ws.merge_cells("B1:K1")
    c = ws['B1']
    c.value = f"FTS xG DAILY SELECTIONS  —  {date_str}"
    c.font  = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    c.fill  = PatternFill("solid", start_color=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center")

    for col_num, formula, bg, fg in [
        (12, "=SUM(L3:L200)", "0B5E6B", "FFFFFF"),
        (13, "=SUM(M3:M200)", "217346", "FFFFFF"),
        (14, "=SUM(N3:N200)", "4A235A", "FFFFFF"),
        (15, "=SUM(O3:O200)", "B35C00", "FFFFFF"),
        (16, "=SUM(P3:P200)", "1A5C9E", "FFFFFF"),
        (17, "=SUM(L1:P1)",   "EEF4FF", "1A5C9E"),
        (20, "=SUM(Q1*10)",   NAVY,     "FFFFFF"),
    ]:
        c = ws.cell(1, col_num, formula)
        c.font      = Font(name="Arial", bold=True, size=11, color=fg)
        c.fill      = PatternFill("solid", start_color=bg)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border    = _bdr()

    # ── Row 2: Headers ────────────────────────────────────────────────────────
    ws.row_dimensions[2].height = 18.0
    for col_num, label, bg in [
        (2,"Date",NAVY),(3,"Time",NAVY),(4,"League",NAVY),(5,"Home",NAVY),
        (6,"Away",NAVY),(7,"Market",NAVY),(8,"6G xG","0B5E6B"),(9,"Rule","0B5E6B"),
        (10,"Odds","1A5C9E"),(11,"Hist ROI","1A5C9E"),
        (12,"Lay U1.5","0B5E6B"),(13,"Back O2.5","217346"),
        (14,"Lay O3.5","4A235A"),(15,"FHG Lay U0.5","B35C00"),
        (16,"Back the Draw","1A5C9E"),(17,"Row Total","1A5C9E"),
        (18,"Month","1A5C9E"),(19,"Cumulative",NAVY),(20,"\u00a3",NAVY),
    ]:
        c = ws.cell(2, col_num, label)
        c.font      = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        c.fill      = PatternFill("solid", start_color=bg)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border    = _bdr()

    # ── Data rows ─────────────────────────────────────────────────────────────
    for i, sig in enumerate(signals):
        row    = i + 3
        ws.row_dimensions[row].height = 16.5
        cfg    = SYS.get(sig.system, SYS["Lay U1.5"])
        light  = cfg["light"]
        dark   = cfg["dark"]
        fg     = cfg["fg"]
        sys_col= cfg["col"]

        # J-K alternating bg — odd data index = F2F6FB, even = FFFFFF
        jk_bg = JK_ODD_BG if i % 2 == 0 else JK_EVEN_BG

        date_s = _fmt_date(sig.date)
        time_s = _fmt_time(sig.time)
        roi_s  = f"+{sig.hist_roi:.2f}%" if sig.hist_roi >= 0 else f"{sig.hist_roi:.2f}%"
        rule_s = sig.rule.replace(" | QUALIFIES","").replace(" | BUFFER"," \u26a0")

        # B-F: system light bg, system fg, size 10
        _c(ws, row,  2, date_s,     light, fg,    False, 10, "left")
        _c(ws, row,  3, time_s,     light, fg,    False, 10, "center")
        _c(ws, row,  4, sig.league, light, fg,    False, 10, "left")
        _c(ws, row,  5, sig.home,   light, fg,    False, 10, "left")
        _c(ws, row,  6, sig.away,   light, fg,    False, 10, "left")
        # G: dark bg, white, bold=True, size 11
        _c(ws, row,  7, sig.system, dark,  "FFFFFF", True, 11, "center")
        # H: system light bg, system fg, bold=True, size 10
        _c(ws, row,  8, sig.xg_value, light, fg,  True, 10, "center")
        # I: system light bg, system fg, bold=False, size 10
        _c(ws, row,  9, rule_s,     light, fg,    False, 10, "center")

        # J: Odds — alternating bg, 1A5C9E fg, bold=True, size 11
        # amber override for BTD buffer zone
        is_btd   = sig.system == "Back the Draw"
        is_buffer= is_btd and sig.odds < 3.60
        _c(ws, row, 10, sig.odds,
           "FFF0DC" if is_buffer else jk_bg,
           "B35C00" if is_buffer else J_FG,
           True, 11, "center")

        # K: Hist ROI — alternating bg, 0B5E6B fg, bold=True, size 11
        _c(ws, row, 11, roi_s, jk_bg, K_FG_POS, True, 11, "center")

        # L-P: inactive=F0F0F0/CCCCCC, active=system light/0D2B55
        for col_num in range(12, 17):
            c = ws.cell(row, col_num)
            if col_num == sys_col:
                c.fill = PatternFill("solid", start_color=light)
                c.font = Font(name="Arial", size=11, color=ACTIVE_FG)
            else:
                c.fill = PatternFill("solid", start_color=INACT_BG)
                c.font = Font(name="Arial", size=11, color=INACT_FG)
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border    = _bdr()

        # Q: Row total
        c = ws.cell(row, 17, f"=SUM(L{row}:P{row})")
        c.font = Font(name="Arial", bold=True, size=11, color="1A5C9E")
        c.fill = PatternFill("solid", start_color="EEF4FF")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _bdr()

        # R: Month
        c = ws.cell(row, 18,
            f'=IF(Q{row}=0,"",Q{row})' if row == 3 else f"=SUM(R{row-1}+Q{row})")
        c.font = Font(name="Arial", bold=True, size=11, color="0D2B55")
        c.fill = PatternFill("solid", start_color="F2F6FB")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _bdr()

        # S: Cumulative
        c = ws.cell(row, 19,
            f'=IF(Q{row}=0,"",Q{row})' if row == 3 else f"=SUM(S{row-1}+Q{row})")
        c.font = Font(name="Arial", bold=True, size=11, color="0D2B55")
        c.fill = PatternFill("solid", start_color="F2F6FB")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _bdr()

        # T: £
        c = ws.cell(row, 20, f"=SUM(S{row}*10)")
        c.font = Font(name="Arial", bold=True, size=11, color="0D2B55")
        c.fill = PatternFill("solid", start_color="F2F6FB")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _bdr()

    ws.freeze_panes = "B3"

    # ── Sheet 2: Results summary ──────────────────────────────────────────────
    from collections import Counter
    ws2 = wb.create_sheet("Results")
    ws2.sheet_view.showGridLines = False
    for col, w in {'A':22,'B':10,'C':10}.items():
        ws2.column_dimensions[col].width = w

    ws2.merge_cells("A1:C1")
    c = ws2['A1']
    c.value = "Daily Summary"
    c.font  = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    c.fill  = PatternFill("solid", start_color=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 24

    mc = Counter(s.system for s in signals)
    for i, sys_name in enumerate(["Lay U1.5","Back O2.5","Lay O3.5","FHG Lay U0.5","Back the Draw"]):
        r   = i + 2
        cfg = SYS[sys_name]
        cnt = mc.get(sys_name, 0)
        for col, val, bg, fg, align in [
            (1, sys_name, cfg["dark"], "FFFFFF", "left"),
            (2, cnt,      cfg["light"], cfg["fg"], "center"),
            (3, "—",      cfg["light"], cfg["fg"], "center"),
        ]:
            c = ws2.cell(r, col, val)
            c.font      = Font(name="Arial", size=10, bold=(col==1), color=fg)
            c.fill      = PatternFill("solid", start_color=bg)
            c.alignment = Alignment(horizontal=align, vertical="center")
            c.border    = _bdr()
        ws2.row_dimensions[r].height = 18

    tot = 7
    ws2.merge_cells(f"A{tot}:C{tot}")
    c = ws2[f'A{tot}']
    c.value = f"Total Selections: {len(signals)}"
    c.font  = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    c.fill  = PatternFill("solid", start_color=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = _bdr()

    wb.save(filepath)
