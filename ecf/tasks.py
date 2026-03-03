"""Tareas de procesamiento e-CF para ejecución por cron/cPanel."""

from ecf.constants import ECF_EVENT_ERROR
from ecf.repository import list_pending_for_retry, log_event, mark_status
from ecf.service import check_one


FINAL_STATUSES = {"ACCEPTED", "CONDITIONAL", "REJECTED", "ERROR"}


def process_pending(limit: int = 50) -> dict:
    docs = list_pending_for_retry(limit=limit)
    summary = {
        "processed": 0,
        "accepted": 0,
        "conditional": 0,
        "rejected": 0,
        "processing": 0,
        "errors": 0,
    }

    for doc in docs:
        if (doc.status or "").upper() in FINAL_STATUSES:
            # Idempotencia defensiva.
            continue

        summary["processed"] += 1
        try:
            updated = check_one(doc.id)
            status = (updated.status or "").upper()
            if status == "ACCEPTED":
                summary["accepted"] += 1
            elif status == "CONDITIONAL":
                summary["conditional"] += 1
            elif status == "REJECTED":
                summary["rejected"] += 1
            elif status in ("SENT", "PROCESSING"):
                summary["processing"] += 1
            elif status == "ERROR":
                summary["errors"] += 1
            else:
                summary["processing"] += 1
        except Exception as exc:
            summary["errors"] += 1
            mark_status(doc.id, "ERROR", message=str(exc))
            log_event(doc.id, ECF_EVENT_ERROR, {"error": str(exc), "source": "tasks.process_pending"})

    return summary
