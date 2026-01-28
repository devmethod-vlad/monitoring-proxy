import sys
from pathlib import Path

import structlog
from litestar.logging.config import LoggingConfig, StructLoggingConfig
from litestar.plugins.structlog import StructlogConfig
from app.settings.settings import settings

def get_structlog_config() -> StructlogConfig:
    """Конфигурация структлога с выводом в консоль и файл"""

    # Создаем директорию для логов
    log_dir = Path(settings.logging.app_dir)
    log_dir.mkdir(exist_ok=True, parents=True)

    log_file = log_dir / settings.logging.app_log_file

    structlog_config = StructLoggingConfig(
        pretty_print_tty=False,
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        standard_lib_logging_config=LoggingConfig(
            version=1,
            disable_existing_loggers=False,
            formatters={
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(colors=False),  # Текст без цветов для файла
                    ],
                },
                "console_formatter": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(colors=True),
                    ],
                },
            },
            handlers={
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "console_formatter",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "plain",  # Текстовый формат
                    "filename": str(log_file),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            loggers={
                "litestar": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "app": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
            root={
                "handlers": ["console", "file"],
                "level": "INFO",
            },
        ),
    )

    return StructlogConfig(
        structlog_logging_config=structlog_config,
        enable_middleware_logging=True,
    )