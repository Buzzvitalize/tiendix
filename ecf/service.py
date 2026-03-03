"""Núcleo de servicio e-CF (FASE 4): emisión + consulta por backend."""

from datetime import datetime
import logging

from ecf.constants import (
    DIRECT_DGII,
    ECF_EVENT_AUTH,
    ECF_EVENT_BUILD_XML,
    ECF_EVENT_ERROR,
    ECF_EVENT_PDF,
    ECF_EVENT_SEND,
    ECF_EVENT_SIGN,
    ECF_EVENT_STATUS_CHECK,
    ECF_FINAL_OK_STATUSES,
    ECF_STATUS_ERROR,
)
from ecf.engine import assert_enabled, get_backend
from ecf.models import EcfDocument
from ecf.repository import (
    create_ecf_document,
    get_company_config,
    log_event,
    mark_sent,
    mark_status,
    save_xml_signed,
    save_xml_unsigned,
    schedule_retry,
)
from ecf.signer import sign_xml
from ecf.xml_builder import build_ecf_xml
from models import CompanyInfo, Invoice, InvoiceItem, db
from weasy_pdf import generate_pdf_bytes

logger = logging.getLogger(__name__)


def issue_ecf_for_invoice(company_id: int, invoice_id: int) -> EcfDocument:
    cfg = get_company_config(company_id)
    assert_enabled(cfg)

    invoice = (
        Invoice.query
        .filter(Invoice.id == int(invoice_id), Invoice.company_id == int(company_id))
        .first()
    )
    if not invoice:
        raise ValueError(f"Factura no encontrada para company_id={company_id}, invoice_id={invoice_id}")

    items = (
        InvoiceItem.query
        .filter(InvoiceItem.invoice_id == int(invoice_id), InvoiceItem.company_id == int(company_id))
        .order_by(InvoiceItem.id.asc())
        .all()
    )
    if not items:
        raise ValueError("La factura no tiene items para emitir e-CF")

    tipo_ecf = _map_tipo_ecf(invoice)
    e_ncf = (invoice.ncf or "").strip() or f"ECF-{company_id}-{invoice.id}"

    doc = create_ecf_document(
        company_id=company_id,
        invoice_id=invoice.id,
        backend_mode=cfg.mode,
        tipo_ecf=tipo_ecf,
        e_ncf=e_ncf,
    )

    invoice.company = db.session.get(CompanyInfo, invoice.company_id)  # helper para xml_builder

    xml_unsigned = build_ecf_xml(invoice, items, cfg, tipo_ecf)
    save_xml_unsigned(doc.id, xml_unsigned)
    log_event(doc.id, ECF_EVENT_BUILD_XML, {"tipo_ecf": tipo_ecf, "e_ncf": e_ncf})

    xml_signed = sign_xml(xml_unsigned, cfg)
    save_xml_signed(doc.id, xml_signed)
    log_event(doc.id, ECF_EVENT_SIGN, {"mock_sign": bool(cfg.mock_sign)})

    backend = get_backend(cfg.mode)
    issue_result = backend.issue(_refresh_doc(doc.id), invoice, items, cfg)

    if cfg.mode == DIRECT_DGII:
        log_event(doc.id, ECF_EVENT_AUTH, {"provider": "DGII", "mock": bool(cfg.mock_sign)})

    mark_sent(doc.id, issue_result.get("track_id"), response_payload=issue_result.get("raw"))
    log_event(
        doc.id,
        ECF_EVENT_SEND,
        {
            "track_id": issue_result.get("track_id"),
            "status": issue_result.get("status"),
            "provider": cfg.mode,
        },
    )

    backoff = compute_backoff_seconds(_refresh_doc(doc.id).attempts or 0)
    if backoff > 0:
        schedule_retry(doc.id, backoff, attempts_increment=False)

    logger.info("e-CF emitido doc_id=%s company_id=%s invoice_id=%s mode=%s", doc.id, company_id, invoice_id, cfg.mode)
    return _refresh_doc(doc.id)


