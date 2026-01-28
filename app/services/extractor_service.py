import uuid
from dataclasses import asdict
from typing import Any

import structlog
from celery.result import AsyncResult

from app.api.v1.responses.job_respose import JobResponse
from app.domain.exceptions import ExtractionException
from app.domain.value_objects.loki import MatchContext
from app.infrastructure.adapters.interfaces import ILokiAdapter
from app.infrastructure.worker.tasks import send_alerts
from app.services.interfaces import IExtractorService
from app.settings.settings import Settings
from app.utils.utils import (
    dt_to_ns,
    ns_to_dt,
    parse_duration_to_seconds,
    rfc3339_to_datetime,
    utc_now,
)

logger = structlog.get_logger(__name__)


class ExtractorService(IExtractorService):
    """Сервис получения данных"""

    def __init__(self, settings: Settings, loki: ILokiAdapter):
        self.settings_alert = settings.alert
        self.loki = loki

    async def extract(self, payload: dict) -> JobResponse:
        """Получение данных из локи"""
        try:
            status = str(payload.get("status") or "unknown")
            alertname = (
                self._label_fallback(payload, "alertname")
                or payload.get("groupLabels", {}).get("alertname")
                or "(no alertname)"
            )
            common_labels: dict[str, str] = {
                k: str(v) for k, v in (payload.get("commonLabels") or {}).items()
            }
            common_annotations: dict[str, str] = {
                k: str(v) for k, v in (payload.get("commonAnnotations") or {}).items()
            }
            selector = (
                self._annotation_lookup(payload, "stream_selector")
                or self.settings_alert.default_stream_selector
            )
            error_filter = (
                self._annotation_lookup(payload, "error_filter")
                or self.settings_alert.default_error_filter
            )

            context_before = int(
                self._annotation_lookup(payload, "context_before")
                or self.settings_alert.context_before
            )
            context_after = int(
                self._annotation_lookup(payload, "context_after")
                or self.settings_alert.context_after
            )
            max_matches = int(
                self._annotation_lookup(payload, "max_matches") or self.settings_alert.max_matches
            )

            search_window = (
                self._annotation_lookup(payload, "search_window")
                or self.settings_alert.search_window
            )
            context_time_range = (
                self._annotation_lookup(payload, "context_time_range")
                or self.settings_alert.context_time_range
            )

            search_window_s = parse_duration_to_seconds(search_window)
            context_range_s = parse_duration_to_seconds(context_time_range)
            end_dt = utc_now()
            alerts = payload.get("alerts") or []

            if alerts and isinstance(alerts, list):
                # Use the latest startsAt in payload as a more "relevant" end time.
                starts = []
                for a in alerts:
                    if isinstance(a, dict) and a.get("startsAt"):

                        starts.append(rfc3339_to_datetime(str(a.get("startsAt"))))
                if starts:
                    end_dt = max(starts)

            start_dt = end_dt - __import__("datetime").timedelta(seconds=search_window_s)

            end_ns = dt_to_ns(end_dt)
            start_ns = dt_to_ns(start_dt)

            # 1) Find matching error records (recent, limited).
            query = f"{selector} |= {error_filter}".strip()
            matches = await self.loki.query_range(
                query=query,
                start_ns=start_ns,
                end_ns=end_ns,
                limit=max_matches,
                direction="BACKWARD",
            )

            # 2) Fetch before/after context for each match.
            contexts: list[MatchContext] = []
            ctx_range_ns = int(context_range_s * 1_000_000_000)
            for m in matches[:max_matches]:
                # Before: query backward ending just before the match timestamp.
                before_start = max(0, m.ts_ns - ctx_range_ns)
                before_end = max(0, m.ts_ns - 1)
                before_entries = await self.loki.query_range(
                    query=selector,
                    start_ns=before_start,
                    end_ns=before_end,
                    limit=context_before,
                    direction="BACKWARD",
                )
                # We want chronological order in output.
                before_lines = [e.line for e in reversed(before_entries)]
                after_start = m.ts_ns + 1
                after_end = m.ts_ns + ctx_range_ns

                after_entries = await self.loki.query_range(
                    query=selector,
                    start_ns=after_start,
                    end_ns=after_end,
                    limit=context_after,
                    direction="FORWARD",
                )
                after_lines = [e.line for e in after_entries]
                contexts.append(
                    MatchContext(
                        ts_ns=m.ts_ns,
                        ts_iso=ns_to_dt(m.ts_ns).isoformat(),
                        line=m.line,
                        before=before_lines,
                        after=after_lines,
                    )
                )

            title = f"[{status.upper()}] {alertname}"
            template_payload = {
                "title": title,
                "status": status,
                "alertname": alertname,
                "common_labels": common_labels,
                "common_annotations": common_annotations,
                "selector": selector,
                "error_filter": error_filter,
                "search_window": search_window,
                "context_before": context_before,
                "context_after": context_after,
                "max_matches": max_matches,
                "contexts": [asdict(c) for c in contexts],
            }
            result = send_alerts.delay(template_payload)
            logger.info(f"Отправка уведомления {alertname} по лейблу {common_labels}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в сервисе {e}")
            raise ExtractionException(msg=f"Ошибка постановки задачи рассылки: {e}")
        return JobResponse(result.id)

    def _annotation_lookup(self, payload: dict[str, Any], key: str) -> str | None:
        """Return the most specific annotation value for `key`.

        Priority:
          per-alert annotations -> commonAnnotations -> None
        """
        alerts = payload.get("alerts") or []
        for a in alerts:
            ann = a.get("annotations") or {}
            if key in ann and ann[key] not in (None, ""):
                return str(ann[key])
        common = payload.get("commonAnnotations") or {}
        if key in common and common[key] not in (None, ""):
            return str(common[key])
        return None

    def _label_fallback(self, payload: dict[str, Any], key: str) -> str | None:
        """Get label from commonLabels or from the first alert."""
        common = payload.get("commonLabels") or {}
        if key in common and common[key] not in (None, ""):
            return str(common[key])
        alerts = payload.get("alerts") or []
        if alerts:
            labels = alerts[0].get("labels") or {}
            if key in labels and labels[key] not in (None, ""):
                return str(labels[key])
        return None

    async def job_status(self, job_id: uuid.UUID) -> dict:
        """Получение статуса парсинга и результаты"""
        result = AsyncResult(str(job_id))

        response = {
            "task_id": job_id,
            "state": result.state,
        }

        if result.state == "SUCCESS":
            response["result"] = result.result  # данные из return задачи
        elif result.state == "FAILURE":
            response["error"] = str(result.result)

        return response
