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
