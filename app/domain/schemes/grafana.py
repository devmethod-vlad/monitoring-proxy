from typing import Any

from pydantic import BaseModel, Field, field_validator


class GrafanaAlert(BaseModel):
    """Отдельный алерт в Grafana webhook"""

    status: str | None = None
    labels: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None
    startsAt: str | None = None
    endsAt: str | None = None
    generatorURL: str | None = None
    fingerprint: str | None = None

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля


class GrafanaWebhookPayload(BaseModel):
    """Основная схема Grafana webhook payload"""

    status: str | None = None
    alerts: list[GrafanaAlert] | None = Field(default_factory=list)
    groupLabels: dict[str, Any] | None = Field(default_factory=dict)
    commonLabels: dict[str, Any] | None = Field(default_factory=dict)
    commonAnnotations: dict[str, Any] | None = Field(default_factory=dict)
    externalURL: str | None = None
    version: str | None = None
    groupKey: str | None = None
    truncatedAlerts: int | None = None

    class Config:
        extra = "allow"

    @field_validator("alerts", mode="before")
    @classmethod
    def ensure_alerts_list(cls, v):
        """Гарантирует, что alerts это список"""
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        return v


class GrafanaAnnotations(BaseModel):
    """Наши кастомные аннотации для извлечения данных"""

    query_match: str | None = None
    context_before: int | None = None
    context_after: int | None = None
    context_time_range: str | None = None
    search_window: str | None = None
    max_matches: int | None = None

    @classmethod
    def from_payload(cls, payload: GrafanaWebhookPayload) -> "GrafanaAnnotations":
        """Извлекает аннотации из payload с учетом приоритета"""

        def get_annotation(key: str) -> Any:
            """Получает аннотацию с приоритетом: per-alert -> common -> None"""
            # Сначала проверяем аннотации отдельных алертов
            if payload.alerts:
                for alert in payload.alerts:
                    if alert.annotations and key in alert.annotations:
                        value = alert.annotations[key]
                        if value not in (None, ""):
                            return value

            # Затем проверяем общие аннотации
            if payload.commonAnnotations and key in payload.commonAnnotations:
                value = payload.commonAnnotations[key]
                if value not in (None, ""):
                    return value

            return None

        return cls(
            query_match=get_annotation("query_match"),
            context_before=get_annotation("context_before"),
            context_after=get_annotation("context_after"),
            context_time_range=get_annotation("context_time_range"),
            search_window=get_annotation("search_window"),
            max_matches=get_annotation("max_matches"),
        )
