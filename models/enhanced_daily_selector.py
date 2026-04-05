"""FTS xG Daily Selector — Excel export"""
import pandas as pd, numpy as np
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from typing import List
import sys, os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.all_systems import BetSignal

def _fill(h): return PatternFill("solid",fgColor=h)
def _font(h,sz=10,bold=False): return Font(name="Calibri",color=h,size=sz,bold=bold)
def _side(): return Side(border_style="thin",color="CCCCCC")
def _bdr(): return Border(left=_side(),right=_side(),top=_side(),bottom=_side())
def _aln(h="left"): return Alignment(horizontal=h,vertical="center")

MKT_BG  ={"Lay U1.5":"0B5E6B","Back O2.5":"217346","Lay O3.5":"4A235A","FHG Lay U0.5":"B35C00"}
MKT_LT  ={"Lay U1.5":"D4EEF2","Back O2.5":"D6EFE1","Lay O3.5":"EBE0F0","FHG Lay U0.5":"FFF0DC"}
MKT_COL ={"Lay U1.5":12,"Back O2.5":13,"Lay O3.5":14,"FHG Lay U0.5":15}

def export_to_excel(signals: List[BetSignal], output_path: str, date_str: str="") -> str:
    from collections import Counter
    wb=Workbook(); ws=wb.active; ws.title="Selections"
    for col,w in [('A',2),('B',13),('C',8),('D',25),('E',20),('F',20),
                  ('G',17),('H',8),('I',9),('J',8),('K',10),
                  ('L',12),('M',12),('N',12),('O',16),('P',10),('Q',12)]:
        ws.column_dimensions[col].width=w

    DS=3; DE=DS+len(signals)-1 if signals else DS
    RES=[(12,'L',"Lay U1.5","0B5E6B"),(13,'M',"Back O2.5","217346"),
         (14,'N',"Lay O3.5","4A235A"),(15,'O',"FHG Lay U0.5","B35C00")]

    # Row 1 — title + totals
    ws.row_dimensions[1].height=22
    ws.merge_cells('B1:K1')
    t=f"FTS xG DAILY SELECTIONS  —  {date_str}" if date_str else "FTS xG DAILY SELECTIONS"
    c=ws.cell(row=1,column=2,value=t)
    c.fill=_fill("0D2B55"); c.font=_font("FFFFFF",sz=11,bold=True)
    c.alignment=_aln("center"); c.border=_bdr()
    for (ci,cl,lbl,bg) in RES:
        c=ws.cell(row=1,column=ci); c.value=f"=SUM({cl}{DS}:{cl}{DE})"
        c.fill=_fill(bg); c.font=_font("FFFFFF",sz=10,bold=True)
        c.alignment=_aln("center"); c.border=_bdr(); c.number_format='+0.00;-0.00;"-"'
    c=ws.cell(row=1,column=16); c.value=f"=SUM(L{DS}:O{DE})"
    c.fill=_fill("1A5C9E"); c.font=_font("FFFFFF",sz=10,bold=True)
    c.alignment=_aln("center"); c.border=_bdr(); c.number_format='+0.00;-0.00;"-"'
    c=ws.cell(row=1,column=17); c.value=f"=Q{DE}"
    c.fill=_fill("0D2B55"); c.font=_font("FFFFFF",sz=10,bold=True)
    c.alignment=_aln("center"); c.border=_bdr(); c.number_format='+0.00;-0.00;"-"'

    # Row 2 — headers
    ws.row_dimensions[2].height=18
    for (ci,lbl,bg) in [(2,"Date","0D2B55"),(3,"Time","0D2B55"),(4,"League","0D2B55"),
                         (5,"Home","0D2B55"),(6,"Away","0D2B55"),(7,"Market","0D2B55"),
                         (8,"6G xG","0B5E6B"),(9,"Rule","0B5E6B"),(10,"Odds","1A5C9E"),(11,"Hist ROI","1A5C9E")]:
        c=ws.cell(row=2,column=ci,value=lbl); c.fill=_fill(bg)
        c.font=_font("FFFFFF",sz=9,bold=True); c.alignment=_aln("center"); c.border=_bdr()
    for (ci,cl,lbl,bg) in RES:
        c=ws.cell(row=2,column=ci,value=lbl); c.fill=_fill(bg)
        c.font=_font("FFFFFF",sz=9,bold=True); c.alignment=_aln("center"); c.border=_bdr()
    c=ws.cell(row=2,column=16,value="Row Total"); c.fill=_fill("1A5C9E")
    c.font=_font("FFFFFF",sz=9,bold=True); c.alignment=_aln("center"); c.border=_bdr()
    c=ws.cell(row=2,column=17,value="Cumulative"); c.fill=_fill("0D2B55")
    c.font=_font("FFFFFF",sz=9,bold=True); c.alignment=_aln("center"); c.border=_bdr()

    ALT=["F2F6FB","FFFFFF"]
    for ri,s in enumerate(signals):
        row=DS+ri; ws.row_dimensions[row].height=17
        bg=ALT[ri%2]; mkt=s.system
        roi=s.hist_roi; roi_col="155C2E" if roi>=20 else ("0B5E6B" if roi>=10 else "1A5C9E")
        try:
            dt=pd.to_datetime(s.date); dd=dt.strftime('%d/%m/%Y')
        except: dd=str(s.date)[:10]
        def sc(col,val,bg_=None,fg="444444",bold=False,h="left",nf=None,sz=9):
            c2=ws.cell(row=row,column=col); c2.value=val
            c2.fill=_fill(bg_ or bg); c2.font=_font(fg,sz=sz,bold=bold)
            c2.alignment=_aln(h=h); c2.border=_bdr()
            if nf: c2.number_format=nf
        sc(2,dd); sc(3,s.time,fg="444444",bold=True,h="center")
        sc(4,s.league,fg="0D2B55",bold=True); sc(5,s.home); sc(6,s.away)
        c2=ws.cell(row=row,column=7); c2.value=mkt
        c2.fill=_fill(MKT_BG.get(mkt,"1A5C9E")); c2.font=_font("FFFFFF",sz=9,bold=True)
        c2.alignment=_aln("center"); c2.border=_bdr()
        sc(8,s.xg_value,bg_=MKT_LT.get(mkt,"DCE9F7"),fg="0D2B55",bold=True,h="center",nf='0.00',sz=10)
        sc(9,s.rule,bg_=MKT_LT.get(mkt,"DCE9F7"),fg="444444",h="center")
        sc(10,s.odds,fg="1A5C9E",bold=True,h="center",nf='0.00',sz=11)
        sc(11,f"+{roi:.2f}%",fg=roi_col,bold=True,h="center")
        for (ci,cl,lbl,rbg) in RES:
            is_this=(MKT_COL.get(mkt)==ci)
            c2=ws.cell(row=row,column=ci)
            c2.fill=_fill(MKT_LT.get(mkt,"F0F0F0") if is_this else "F0F0F0")
            c2.font=_font("0D2B55" if is_this else "CCCCCC",sz=10)
            c2.alignment=_aln("center"); c2.border=_bdr(); c2.number_format='+0.00;-0.00;"-"'
        c2=ws.cell(row=row,column=16); c2.value=f"=SUM(L{row}:O{row})"
        c2.fill=_fill("EEF4FF"); c2.font=_font("1A5C9E",sz=10,bold=True)
        c2.alignment=_aln("center"); c2.border=_bdr(); c2.number_format='+0.00;-0.00;"-"'
        c2=ws.cell(row=row,column=17)
        c2.value=(f"=IF(P{row}=0,\"\",P{row})" if row==DS else
                  f"=IF(AND(P{row}=0,Q{row-1}=\"\"),\"\",IF(Q{row-1}=\"\",P{row},Q{row-1}+P{row}))")
        c2.fill=_fill("F2F6FB"); c2.font=_font("0D2B55",sz=10,bold=True)
        c2.alignment=_aln("center"); c2.border=_bdr(); c2.number_format='+0.00;-0.00;"-"'

    if signals:
        mc=Counter(s.system for s in signals); fr=DE+1
        ws.merge_cells(f'B{fr}:Q{fr}')
        c2=ws.cell(row=fr,column=2)
        c2.value=(f"  {len(signals)} selections  ·  Lay U1.5:{mc.get('Lay U1.5',0)}  ·  "
                  f"Back O2.5:{mc.get('Back O2.5',0)}  ·  Lay O3.5:{mc.get('Lay O3.5',0)}  ·  "
                  f"FHG Lay U0.5:{mc.get('FHG Lay U0.5',0)}")
        c2.fill=_fill("DCE9F7"); c2.font=_font("1A5C9E",sz=9); c2.border=_bdr()
        ws.row_dimensions[fr].height=14
    ws.freeze_panes='B3'
    wb.save(output_path)
    return output_path
