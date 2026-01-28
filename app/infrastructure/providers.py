import redis.asyncio as redis
from dishka import Provider, Scope, from_context, provide

from app.settings.settings import RedisSettings


class RedisProvider(Provider):
    """Провайдер для Redis."""

    redis_settings = from_context(provides=RedisSettings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def redis_client(self, redis_settings: RedisSettings) -> redis.Redis:
        """Получение клиента Redis."""
        dsn = str(redis_settings.dsn)
        connection = redis.from_url(dsn)
        return connection.client()
