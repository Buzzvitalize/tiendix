import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
import weasy_pdf


def test_generate_pdf_creates_pdf_with_fpdf_renderer(tmp_path):
    output = tmp_path / 'factura.pdf'
    company = {'name': 'Comp', 'address': 'Street', 'phone': '809-555-0000'}
    client = {'name': 'Cliente', 'identifier': '001-0000000-1'}
    items = [{'product_name': 'Producto 1', 'quantity': 2, 'unit_price': 100.0, 'discount': 0.0}]

    with app.app_context():
        path = weasy_pdf.generate_pdf(
            'Factura', company, client, items,
            subtotal=200.0, itbis=36.0, total=236.0,
            output_path=output,
        )

    assert path == str(output)
    assert output.exists()
    assert output.stat().st_size > 100
