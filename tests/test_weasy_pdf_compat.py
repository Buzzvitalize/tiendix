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


def test_generate_pdf_bytes_handles_accented_text_without_ascii_crash(monkeypatch):
    monkeypatch.setattr(weasy_pdf, '_CELL_SUPPORTS_NEW_X', False)
    data = weasy_pdf.generate_pdf_bytes(
        'Cotización',
        {'name': 'Compañía Ñandú', 'address': 'Dirección céntrica', 'phone': '809', 'website': 'x.com', 'logo': None},
        {'name': 'José Peña', 'address': 'Santo Domingo', 'phone': '809', 'identifier': '001', 'email': 'jose@example.com'},
        [{'code': 'P1', 'reference': 'R1', 'product_name': 'Servicio instalación', 'unit': 'Unidad', 'unit_price': 100, 'quantity': 1, 'discount': 0}],
        100,
        18,
        118,
        note='Válida por 30 días',
        doc_number=2,
    )
    assert data.startswith(b'%PDF')


def test_generate_pdf_bytes_prefers_dest_s_output(monkeypatch):
    called = {'dest': None}
    original = weasy_pdf.FPDF.output

    def _wrapped(self, *args, **kwargs):
        if 'dest' in kwargs:
            called['dest'] = kwargs['dest']
        return original(self, *args, **kwargs)

    monkeypatch.setattr(weasy_pdf.FPDF, 'output', _wrapped)
    data = weasy_pdf.generate_pdf_bytes(
        'Cotizacion',
        {'name': 'CompA', 'address': 'Dir', 'phone': '809', 'website': 'x.com', 'logo': None},
        {'name': 'Cliente', 'address': 'A', 'phone': '809', 'identifier': '001', 'email': 'a@b.com'},
        [{'code': 'P1', 'reference': 'R1', 'product_name': 'Prod', 'unit': 'Unidad', 'unit_price': 100, 'quantity': 1, 'discount': 0}],
        100,
        18,
        118,
        doc_number=3,
    )
    assert data.startswith(b'%PDF')
    assert called['dest'] == 'S'


def test_client_to_dict_omits_none_literals():
    class Dummy:
        name = 'Juan'
        last_name = None
        street = None
        sector = 'Centro'
        province = None
        phone = None
        identifier = None
        email = None

    client = weasy_pdf._client_to_dict(Dummy())
    assert client['name'] == 'Juan'
    assert client['address'] == 'Centro'
    assert client['phone'] == ''
    assert client['identifier'] == ''
    assert client['email'] == ''
