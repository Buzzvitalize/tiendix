from datetime import datetime, timedelta

from ecf.backends.base import FeBackend
from ecf.constants import (
    ECF_STATUS_ACCEPTED,
    ECF_STATUS_PROCESSING,
    ECF_STATUS_REJECTED,
)


class DirectDgiiBackend(FeBackend):
    mode = "DIRECT_DGII"

    def issue(self, doc, invoice, items, cfg) -> dict:
        token = self.auth(cfg)
        track_id = self.send(doc.xml_signed or "", cfg, token, doc_id=doc.id)
        return {
            "track_id": track_id,
            "status": ECF_STATUS_PROCESSING,
            "raw": {"provider": "DGII", "mock": self._is_stub(cfg), "token": bool(token)},
        }

    def check_status(self, doc, cfg) -> dict:
        token = self.auth(cfg)
        status, message, raw = self.check(doc.track_id, cfg, token, attempts=int(doc.attempts or 0))
        return {"status": status, "message": message, "raw": raw}

    def fetch_pdf(self, doc, cfg) -> bytes | None:
        return None

    def auth(self, cfg) -> str:
        now = datetime.utcnow()
        if getattr(cfg, "token_cache", None) and getattr(cfg, "token_expires_at", None):
            if cfg.token_expires_at > now:
                return cfg.token_cache

        if self._is_stub(cfg):
            return "DGII-MOCK-TOKEN"

        # TODO: Integrar endpoint real de autenticación DGII.
        raise RuntimeError("Auth DGII real no implementado (configure stub/mock_sign para pruebas)")

    def send(self, xml_signed: str, cfg, token: str, *, doc_id: int) -> str:
        if not xml_signed:
            raise ValueError("xml_signed vacío para envío DGII")
        if self._is_stub(cfg):
            return f"DGII-MOCK-{doc_id}"

        # TODO: Integrar endpoint real de envío DGII.
        raise RuntimeError("Envío DGII real no implementado")

    def check(self, track_id: str | None, cfg, token: str, *, attempts: int) -> tuple[str, str, dict]:
        if not track_id:
            return ECF_STATUS_PROCESSING, "Sin track_id aún", {"mock": self._is_stub(cfg)}

        if self._is_stub(cfg):
            settings = getattr(cfg, "settings_json", {}) or {}
            force_reject = bool(settings.get("force_reject")) if isinstance(settings, dict) else False
            if force_reject and attempts >= 2:
                return ECF_STATUS_REJECTED, "Mock DGII: rechazado por force_reject", {"track_id": track_id}
            if attempts >= 2:
                return ECF_STATUS_ACCEPTED, "Mock DGII: aceptado", {"track_id": track_id}
            return ECF_STATUS_PROCESSING, "Mock DGII: en proceso", {"track_id": track_id}

        # TODO: Integrar endpoint real de consulta DGII.
        raise RuntimeError("Consulta de estado DGII real no implementada")

    @staticmethod
    def _is_stub(cfg) -> bool:
        dgii_env = (getattr(cfg, "dgii_env", None) or "").strip()
        mock_sign = bool(getattr(cfg, "mock_sign", True))
        return (not dgii_env) or mock_sign
