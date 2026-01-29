import uuid
from dataclasses import asdict

import structlog
from celery.result import AsyncResult
from pydantic import ValidationError

from app.api.v1.responses.job_respose import JobResponse
from app.domain.exceptions import ExtractionException
from app.domain.schemes.grafana import GrafanaAnnotations, GrafanaWebhookPayload
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
            try:
                validated_payload = GrafanaWebhookPayload.model_validate(payload)
            except ValidationError as e:
                logger.error(f"Ошибка валидации Grafana webhook payload: {e}")
                raise ExtractionException(msg=f"Невалидный payload от Grafana: {e}")

            annotations = GrafanaAnnotations.from_payload(validated_payload)

            status = str(validated_payload.status or "unknown")
            alertname = (
                self._label_fallback(validated_payload, "alertname")
                or validated_payload.groupLabels.get("alertname")
                or "(no alertname)"
            )
            common_labels: dict[str, str] = {
                k: str(v) for k, v in (validated_payload.commonLabels or {}).items()
            }
            common_annotations: dict[str, str] = {
                k: str(v) for k, v in (validated_payload.commonAnnotations or {}).items()
            }

            query_match = annotations.query_match or self.settings_alert.default_query_match

            if not query_match:
                raise ExtractionException(
                    msg="query_match не указан в аннотациях и отсутствует default_query_match в настройках"
                )

            try:
                validated_query = await self.loki.validate_query(query=query_match)
                logger.info(f"Query валидирован: {validated_query}")
            except Exception as e:
                logger.error(f"Невалидный LogQL запрос: {e}")
                raise ExtractionException(msg=f"Невалидный LogQL запрос '{query_match}': {e}")

            context_before = int(annotations.context_before or self.settings_alert.context_before)
            context_after = int(annotations.context_after or self.settings_alert.context_after)
            max_matches = int(annotations.max_matches or self.settings_alert.max_matches)

            search_window = annotations.search_window or self.settings_alert.search_window
            context_time_range = (
                annotations.context_time_range or self.settings_alert.context_time_range
            )

            search_window_s = parse_duration_to_seconds(search_window)
            context_range_s = parse_duration_to_seconds(context_time_range)
            end_dt = utc_now()
            alerts = validated_payload.alerts or []

            if alerts and isinstance(alerts, list):
                starts = []
                for a in alerts:
                    if a.startsAt:
                        starts.append(rfc3339_to_datetime(str(a.startsAt)))
                if starts:
                    end_dt = max(starts)

            start_dt = end_dt - __import__("datetime").timedelta(seconds=search_window_s)

            end_ns = dt_to_ns(end_dt)
            start_ns = dt_to_ns(start_dt)

            matches = await self.loki.query_range(
                query=validated_query,
                start_ns=start_ns,
                end_ns=end_ns,
                limit=max_matches,
                direction="BACKWARD",
            )

            # Нужно извлечь selector из query_match
            # берем часть до первого pipe |
            selector_for_context = validated_query.split("|")[0].strip()

            contexts: list[MatchContext] = []
            ctx_range_ns = int(context_range_s * 1_000_000_000)

            for m in matches[:max_matches]:

                before_start = max(0, m.ts_ns - ctx_range_ns)
                before_end = max(0, m.ts_ns - 1)
                before_entries = await self.loki.query_range(
                    query=selector_for_context,
                    start_ns=before_start,
                    end_ns=before_end,
                    limit=context_before,
                    direction="BACKWARD",
                )

                before_lines = [e.line for e in reversed(before_entries)]

                after_start = m.ts_ns + 1
                after_end = m.ts_ns + ctx_range_ns

                after_entries = await self.loki.query_range(
                    query=selector_for_context,
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
                "query_match": validated_query,
                "search_window": search_window,
                "context_before": context_before,
                "context_after": context_after,
                "max_matches": max_matches,
                "contexts": [asdict(c) for c in contexts],
            }

            result = send_alerts.delay(template_payload)
            logger.info(f"Отправка уведомления {alertname} по лейблу {common_labels}")

        except ExtractionException:
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка в сервисе {e}")
            raise ExtractionException(msg=f"Ошибка постановки задачи рассылки: {e}")

        return JobResponse(result.id)

    def _label_fallback(self, payload: GrafanaWebhookPayload, key: str) -> str | None:
        """Get label from commonLabels or from the first alert."""
        common = payload.commonLabels or {}
        if key in common and common[key] not in (None, ""):
            return str(common[key])
        alerts = payload.alerts or []
        if alerts:
            labels = alerts[0].labels or {}
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
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["error"] = str(result.result)

        return response
