"""
FTS xG Portfolio — Enhanced Daily Selector Excel Export
Generates a colour-coded Excel file with all qualifying selections,
result entry columns, and running P/L totals.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.all_systems import BetSignal

# System colours
SYS_COLOURS = {
    "Lay U1.5":      {"bg": "D4EEF2", "fg": "0B5E6B", "hdr": "0B5E6B"},
    "Back O2.5":     {"bg": "D6EFE1", "fg": "217346", "hdr": "217346"},
    "Lay O3.5":      {"bg": "EBE0F0", "fg": "4A235A", "hdr": "4A235A"},
    "FHG Lay U0.5":  {"bg": "FFF0DC", "fg": "B35C00", "hdr": "B35C00"},
    "Back the Draw": {"bg": "D6EAF8", "fg": "1A5276", "hdr": "1A5276"},
}
DEFAULT_CLR = {"bg": "F5F5F5", "fg": "333333", "hdr": "333333"}

def thin_border():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def export_to_excel(signals: List[BetSignal], filepath: str, date_str: str):
    """Export qualifying selections to colour-coded Excel with result columns."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Selections"
    ws.sheet_view.showGridLines = False

    # ── Title row ─────────────────────────────────────────────────────────────
    ws.merge_cells("A1:S1")
    title_cell = ws["A1"]
    title_cell.value = f"FTS xG Portfolio — Daily Selections — {date_str}"
    title_cell.font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
    title_cell.fill = PatternFill("solid", start_color="0D2B55")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # ── Column headers ────────────────────────────────────────────────────────
    # Main selection columns + result entry columns for each system
    HEADERS = [
        ("A", "Date",        12),
        ("B", "Time",         8),
        ("C", "League",      22),
        ("D", "Home",        20),
        ("E", "Away",        20),
        ("F", "System",      16),
        ("G", "6G xG / Sup", 12),
        ("H", "Rule",        22),
        ("I", "Odds",         8),
        ("J", "Hist ROI",     9),
        # Result entry columns — one per system + BtD
        ("K", "U1.5 Result",  11),
        ("L", "U1.5 P/L",     9),
        ("M", "O2.5 Result",  11),
        ("N", "O2.5 P/L",     9),
        ("O", "O3.5 Result",  11),
        ("P", "O3.5 P/L",     9),
        ("Q", "FHG Result",   11),
        ("R", "FHG P/L",      9),
        ("S", "BtD Result",   11),
        ("T", "BtD P/L",      9),
    ]

    HDR_FILL = PatternFill("solid", start_color="1F6FEB")
    HDR_FONT = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    HDR_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_letter, header, width in HEADERS:
        c = ws[f"{col_letter}2"]
        c.value = header
        c.font = HDR_FONT
        c.fill = HDR_FILL
        c.alignment = HDR_ALIGN
        c.border = thin_border()
        ws.column_dimensions[col_letter].width = width
    ws.row_dimensions[2].height = 24

    # ── Data rows ─────────────────────────────────────────────────────────────
    for row_idx, sig in enumerate(signals, start=3):
        clr = SYS_COLOURS.get(sig.system, DEFAULT_CLR)
        bg  = PatternFill("solid", start_color=clr["bg"])
        fg  = clr["fg"]
        bdr = thin_border()

        is_btd = sig.system == "Back the Draw"

        row_data = [
            sig.date,
            sig.time,
            sig.league,
            sig.home,
            sig.away,
            sig.system,
            sig.xg_value,
            sig.rule,
            sig.odds,
            f"+{sig.hist_roi:.1f}%" if sig.hist_roi >= 0 else f"{sig.hist_roi:.1f}%",
        ]

        for col_idx, val in enumerate(row_data, start=1):
            c = ws.cell(row_idx, col_idx, val)
            c.font  = Font(name="Arial", size=10, color=fg,
                           bold=(col_idx == 6))  # bold system name
            c.fill  = bg
            c.border = bdr
            c.alignment = Alignment(
                horizontal="center" if col_idx not in [3,4,5,8] else "left",
                vertical="center"
            )

        # Odds formatting
        odds_cell = ws.cell(row_idx, 9)
        if is_btd and sig.odds < 3.60:
            # Buffer zone — amber highlight
            odds_cell.fill = PatternFill("solid", start_color="FFF0DC")
            odds_cell.font = Font(name="Arial", size=10, bold=True, color="B35C00")
        else:
            odds_cell.fill = bg

        # Result entry columns (blank, user fills in)
        result_cols = {
            "Lay U1.5":      (11, 12),
            "Back O2.5":     (13, 14),
            "Lay O3.5":      (15, 16),
            "FHG Lay U0.5":  (17, 18),
            "Back the Draw": (19, 20),
        }
        active_result_col, active_pl_col = result_cols.get(sig.system, (None, None))

        for col_num in range(11, 21):
            c = ws.cell(row_idx, col_num)
            if col_num == active_result_col:
                # Active result entry cell
                c.fill = PatternFill("solid", start_color="FFFDE7")
                c.font = Font(name="Arial", size=10)
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = Border(
                    left=Side(style="medium", color=clr["hdr"]),
                    right=Side(style="thin", color="CCCCCC"),
                    top=Side(style="thin", color="CCCCCC"),
                    bottom=Side(style="thin", color="CCCCCC"),
                )
            elif col_num == active_pl_col:
                # Active P/L entry cell
                c.fill = PatternFill("solid", start_color="E8F8F5")
                c.font = Font(name="Arial", size=10)
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = Border(
                    right=Side(style="medium", color=clr["hdr"]),
                    left=Side(style="thin", color="CCCCCC"),
                    top=Side(style="thin", color="CCCCCC"),
                    bottom=Side(style="thin", color="CCCCCC"),
                )
            else:
                # Inactive — light grey
                c.fill = PatternFill("solid", start_color="F5F5F5")
                c.border = thin_border()
            ws.row_dimensions[row_idx].height = 18

    # ── Totals row ─────────────────────────────────────────────────────────────
    if signals:
        tot_row = len(signals) + 3
        ws.merge_cells(f"A{tot_row}:J{tot_row}")
        tc = ws[f"A{tot_row}"]
        tc.value = f"Total Selections: {len(signals)}"
        tc.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        tc.fill = PatternFill("solid", start_color="0D2B55")
        tc.alignment = Alignment(horizontal="center", vertical="center")
        tc.border = thin_border()
        ws.row_dimensions[tot_row].height = 20

        # P/L sum formulas for each system result column
        pl_cols = [12, 14, 16, 18, 20]
        pl_labels = ["U1.5", "O2.5", "O3.5", "FHG", "BtD"]
        for pl_col, lbl in zip(pl_cols, pl_labels):
            col_letter = get_column_letter(pl_col)
            c = ws.cell(tot_row, pl_col)
            c.value = f"=SUM({col_letter}3:{col_letter}{tot_row-1})"
            c.font = Font(name="Arial", bold=True, size=10)
            c.fill = PatternFill("solid", start_color="E8F5E9")
            c.alignment = Alignment(horizontal="center")
            c.border = thin_border()

    # ── Freeze panes ──────────────────────────────────────────────────────────
    ws.freeze_panes = "A3"

    wb.save(filepath)
