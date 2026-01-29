from collections.abc import AsyncIterable
from datetime import timedelta

import redis.asyncio as redis
from dishka import Provider, Scope, from_context, provide
from pyreqwest.client import Client, ClientBuilder

from app.settings.settings import RedisSettings, Settings


class RedisProvider(Provider):
    """Провайдер для Redis."""

    redis_settings = from_context(provides=RedisSettings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def redis_client(self, redis_settings: RedisSettings) -> redis.Redis:
        """Получение клиента Redis."""
        dsn = str(redis_settings.dsn)
        connection = redis.from_url(dsn)
        return connection.client()


class HttpProvider(Provider):
    """Провайдер http клиента"""

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    async def loki_http_client(self, settings: Settings) -> AsyncIterable[Client]:
        """Получение pooling клиента для Loki"""
        async with (
            ClientBuilder()
            .error_for_status(True)
            .timeout(timedelta(seconds=settings.loki.timeout_s))
            .build()
        ) as client:
            yield client
