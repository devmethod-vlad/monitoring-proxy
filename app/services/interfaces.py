import uuid
from abc import ABC, abstractmethod

from app.api.v1.responses.job_respose import JobResponse


class IExtractorService(ABC):
    """Сервис обработки данных от Graphana"""

    @abstractmethod
    async def extract(self, payload: dict) -> JobResponse:
        """Извлекает и обрабатывает данные из Loki"""

    @abstractmethod
    async def job_status(self, job_id: uuid.UUID) -> dict:
        """Получение статуса задачи и результаты"""
