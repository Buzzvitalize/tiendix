from flask import Blueprint, render_template


ecf_admin_bp = Blueprint("ecf_admin_bp", __name__, url_prefix="/fe")


@ecf_admin_bp.route("/guia", methods=["GET"])
def fe_guia():
    return render_template("ecf/guia.html")


@ecf_admin_bp.route("/wizard", methods=["GET"])
def fe_wizard():
    return render_template("ecf/wizard.html")
