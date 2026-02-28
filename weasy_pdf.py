"""FPDF2-based PDF renderer for Tiendix documents.

This module keeps the same public API (`generate_pdf`) used across the app,
but renders directly with fpdf2 to avoid native WeasyPrint dependencies.
"""
from __future__ import annotations

from datetime import datetime
import inspect
import os
from zoneinfo import ZoneInfo
from pathlib import Path

from fpdf import FPDF
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
    """Compatibility wrapper for fpdf2 and legacy pyfpdf cell signatures."""
    if _CELL_SUPPORTS_NEW_X:
        return pdf.cell(w, h, txt, border=border, align=align, fill=fill, new_x=new_x, new_y=new_y)

    ln = 1 if new_y == YPos.NEXT else 0
    result = pdf.cell(w, h, txt, border=border, align=align, fill=fill, ln=ln)
    if new_x == XPos.LMARGIN:
        pdf.set_x(pdf.l_margin)
    return result


def _to_dom_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(DOM_TZ).replace(tzinfo=None)


def _fmt_money(value: float) -> str:
    return f"RD$ {value:,.2f}"


def _safe_text(value) -> str:
    """Return latin-1-safe text for built-in fonts (keeps Spanish accents)."""
    text = '' if value is None else str(value)
    return text.encode('latin-1', 'replace').decode('latin-1')


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
        filter(None, [getattr(client, 'street', None), getattr(client, 'sector', None), getattr(client, 'province', None)])
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


