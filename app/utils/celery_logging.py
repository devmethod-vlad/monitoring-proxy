import sys
from pathlib import Path

import structlog
from celery.signals import setup_logging
from app.settings.settings import settings

def setup_celery_logging(**kwargs):
    """Настройка логирования для Celery"""

    # Создаем директорию для логов
    log_dir = Path(settings.logging.celery_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / settings.logging.celery_log_file
    # Конфигурация для стандартной библиотеки logging
    import logging.config

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "celery_plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=False),
                ],
            },
            "celery_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
            },
        },
        "handlers": {
            "celery_console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "celery_console",
                "stream": "ext://sys.stdout",
            },
            "celery_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "celery_plain",
                "filename": log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
                "delay": False,
            },
        },
        "loggers": {
            "celery": {
                "handlers": ["celery_console", "celery_file"],
                "level": "INFO",
                "propagate": False,
            },
            "celery.app.trace": {
                "handlers": ["celery_console", "celery_file"],
                "level": "INFO",
                "propagate": False,
            },
            "celery.worker": {
                "handlers": ["celery_console", "celery_file"],
                "level": "INFO",
                "propagate": False,
            },
            "app": {  # Все логгеры app.* (app.worker, app.infrastructure, и т.д.)
                "handlers": ["celery_console", "celery_file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["celery_console", "celery_file"],
            "level": "INFO",
        },
    })

    # Настройка structlog для Celery
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_celery_logger(name: str = "app.worker"):
    """Получить логгер для Celery задач"""
    return structlog.get_logger(name)


# Подключаем настройку при инициализации Celery
setup_logging.connect(setup_celery_logging)