import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db


def test_sensitive_paths_are_blocked(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        assert client.get('/app.py').status_code == 404
        assert client.get('/requirements.txt').status_code == 404
        assert client.get('/database.sqlite').status_code == 404
        # Normal public route should remain reachable
        assert client.get('/login').status_code == 200

    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()
