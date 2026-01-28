import logging
from datetime import timedelta
from typing import Any

from pyreqwest.client import ClientBuilder
from pyreqwest.exceptions import JSONDecodeError, StatusError

from app.domain.value_objects.loki import Direction, LokiEntry
from app.infrastructure.adapters.interfaces import ILokiAdapter
from app.infrastructure.exceptions import BaseAppError
from app.settings.settings import Settings

logger = logging.getLogger(__name__)


class LokiAdapter(ILokiAdapter):
    """Адаптер для Loki"""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.loki.base_url.rstrip("/")
        self.timeout = settings.loki.timeout_s

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
        try:
            async with (
                ClientBuilder()
                .error_for_status(True)
                .timeout(timedelta(seconds=self.timeout))
                .build() as client
            ):
                r = await client.get(url).query(params).build().send()

                payload: dict[str, Any] = await r.json()
        except JSONDecodeError as e:
            raise BaseAppError(msg=f"Ошибка получения тела запроса из Loki: {e.details}")
        except StatusError as e:
            raise BaseAppError(msg=f"Ошибка запроса к Loki: {e.details}, status code: {r.status}")

        data = payload.get("data", {})
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

        # Loki may return multiple streams; unify order.
        out.sort(key=lambda e: e.ts_ns)
        if direction == "BACKWARD":
            out.reverse()
        return out
