from flask import Blueprint, jsonify, request, session

from ecf.service import EcfService


ecf_api_bp = Blueprint("ecf_api_bp", __name__, url_prefix="/api/fe")


def _company_id_from_request() -> int:
    payload = request.get_json(silent=True) or {}
    company_id = payload.get("company_id") or request.args.get("company_id") or session.get("company_id")
    if not company_id:
        raise ValueError("company_id es requerido")
    return int(company_id)


@ecf_api_bp.route("/configure", methods=["POST"])
def configure_ecf():
    payload = request.get_json(silent=True) or {}
    company_id = int(payload.get("company_id") or session.get("company_id") or 0)
    if not company_id:
        return jsonify({"ok": False, "error": "company_id es requerido"}), 400

    try:
        EcfService.upsert_company_config(
            company_id=company_id,
            enabled=bool(payload.get("enabled", False)),
            mode=str(payload.get("mode", "DIRECT_DGII")),
            settings=payload.get("settings", {}),
        )
        return jsonify({"ok": True, "company_id": company_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.route("/configure/<int:company_id>", methods=["GET"])
def get_config(company_id: int):
    config = EcfService.get_company_config(company_id)
    return jsonify({"ok": True, "config": config})


@ecf_api_bp.route("/emit", methods=["POST"])
def emit_ecf():
    payload = request.get_json(silent=True) or {}
    invoice_id = int(payload.get("invoice_id") or 0)
    if not invoice_id:
        return jsonify({"ok": False, "error": "invoice_id es requerido"}), 400
    try:
        company_id = _company_id_from_request()
        doc_id = EcfService.enqueue_invoice(invoice_id=invoice_id, company_id=company_id, xml_payload=payload.get("xml_payload"))
        return jsonify({"ok": True, "doc_id": doc_id, "status": "PENDING"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.route("/status/<int:doc_id>", methods=["GET"])
def get_status(doc_id: int):
    doc = EcfService.get_document(doc_id)
    if not doc:
        return jsonify({"ok": False, "error": "Documento no encontrado"}), 404
    return jsonify({"ok": True, "document": doc})


@ecf_api_bp.route("/process_pending", methods=["POST"])
def process_pending_endpoint():
    payload = request.get_json(silent=True) or {}
    limit = int(payload.get("limit") or request.args.get("limit") or 50)
    results = EcfService.process_pending(limit=limit)
    return jsonify({"ok": True, "processed": len(results), "results": results})
