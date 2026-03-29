"""
FTS xG Enhanced Daily Selector
Generates daily bet selections from FTS PreMatch fixture files
and exports to colour-coded Excel in the standard format.
"""
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.all_systems import load_fixture_file, scan_all_systems, signals_to_dataframe, BetSignal

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY    = "0D2B55"; MIDBLUE = "1A5C9E"; LTBLUE  = "DCE9F7"
TEAL    = "0B5E6B"; TEALLT  = "D4EEF2"
GREEN   = "155C2E"; GREENLT = "D6EFE1"; GREENMD = "217346"
PURPLE  = "4A235A"; PURPLELT= "EBE0F0"
ORANGE  = "B35C00"; ORANGELT= "FFF0DC"
WHITE   = "FFFFFF"; GREY    = "444444"; LTGREY  = "F2F6FB"
AMBERLT = "FEF3C7"; AMBER   = "92580B"

MKT_COL   = {"Lay U1.5":TEAL,"Back O2.5":GREENMD,"Lay O3.5":PURPLE,"FHG Lay U0.5":ORANGE}
MKT_LIGHT = {"Lay U1.5":TEALLT,"Back O2.5":GREENLT,"Lay O3.5":PURPLELT,"FHG Lay U0.5":ORANGELT}
MKT_TO_RESULT_COL = {"Lay U1.5":12,"Back O2.5":13,"Lay O3.5":14,"FHG Lay U0.5":15}

def _fill(h): return PatternFill("solid", fgColor=h)
def _font(h, sz=10, bold=False, italic=False):
    return Font(name="Calibri", color=h, size=sz, bold=bold, italic=italic)
def _side(s="thin", c="CCCCCC"): return Side(border_style=s, color=c)
def _bdr(): return Border(left=_side(),right=_side(),top=_side(),bottom=_side())
def _bdr_thick():
    return Border(left=_side(),right=_side(),top=_side("medium",MIDBLUE),bottom=_side())
def _aln(h="left",v="center"): return Alignment(horizontal=h,vertical=v)

def _sc(ws, row, col, val=None, bg=None, fg=WHITE, sz=10, bold=False,
        h="left", italic=False, nf=None, thick=False):
    c = ws.cell(row=row, column=col)
    if val is not None: c.value = val
    if bg: c.fill = _fill(bg)
    c.font = _font(fg, sz=sz, bold=bold, italic=italic)
    c.alignment = _aln(h=h)
    c.border = _bdr_thick() if thick else _bdr()
    if nf: c.number_format = nf
    return c


def generate_selections(fixture_path: str) -> pd.DataFrame:
    """Load fixtures, run all systems, return selections DataFrame."""
    fixtures = load_fixture_file(fixture_path)
    signals = scan_all_systems(fixtures)
    return signals_to_dataframe(signals), signals


