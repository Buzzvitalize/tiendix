from ecf.admin import ecf_admin_bp
from ecf.api import ecf_api_bp
from ecf.cli import register_cli
from ecf.pse_gateway import pse_gateway_bp


def init_app(app):
    app.register_blueprint(ecf_api_bp)
    app.register_blueprint(ecf_admin_bp)
    app.register_blueprint(pse_gateway_bp)
    register_cli(app)
