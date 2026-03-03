from datetime import datetime

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover
    requests = None

import urllib.error
import urllib.parse
import urllib.request

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
        resp = _http_request('POST', issue_url, headers=headers, json_payload=payload)
        if resp['status_code'] >= 400:
            raise RuntimeError(f"PSE issue error HTTP {resp['status_code']}")
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
        resp = _http_request('GET', status_url, headers=headers, params={"track_id": doc.track_id})
        if resp['status_code'] >= 400:
            raise RuntimeError(f"PSE status error HTTP {resp['status_code']}")
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
        resp = _http_request('GET', pdf_url, headers=headers, params={"track_id": doc.track_id})
        if resp['status_code'] < 400 and resp.get('content'):
            return resp['content']
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


def _safe_json(resp: dict) -> dict:
    text = resp.get('text') or ''
    if not text:
        return {}
    try:
        import json

        return json.loads(text)
    except Exception:
        return {"raw_text": text[:1000], "timestamp": datetime.utcnow().isoformat()}


def _http_request(method: str, url: str, *, headers: dict | None = None, params: dict | None = None, json_payload: dict | None = None) -> dict:
    headers = dict(headers or {})
    params = params or {}

    if params:
        query = urllib.parse.urlencode(params)
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}{query}"

    if requests is not None:
        kwargs = {"headers": headers, "timeout": 20}
        if json_payload is not None:
            kwargs["json"] = json_payload
        r = requests.request(method, url, **kwargs)
        return {
            "status_code": r.status_code,
            "text": r.text or "",
            "content": r.content or b"",
        }

    # Fallback urllib para entornos cPanel sin requests instalado.
    data = None
    if json_payload is not None:
        import json

        data = json.dumps(json_payload).encode('utf-8')
        headers.setdefault('Content-Type', 'application/json')

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return {
                "status_code": int(getattr(r, 'status', 200) or 200),
                "text": body.decode('utf-8', errors='replace'),
                "content": body,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, 'read') else b''
        return {
            "status_code": int(exc.code),
            "text": body.decode('utf-8', errors='replace'),
            "content": body,
        }
    except Exception as exc:
        raise RuntimeError(
            "No se pudo conectar con PSE_EXTERNAL. Verifique red/URLs o instale requests en el entorno."
        ) from exc
