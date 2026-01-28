import asyncio
import threading
from collections.abc import Callable
from typing import Any

from celery import Celery
from celery.signals import task_prerun, worker_process_init
from dishka import AsyncContainer, make_async_container

from app.settings.settings import RedisSettings, Settings, settings

container: AsyncContainer | None = None
loop = asyncio.new_event_loop()


celery_app = Celery("alert-proxy")

celery_app.conf.update(
    broker_url=str(settings.redis.dsn),
    result_backend=str(settings.redis.dsn),
    include=["app.infrastructure.worker.tasks"],
    worker_proc_alive_timeout=120,
)


def run_coroutine(coro):
    """Функция запуска корутин потокобезопасно"""
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def init_container() -> AsyncContainer:
    """Пробрасывание контейнера в celery app"""
    from app.infrastructure.ioc import CeleryProvider
    from app.infrastructure.providers import RedisProvider

    global container
    container = make_async_container(
        CeleryProvider(),
        RedisProvider(),
        context={RedisSettings: settings.redis, Settings: settings},
    )
    return container


@worker_process_init.connect
def on_worker_start(**_):
    """Запуск воркера"""
    asyncio.set_event_loop(loop)
    init_container()

    def _start_loop():
        loop.run_forever()

    threading.Thread(target=_start_loop, daemon=True).start()


@task_prerun.connect
def on_task_prerun(task: Callable, task_id: str, **kwargs: dict[str, Any]) -> None:
    """Проброс контейнера"""
    task.container = container