def check_one(doc_id: int) -> EcfDocument:
    doc = _refresh_doc(doc_id)
    cfg = get_company_config(doc.company_id)
    assert_enabled(cfg)

    backend = get_backend(cfg.mode)
    check = backend.check_status(doc, cfg)

    status = check.get("status") or ECF_STATUS_ERROR
    message = check.get("message") or ""
    raw = check.get("raw")

    mark_status(doc.id, status, message=message, response_payload=raw)
    log_event(doc.id, ECF_EVENT_STATUS_CHECK, {"status": status, "message": message})

    doc = _refresh_doc(doc.id)
    if doc.status in ECF_FINAL_OK_STATUSES:
        pdf_bytes = backend.fetch_pdf(doc, cfg)
        if not pdf_bytes:
            pdf_bytes = _generate_pdf_from_invoice(doc)

        if pdf_bytes:
            doc.pdf_blob = pdf_bytes
            doc.pdf_size_bytes = len(pdf_bytes)
            doc.pdf_filename = doc.pdf_filename or f"ecf-{doc.id}.pdf"
            doc.pdf_mime = doc.pdf_mime or "application/pdf"
            db.session.commit()
            log_event(doc.id, ECF_EVENT_PDF, {"size_bytes": len(pdf_bytes), "filename": doc.pdf_filename})
    else:
        backoff = compute_backoff_seconds(doc.attempts or 0)
        if backoff < 0:
            mark_status(doc.id, ECF_STATUS_ERROR, message="Máximo de reintentos alcanzado")
            log_event(doc.id, ECF_EVENT_ERROR, {"message": "Máximo de reintentos alcanzado"})
        else:
            schedule_retry(doc.id, backoff, attempts_increment=True)

    return _refresh_doc(doc.id)


def compute_backoff_seconds(attempts: int) -> int:
    attempts = int(attempts or 0)
    if attempts <= 5:
        return 30
    if attempts <= 10:
        return 120
    if attempts <= 25:
        return 300
    return -1


class EcfService:
    """Compatibilidad de import para capas superiores existentes."""

    @staticmethod
    def issue_ecf_for_invoice(company_id: int, invoice_id: int) -> EcfDocument:
        return issue_ecf_for_invoice(company_id, invoice_id)

    @staticmethod
    def check_one(doc_id: int) -> EcfDocument:
        return check_one(doc_id)

    @staticmethod
    def compute_backoff_seconds(attempts: int) -> int:
        return compute_backoff_seconds(attempts)


def _map_tipo_ecf(invoice: Invoice) -> str:
    invoice_type = (getattr(invoice, "invoice_type", None) or "").strip().lower()
    ncf = (getattr(invoice, "ncf", None) or "").strip().upper()

    if "consumidor" in invoice_type or ncf.startswith("B02"):
        return "31"
    if "crédito" in invoice_type or "credito" in invoice_type or ncf.startswith("B01"):
        return "33"
    return "31"


def _refresh_doc(doc_id: int) -> EcfDocument:
    doc = db.session.get(EcfDocument, int(doc_id))
    if not doc:
        raise ValueError(f"Documento e-CF no encontrado: {doc_id}")
    return doc


def _generate_pdf_from_invoice(doc: EcfDocument) -> bytes | None:
    invoice = db.session.get(Invoice, int(doc.invoice_id))
    if not invoice:
        return None

    items = (
        InvoiceItem.query
        .filter(InvoiceItem.invoice_id == invoice.id, InvoiceItem.company_id == doc.company_id)
        .order_by(InvoiceItem.id.asc())
        .all()
    )
    if not items:
        return None

    company_obj = db.session.get(CompanyInfo, int(doc.company_id))
    company = {
        "name": getattr(company_obj, "name", ""),
        "address": " ".join(filter(None, [getattr(company_obj, "street", ""), getattr(company_obj, "sector", ""), getattr(company_obj, "province", "")])),
        "website": getattr(company_obj, "website", None),
        "phone": getattr(company_obj, "phone", None),
    }

    client = {
        "name": getattr(invoice.client, "name", ""),
        "identifier": getattr(invoice.client, "identifier", ""),
        "address": " ".join(filter(None, [getattr(invoice.client, "street", ""), getattr(invoice.client, "sector", ""), getattr(invoice.client, "province", "")])),
        "phone": getattr(invoice.client, "phone", ""),
        "email": getattr(invoice.client, "email", ""),
    }

    return generate_pdf_bytes(
        "Factura",
        company,
        client,
        items,
        float(invoice.subtotal or 0),
        float(invoice.itbis or 0),
        float(invoice.total or 0),
        ncf=invoice.ncf,
        seller=invoice.seller,
        payment_method=invoice.payment_method,
        bank=invoice.bank,
        doc_number=invoice.id,
        invoice_type=invoice.invoice_type,
        note=invoice.note,
        date=invoice.date,
    )
