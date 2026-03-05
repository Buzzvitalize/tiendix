import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, _archived_download_url, _public_logo_url


def test_app_boot_registers_legacy_archivo_endpoints_once():
    rules = [r for r in app.url_map.iter_rules() if r.rule in {
        '/pedidos/<int:order_id>/archivo',
        '/facturas/<int:invoice_id>/archivo',
    }]
    assert len([r for r in rules if r.endpoint == 'order_archived_link']) == 1
    assert len([r for r in rules if r.endpoint == 'invoice_archived_link']) == 1


def test_archived_link_generation_works_without_request_context(tmp_path):
    with app.app_context():
        old_base = app.config.get('PUBLIC_DOCS_BASE_URL')
        old_docs = app.config.get('PDF_ARCHIVE_ROOT')
        try:
            app.config['PUBLIC_DOCS_BASE_URL'] = 'https://docs.example.com'
            app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path)
            fake = tmp_path / 'acme' / '123456' / 'pedido' / 'pedido-1.pdf'
            fake.parent.mkdir(parents=True, exist_ok=True)
            fake.write_bytes(b'%PDF-1.4')
            url = _archived_download_url('pedido', 1, full_path=str(fake))
            assert url == 'https://docs.example.com/generated_docs/acme/123456/pedido/pedido-1.pdf'
        finally:
            app.config['PUBLIC_DOCS_BASE_URL'] = old_base
            app.config['PDF_ARCHIVE_ROOT'] = old_docs


def test_public_logo_url_skips_missing_and_serves_existing_file(tmp_path):
    static_dir = Path(app.static_folder)
    upload_dir = static_dir / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    missing_logo = f'uploads/logo_missing_{os.getpid()}.png'

    with app.test_request_context('/'):
        assert _public_logo_url(missing_logo) is None

    filename = f'logo_test_{os.getpid()}.png'
    logo_rel = f'uploads/{filename}'
    logo_file = upload_dir / filename
    logo_file.write_bytes(b'\x89PNG\r\n\x1a\n')

    try:
        with app.test_request_context('/'):
            served_url = _public_logo_url(filename)
            assert served_url == f'/static/{logo_rel}'

        with app.test_client() as client:
            resp = client.get(served_url)
            assert resp.status_code == 200
    finally:
        if logo_file.exists():
            logo_file.unlink()
