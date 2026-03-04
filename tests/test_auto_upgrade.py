import importlib

def test_ensure_admin_bootstraps_schema(monkeypatch):
    app_module = importlib.import_module('app')
    called = {}

    def fake_create_all():
        called['yes'] = True

    monkeypatch.setattr(app_module.db, 'create_all', fake_create_all)
    app_module.ensure_admin()
    assert called.get('yes') is True
