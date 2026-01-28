from app.infrastructure.worker.celery import celery_app
from app.utils.celery_logging import get_celery_logger

logger = get_celery_logger(__name__)


@celery_app.task(name="send_alerts", bind=True, max_retries=3)
def send_alerts(self, payload: dict):  # noqa: ANN001, ANN201
    """Задача рассылки уведомлениц"""
    from app.domain.registry.interfaces import INotificationRegistry  # noqa: PLC0415
    from app.infrastructure.worker.celery import run_coroutine  # noqa: PLC0415

    async def _run() -> dict[str, str]:
        container = getattr(self, "container", None)
        if not container:
            raise self.retry(exc=Exception("Dishka container not initialized"), countdown=5)
        registry = await container.get(INotificationRegistry)
        try:
            await registry.send_all(payload)
            logger.info("Задача рассылки уведомления выполнена успешно")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Задача рассылки уведомлений завершилась с ошибкой {e}")
            return {"status": "error", "message": str(e)}

    return run_coroutine(_run())
