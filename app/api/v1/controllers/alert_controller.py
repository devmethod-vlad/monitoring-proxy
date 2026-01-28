import json
import uuid

from dishka import FromDishka
from dishka.integrations.litestar import inject
from litestar import Controller, Request, get, post

from app.api.v1.responses.job_respose import JobResponse
from app.services.interfaces import IExtractorService


class AlertController(Controller):
    """Контроллер для алертов графаны"""

    path = ""
    tags = ["Grafana Webhook"]

    @post(
        path="/webhook/grafana",
        summary="Вебхук Grafana",
        description="Принимает информацию об alert из Grafana, ставит задачу рассылки в очередь",
    )
    @inject
    async def webhook(
        self, request: Request, service: FromDishka[IExtractorService]
    ) -> JobResponse:
        """Вебхук для графаны"""
        raw = await request.body()
        payload = json.loads(raw.decode("utf-8"))
        return await service.extract(payload)

    @get(path="/status/{job_id:uuid}", summary="Получение статуса задачи")
    @inject
    async def status(
        self, request: Request, job_id: uuid.UUID, service: FromDishka[IExtractorService]
    ) -> dict:
        """Получение статуса задачи"""
        return await service.job_status(job_id)
