import logging
from typing import Any

from pyreqwest.client import Client
from pyreqwest.exceptions import JSONDecodeError, StatusError

from app.domain.value_objects.loki import Direction, LokiEntry
from app.infrastructure.adapters.interfaces import ILokiAdapter
from app.infrastructure.exceptions import BaseAppError
from app.settings.settings import Settings

logger = logging.getLogger(__name__)


class LokiAdapter(ILokiAdapter):
    """Адаптер для Loki"""

    def __init__(self, settings: Settings, client: Client) -> None:
        self.base_url = settings.loki.base_url.rstrip("/")
        self.timeout = settings.loki.timeout_s
        self._client = client

    async def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            r = await self._client.get(url).query(params).build().send()
            return await r.json()

        except JSONDecodeError as e:
            raise BaseAppError(msg=f"Ошибка получения тела запроса из Loki: {e.details}")

        except StatusError as e:
            raise BaseAppError(msg=f"Ошибка запроса к Loki: {e.details}, status code: {e.message}")

    async def validate_query(self, *, query: str) -> str:
        """Валидирует LogQL через Loki. Если query невалиден — Loki вернёт 4xx."""
        url = f"{self.base_url}/loki/api/v1/format_query"
        params = {"query": query}

        payload = await self._get_json(url, params)

        data = payload.get("data")
        if not isinstance(data, str) or not data.strip():
            raise BaseAppError(msg="Loki format_query: unexpected response (no data).")
        return data.strip()

    async def query_range(
        self,
        *,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
        direction: Direction,
    ) -> list[LokiEntry]:
        """Запускает LogQL query_range и выдает уплощенные сущности"""
        url = f"{self.base_url}/loki/api/v1/query_range"
        params = {
            "query": query,
            "start": str(start_ns),
            "end": str(end_ns),
            "limit": str(limit),
            "direction": direction,
        }

        payload = await self._get_json(url, params)

        # Проверяем, что resultType является streams (логи), а не matrix (метрики)
        data = payload.get("data") or {}
        result_type = data.get("resultType")
        if result_type != "streams":
            raise BaseAppError(
                msg=f"LogQL must return streams for enrichment, got resultType={result_type!r}."
            )

        results = data.get("result", []) or []
        out: list[LokiEntry] = []

        for stream_block in results:
            stream = stream_block.get("stream", {}) or {}
            values = stream_block.get("values", []) or []
            for ts_str, line in values:
                try:
                    ts_ns = int(ts_str)
                except Exception:
                    continue
                out.append(LokiEntry(ts_ns=ts_ns, line=line, stream=dict(stream)))

        out.sort(key=lambda e: e.ts_ns)
        if direction == "BACKWARD":
            out.reverse()
        return out
