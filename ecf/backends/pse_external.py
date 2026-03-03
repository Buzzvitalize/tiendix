from datetime import datetime

import requests

from ecf.backends.base import FeBackend
from ecf.constants import ECF_STATUS_ACCEPTED, ECF_STATUS_PROCESSING


class PseExternalBackend(FeBackend):
    mode = "PSE_EXTERNAL"

    def issue(self, doc, invoice, items, cfg) -> dict:
        if self._is_mock(cfg):
            return {
                "track_id": f"PSE-MOCK-{doc.id}",
                "status": ECF_STATUS_PROCESSING,
                "raw": {"mock": True},
            }

        issue_url, _, _ = self._resolve_urls(cfg)
        headers = self._build_headers(cfg)
        payload = {
            "doc_id": doc.id,
            "invoice_id": doc.invoice_id,
            "e_ncf": doc.e_ncf,
            "tipo_ecf": doc.tipo_ecf,
            "xml_signed": doc.xml_signed,
        }
        resp = requests.post(issue_url, json=payload, headers=headers, timeout=20)
        if not resp.ok:
            raise RuntimeError(f"PSE issue error HTTP {resp.status_code}")
        data = _safe_json(resp)
        return {
            "track_id": data.get("track_id") or f"PSE-{doc.id}",
            "status": data.get("status") or ECF_STATUS_PROCESSING,
            "raw": data,
        }

    def check_status(self, doc, cfg) -> dict:
        if self._is_mock(cfg):
            if int(doc.attempts or 0) >= 2:
                return {"status": ECF_STATUS_ACCEPTED, "message": "Mock PSE: aceptado", "raw": {"mock": True}}
            return {"status": ECF_STATUS_PROCESSING, "message": "Mock PSE: en proceso", "raw": {"mock": True}}

        _, status_url, _ = self._resolve_urls(cfg)
        headers = self._build_headers(cfg)
        resp = requests.get(status_url, params={"track_id": doc.track_id}, headers=headers, timeout=20)
        if not resp.ok:
            raise RuntimeError(f"PSE status error HTTP {resp.status_code}")
        data = _safe_json(resp)
        return {
            "status": data.get("status") or ECF_STATUS_PROCESSING,
            "message": data.get("message") or "Estado consultado",
            "raw": data,
        }

    def fetch_pdf(self, doc, cfg) -> bytes | None:
        if self._is_mock(cfg):
            return b"%PDF-1.4\n% Mock PSE PDF\n"

        _, _, pdf_url = self._resolve_urls(cfg)
        headers = self._build_headers(cfg)
        resp = requests.get(pdf_url, params={"track_id": doc.track_id}, headers=headers, timeout=20)
        if resp.ok and resp.content:
            return resp.content
        return None

    def _resolve_urls(self, cfg) -> tuple[str, str, str]:
        base = (getattr(cfg, "pse_base_url", None) or "").rstrip("/")
        issue_url = (getattr(cfg, "pse_issue_url", None) or "").strip()
        status_url = (getattr(cfg, "pse_status_url", None) or "").strip()
        pdf_url = (getattr(cfg, "pse_pdf_url", None) or "").strip()

        if not issue_url and base:
            issue_url = f"{base}/issue"
        if not status_url and base:
            status_url = f"{base}/status"
        if not pdf_url and base:
            pdf_url = f"{base}/pdf"

        if not issue_url or not status_url:
            raise ValueError("PSE_EXTERNAL requiere pse_issue_url/pse_status_url o pse_base_url")
        return issue_url, status_url, pdf_url

    def _build_headers(self, cfg) -> dict:
        api_key = (getattr(cfg, "pse_api_key", None) or "").strip()
        client_id = (getattr(cfg, "pse_client_id", None) or "").strip()
        client_secret = (getattr(cfg, "pse_client_secret", None) or "").strip()

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            return headers
        if client_id and client_secret:
            headers["X-Client-Id"] = client_id
            headers["X-Client-Secret"] = client_secret
            return headers
        raise ValueError("PSE_EXTERNAL requiere api_key o client_id/client_secret")

    @staticmethod
    def _is_mock(cfg) -> bool:
        settings = getattr(cfg, "settings_json", {}) or {}
        return isinstance(settings, dict) and bool(settings.get("mock_pse"))


def _safe_json(resp) -> dict:
    try:
        return resp.json() if resp.content else {}
    except Exception:
        return {"raw_text": (resp.text or "")[:1000], "timestamp": datetime.utcnow().isoformat()}
