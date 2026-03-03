import io
import os
from collections import defaultdict

from flask import Blueprint, jsonify, request, send_file


pse_gateway_bp = Blueprint("pse_gateway_bp", __name__, url_prefix="/pse")
_TRACK_COUNTERS = defaultdict(int)


def _enabled() -> bool:
    return (os.getenv("ECOSEA_PSE_STUB_ENABLED", "0").strip() == "1")


def _authorized() -> bool:
    expected = (os.getenv("ECOSEA_PSE_STUB_SECRET", "") or "").strip()
    if not expected:
        return False
    provided = (request.headers.get("X-PSE-SECRET", "") or "").strip()
    return provided == expected


def _guard():
    if not _enabled():
        return jsonify({"ok": False, "error": "PSE stub deshabilitado"}), 404
    if not _authorized():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    return None


@pse_gateway_bp.post("/v1/invoices")
def stub_issue_invoice():
    guard = _guard()
    if guard:
        return guard
    payload = request.get_json(silent=True) or {}
    key = payload.get("e_ncf") or payload.get("invoice_id") or "GEN"
    track_id = f"ECOSEA-PSE-{key}"
    _TRACK_COUNTERS[track_id] = 0
    return jsonify({"track_id": track_id, "status": "PROCESSING"})


@pse_gateway_bp.get("/v1/invoices/<track_id>/status")
def stub_status(track_id: str):
    guard = _guard()
    if guard:
        return guard
    _TRACK_COUNTERS[track_id] += 1
    if _TRACK_COUNTERS[track_id] >= 2:
        return jsonify({"status": "ACCEPTED", "message": "Stub accepted", "track_id": track_id})
    return jsonify({"status": "PROCESSING", "message": "Stub processing", "track_id": track_id})


@pse_gateway_bp.get("/v1/invoices/<track_id>/pdf")
def stub_pdf(track_id: str):
    guard = _guard()
    if guard:
        return guard
    data = b"%PDF-1.4\n% ECOSEA STUB\n"
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=f"{track_id}.pdf")
