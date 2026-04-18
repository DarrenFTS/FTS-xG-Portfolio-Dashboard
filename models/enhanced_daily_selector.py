"""
FTS xG Portfolio — Enhanced Daily Selector Excel Export
Generates output exactly matching the Claude_Results.xlsx 'Results xG' template format.
Two sheets: 'Results xG' (selections + result entry) and 'Results' (summary).
"""
import os, sys
from datetime import datetime
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.all_systems import BetSignal

# ── System colours (exact from template) ─────────────────────────────────────
SYS_CONFIG = {
    "Lay U1.5":      {"col": 12, "bg": "D4EEF2", "hdr": "0B5E6B"},
    "Back O2.5":     {"col": 13, "bg": "D6EFE1", "hdr": "217346"},
    "Lay O3.5":      {"col": 14, "bg": "EBE0F0", "hdr": "4A235A"},
    "FHG Lay U0.5":  {"col": 15, "bg": "FFF0DC", "hdr": "B35C00"},
    "Back the Draw": {"col": 16, "bg": "D6EAF8", "hdr": "0070C0"},
}

# Header background colours matching template exactly
HDR_NAVY   = "0D2B55"
HDR_TEAL   = "0B5E6B"
HDR_BLUE   = "1A5C9E"
HDR_DARKBL = "0D2B55"
INACTIVE   = "F0F0F0"  # inactive result cells
ROW_TOTAL  = "EEF4FF"
MONTH_CLR  = "EEF4FF"
CUM_CLR    = "F2F6FB"
DATE_GREEN = "92D050"  # default date cell colour (result filled in later)

