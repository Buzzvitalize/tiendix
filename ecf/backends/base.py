from dataclasses import dataclass, field
from typing import Any


@dataclass
class BackendResult:
    status: str
    message: str = ""
    track_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    pdf_bytes: bytes | None = None
    pdf_filename: str | None = None


class EcfBackend:
    mode = "BASE"

    def issue(self, document: dict, company_config: dict) -> BackendResult:
        raise NotImplementedError

    def check(self, document: dict, company_config: dict) -> BackendResult:
        raise NotImplementedError

    def get_pdf(self, document: dict, company_config: dict) -> BackendResult:
        return BackendResult(status=document.get("status", "PENDING"), message="PDF no disponible")
