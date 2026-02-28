from __future__ import annotations
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

BLUE = (30, 58, 138)
DOM_TZ = ZoneInfo("America/Santo_Domingo")

def _money(v: float) -> str:
    return f"RD$ {v:,.2f}"

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
    pdf.cell(0, 10, company.get('name', ''), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    details = f"{company.get('street','')}\nTel: {company.get('phone','')}\nRNC: {company.get('rnc','')}"
    pdf.multi_cell(0, 5, details, align='C')
    pdf.ln(2)
    pdf.set_text_color(*BLUE)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 8, 'Estado de Cuenta de Cliente', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0,0,0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, f"Fecha: {datetime.now(DOM_TZ).strftime('%d/%m/%Y')}", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    # client info
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 5, f"Cliente: {client.get('name','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 10)
    if client.get('identifier'):
        pdf.cell(0,5,f"RNC: {client.get('identifier')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    addr = ", ".join(filter(None,[client.get('street'), client.get('sector'), client.get('province')]))
    if addr:
        pdf.cell(0,5,f"Dirección: {addr}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('phone'):
        pdf.cell(0,5,f"Tel: {client.get('phone')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('email'):
        pdf.cell(0,5,f"Email: {client.get('email')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    # table
    headers = ["Documento","No. Pedido","Fecha doc.","Fecha venc.","Info","Importe","Saldo"]
    widths = [25,25,25,25,40,25,25]
    pdf.set_fill_color(*BLUE)
    pdf.set_text_color(255,255,255)
    pdf.set_font('Helvetica','B',9)
    for h,w in zip(headers,widths):
        pdf.cell(w,8,h,1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='C',fill=True)
    pdf.ln()
    pdf.set_font('Helvetica','',9)
    pdf.set_text_color(0,0,0)
    for r in rows:
        pdf.cell(widths[0],6,r['document'],1)
        pdf.cell(widths[1],6,str(r['order'] or ''),1)
        pdf.cell(widths[2],6,r['date'],1)
        pdf.cell(widths[3],6,r['due'],1)
        pdf.cell(widths[4],6,r['info'][:30],1)
        pdf.cell(widths[5],6,_money(r['amount']),1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='R')
        pdf.cell(widths[6],6,_money(r['balance']),1,new_x=XPos.RIGHT,new_y=YPos.TOP,align='R')
        pdf.ln()
    pdf.ln(4)
    pdf.set_font('Helvetica','B',10)
    pdf.cell(0,6,f'Total general: {_money(total)}',align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica','',9)
    bucket_line = (
        f"0-30: {_money(aging['0-30'])}  31-60: {_money(aging['31-60'])}  "
        f"61-90: {_money(aging['61-90'])}  91-120: {_money(aging['91-120'])}  121+: {_money(aging['121+'])}"
    )
    pdf.multi_cell(0,5,bucket_line,align='R')
    pdf.cell(0,5,f"% vencido: {overdue_pct:.2f}%",align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