def _thin(color="CCCCCC"):
    s = Side(style="thin", color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def _fmt_date(val):
    """Return DD/MM/YYYY string, strip time component."""
    if not val or val in ('', 'nan', 'None'):
        return ''
    try:
        if isinstance(val, datetime):
            return val.strftime('%d/%m/%Y')
        s = str(val).strip()
        # Already DD/MM/YYYY
        if len(s) == 10 and s[2] == '/' and s[5] == '/':
            return s
        # YYYY-MM-DD
        if len(s) >= 10 and s[4] == '-':
            return datetime.strptime(s[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        return s
    except Exception:
        return str(val).split(' ')[0].split('T')[0]

def _fmt_time(val):
    """Return HH:MM string only."""
    if not val or val in ('', 'nan', 'None'):
        return ''
    s = str(val).strip()
    # Remove date part if present
    if ' ' in s:
        s = s.split(' ')[-1]
    # Strip seconds
    parts = s.split(':')
    if len(parts) >= 2:
        return f"{parts[0]}:{parts[1]}"
    return s


def export_to_excel(signals: List[BetSignal], filepath: str, date_str: str):
    wb = Workbook()

    # ══════════════════════════════════════════════════════════════════════════
    # SHEET 1: Results xG  — exact template match
    # ══════════════════════════════════════════════════════════════════════════
    ws = wb.active
    ws.title = "Results xG"
    ws.sheet_view.showGridLines = False

    # ── Column widths (matching template) ─────────────────────────────────────
    col_widths = {
        'A': 2.0,  'B': 12.0, 'C': 8.0,  'D': 25.0, 'E': 20.0,
        'F': 13.0, 'G': 17.0, 'H': 8.0,  'I': 21.5, 'J': 8.0,
        'K': 10.0, 'L': 14.8, 'M': 13.0, 'N': 13.0, 'O': 13.0,
        'P': 13.0, 'Q': 10.0, 'R': 13.0, 'S': 12.0, 'T': 8.7,
    }
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width

    # ── Row 1: Title + system totals ──────────────────────────────────────────
    ws.row_dimensions[1].height = 21.75
    ws.merge_cells("B1:K1")
    c = ws['B1']
    c.value = f"FTS xG DAILY SELECTIONS  —  {date_str}"
    c.font = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    c.fill = PatternFill("solid", start_color=HDR_NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center")

    # System total formulas in result columns (row 1)
    n = len(signals)
    last_data = n + 2  # row 1=title, row 2=headers, data starts row 3
    total_configs = [
        ('L', "=SUM(L3:L65)"),
        ('M', "=SUM(M3:M65)"),
        ('N', "=SUM(N3:N65)"),
        ('O', "=SUM(O3:O65)"),
        ('P', "=SUM(P3:P65)"),
        ('Q', "=SUM(L1:P1)"),
        ('T', "=SUM(Q1*10)"),
    ]
    sys_hdr_colors = {
        'L': "0B5E6B", 'M': "217346", 'N': "4A235A",
        'O': "B35C00", 'P': "0070C0", 'Q': HDR_BLUE, 'T': HDR_NAVY,
    }
    for col_letter, formula in total_configs:
        c = ws[f'{col_letter}1']
        c.value = formula
        c.font = Font(name="Arial", bold=True, size=11, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=sys_hdr_colors.get(col_letter, HDR_NAVY))
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

    # ── Row 2: Column headers ─────────────────────────────────────────────────
    ws.row_dimensions[2].height = 18.0
    headers = [
        ('B', "Date",           HDR_NAVY),
        ('C', "Time",           HDR_NAVY),
        ('D', "League",         HDR_NAVY),
        ('E', "Home",           HDR_NAVY),
        ('F', "Away",           HDR_NAVY),
        ('G', "Market",         HDR_NAVY),
        ('H', "6G xG",          HDR_TEAL),
        ('I', "Rule",           HDR_TEAL),
        ('J', "Odds",           HDR_BLUE),
        ('K', "Hist ROI",       HDR_BLUE),
        ('L', "Lay U1.5",       "0B5E6B"),
        ('M', "Back O2.5",      "217346"),
        ('N', "Lay O3.5",       "4A235A"),
        ('O', "FHG Lay U0.5",   "B35C00"),
        ('P', "Back the Draw",  "0070C0"),
        ('Q', "Row Total",      HDR_BLUE),
        ('R', "Month",          HDR_BLUE),
        ('S', "Cumulative",     HDR_NAVY),
        ('T', "\u00a3",         HDR_NAVY),
    ]
    for col_letter, label, bg in headers:
        c = ws[f'{col_letter}2']
        c.value = label
        c.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=bg)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

    # ── Data rows ─────────────────────────────────────────────────────────────
    for i, sig in enumerate(signals):
        row = i + 3
        ws.row_dimensions[row].height = 16.5
        cfg = SYS_CONFIG.get(sig.system, {"col": 12, "bg": "F0F0F0", "hdr": "333333"})
        sys_col = cfg["col"]
        sys_bg  = cfg["bg"]
        is_btd  = sig.system == "Back the Draw"

        # Format date and time cleanly
        date_str_fmt = _fmt_date(sig.date)
        time_str_fmt = _fmt_time(sig.time)

        # ── Columns B–K: match info ───────────────────────────────────────────
        match_data = [
            ('B', date_str_fmt,  "left",   False, DATE_GREEN),
            ('C', time_str_fmt,  "center", False, "FFFFFF"),
            ('D', sig.league,    "left",   False, "FFFFFF"),
            ('E', sig.home,      "left",   False, "FFFFFF"),
            ('F', sig.away,      "left",   False, "FFFFFF"),
            ('G', sig.system,    "center", True,  cfg["hdr"]),
            ('H', sig.xg_value,  "center", False, "FFFFFF"),
            ('I', sig.rule,      "center", False, "FFFFFF"),
            ('J', sig.odds,      "center", False,
                  "FFF0DC" if is_btd and sig.odds < 3.60 else "FFFFFF"),
            ('K', f"+{sig.hist_roi:.2f}%" if sig.hist_roi >= 0 else f"{sig.hist_roi:.2f}%",
                  "center", False, "FFFFFF"),
        ]
        for col_letter, val, align, bold, bg in match_data:
            c = ws[f'{col_letter}{row}']
            c.value = val
            c.font = Font(name="Arial", bold=bold, size=11,
                          color="FFFFFF" if col_letter == 'G' else "000000")
            c.fill = PatternFill("solid", start_color=bg)
            c.alignment = Alignment(horizontal=align, vertical="center")
            c.border = _thin()

        # ── Columns L–P: result entry cells ───────────────────────────────────
        for col_num in range(12, 17):
            c = ws.cell(row, col_num)
            if col_num == sys_col:
                # Active result cell — use system colour
                c.fill = PatternFill("solid", start_color=sys_bg)
            else:
                # Inactive — grey
                c.fill = PatternFill("solid", start_color=INACTIVE)
            c.font = Font(name="Arial", size=11)
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = _thin()

        # ── Columns Q–T: running totals ────────────────────────────────────────
        # Q: Row total
        c = ws.cell(row, 17)
        c.value = f"=SUM(L{row}:P{row})"
        c.font = Font(name="Arial", bold=True, size=11)
        c.fill = PatternFill("solid", start_color=ROW_TOTAL)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

        # R: Month running total
        c = ws.cell(row, 18)
        if row == 3:
            c.value = f'=IF(Q{row}=0,"",Q{row})'
        else:
            c.value = f"=SUM(R{row-1}+Q{row})"
        c.font = Font(name="Arial", bold=True, size=11)
        c.fill = PatternFill("solid", start_color=MONTH_CLR)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

        # S: Cumulative
        c = ws.cell(row, 19)
        if row == 3:
            c.value = f'=IF(Q{row}=0,"",Q{row})'
        else:
            c.value = f"=SUM(S{row-1}+Q{row})"
        c.font = Font(name="Arial", bold=True, size=11)
        c.fill = PatternFill("solid", start_color=CUM_CLR)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

        # T: £ value (cumulative × 10)
        c = ws.cell(row, 20)
        c.value = f"=SUM(S{row}*10)"
        c.font = Font(name="Arial", bold=True, size=11)
        c.fill = PatternFill("solid", start_color=CUM_CLR)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

    ws.freeze_panes = "B3"

    # ══════════════════════════════════════════════════════════════════════════
    # SHEET 2: Results (summary by system)
    # ══════════════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet("Results")
    ws2.sheet_view.showGridLines = False

    from collections import Counter
    mc = Counter(s.system for s in signals)

    ws2.column_dimensions['A'].width = 22
    ws2.column_dimensions['B'].width = 10
    ws2.column_dimensions['C'].width = 10
    ws2.column_dimensions['D'].width = 12

    ws2.merge_cells("A1:D1")
    c = ws2['A1']
    c.value = "Daily Summary"
    c.font = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    c.fill = PatternFill("solid", start_color=HDR_NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 24

    for col, label in zip(['A','B','C','D'],["System","Bets","P/L","Buffer?"]):
        c = ws2[f'{col}2']
        c.value = label
        c.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", start_color=HDR_BLUE)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = _thin()

    sys_order = ["Lay U1.5","Back O2.5","Lay O3.5","FHG Lay U0.5","Back the Draw"]
    for i, sys_name in enumerate(sys_order):
        r = i + 3
        cfg = SYS_CONFIG.get(sys_name, {"bg":"F0F0F0","hdr":"333333"})
        count = mc.get(sys_name, 0)
        # Flag buffer zone bets for BTD
        buf_count = sum(1 for s in signals if s.system == sys_name
                        and sys_name == "Back the Draw" and s.odds < 3.60)

        for col, val in zip(['A','B','C','D'],[
            sys_name, count,
            f"=Selections!{get_column_letter(SYS_CONFIG[sys_name]['col'])}1" if sys_name in SYS_CONFIG else "—",
            f"{buf_count} in buffer" if buf_count > 0 else "—"
        ]):
            c = ws2.cell(r, ord(col)-64, val)
            c.font = Font(name="Arial", size=10,
                          bold=(col=='A'),
                          color="FFFFFF" if col=='A' else "000000")
            c.fill = PatternFill("solid", start_color=cfg["hdr"] if col=='A' else cfg["bg"])
            c.alignment = Alignment(horizontal="left" if col=='A' else "center",
                                    vertical="center")
            c.border = _thin()
        ws2.row_dimensions[r].height = 18

    # Total row
    tot_row = len(sys_order) + 3
    ws2.merge_cells(f"A{tot_row}:B{tot_row}")
    c = ws2[f'A{tot_row}']
    c.value = f"Total Selections: {len(signals)}"
    c.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    c.fill = PatternFill("solid", start_color=HDR_NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = _thin()

    # Rename sheet1 for cross-reference
    ws.title = "Selections"
    ws2.title = "Results"

    wb.save(filepath)
