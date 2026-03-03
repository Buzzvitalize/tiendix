from abc import ABC, abstractmethod


class FeBackend(ABC):
    mode = "BASE"

    @abstractmethod
    def issue(self, doc, invoice, items, cfg) -> dict:
        """Retorna dict: {'track_id': str|None, 'status': str, 'raw': dict}."""

    @abstractmethod
    def check_status(self, doc, cfg) -> dict:
        """Retorna dict: {'status': str, 'message': str, 'raw': dict}."""

    @abstractmethod
    def fetch_pdf(self, doc, cfg) -> bytes | None:
        """Retorna bytes PDF o None."""
