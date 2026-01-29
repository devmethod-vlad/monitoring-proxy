from collections.abc import Iterable
from typing import Any

from app.domain.exceptions import TemplateRenderingException
from app.domain.registry.interfaces import INotificationRegistry
from app.domain.value_objects.notification import Notification
from app.infrastructure.adapters.email import EmailAdapter
from app.infrastructure.adapters.interfaces import NotificationSender, NotificationSenderFactory
from app.infrastructure.adapters.telegram import TelegramAdapter
from app.infrastructure.template_render.interfaces import ITemplateRenderer
from app.settings.settings import Settings
from app.utils.celery_logging import get_celery_logger

logger = get_celery_logger(__name__)


class NotificationRegistry(INotificationRegistry):
    """Реестр рассыльщиков для передачи им полномочий рассылки"""

    _FACTORY: dict[str, NotificationSenderFactory] = {
        "telegram": TelegramAdapter,
        "email": EmailAdapter,
    }

    def __init__(self, settings: Settings, render_engine: ITemplateRenderer) -> None:
        self._settings = settings
        self._senders: dict[str, NotificationSender] = {}
        self._template_engine: ITemplateRenderer = render_engine
        self._enabled_channels = self._settings.channels.channels_list
        self._init_senders()
        self._template_map = {
            "telegram": settings.templates.tg,
            "email": settings.templates.email,
        }

    def _init_senders(self) -> None:
        """Инициализация доступных рассыльщиков"""
        for channel in self._enabled_channels:
            sender_cls = self._FACTORY.get(channel)
            if not sender_cls:
                continue

            self._senders[channel] = sender_cls(self._settings)

    def get_senders(self) -> Iterable[NotificationSender]:
        """Получение объектов"""
        return self._senders.values()

    def _process_payload(self, payload: dict[str, Any]) -> dict[str, Notification]:
        notifications = {}
        try:
            for channel in self._enabled_channels:
                template_name = self._template_map.get(channel)
                notification = self._template_engine.render(template_name, payload=payload)
                notifications[channel] = notification
        except Exception as e:
            logger.error(f"Рендеринг шаблонов уведомлений завершился с ошибкой{e}")
            raise TemplateRenderingException(msg=f"Ошибка рендеринга шаблонов {e}")
        return notifications

    async def send_all(self, payload: dict[str, Any]) -> None:
        """Отправка уведомлений рассыльщиками"""
        results = {}
        errors = []
        notifications = self._process_payload(payload)
        for channel, sender in self._senders.items():
            notification = notifications.get(channel)
            if not notification:
                continue
            try:
                success = await sender.send(notification)
                results[channel] = success
            except Exception as e:
                logger.error(f"Ошибка канала, channel= {channel}, error={str(e)}")
                results[channel] = False
                errors.append(f"{channel}: {str(e)}")
        logger.info(f"Результаты отправки по каналам: {results}, ошибки: {errors}")
