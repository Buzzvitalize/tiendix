from __future__ import annotations
from fpdf import FPDF
from datetime import datetime
import inspect
from zoneinfo import ZoneInfo
from pathlib import Path
import unicodedata

try:
    from fpdf.enums import XPos, YPos
except Exception:  # pragma: no cover
    class XPos:
        LMARGIN = 'LMARGIN'
        RIGHT = 'RIGHT'

    class YPos:
        NEXT = 'NEXT'
        TOP = 'TOP'


BLUE = (30, 58, 138)
DOM_TZ = ZoneInfo("America/Santo_Domingo")

_CELL_SUPPORTS_NEW_X = 'new_x' in inspect.signature(FPDF.cell).parameters


def _cell(pdf: FPDF, w, h=0, txt='', border=0, align='', fill=False, new_x=None, new_y=None):
    if _CELL_SUPPORTS_NEW_X:
        kwargs = {'border': border, 'align': align, 'fill': fill}
        if new_x is not None:
            kwargs['new_x'] = new_x
        if new_y is not None:
            kwargs['new_y'] = new_y
        return pdf.cell(w, h, txt, **kwargs)

    ln = 1 if new_y == YPos.NEXT else 0
    result = pdf.cell(w, h, txt, border=border, align=align, fill=fill, ln=ln)
    if new_x == XPos.LMARGIN:
        pdf.set_x(pdf.l_margin)
    return result

def _money(v: float) -> str:
    return f"RD$ {v:,.2f}"


def _plain_text(value: str) -> str:
    text = '' if value is None else str(value)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text

def generate_account_statement_pdf_bytes(company: dict, client: dict, rows: list, total: float,
                                         aging: dict, overdue_pct: float) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    # header with logo and company
    logo = company.get('logo')
    if logo:
        logo_path = Path(str(logo))
        if not logo_path.is_absolute():
            logo_path = Path('static') / str(logo).lstrip('/')
        if logo_path.exists():
            pdf.image(str(logo_path), 10, 8, 30)
    pdf.set_text_color(*BLUE)
    pdf.set_font('Helvetica', 'B', 16)
    _cell(pdf, 0, 10, _plain_text(company.get('name', '')), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    details = f"{company.get('street','')}\nTel: {company.get('phone','')}\nRNC: {company.get('rnc','')}"
    pdf.multi_cell(0, 5, _plain_text(details), align='C')
    pdf.ln(2)
    pdf.set_text_color(*BLUE)
    pdf.set_font('Helvetica', 'B', 14)
    _cell(pdf, 0, 8, 'Estado de Cuenta de Cliente', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0,0,0)
    pdf.set_font('Helvetica', '', 10)
    _cell(pdf, 0, 5, _plain_text(f"Fecha: {datetime.now(DOM_TZ).strftime('%d/%m/%Y')}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    # client info
    pdf.set_font('Helvetica', 'B', 10)
    _cell(pdf, 0, 5, _plain_text(f"Cliente: {client.get('name','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 10)
    if client.get('identifier'):
        _cell(pdf, 0,5,_plain_text(f"RNC: {client.get('identifier')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    addr = ", ".join(filter(None,[client.get('street'), client.get('sector'), client.get('province')]))
    if addr:
        _cell(pdf, 0,5,_plain_text(f"Direccion: {addr}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('phone'):
        _cell(pdf, 0,5,_plain_text(f"Tel: {client.get('phone')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('email'):
        _cell(pdf, 0,5,_plain_text(f"Email: {client.get('email')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    # table
    headers = ["Documento","No. Pedido","Fecha doc.","Fecha venc.","Info","Importe","Saldo"]
    widths = [25,25,25,25,40,25,25]
    pdf.set_fill_color(*BLUE)
    pdf.set_text_color(255,255,255)
    pdf.set_font('Helvetica','B',9)
    for h,w in zip(headers,widths):
        _cell(pdf, w,8,_plain_text(h),1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='C',fill=True)
    pdf.ln()
    pdf.set_font('Helvetica','',9)
    pdf.set_text_color(0,0,0)
    for r in rows:
        _cell(pdf, widths[0],6,_plain_text(r['document']),1)
        _cell(pdf, widths[1],6,str(r['order'] or ''),1)
        _cell(pdf, widths[2],6,_plain_text(r['date']),1)
        _cell(pdf, widths[3],6,_plain_text(r['due']),1)
        _cell(pdf, widths[4],6,_plain_text(r['info'][:30]),1)
        _cell(pdf, widths[5],6,_money(r['amount']),1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='R')
        _cell(pdf, widths[6],6,_money(r['balance']),1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='R')
        pdf.ln()
    pdf.ln(4)
    pdf.set_font('Helvetica','B',10)
    _cell(pdf, 0,6,_plain_text(f'Total general: {_money(total)}'),align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica','',9)
    bucket_line = (
        f"0-30: {_money(aging['0-30'])}  31-60: {_money(aging['31-60'])}  "
        f"61-90: {_money(aging['61-90'])}  91-120: {_money(aging['91-120'])}  121+: {_money(aging['121+'])}"
    )
    pdf.multi_cell(0,5,_plain_text(bucket_line),align='R')
    _cell(pdf, 0,5,_plain_text(f"% vencido: {overdue_pct:.2f}%"),align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_font('Helvetica','',8)
    pdf.multi_cell(0,4,'Pagos a cuentas: ______\nLas facturas no pagadas luego de la fecha de vencimiento generan un cargo mensual de un 3% de mora.')
    return bytes(pdf.output())


def generate_account_statement_pdf(company: dict, client: dict, rows: list, total: float,
                                   aging: dict, overdue_pct: float) -> str:
    """Compat legacy: conserva API anterior escribiendo archivo local.

    Se mantiene por compatibilidad de importaciones antiguas, pero el flujo
    principal debe usar `generate_account_statement_pdf_bytes` para evitar
    problemas de permisos en cPanel.
    """
    payload = generate_account_statement_pdf_bytes(company, client, rows, total, aging, overdue_pct)
    output_path = 'estado_cuenta.pdf'
    with open(output_path, 'wb') as fh:
        fh.write(payload)
    return output_path
