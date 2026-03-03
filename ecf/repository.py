"""Repositorio de acceso a datos e-CF (sin capa HTTP).

Este módulo se limita a CRUD/queries y mutaciones de estado.
"""

from datetime import datetime, timedelta

from ecf.constants import (
    ECF_EVENT_TYPES,
    ECF_FINAL_OK_STATUSES,
    ECF_MODES,
    ECF_PENDING_CHECK_STATUSES,
    ECF_STATUS_ACCEPTED,
    ECF_STATUS_PROCESSING,
    ECF_STATUS_SENT,
)
from ecf.models import EcfCompanyConfig, EcfDocument, EcfEvent
from models import db


def get_company_config(company_id: int) -> EcfCompanyConfig | None:
    return db.session.get(EcfCompanyConfig, int(company_id))


def upsert_company_config(company_id: int, **fields) -> EcfCompanyConfig:
    cfg = db.session.get(EcfCompanyConfig, int(company_id))
    if cfg is None:
        cfg = EcfCompanyConfig(company_id=int(company_id))
        db.session.add(cfg)

    for key, value in fields.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)

    if cfg.mode and cfg.mode not in ECF_MODES:
        raise ValueError(f"Modo e-CF inválido: {cfg.mode}")

    db.session.commit()
    return cfg


def set_company_enabled(company_id: int, enabled: bool) -> EcfCompanyConfig:
    return upsert_company_config(int(company_id), enabled=bool(enabled))


def create_ecf_document(company_id: int, invoice_id: int, backend_mode: str, tipo_ecf: str, e_ncf: str) -> EcfDocument:
    if backend_mode not in ECF_MODES:
        raise ValueError(f"backend_mode inválido: {backend_mode}")

    doc = EcfDocument(
        company_id=int(company_id),
        invoice_id=int(invoice_id),
        backend_mode=backend_mode,
        tipo_ecf=str(tipo_ecf),
        e_ncf=str(e_ncf),
    )
    db.session.add(doc)
    db.session.commit()
    return doc


def save_xml_unsigned(doc_id: int, xml_str: str) -> EcfDocument:
    doc = _require_doc(doc_id)
    doc.xml_unsigned = xml_str
    db.session.commit()
    return doc


def save_xml_signed(doc_id: int, xml_str: str) -> EcfDocument:
    doc = _require_doc(doc_id)
    doc.xml_signed = xml_str
    db.session.commit()
    return doc


def mark_sent(doc_id: int, track_id: str | None, response_payload=None) -> EcfDocument:
    doc = _require_doc(doc_id)
    doc.track_id = track_id
    doc.status = ECF_STATUS_PROCESSING if track_id else ECF_STATUS_SENT
    doc.sent_at = datetime.utcnow()
    doc.last_check_at = datetime.utcnow()
    if response_payload is not None:
        doc.response_payload = _as_json_text(response_payload)
    if not doc.next_retry_at:
        doc.next_retry_at = datetime.utcnow() + timedelta(minutes=1)
    db.session.commit()
    return doc


def mark_status(doc_id: int, status: str, message: str | None = None, response_payload=None) -> EcfDocument:
    doc = _require_doc(doc_id)
    doc.status = status
    doc.last_check_at = datetime.utcnow()
    doc.error_message = message
    if response_payload is not None:
        doc.response_payload = _as_json_text(response_payload)

    if status in ECF_FINAL_OK_STATUSES:
        doc.accepted_at = datetime.utcnow()
        doc.next_retry_at = None
    elif status in (ECF_STATUS_SENT, ECF_STATUS_PROCESSING):
        if doc.next_retry_at is None:
            doc.next_retry_at = datetime.utcnow() + timedelta(minutes=1)
    else:
        doc.next_retry_at = None

    db.session.commit()
    return doc


def schedule_retry(doc_id: int, seconds: int, attempts_increment: bool = True) -> EcfDocument:
    doc = _require_doc(doc_id)
    doc.next_retry_at = datetime.utcnow() + timedelta(seconds=max(int(seconds), 0))
    if attempts_increment:
        doc.attempts = int(doc.attempts or 0) + 1
    db.session.commit()
    return doc


def list_pending_for_retry(limit: int = 50) -> list[EcfDocument]:
    now = datetime.utcnow()
    return (
        EcfDocument.query
        .filter(EcfDocument.status.in_(ECF_PENDING_CHECK_STATUSES))
        .filter((EcfDocument.next_retry_at.is_(None)) | (EcfDocument.next_retry_at <= now))
        .order_by(EcfDocument.next_retry_at.asc(), EcfDocument.id.asc())
        .limit(max(int(limit), 1))
        .all()
    )


def log_event(doc_id: int, event_type: str, payload_dict: dict | None = None) -> EcfEvent:
    if event_type not in ECF_EVENT_TYPES:
        raise ValueError(f"event_type inválido: {event_type}")
    _require_doc(doc_id)
    event = EcfEvent(ecf_id=int(doc_id), event_type=event_type, payload_json=payload_dict)
    db.session.add(event)
    db.session.commit()
    return event


def get_company_config_safe(company_id: int) -> dict | None:
    """Retorna configuración sin secretos sensibles."""
    cfg = get_company_config(company_id)
    return cfg.to_safe_dict() if cfg else None


def _require_doc(doc_id: int) -> EcfDocument:
    doc = db.session.get(EcfDocument, int(doc_id))
    if not doc:
        raise ValueError(f"Documento e-CF no encontrado: {doc_id}")
    return doc


def _as_json_text(payload) -> str:
    if isinstance(payload, str):
        return payload
    try:
        import json

        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        return str(payload)
