"""Paquete e-CF (FASE 3: capa de datos solamente)."""

from ecf.models import EcfCompanyConfig, EcfDocument, EcfEvent


def init_app(app):
    """Stub de inicialización para no registrar blueprints/CLI en FASE 3."""
    return app


__all__ = ["EcfCompanyConfig", "EcfDocument", "EcfEvent", "init_app"]
