import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import weasy_pdf


def test_generate_pdf_bytes_works_without_new_x_mode(monkeypatch):
    monkeypatch.setattr(weasy_pdf, '_CELL_SUPPORTS_NEW_X', False)
    data = weasy_pdf.generate_pdf_bytes(
        'Cotización',
        {'name': 'CompA', 'address': 'Dir', 'phone': '809', 'website': 'x.com', 'logo': None},
        {'name': 'Cliente', 'address': 'A', 'phone': '809', 'identifier': '001', 'email': 'a@b.com'},
        [{'code': 'P1', 'reference': 'R1', 'product_name': 'Prod', 'unit': 'Unidad', 'unit_price': 100, 'quantity': 1, 'discount': 0}],
        100,
        18,
        118,
        doc_number=1,
    )
    assert data.startswith(b'%PDF')
