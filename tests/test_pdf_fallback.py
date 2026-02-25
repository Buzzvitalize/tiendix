import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
import weasy_pdf


def test_generate_pdf_uses_fallback_when_weasyprint_fails(tmp_path, monkeypatch):
    class BrokenHTML:
        def __init__(self, *args, **kwargs):
            pass

        def write_pdf(self, *_args, **_kwargs):
            raise RuntimeError('missing cairo runtime')

    monkeypatch.setattr(weasy_pdf, 'HTML', BrokenHTML)

    output = tmp_path / 'fallback.pdf'
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
