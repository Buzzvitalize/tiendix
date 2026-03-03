from flask import Blueprint, Response, current_app, redirect, render_template, request, session, url_for

from ecf.repository import get_company_config_safe


ecf_panel_bp = Blueprint("ecf_panel_bp", __name__)


def _require_user():
    if session.get("user_id"):
        return None
    if "auth.login" in current_app.view_functions:
        return redirect(url_for("auth.login"))
    return Response("Forbidden", status=403)


def _resolve_company_id() -> int:
    role = (session.get("role") or "").strip().lower()
    q_company = request.args.get("company_id")
    if role == "admin" and q_company:
        return int(q_company)
    if session.get("company_id") is not None:
        return int(session.get("company_id"))
    raise ValueError("company_id no disponible en sesión")


@ecf_panel_bp.get("/cpaneltx/ecf")
def cpaneltx_panel():
    auth = _require_user()
    if auth is not None:
        return auth
    company_id = _resolve_company_id()
    config_safe = get_company_config_safe(company_id) or {}
    return render_template("cpaneltx_ecf.html", company_id=company_id, config=config_safe)


@ecf_panel_bp.get("/cpaneltx/ecf/help")
def cpaneltx_help():
    auth = _require_user()
    if auth is not None:
        return auth
    return redirect("/fe/guia")
