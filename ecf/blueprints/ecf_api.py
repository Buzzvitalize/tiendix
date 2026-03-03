import base64
import io
from flask import Blueprint, jsonify, request, send_file, session

from ecf.constants import ECF_MODES
from ecf.models import EcfDocument
from ecf.repository import get_company_config_safe, get_company_config, upsert_company_config
from ecf.service import issue_ecf_for_invoice, check_one


ecf_api_bp = Blueprint("ecf_api_bp", __name__, url_prefix="/api")


def _require_session() -> None:
    if not session.get("user_id"):
        raise PermissionError("Sesión requerida")


def _resolve_company_id(from_body: bool = False) -> int:
    _require_session()
    role = (session.get("role") or "").strip().lower()
    session_company = session.get("company_id")

    payload = request.get_json(silent=True) or {}
    candidate = payload.get("company_id") if from_body else request.args.get("company_id")

    if role == "admin" and candidate:
        return int(candidate)

    if session_company is not None:
        return int(session_company)

    raise ValueError("company_id no disponible en sesión")


def _can_access_doc(doc: EcfDocument, company_id: int) -> bool:
    role = (session.get("role") or "").strip().lower()
    return role == "admin" or int(doc.company_id) == int(company_id)


@ecf_api_bp.get("/fe/config")
def fe_get_config():
    try:
        company_id = _resolve_company_id(from_body=False)
        cfg = get_company_config_safe(company_id)
        return jsonify({"ok": True, "company_id": company_id, "config": cfg})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.post("/fe/config")
def fe_set_config():
    try:
        company_id = _resolve_company_id(from_body=True)
        payload = request.get_json(silent=True) or {}

        fields = {}
        for key in (
            "enabled", "mode", "dgii_env", "mock_sign", "cert_storage_mode", "cert_password", "cert_path",
            "seq_enfcf_consumidor_last", "seq_enfcf_credito_last", "pse_base_url", "pse_issue_url", "pse_status_url",
            "pse_pdf_url", "pse_api_key", "pse_client_id", "pse_client_secret", "pse_webhook_secret", "pse_env",
        ):
            if key in payload:
                fields[key] = payload[key]

        if "mode" in fields and fields["mode"] not in ECF_MODES:
            raise ValueError(f"mode inválido: {fields['mode']}")

        settings = payload.get("settings_json") if isinstance(payload.get("settings_json"), dict) else None
        if settings is None:
            cfg_prev = get_company_config(company_id)
            settings = dict(getattr(cfg_prev, "settings_json", {}) or {})

        if "rnc_emisor" in payload:
            raw_rnc = payload.get("rnc_emisor")
            if isinstance(raw_rnc, str):
                normalized_rnc = raw_rnc.strip()
                # Permite limpiar el valor si viene vacío.
                normalized_rnc = normalized_rnc or None
            else:
                normalized_rnc = raw_rnc
            # Guardar en columna directa del modelo/config (sin duplicar en settings_json).
            fields["rnc_emisor"] = normalized_rnc
        if "settings_json" in payload and isinstance(payload["settings_json"], dict):
            incoming_settings = dict(payload["settings_json"])
            # settings_json queda para flags; evitar duplicidad de rnc_emisor.
            incoming_settings.pop("rnc_emisor", None)
            settings.update(incoming_settings)
        fields["settings_json"] = settings

        if fields.get("cert_storage_mode") == "DB" and payload.get("p12_base64"):
            try:
                cert_blob = base64.b64decode(payload["p12_base64"], validate=True)
            except Exception as exc:
                raise ValueError("p12_base64 inválido") from exc
            if len(cert_blob) > (5 * 1024 * 1024):
                raise ValueError("Certificado demasiado grande (máx 5MB)")
            fields["cert_p12_bytes"] = cert_blob

        if fields.get("cert_storage_mode") == "PATH" and not fields.get("cert_path"):
            raise ValueError("cert_path es requerido cuando cert_storage_mode=PATH")

        upsert_company_config(company_id, **fields)
        return jsonify({"ok": True, "company_id": company_id, "config": get_company_config_safe(company_id)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.post("/fe/issue")
def fe_issue():
    try:
        company_id = _resolve_company_id(from_body=True)
        payload = request.get_json(silent=True) or {}
        invoice_id = int(payload.get("invoice_id") or 0)
        if not invoice_id:
            raise ValueError("invoice_id es requerido")

        doc = issue_ecf_for_invoice(company_id, invoice_id)
        return jsonify({
            "ok": True,
            "doc_id": doc.id,
            "status": doc.status,
            "track_id": doc.track_id,
            "e_ncf": doc.e_ncf,
            "tipo_ecf": doc.tipo_ecf,
        })
    except ValueError as exc:
        msg = str(exc)
        if "Facturación electrónica no está habilitada para la compañía" in msg:
            return jsonify({"ok": False, "error": msg}), 409
        return jsonify({"ok": False, "error": msg}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.get("/fe/doc/<int:doc_id>")
def fe_doc(doc_id: int):
    try:
        company_id = _resolve_company_id(from_body=False)
        doc = EcfDocument.query.filter_by(id=doc_id).first()
        if not doc:
            return jsonify({"ok": False, "error": "Documento no encontrado"}), 404
        if not _can_access_doc(doc, company_id):
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        return jsonify({
            "ok": True,
            "doc": {
                "id": doc.id,
                "company_id": doc.company_id,
                "invoice_id": doc.invoice_id,
                "backend_mode": doc.backend_mode,
                "tipo_ecf": doc.tipo_ecf,
                "e_ncf": doc.e_ncf,
                "status": doc.status,
                "attempts": doc.attempts,
                "track_id": doc.track_id,
                "error_message": doc.error_message,
                "sent_at": doc.sent_at.isoformat() if doc.sent_at else None,
                "last_check_at": doc.last_check_at.isoformat() if doc.last_check_at else None,
                "accepted_at": doc.accepted_at.isoformat() if doc.accepted_at else None,
                "pdf_filename": doc.pdf_filename,
                "pdf_size_bytes": doc.pdf_size_bytes,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            },
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.get("/fe/doc/<int:doc_id>/pdf")
def fe_doc_pdf(doc_id: int):
    try:
        company_id = _resolve_company_id(from_body=False)
        doc = EcfDocument.query.filter_by(id=doc_id).first()
        if not doc:
            return jsonify({"ok": False, "error": "Documento no encontrado"}), 404
        if not _can_access_doc(doc, company_id):
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        if not doc.pdf_blob and doc.status in ("ACCEPTED", "CONDITIONAL"):
            doc = check_one(doc.id)

        if not doc.pdf_blob:
            return jsonify({"ok": False, "error": "PDF no disponible todavía"}), 409

        return send_file(
            io.BytesIO(doc.pdf_blob),
            mimetype=doc.pdf_mime or "application/pdf",
            as_attachment=True,
            download_name=doc.pdf_filename or f"ecf-{doc.id}.pdf",
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@ecf_api_bp.post("/fe/doc/<int:doc_id>/check")
def fe_doc_check(doc_id: int):
    try:
        company_id = _resolve_company_id(from_body=True)
        doc = EcfDocument.query.filter_by(id=doc_id).first()
        if not doc:
            return jsonify({"ok": False, "error": "Documento no encontrado"}), 404
        if not _can_access_doc(doc, company_id):
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        doc = check_one(doc.id)
        return jsonify({"ok": True, "doc_id": doc.id, "status": doc.status, "track_id": doc.track_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
