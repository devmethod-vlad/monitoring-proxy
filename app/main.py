from pathlib import Path

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka as setup_dishka_for_litestar
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins.prometheus import PrometheusController
from litestar.plugins.structlog import StructlogPlugin
from litestar.template import TemplateConfig

from app.api import v1_router
from app.infrastructure.exception_handler import exception_handler
from app.infrastructure.ioc import ApplicationProvider
from app.infrastructure.providers import RedisProvider
from app.settings.settings import (
    RedisSettings,
    Settings,
    settings as config,
)
from app.utils.logging import get_structlog_config
from app.utils.version import get_app_version


def get_app() -> Litestar:
    """Генерация Litestar приложения."""
    cors_config = CORSConfig(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    template_config = TemplateConfig(
        directory=Path(__file__).parent / "templates",
        engine=JinjaTemplateEngine,
    )
    container = make_async_container(
        ApplicationProvider(),
        RedisProvider(),
        context={RedisSettings: config.redis, Settings: config},
    )

    litestar_app = Litestar(
        route_handlers=[v1_router, PrometheusController],
        cors_config=cors_config,
        template_config=template_config,
        plugins=[StructlogPlugin(config=get_structlog_config())],
        path=config.app.root_path,
        debug=config.app.debug,
        middleware=[],
        request_max_body_size=200 * 1024 * 1024,
        exception_handlers=exception_handler,
        openapi_config=OpenAPIConfig(
            title=config.app.title,
            version=get_app_version(),
            render_plugins=[ScalarRenderPlugin()],
            path="/docs",
        ),
    )
    setup_dishka_for_litestar(container, litestar_app)
    return litestar_app


app = get_app()
