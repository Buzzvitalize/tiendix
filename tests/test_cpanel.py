import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import User, CompanyInfo, AccountRequest, AuditLog, SystemAnnouncement, AppSetting
from werkzeug.security import generate_password_hash

@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.sqlite"
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Comp', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        admin = User(username='admin', first_name='Ad', last_name='Min', role='admin', company_id=company.id, email='admin@example.com')
        admin.set_password('363636')
        user = User(username='user', first_name='U', last_name='Ser', role='company', company_id=company.id, email='old@ex.com')
        user.set_password('123')
        db.session.add_all([admin, user])
        db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


def login(c, username, password):
    return c.post('/login', data={'username': username, 'password': password})


def test_admin_access_and_role_change(client):
    login(client, 'admin', '363636')
    r = client.get('/cpaneltx')
    assert r.status_code == 200
    # change role
    with app.app_context():
        user = User.query.filter_by(username='user').first()
    client.post(f'/cpaneltx/users/{user.id}/role', data={'role': 'manager'})
    with app.app_context():
        assert db.session.get(User, user.id).role == 'manager'


def test_admin_update_email_password(client):
    login(client, 'admin', '363636')
    with app.app_context():
        user = User.query.filter_by(username='user').first()
    client.post(f'/cpaneltx/users/{user.id}/update', data={'email': 'new@ex.com', 'password': 'newpass'})
    with app.app_context():
        u = db.session.get(User, user.id)
        assert u.email == 'new@ex.com'
        assert u.check_password('newpass')


def test_non_admin_denied(client):
    login(client, 'user', '123')
    r = client.get('/cpaneltx')
    assert r.status_code == 302


def test_account_approval_sends_email(client, monkeypatch):
    with app.app_context():
        req = AccountRequest(
            account_type='personal',
            first_name='Ana',
            last_name='Doe',
            company='AnaCo',
            identifier='001',
            phone='123',
            email='ana@example.com',
            username='anita',
            password=generate_password_hash('pw'),
            accepted_terms=True,
        )
        db.session.add(req)
        db.session.commit()
        rid = req.id
    sent = {}
    def fake_send(to, subject, html, attachments=None):
        sent['to'] = to
        sent['subject'] = subject
        sent['html'] = html
        sent['attachments'] = attachments
    monkeypatch.setattr('app.send_email', fake_send)
    login(client, 'admin', '363636')
    client.post(f'/admin/solicitudes/{rid}/aprobar', data={'role': 'company'})
    assert sent['to'] == 'ana@example.com'
    assert 'aprobada' in sent['subject'].lower()
    with app.app_context():
        user = User.query.filter_by(username='anita').first()
        assert user is not None
        assert user.check_password('pw')
        # El hash nunca debe aparecer en el correo
        assert user.password not in sent['html']
        assert '/reset/' in sent['html']


def test_cpanel_auditoria_view(client):
    login(client, 'admin', '363636')
    r = client.get('/cpaneltx/auditoria')
    assert r.status_code == 200
    assert b'Auditor' in r.data


def test_account_request_approval_writes_audit(client, monkeypatch):
    with app.app_context():
        req = AccountRequest(
            account_type='personal',
            first_name='Luis',
            last_name='Doe',
            company='LuisCo',
            identifier='002',
            phone='123',
            email='luis@example.com',
            username='luis',
            password=generate_password_hash('pw'),
            accepted_terms=True,
        )
        db.session.add(req)
        db.session.commit()
        rid = req.id

    monkeypatch.setattr('app.send_email', lambda *args, **kwargs: None)
    login(client, 'admin', '363636')
    client.post(f'/admin/solicitudes/{rid}/aprobar', data={'role': 'company'})

    with app.app_context():
        row = AuditLog.query.filter_by(action='account_request_approve').order_by(AuditLog.id.desc()).first()
        assert row is not None
        assert row.entity == 'account_request'


def test_suspicious_ips_counts_only_request_creation_action(client):
    with app.app_context():
        db.session.add_all([
            AuditLog(action='account_request_approve', entity='account_request', ip='10.10.10.10', status='ok'),
            AuditLog(action='account_request_reject', entity='account_request', ip='10.10.10.10', status='ok'),
        ])
        db.session.commit()

    login(client, 'admin', '363636')
    resp = client.get('/cpaneltx/auditoria')
    assert resp.status_code == 200
    assert b'No hay IPs repetidas en solicitudes de cuenta' in resp.data


def test_admin_can_create_system_announcement(client):
    login(client, 'admin', '363636')
    resp = client.post('/cpaneltx/avisos', data={
        'title': 'Mantenimiento',
        'message': 'Evite registrar cambios entre 10pm y 11pm',
        'is_active': 'on',
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        ann = SystemAnnouncement.query.first()
        assert ann is not None
        assert ann.is_active is True



def test_cpanel_companies_can_select_company_context(client):
    with app.app_context():
        other = CompanyInfo(name='Otra', street='', sector='', province='', phone='', rnc='')
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    login(client, 'admin', '363636')
    r = client.get(f'/cpaneltx/companies/select/{other_id}', follow_redirects=False)
    assert r.status_code == 302

    with client.session_transaction() as sess:
        assert sess.get('company_id') == other_id

    clear_resp = client.get('/cpaneltx/companies/clear', follow_redirects=False)
    assert clear_resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get('company_id') is None


def test_cpanel_can_toggle_signup_mode(client):
    login(client, 'admin', '363636')
    resp = client.post('/cpaneltx/signup-mode', data={'signup_auto_approve': '1'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        setting = db.session.get(AppSetting, 'signup_auto_approve')
        assert setting is not None
        assert setting.value == '1'


def test_signup_auto_approve_creates_manager_without_request(client):
    login(client, 'admin', '363636')
    client.post('/cpaneltx/signup-mode', data={'signup_auto_approve': '1'})

    payload = {
        'account_type': 'personal',
        'first_name': 'Auto',
        'last_name': 'Manager',
        'company': 'AutoCo',
        'identifier': '12345678901',
        'phone': '8095551234',
        'email': 'auto@example.com',
        'address': 'Santo Domingo',
        'website': '',
        'username': 'AutoUser',
        'password': '123456',
        'confirm_password': '123456',
        'accepted_terms': 'y',
        'captcha_answer': '0',
    }
    resp = client.post('/solicitar-cuenta', data=payload, follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        created = User.query.filter_by(username='autouser').first()
        assert created is not None
        assert created.role == 'manager'
        assert AccountRequest.query.filter_by(username='autouser').first() is None
