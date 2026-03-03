import uuid

from ecf.backends.base import BackendResult, EcfBackend


class PseEcoseaStubBackend(EcfBackend):
    mode = "PSE_ECOSEA"

    def issue(self, document: dict, company_config: dict) -> BackendResult:
        return BackendResult(
            status="SENT",
            message="ECOSEA stub: issue recibido",
            track_id=f"ecosea-{uuid.uuid4()}",
            payload={"stub": True},
        )

    def check(self, document: dict, company_config: dict) -> BackendResult:
        if document.get("status") == "SENT":
            return BackendResult(status="CONDITIONAL", message="ECOSEA stub: estado condicional")
        return BackendResult(status=document.get("status", "PENDING"), message="Sin cambios")

    def get_pdf(self, document: dict, company_config: dict) -> BackendResult:
        content = b"PDF STUB ECOSEA"
        return BackendResult(
            status=document.get("status", "PENDING"),
            message="PDF stub ECOSEA",
            pdf_bytes=content,
            pdf_filename=f"ecosea-{document.get('id')}.pdf",
        )
