import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db, notify
from models import CompanyInfo, User, Notification


def test_notifications_modal_and_archive_flow(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.drop_all()
        db.create_all()
        comp = CompanyInfo(name='Comp', street='', sector='', province='', phone='', rnc='')
        db.session.add(comp)
        db.session.flush()
        u = User(username='u_notif', first_name='U', last_name='Notif', role='company', company_id=comp.id)
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()

    with app.test_client() as c:
        c.post('/login', data={'username': 'u_notif', 'password': 'pass'})
        with app.app_context():
            notify('Notificación de prueba')
            nid = Notification.query.order_by(Notification.id.desc()).first().id

        resp = c.get('/cotizaciones')
        body = resp.get_data(as_text=True)
        assert 'notifications-modal' in body
        assert 'Notificaciones archivadas' in body

        ajax = c.post(f'/notificaciones/{nid}/leer', headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})
        assert ajax.status_code == 200
        data = ajax.get_json()
        assert data.get('ok') is True
        assert data.get('read_at')

        with app.app_context():
            n = db.session.get(Notification, nid)
            assert n.is_read is True
            assert n.read_at is not None