def export_to_excel(signals: List[BetSignal], output_path: str, date_str: str = "") -> str:
    """
    Export selections to colour-coded Excel in the standard FTS format.
    Columns: Date | Time | League | Home | Away | Market | 6G xG | Rule | Odds | Hist ROI
    Result cols: Lay U1.5 | Back O2.5 | Lay O3.5 | FHG Lay U0.5
    Totals: Row Total | Cumulative
    """
    from collections import Counter

    wb = Workbook()
    ws = wb.active
    ws.title = "Selections"

    for col, w in [('A',2),('B',12),('C',8),('D',25),('E',20),('F',20),
                   ('G',17),('H',8),('I',9),('J',8),('K',10),
                   ('L',12),('M',12),('N',12),('O',16),('P',10),('Q',12)]:
        ws.column_dimensions[col].width = w

    RESULT_COLS = [
        (12,'L',"Lay U1.5",TEAL),(13,'M',"Back O2.5",GREENMD),
        (14,'N',"Lay O3.5",PURPLE),(15,'O',"FHG Lay U0.5",ORANGE),
    ]

    DATA_START = 3
    DATA_END   = DATA_START + len(signals) - 1 if signals else DATA_START

    # Row 1: title + live totals
    ws.row_dimensions[1].height = 22
    ws.merge_cells('B1:K1')
    title = f"FTS xG DAILY SELECTIONS  —  {date_str}" if date_str else "FTS xG DAILY SELECTIONS"
    _sc(ws,1,2,title,bg=NAVY,fg=WHITE,sz=11,bold=True,h="center")

    for (ci,cl,lbl,bg) in RESULT_COLS:
        c=ws.cell(row=1,column=ci)
        c.value=f"=SUM({cl}{DATA_START}:{cl}{DATA_END})"
        c.fill=_fill(bg); c.font=_font(WHITE,sz=10,bold=True)
        c.alignment=_aln(h="center"); c.border=_bdr()
        c.number_format='+0.00;-0.00;"-"'
    c=ws.cell(row=1,column=16); c.value=f"=SUM(L{DATA_START}:O{DATA_END})"
    c.fill=_fill(MIDBLUE); c.font=_font(WHITE,sz=10,bold=True)
    c.alignment=_aln(h="center"); c.border=_bdr(); c.number_format='+0.00;-0.00;"-"'
    c=ws.cell(row=1,column=17); c.value=f"=Q{DATA_END}"
    c.fill=_fill(NAVY); c.font=_font(WHITE,sz=10,bold=True)
    c.alignment=_aln(h="center"); c.border=_bdr(); c.number_format='+0.00;-0.00;"-"'

    # Row 2: column headers
    ws.row_dimensions[2].height = 18
    for (ci,lbl,bg) in [(2,"Date",NAVY),(3,"Time",NAVY),(4,"League",NAVY),
                         (5,"Home",NAVY),(6,"Away",NAVY),(7,"Market",NAVY),
                         (8,"6G xG",TEAL),(9,"Rule",TEAL),
                         (10,"Odds",MIDBLUE),(11,"Hist ROI",MIDBLUE)]:
        c=ws.cell(row=2,column=ci); c.value=lbl; c.fill=_fill(bg)
        c.font=_font(WHITE,sz=9,bold=True); c.alignment=_aln(h="center"); c.border=_bdr()
    for (ci,cl,lbl,bg) in RESULT_COLS:
        c=ws.cell(row=2,column=ci); c.value=lbl; c.fill=_fill(bg)
        c.font=_font(WHITE,sz=9,bold=True); c.alignment=_aln(h="center"); c.border=_bdr()
    c=ws.cell(row=2,column=16); c.value="Row Total"; c.fill=_fill(MIDBLUE)
    c.font=_font(WHITE,sz=9,bold=True); c.alignment=_aln(h="center"); c.border=_bdr()
    c=ws.cell(row=2,column=17); c.value="Cumulative"; c.fill=_fill(NAVY)
    c.font=_font(WHITE,sz=9,bold=True); c.alignment=_aln(h="center"); c.border=_bdr()

    # Data rows
    ALT=[LTGREY,WHITE]; prev_time=None
    for ri, s in enumerate(signals):
        row = DATA_START + ri
        ws.row_dimensions[row].height = 17
        thick = prev_time is not None and s.time != prev_time
        prev_time = s.time
        bg = ALT[ri%2]; mkt = s.system
        roi = s.hist_roi
        roi_col = GREEN if roi>=20 else (TEAL if roi>=10 else MIDBLUE)

        def cell(col_, val, bg_=None, fg_=GREY, bold_=False, h_="left", nf_=None, sz_=9):
            c=ws.cell(row=row,column=col_)
            if val is not None: c.value=val
            c.fill=_fill(bg_ or bg); c.font=_font(fg_,sz=sz_,bold=bold_)
            c.alignment=_aln(h=h_); c.border=_bdr_thick() if thick else _bdr()
            if nf_: c.number_format=nf_

        # Try to get a formatted date string
        date_val = s.date
        try:
            dt = pd.to_datetime(date_val)
            date_display = dt.strftime('%d/%m/%Y')
        except:
            date_display = str(date_val)[:10]

        cell(2, date_display, fg_=GREY)
        cell(3, s.time, fg_=GREY, bold_=True, h_="center")
        cell(4, s.league, fg_=NAVY, bold_=True)
        cell(5, s.home, fg_=GREY)
        cell(6, s.away, fg_=GREY)

        c=ws.cell(row=row,column=7)
        c.value=mkt; c.fill=_fill(MKT_COL.get(mkt,MIDBLUE))
        c.font=_font(WHITE,sz=9,bold=True); c.alignment=_aln(h="center")
        c.border=_bdr_thick() if thick else _bdr()

        cell(8,  s.xg_value, bg_=MKT_LIGHT.get(mkt,LTBLUE), fg_=NAVY, bold_=True, h_="center", nf_='0.00', sz_=10)
        cell(9,  s.rule, bg_=MKT_LIGHT.get(mkt,LTBLUE), fg_=GREY, h_="center")
        cell(10, s.odds, fg_=MIDBLUE, bold_=True, h_="center", nf_='0.00', sz_=11)
        cell(11, f"+{roi:.1f}%", fg_=roi_col, bold_=True, h_="center")

        for (ci,cl,lbl,res_bg) in RESULT_COLS:
            is_this = (MKT_TO_RESULT_COL.get(mkt)==ci)
            c=ws.cell(row=row,column=ci)
            c.fill=_fill(MKT_LIGHT.get(mkt,LTBLUE) if is_this else "F0F0F0")
            c.font=_font(NAVY if is_this else "CCCCCC",sz=10)
            c.alignment=_aln(h="center"); c.border=_bdr_thick() if thick else _bdr()
            c.number_format='+0.00;-0.00;"-"'

        c=ws.cell(row=row,column=16)
        c.value=f"=SUM(L{row}:O{row})"; c.fill=_fill("EEF4FF")
        c.font=_font(MIDBLUE,sz=10,bold=True); c.alignment=_aln(h="center")
        c.border=_bdr_thick() if thick else _bdr(); c.number_format='+0.00;-0.00;"-"'

        c=ws.cell(row=row,column=17)
        c.value=(f"=IF(P{row}=0,\"\",P{row})" if row==DATA_START else
                 f"=IF(AND(P{row}=0,Q{row-1}=\"\"),\"\",IF(Q{row-1}=\"\",P{row},Q{row-1}+P{row}))")
        c.fill=_fill(LTGREY); c.font=_font(NAVY,sz=10,bold=True)
        c.alignment=_aln(h="center"); c.border=_bdr_thick() if thick else _bdr()
        c.number_format='+0.00;-0.00;"-"'

    # Footer
    if signals:
        mc = Counter(s.system for s in signals)
        footer = DATA_END+1
        ws.merge_cells(f'B{footer}:Q{footer}')
        _sc(ws,footer,2,
           f"  {len(signals)} selections  ·  "
           f"Lay U1.5: {mc.get('Lay U1.5',0)}  ·  "
           f"Back O2.5: {mc.get('Back O2.5',0)}  ·  "
           f"Lay O3.5: {mc.get('Lay O3.5',0)}  ·  "
           f"FHG Lay U0.5: {mc.get('FHG Lay U0.5',0)}  ·  All selections: hist ROI ≥ 10%",
           bg=LTBLUE,fg=MIDBLUE,sz=9,italic=True,h="left")
        ws.row_dimensions[footer].height=14
    else:
        ws.merge_cells('B3:Q3')
        c=ws.cell(row=3,column=2)
        c.value="NO SELECTIONS TODAY — No qualifying fixtures found in today's card."
        c.fill=_fill(AMBERLT); c.font=_font(AMBER,sz=11,bold=True,italic=True)
        c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
        c.border=_bdr(); ws.row_dimensions[3].height=35

    ws.freeze_panes='B3'
    wb.save(output_path)
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python enhanced_daily_selector.py <fixture_file.xlsx> [output.xlsx]")
        sys.exit(1)
    fixture_file = sys.argv[1]
    output_file  = sys.argv[2] if len(sys.argv)>2 else "selections_output.xlsx"
    df_result, sigs = generate_selections(fixture_file)
    export_to_excel(sigs, output_file)
    print(f"Generated {len(sigs)} selections → {output_file}")
    if not df_result.empty:
        print(df_result[['Date','Time','League','Home','Away','Market','6G xG','Rule','Odds','Hist ROI']].to_string(index=False))