def _draw_header(pdf: FPDF, title: str, company: dict, date: datetime, doc_number: int | None, ncf: str | None, valid_until: datetime | None):
    left_x = pdf.l_margin
    top_y = 10
    logo_box_w = 28
    text_x = left_x + logo_box_w + 4

    # Logo a la izquierda
    logo = company.get('logo')
    logo_bottom_y = top_y
    if logo:
        logo_path = str(logo)
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=left_x, y=top_y, w=logo_box_w)
            logo_bottom_y = top_y + logo_box_w

    # Nombre y dirección/web a la derecha del logo
    pdf.set_xy(text_x, top_y)
    pdf.set_text_color(*BLUE)
    pdf.set_font('Helvetica', 'B', 18)
    _cell(pdf, 0, 8, _safe_text(company.get('name', 'Tiendix')), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    if company.get('address'):
        pdf.set_x(text_x)
        pdf.multi_cell(0, 5, _safe_text(company['address']))
    if company.get('website'):
        pdf.set_x(text_x)
        _cell(pdf, 0, 5, _safe_text(company['website']), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if company.get('phone'):
        pdf.set_x(text_x)
        _cell(pdf, 0, 5, _safe_text(f"Tel: {company['phone']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    company_block_bottom = max(pdf.get_y(), logo_bottom_y)
    pdf.set_y(company_block_bottom + 15)  # 1.5 cm

    # Bloque de documento y fechas
    pdf.set_text_color(*BLUE)
    pdf.set_font('Helvetica', 'B', 16)
    _cell(pdf, 0, 8, _safe_text(title), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    if doc_number is not None:
        _cell(pdf, 0, 5, _safe_text(f"{title} N° {doc_number}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _cell(pdf, 0, 5, _safe_text(f"Fecha de creación: {date.strftime('%d/%m/%Y %I:%M %p')}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if ncf:
        _cell(pdf, 0, 5, _safe_text(f"NCF: {ncf}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if valid_until:
        _cell(pdf, 0, 5, _safe_text(f"Válido hasta: {valid_until.strftime('%d/%m/%Y')}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(15)  # 1.5 cm


def _draw_client_block(pdf: FPDF, client: dict):
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 11)
    _cell(pdf, 0, 6, _safe_text('Detalles del cliente'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 10)
    _cell(pdf, 0, 5, _safe_text(f"Nombre: {client.get('name','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('identifier'):
        _cell(pdf, 0, 5, _safe_text(f"Cédula/RNC: {client['identifier']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('address'):
        _cell(pdf, 0, 5, _safe_text(f"Dirección: {client['address']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('phone'):
        _cell(pdf, 0, 5, _safe_text(f"Teléfono: {client['phone']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if client.get('email'):
        _cell(pdf, 0, 5, _safe_text(f"Correo: {client['email']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _draw_meta_block(pdf: FPDF, seller: str | None, payment_method: str | None, bank: str | None, purchase_order: str | None):
    details = []
    if seller:
        details.append(f"Vendedor: {seller}")
    if payment_method:
        pay = f"Método de pago: {payment_method}"
        if bank:
            pay += f" - {bank}"
        details.append(pay)
    if purchase_order:
        details.append(f"Orden de compra cliente: {purchase_order}")

    if details:
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 10)
        for line in details:
            _cell(pdf, 0, 5, _safe_text(line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _draw_items_table(pdf: FPDF, items: list[dict], min_rows: int = 15):
    headers = ["Código", "Ref", "Producto", "Unidad", "Precio", "Cant.", "Desc.", "Total"]
    widths = [18, 18, 52, 18, 24, 14, 22, 24]

    pdf.ln(3)
    pdf.set_fill_color(*BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 8)
    for h, w in zip(headers, widths):
        _cell(pdf, w, 7, _safe_text(h), border=1, align='C', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 8)
    for i in items:
        line_total = i['unit_price'] * i['quantity'] - i.get('discount', 0)
        row = [
            str(i.get('code', '')),
            str(i.get('reference', '')),
            str(i.get('product_name', ''))[:28],
            str(i.get('unit', '')),
            _fmt_money(i['unit_price']),
            str(i['quantity']),
            _fmt_money(i.get('discount', 0)),
            _fmt_money(line_total),
        ]
        for idx, (text, w) in enumerate(zip(row, widths)):
            align = 'R' if idx in (4, 6, 7) else ('C' if idx == 5 else 'L')
            _cell(pdf, w, 6, _safe_text(text), border=1, align=align, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln()

    # Añade filas vacías para que el documento no se vea vacío cuando hay pocos productos.
    empty_rows = max(0, min_rows - len(items))
    for _ in range(empty_rows):
        for idx, w in enumerate(widths):
            align = 'R' if idx in (4, 6, 7) else ('C' if idx == 5 else 'L')
            _cell(pdf, w, 6, '', border=1, align=align, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln()


def _draw_totals(pdf: FPDF, subtotal: float, itbis: float, total: float, discount: float, note: str | None, footer: str | None):
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 10)
    _cell(pdf, 0, 6, _safe_text(f"Subtotal: {_fmt_money(subtotal)}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _cell(pdf, 0, 6, _safe_text(f"Descuento: {_fmt_money(discount)}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _cell(pdf, 0, 6, _safe_text(f"ITBIS (18%): {_fmt_money(itbis)}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*BLUE)
    _cell(pdf, 0, 7, _safe_text(f"Total: {_fmt_money(total)}"), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    if note:
        pdf.ln(3)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, _safe_text(f"Nota: {note}"))
    if footer:
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, _safe_text(footer))


def generate_pdf(title: str, company: dict, client: dict, items: list,
                 subtotal: float, itbis: float, total: float, ncf: str | None = None,
                 seller: str | None = None, payment_method: str | None = None,
                 bank: str | None = None, purchase_order: str | None = None,
                 doc_number: int | None = None, invoice_type: str | None = None,
                 note: str | None = None, output_path: str | Path | None = None,
                 date: datetime | None = None,
                 valid_until: datetime | None = None, footer: str | None = None) -> str:
    item_dicts = [_item_to_dict(i) for i in items]
    client_dict = _client_to_dict(client)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    base_date = _to_dom_time(date or datetime.now(DOM_TZ))
    _draw_header(pdf, title, company, base_date, doc_number, ncf, valid_until)
    _draw_client_block(pdf, client_dict)
    _draw_meta_block(pdf, seller, payment_method, bank, purchase_order)
    _draw_items_table(pdf, item_dicts)
    total_discount = sum(float(i.get('discount', 0) or 0) for i in item_dicts)
    _draw_totals(pdf, subtotal, itbis, total, total_discount, note, footer)

    output_path = Path(output_path or 'document.pdf')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return str(output_path)


def _output_pdf_bytes(pdf: FPDF) -> bytes:
    """Return bytes for both fpdf2 and legacy pyfpdf implementations."""
    try:
        payload = pdf.output(dest='S')
    except TypeError:
        payload = pdf.output()
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode('latin-1', 'replace')
    return bytes(payload)


def generate_pdf_bytes(title: str, company: dict, client: dict, items: list,
                       subtotal: float, itbis: float, total: float, ncf: str | None = None,
                       seller: str | None = None, payment_method: str | None = None,
                       bank: str | None = None, purchase_order: str | None = None,
                       doc_number: int | None = None, invoice_type: str | None = None,
                       note: str | None = None, date: datetime | None = None,
                       valid_until: datetime | None = None, footer: str | None = None) -> bytes:
    """Render a PDF and return raw bytes (faster for direct downloads/emails)."""
    item_dicts = [_item_to_dict(i) for i in items]
    client_dict = _client_to_dict(client)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    base_date = _to_dom_time(date or datetime.now(DOM_TZ))
    _draw_header(pdf, title, company, base_date, doc_number, ncf, valid_until)
    _draw_client_block(pdf, client_dict)
    _draw_meta_block(pdf, seller, payment_method, bank, purchase_order)
    _draw_items_table(pdf, item_dicts)
    total_discount = sum(float(i.get('discount', 0) or 0) for i in item_dicts)
    _draw_totals(pdf, subtotal, itbis, total, total_discount, note, footer)

    return _output_pdf_bytes(pdf)
