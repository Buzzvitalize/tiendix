"""WeasyPrint-based PDF renderer for Tiendix documents."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os

from flask import current_app
try:
    from weasyprint import HTML
except ModuleNotFoundError:  # pragma: no cover
    HTML = None

from fpdf import FPDF
from fpdf.enums import XPos, YPos

BLUE = "#1e3a8a"
STYLE = f"""
@page {{ size: A4; margin: 2cm; }}
body {{ font-family: Helvetica, Arial, sans-serif; margin:0; }}
.company-header {{ display:flex; align-items:center; margin-bottom:15px; }}
.company-logo {{ height:60px; margin-right:15px; }}
.company-name {{ font-size:24px; font-weight:bold; color:{BLUE}; }}
.company-details {{ font-size:14px; line-height:1.2; }}
.doc-title {{ text-align:right; color:{BLUE}; font-size:20px; margin-bottom:10px; }}
.meta {{ text-align:right; font-size:12px; margin-bottom:20px; }}
.client-details {{ margin-bottom:40px; font-size:14px; }}
.items {{ width:100%; border-collapse:collapse; margin-bottom:20px; font-size:14px; }}
.items th {{ background:{BLUE}; color:white; padding:6px; text-align:left; }}
.items td {{ padding:6px; border-bottom:1px solid #e5e7eb; }}
.items tr:nth-child(even) td {{ background:#f9fafb; }}
.totals {{ width:40%; margin-left:auto; font-size:14px; }}
.totals td {{ padding:4px 6px; }}
.totals tr:last-child td {{ font-size:16px; font-weight:bold; color:{BLUE}; border-top:2px solid {BLUE}; }}
.notes {{ margin-top:30px; font-size:12px; }}
.seller-pay {{ display:flex; justify-content:space-between; margin-bottom:20px; font-size:14px; }}
.footer {{ position:absolute; bottom:80px; left:20px; font-size:12px; }}
"""

def _fmt_money(value: float) -> str:
    return f"RD$ {value:,.2f}"

def _item_to_dict(item) -> dict:
    if isinstance(item, dict):
        return item
    return {
        'code': getattr(item, 'code', ''),
        'reference': getattr(item, 'reference', ''),
        'product_name': getattr(item, 'product_name', getattr(item, 'name', '')),
        'unit': getattr(item, 'unit', ''),
        'unit_price': getattr(item, 'unit_price', getattr(item, 'price', 0.0)),
        'quantity': getattr(item, 'quantity', 0),
        'discount': getattr(item, 'discount', 0.0),
    }

def _client_to_dict(client) -> dict:
    if isinstance(client, dict):
        return client
    address = ", ".join(
        filter(None, [getattr(client, 'street', None),
                      getattr(client, 'sector', None),
                      getattr(client, 'province', None)])
    )
    name = getattr(client, 'name', '')
    last = getattr(client, 'last_name', '')
    full_name = f"{name} {last}".strip()
    return {
        'name': full_name,
        'address': address,
        'phone': getattr(client, 'phone', '') or '',
        'identifier': getattr(client, 'identifier', '') or '',
        'email': getattr(client, 'email', '') or '',
    }

def build_html(title: str, company: dict, client: dict, items: list,
               subtotal: float, discount: float, itbis: float,
               total: float, meta: dict) -> str:
    rows = "".join(
        f"<tr><td>{i.get('code','')}</td><td>{i.get('reference','')}</td>"
        f"<td>{i['product_name']}</td><td>{i.get('unit','')}</td>"
        f"<td>{_fmt_money(i['unit_price'])}</td><td>{i['quantity']}</td>"
        f"<td>{_fmt_money(i.get('discount',0))}</td>"
        f"<td>{_fmt_money(i['unit_price']*i['quantity']-i.get('discount',0))}</td></tr>"
        for i in items
    )
    if len(items) < 10:
        empty_row = "<tr>" + "<td>&nbsp;</td>" * 8 + "</tr>"
        rows += empty_row * (10 - len(items))
    date = meta.get('date', datetime.now())
    meta_block = []
    if meta.get('doc_number'):
        label = meta.get('doc_label', title)
        meta_block.append(f"{label} N° {meta['doc_number']}")
    if meta.get('purchase_order'):
        meta_block.append(f"Orden de compra por cliente: {meta['purchase_order']}")
    meta_block.append(date.strftime('%d/%m/%Y %I:%M %p'))
    if meta.get('ncf'):
        meta_block.append(f"NCF: {meta['ncf']}")
    if meta.get('valid_until'):
        meta_block.append(f"Válido hasta: {meta['valid_until'].strftime('%d/%m/%Y')}")
    meta_html = "".join(f"<div>{m}</div>" for m in meta_block)
    note_html = f"<div class='notes'>{meta['note']}</div>" if meta.get('note') else ""
    seller_html = f"<div>Vendedor: {meta['seller']}</div>" if meta.get('seller') else ""
    pay_html = ""
    if meta.get('payment_method'):
        pay_html = f"<div>Método de pago: {meta['payment_method']}{' - '+meta['bank'] if meta.get('bank') else ''}</div>"
    seller_block = f"<div class='seller-pay'>{seller_html}{pay_html}</div>" if (seller_html or pay_html) else ""
    footer_html = f"<div class='footer'>{meta['footer']}</div>" if meta.get('footer') else ""
    email_line = f"Correo: {client.get('email','')}<br>" if client.get('email') else ""
    return f"""<!DOCTYPE html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<style>{STYLE}</style>
</head>
<body>
<div class='company-header'>
  <img src='{company.get('logo','')}' class='company-logo'>
  <div class='company-details'>
    <div class='company-name'>{company['name']}</div>
    <div>{company.get('address','')}<br>{company.get('phone','')}</div>
  </div>
</div>
<h1 class='doc-title'>{title}</h1>
<div class='meta'>{meta_html}</div>
<div class='client-details'>
  <strong>Detalles</strong><br>
  Nombre: {client['name']}<br>
  Cédula/RNC: {client.get('identifier','')}<br>
  Dirección: {client.get('address','')}<br>
  Teléfono: {client.get('phone','')}<br>
  {email_line}
</div>
{seller_block}
<table class='items'>
  <thead>
    <tr><th>Código</th><th>Ref</th><th>Producto</th><th>Unidad</th><th>Precio</th><th>Cant.</th><th>Desc.</th><th>Total</th></tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
<table class='totals'>
  <tr><td>Subtotal</td><td style='text-align:right'>{_fmt_money(subtotal)}</td></tr>
  <tr><td>Descuento</td><td style='text-align:right'>{_fmt_money(discount)}</td></tr>
  <tr><td>ITBIS (18%)</td><td style='text-align:right'>{_fmt_money(itbis)}</td></tr>
<tr><td>Total</td><td style='text-align:right'>{_fmt_money(total)}</td></tr>
 </table>
 {note_html}{footer_html}
</body>
</html>
"""


def _write_fallback_pdf(title: str, company: dict, client: dict, items: list,
                        subtotal: float, itbis: float, total: float,
                        output_path: Path) -> None:
    """Generate a basic PDF when WeasyPrint cannot render in the server."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, company.get('name', 'Tiendix'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Cliente: {client.get('name', '')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('identifier'):
        pdf.cell(0, 6, f"Cédula/RNC: {client.get('identifier')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(90, 7, 'Producto', border=1)
    pdf.cell(25, 7, 'Cant.', border=1)
    pdf.cell(35, 7, 'Precio', border=1)
    pdf.cell(40, 7, 'Total', border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 9)
    for item in items:
        amount = item['unit_price'] * item['quantity'] - item.get('discount', 0)
        pdf.cell(90, 6, str(item.get('product_name', ''))[:40], border=1)
        pdf.cell(25, 6, str(item.get('quantity', 0)), border=1)
        pdf.cell(35, 6, _fmt_money(item.get('unit_price', 0)), border=1)
        pdf.cell(40, 6, _fmt_money(amount), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, f"Subtotal: {_fmt_money(subtotal)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"ITBIS: {_fmt_money(itbis)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Total: {_fmt_money(total)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(output_path))

def generate_pdf(title: str, company: dict, client: dict, items: list,
                 subtotal: float, itbis: float, total: float, ncf: str | None = None,
                 seller: str | None = None, payment_method: str | None = None,
                 bank: str | None = None, purchase_order: str | None = None,
                 doc_number: int | None = None, invoice_type: str | None = None,
                 note: str | None = None, output_path: str | Path | None = None,
                 date: datetime | None = None,
                 valid_until: datetime | None = None, footer: str | None = None) -> str:
    meta = {
        'doc_number': doc_number,
        'purchase_order': purchase_order,
        'doc_label': title,
        'ncf': ncf,
        'seller': seller,
        'payment_method': payment_method,
        'bank': bank,
        'note': note,
        'date': date or datetime.now(),
        'valid_until': valid_until,
        'footer': footer,
    }
    item_dicts = [_item_to_dict(i) for i in items]
    discount_total = sum(i.get('discount', 0.0) for i in item_dicts)
    client_dict = _client_to_dict(client)
    html = build_html(title, company, client_dict, item_dicts, subtotal,
                      discount_total, itbis, total, meta)
    output_path = Path(output_path or 'document.pdf')
    current_app.logger.info("Rendering %s PDF to %s", title, output_path)

    try:
        if HTML is None:
            raise RuntimeError('WeasyPrint not available in this environment')
        HTML(string=html, base_url='.').write_pdf(output_path)
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("WeasyPrint render failed, using FPDF fallback: %s", exc)
        _write_fallback_pdf(title, company, client_dict, item_dicts, subtotal, itbis, total, output_path)

    return str(output_path)
