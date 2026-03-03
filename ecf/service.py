import json
from datetime import datetime

from sqlalchemy import text

from ecf.backends import get_backend
from ecf.constants import EcfMode, EcfPdfStatuses
from models import db


class EcfService:
    @staticmethod
    def get_company_config(company_id: int) -> dict | None:
        row = db.session.execute(
            text(
                """
                SELECT company_id, enabled, mode, settings_json, updated_at
                FROM ecf_company_config
                WHERE company_id = :company_id
                """
            ),
            {"company_id": company_id},
        ).mappings().first()
        if not row:
            return None
        settings = {}
        if row["settings_json"]:
            try:
                settings = json.loads(row["settings_json"])
            except json.JSONDecodeError:
                settings = {}
        return {
            "company_id": row["company_id"],
            "enabled": bool(row["enabled"]),
            "mode": row["mode"],
            "settings": settings,
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def upsert_company_config(company_id: int, enabled: bool, mode: str, settings: dict) -> None:
        if mode not in EcfMode:
            raise ValueError("Modo e-CF inválido")
        db.session.execute(
            text(
                """
                INSERT INTO ecf_company_config (company_id, enabled, mode, settings_json, updated_at)
                VALUES (:company_id, :enabled, :mode, :settings_json, NOW())
                ON DUPLICATE KEY UPDATE
                    enabled = VALUES(enabled),
                    mode = VALUES(mode),
                    settings_json = VALUES(settings_json),
                    updated_at = NOW()
                """
            ),
            {
                "company_id": company_id,
                "enabled": 1 if enabled else 0,
                "mode": mode,
                "settings_json": json.dumps(settings or {}),
            },
        )
        db.session.commit()

    @staticmethod
    def enqueue_invoice(invoice_id: int, company_id: int, xml_payload: str | None = None) -> int:
        config = EcfService.get_company_config(company_id)
        if not config or not config["enabled"]:
            raise ValueError("Facturación electrónica no está activada para esta compañía")

        result = db.session.execute(
            text(
                """
                INSERT INTO ecf_documents (
                    company_id, invoice_id, backend_mode, status, xml_payload, created_at, updated_at
                ) VALUES (
                    :company_id, :invoice_id, :backend_mode, 'PENDING', :xml_payload, NOW(), NOW()
                )
                """
            ),
            {
                "company_id": company_id,
                "invoice_id": invoice_id,
                "backend_mode": config["mode"],
                "xml_payload": xml_payload,
            },
        )
        db.session.commit()
        return int(result.lastrowid)

    @staticmethod
    def get_document(doc_id: int) -> dict | None:
        row = db.session.execute(
            text("SELECT * FROM ecf_documents WHERE id = :id"),
            {"id": doc_id},
        ).mappings().first()
        return dict(row) if row else None

    @staticmethod
    def process_document(doc_id: int) -> dict:
        document = EcfService.get_document(doc_id)
        if not document:
            raise ValueError("Documento e-CF no encontrado")
        config = EcfService.get_company_config(document["company_id"])
        if not config:
            raise ValueError("Configuración e-CF no encontrada")
        backend = get_backend(config["mode"])
        if not backend:
            raise ValueError("Backend no soportado")

        if document["status"] in ("PENDING", "ERROR"):
            result = backend.issue(document, config["settings"])
        else:
            result = backend.check(document, config["settings"])

        EcfService._save_result(document, result, config)
        return {"id": doc_id, "status": result.status, "message": result.message}

    @staticmethod
    def process_pending(limit: int = 50) -> list[dict]:
        rows = db.session.execute(
            text(
                """
                SELECT id FROM ecf_documents
                WHERE status IN ('PENDING', 'SENT', 'ERROR')
                ORDER BY created_at ASC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
        output = []
        for row in rows:
            try:
                output.append(EcfService.process_document(int(row["id"])))
            except Exception as exc:  # pragma: no cover
                output.append({"id": int(row["id"]), "status": "ERROR", "message": str(exc)})
        return output

    @staticmethod
    def _save_result(document: dict, result, config: dict) -> None:
        accepted_at = "NOW()" if result.status in EcfPdfStatuses else "accepted_at"
        sql = f"""
            UPDATE ecf_documents
            SET
                status = :status,
                error_message = :error_message,
                provider_track_id = COALESCE(:provider_track_id, provider_track_id),
                response_payload = :response_payload,
                attempts = COALESCE(attempts, 0) + 1,
                updated_at = NOW(),
                accepted_at = {accepted_at}
            WHERE id = :id
        """
        db.session.execute(
            text(sql),
            {
                "id": document["id"],
                "status": result.status,
                "error_message": None if result.status != "ERROR" else result.message,
                "provider_track_id": result.track_id,
                "response_payload": json.dumps(result.payload or {}),
            },
        )

        if result.status in EcfPdfStatuses:
            backend = get_backend(config["mode"])
            pdf_result = backend.get_pdf(document, config["settings"])
            if pdf_result.pdf_bytes:
                db.session.execute(
                    text(
                        """
                        UPDATE ecf_documents
                        SET pdf_blob = :pdf_blob,
                            pdf_filename = :pdf_filename,
                            pdf_mime = 'application/pdf'
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": document["id"],
                        "pdf_blob": pdf_result.pdf_bytes,
                        "pdf_filename": pdf_result.pdf_filename or f"ecf-{document['id']}.pdf",
                    },
                )
        db.session.commit()
