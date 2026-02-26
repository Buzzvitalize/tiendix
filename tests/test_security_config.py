import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app as app_module
from config import validate_runtime_config


def test_validate_runtime_config_requires_secret_in_production():
    with pytest.raises(RuntimeError, match='SECRET_KEY is required in production'):
        validate_runtime_config({'APP_ENV': 'production', 'SECRET_KEY': '', 'WTF_CSRF_ENABLED': True})


def test_validate_runtime_config_requires_csrf_outside_tests():
    with pytest.raises(RuntimeError, match='WTF_CSRF_ENABLED must be True'):
        validate_runtime_config({'APP_ENV': 'development', 'TESTING': False, 'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'x'})


def test_send_email_retries_and_metrics(monkeypatch):
    attempts = {'count': 0}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def login(self, *_):
            return None

        def sendmail(self, *_):
            attempts['count'] += 1
            if attempts['count'] < 3:
                raise RuntimeError('smtp down')

    monkeypatch.setattr(app_module, 'MAIL_SERVER', 'smtp.example.com')
    monkeypatch.setattr(app_module, 'MAIL_DEFAULT_SENDER', 'no-reply@example.com')
    monkeypatch.setattr(app_module, 'MAIL_MAX_RETRIES', 3)
    monkeypatch.setattr(app_module, 'MAIL_RETRY_DELAY_SEC', 0)
    monkeypatch.setattr(app_module.smtplib, 'SMTP', FakeSMTP)

    for key in app_module.EMAIL_METRICS:
        app_module.EMAIL_METRICS[key] = 0

    app_module.send_email('to@example.com', 'subject', '<b>ok</b>', asynchronous=False)

    assert attempts['count'] == 3
    assert app_module.EMAIL_METRICS['retries'] == 2
    assert app_module.EMAIL_METRICS['sent'] == 1
    assert app_module.EMAIL_METRICS['failed'] == 0


def test_normalized_database_url_for_mysql_scheme():
    assert app_module._normalized_database_url('mysql://u:p@localhost/db') == 'mysql+pymysql://u:p@localhost/db'
    assert app_module._normalized_database_url('mysql+pymysql://u:p@localhost/db') == 'mysql+pymysql://u:p@localhost/db'


def test_database_url_from_parts_builds_mysql_url(monkeypatch):
    monkeypatch.setenv('DB_NAME', 'cpanel_db')
    monkeypatch.setenv('DB_USER', 'cpanel_user')
    monkeypatch.setenv('DB_PASSWORD', 'my pass@123')
    monkeypatch.setenv('DB_HOST', 'localhost')
    monkeypatch.setenv('DB_PORT', '3306')
    monkeypatch.delenv('DATABASE_URL', raising=False)

    built = app_module._database_url_from_parts()

    assert built == 'mysql+pymysql://cpanel_user:my+pass%40123@localhost:3306/cpanel_db?charset=utf8mb4'


def test_resolve_database_url_prioritizes_database_url(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'mysql://u:p@localhost/db')
    monkeypatch.setenv('DB_NAME', 'ignored_db')
    monkeypatch.setenv('DB_USER', 'ignored_user')
    monkeypatch.setenv('DB_PASSWORD', 'ignored_password')

    resolved, source = app_module._resolve_database_url()

    assert resolved == 'mysql+pymysql://u:p@localhost/db'
    assert source == 'DATABASE_URL'


def test_app_version_metadata_present():
    assert app_module.APP_VERSION
    assert isinstance(app_module.APP_VERSION_HIGHLIGHTS, list)
    assert app_module.APP_VERSION_HIGHLIGHTS


def test_unhandled_exception_returns_custom_500_page():
    endpoint = 'test_force_500_runtime'
    if endpoint not in app_module.app.view_functions:
        app_module.app.add_url_rule('/_test/force-500', endpoint, lambda: (_ for _ in ()).throw(RuntimeError('boom')))

    client = app_module.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    resp = client.get('/_test/force-500')

    assert resp.status_code == 500
    assert b'ID de error' in resp.data



def test_apply_database_uri_override_sets_uri():
    cfg = {'SQLALCHEMY_DATABASE_URI': 'sqlite:///database.sqlite'}
    app_module._apply_database_uri_override(cfg, 'mysql+pymysql://u:p@localhost/db?charset=utf8mb4')
    assert cfg['SQLALCHEMY_DATABASE_URI'] == 'mysql+pymysql://u:p@localhost/db?charset=utf8mb4'


def test_apply_database_uri_override_keeps_existing_when_none():
    cfg = {'SQLALCHEMY_DATABASE_URI': 'sqlite:///database.sqlite'}
    app_module._apply_database_uri_override(cfg, None)
    assert cfg['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///database.sqlite'
