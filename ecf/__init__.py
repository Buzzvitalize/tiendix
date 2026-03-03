"""Paquete e-CF."""

from ecf.blueprints.ecf_admin import ecf_admin_bp
from ecf.blueprints.ecf_api import ecf_api_bp
from ecf.blueprints.pse_gateway_stub import pse_gateway_bp
from ecf.blueprints.ecf_panel import ecf_panel_bp
from ecf.cli import register_cli
from ecf.models import EcfCompanyConfig, EcfDocument, EcfEvent


def init_app(app):
    """Registra blueprints e-CF (FASE 5/6)."""
    app.register_blueprint(ecf_api_bp)
    app.register_blueprint(ecf_admin_bp)
    app.register_blueprint(pse_gateway_bp)
    app.register_blueprint(ecf_panel_bp)
    return app


def register_blueprints(app):
    return init_app(app)


def init_cli(app):
    register_cli(app)
    return app


__all__ = [
    "EcfCompanyConfig",
    "EcfDocument",
    "EcfEvent",
    "init_app",
    "register_blueprints",
    "register_cli",
    "init_cli",
    "ecf_api_bp",
    "ecf_admin_bp",
    "pse_gateway_bp",
    "ecf_panel_bp",
]
