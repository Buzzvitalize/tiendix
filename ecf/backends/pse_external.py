import uuid

import requests

from ecf.backends.base import BackendResult, EcfBackend


class PseExternalBackend(EcfBackend):
    mode = "PSE_EXTERNAL"

    def issue(self, document: dict, company_config: dict) -> BackendResult:
        endpoint = company_config.get("pse_issue_url")
        api_key = company_config.get("pse_api_key")
        body = {
            "document_id": document.get("id"),
            "invoice_id": document.get("invoice_id"),
            "xml_payload": document.get("xml_payload"),
        }
        if not endpoint:
            return BackendResult(
                status="SENT",
                message="PSE externo no configurado. Se dejó en estado SENT (simulado).",
                track_id=str(uuid.uuid4()),
                payload=body,
            )
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            resp = requests.post(endpoint, json=body, headers=headers, timeout=20)
            if resp.ok:
                data = resp.json() if "application/json" in resp.headers.get("Content-Type", "") else {}
                return BackendResult(
                    status=data.get("status", "SENT"),
                    message="Enviado a PSE externo",
                    track_id=data.get("track_id") or str(uuid.uuid4()),
                    payload={"provider_response": resp.text[:1000]},
                )
            return BackendResult(status="ERROR", message=f"PSE HTTP {resp.status_code}")
        except Exception as exc:
            return BackendResult(status="ERROR", message=f"Error PSE externo: {exc}")

    def check(self, document: dict, company_config: dict) -> BackendResult:
        return BackendResult(status=document.get("status", "SENT"), message="Check delegado a PSE externo")
