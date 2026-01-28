from pyreqwest.client import ClientBuilder

from app.domain.value_objects.notification import Notification
from app.infrastructure.adapters.interfaces import NotificationSender
from app.settings.settings import Settings
from app.utils.celery_logging import get_celery_logger
from app.utils.utils import safe_join_lines

logger = get_celery_logger(__name__)


class TelegramAdapter(NotificationSender):
    """Работа с телеграммом"""

    def __init__(self, settings: Settings):
        self.bot_token = settings.telegram.bot_token
        self.chat_ids = settings.receivers.tg_ids_list
        self.parse_mode = settings.telegram.parse_mode
        self.max_chars = settings.telegram.max_chars

    async def send(self, notification: Notification) -> bool:
        """Рассылка"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        text = safe_join_lines(
            [notification.title, "", notification.body], max_chars=self.max_chars
        )
        payloads = [
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
                "parse_mode": self.parse_mode,
            }
            for chat_id in self.chat_ids
        ]
        success_count = 0
        failed_count = 0
        async with ClientBuilder().error_for_status(True).build() as client:
            logger.info(f"Отправка телеграмм-уведомлений {len(self.chat_ids)} пользователям")
            for payload in payloads:
                try:
                    chat_id = payload["chat_id"]
                    await client.post(url).body_json(payload).build().send()
                    logger.info("Сообщение успешно отправлено в Telegram", chat_id=chat_id)
                    success_count += 1
                except Exception as e:
                    logger.error("Ошибка отправки в Telegram", chat_id=chat_id, error=str(e))
                    failed_count += 1
        logger.info(
            "Рассылка в Telegram завершена",
            total=len(payloads),
            success=success_count,
            failed=failed_count,
        )
        return success_count > 0
