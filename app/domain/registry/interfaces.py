from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.domain.value_objects.notification import Notification
from app.infrastructure.adapters.interfaces import NotificationSender


class INotificationRegistry(ABC):
    """Интерфейс регистрации"""

    @abstractmethod
    def get_senders(self) -> Iterable[NotificationSender]:
        """Получение объектов"""

    @abstractmethod
    async def send_all(self, notification: Notification) -> None:
        """Отправка уведомлений рассыльщиками"""
