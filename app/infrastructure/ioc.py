from dishka import Provider, Scope, from_context, provide

from app.domain.registry.interfaces import INotificationRegistry
from app.domain.registry.registry import NotificationRegistry
from app.infrastructure.adapters.interfaces import ILokiAdapter
from app.infrastructure.adapters.loki import LokiAdapter
from app.infrastructure.template_render.interfaces import ITemplateRenderer
from app.infrastructure.template_render.jinja_template_renderer import JinjaTemplateRenderer
from app.services.extractor_service import ExtractorService
from app.services.interfaces import IExtractorService
from app.settings.settings import RedisSettings, Settings


class ApplicationProvider(Provider):
    """Провайдер зависимостей приложения"""

    settings = from_context(provides=Settings, scope=Scope.APP)
    redis_settings = from_context(provides=RedisSettings, scope=Scope.APP)
    notification_registry = provide(
        NotificationRegistry, scope=Scope.APP, provides=INotificationRegistry
    )
    template_renderer = provide(JinjaTemplateRenderer, scope=Scope.APP, provides=ITemplateRenderer)
    loki = provide(LokiAdapter, scope=Scope.APP, provides=ILokiAdapter)
    extract_service = provide(ExtractorService, scope=Scope.REQUEST, provides=IExtractorService)


class CeleryProvider(Provider):
    """Провайдер для CELERY"""

    settings = from_context(provides=Settings, scope=Scope.APP)
    redis_settings = from_context(provides=RedisSettings, scope=Scope.APP)
    template_renderer = provide(JinjaTemplateRenderer, scope=Scope.APP, provides=ITemplateRenderer)
    notification_registry = provide(
        NotificationRegistry, scope=Scope.APP, provides=INotificationRegistry
    )
