from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.notification import Notification


class ITemplateRenderer(ABC):
    """Порт для рендеринга шаблонов уведомлений."""

    @abstractmethod
    def render(self, template_name: str, payload: dict) -> Notification:
        """Рендеринг и создание уведомления"""
        raise NotImplementedError
