from ecf.backends.base import FeBackend
from ecf.constants import ECF_STATUS_ACCEPTED, ECF_STATUS_PROCESSING


class PseEcoseaStubBackend(FeBackend):
    mode = "PSE_ECOSEA"

    def issue(self, doc, invoice, items, cfg) -> dict:
        return {
            "track_id": f"ECOSEA-PSE-{doc.id}",
            "status": ECF_STATUS_PROCESSING,
            "raw": {"stub": True},
        }

    def check_status(self, doc, cfg) -> dict:
        if int(doc.attempts or 0) >= 2:
            return {"status": ECF_STATUS_ACCEPTED, "message": "ECOSEA stub: aceptado", "raw": {"stub": True}}
        return {"status": ECF_STATUS_PROCESSING, "message": "ECOSEA stub: procesando", "raw": {"stub": True}}

    def fetch_pdf(self, doc, cfg) -> bytes | None:
        # TODO: generar PDF válido completo desde backend ECOSEA cuando exista servicio real.
        return b"%PDF-1.4\n% ECOSEA STUB PDF\n"
