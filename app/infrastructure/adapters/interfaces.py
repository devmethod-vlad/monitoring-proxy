from abc import ABC, abstractmethod
from typing import Protocol

from app.domain.value_objects.loki import Direction, LokiEntry
from app.domain.value_objects.notification import Notification
from app.settings.settings import Settings


class NotificationSender(ABC):
    """Порт адаптера для отправки уведомлений"""

    settings: Settings

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Интерфейс отправки уведомления"""


class NotificationSenderFactory(Protocol):
    """Протокол иницилизации"""

    def __call__(self, settings: Settings) -> NotificationSender:
        """Инициализация"""
        ...


class ILokiAdapter(ABC):
    """Адаптер для локи"""

    @abstractmethod
    async def query_range(
        self,
        *,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
        direction: Direction,
    ) -> list[LokiEntry]:
        """Метод извлечения"""
