import uuid
from datetime import datetime

import requests

from ecf.backends.base import BackendResult, EcfBackend
from ecf.signer import sign_xml


class DirectDgiiBackend(EcfBackend):
    mode = "DIRECT_DGII"

    def issue(self, document: dict, company_config: dict) -> BackendResult:
        payload = document.get("xml_payload") or self._build_min_xml(document)
        signed_xml = sign_xml(payload, mock_mode=company_config.get("mock_sign", True))
        dgii_url = company_config.get("dgii_submit_url")
        if dgii_url:
            try:
                resp = requests.post(dgii_url, data=signed_xml.encode("utf-8"), timeout=20)
                return BackendResult(
                    status="SENT" if resp.ok else "ERROR",
                    message=f"DGII HTTP {resp.status_code}",
                    track_id=str(uuid.uuid4()),
                    payload={"response_text": resp.text[:1000], "signed_xml": signed_xml},
                )
            except Exception as exc:
                return BackendResult(status="ERROR", message=f"Error enviando a DGII: {exc}")
        return BackendResult(
            status="SENT",
            message="Documento enviado en modo mock DIRECT_DGII",
            track_id=str(uuid.uuid4()),
            payload={"signed_xml": signed_xml},
        )

    def check(self, document: dict, company_config: dict) -> BackendResult:
        current_status = document.get("status")
        if current_status == "SENT":
            return BackendResult(
                status="ACCEPTED",
                message="Mock: DGII marcó el e-CF como aceptado",
                payload={"accepted_at": datetime.utcnow().isoformat()},
            )
        return BackendResult(status=current_status or "PENDING", message="Sin cambios")

    def get_pdf(self, document: dict, company_config: dict) -> BackendResult:
        content = f"e-CF {document.get('id')} / modo DIRECT_DGII".encode("utf-8")
        return BackendResult(
            status=document.get("status", "PENDING"),
            message="PDF simulado",
            pdf_bytes=content,
            pdf_filename=f"ecf-{document.get('id')}.pdf",
        )

    @staticmethod
    def _build_min_xml(document: dict) -> str:
        return (
            "<eCF>"
            f"<Id>{document.get('id')}</Id>"
            f"<InvoiceId>{document.get('invoice_id')}</InvoiceId>"
            "</eCF>"
        )
