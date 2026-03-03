from flask import Blueprint, jsonify


pse_gateway_bp = Blueprint("pse_gateway_bp", __name__, url_prefix="/pse/ecosea")


@pse_gateway_bp.route("/issue", methods=["POST"])
def ecosea_issue():
    return jsonify({"ok": True, "mode": "stub", "message": "ECOSEA issue stub listo"})


@pse_gateway_bp.route("/check/<track_id>", methods=["GET"])
def ecosea_check(track_id: str):
    return jsonify({"ok": True, "track_id": track_id, "status": "CONDITIONAL", "mode": "stub"})


@pse_gateway_bp.route("/get_pdf/<track_id>", methods=["GET"])
def ecosea_get_pdf(track_id: str):
    return jsonify({"ok": True, "track_id": track_id, "pdf": "stub-pending"})
