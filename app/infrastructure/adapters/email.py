from email.message import EmailMessage

import aiosmtplib

from app.domain.value_objects.notification import Notification
from app.infrastructure.adapters.interfaces import NotificationSender
from app.settings.settings import Settings
from app.utils.celery_logging import get_celery_logger

logger = get_celery_logger(__name__)


class EmailAdapter(NotificationSender):
    """Адаптер для email"""

    def __init__(self, settings: Settings):
        self._smtp = settings.smtp
        self._receivers = settings.receivers.emails_list  # list[str]

    async def send(self, notification: Notification) -> bool:
        """Рассылка email"""
        msg = EmailMessage()
        msg["From"] = self._smtp.smtp_username
        msg["To"] = ", ".join(self._receivers)  # ← строка
        msg["Subject"] = notification.title
        msg.set_content(notification.body)
        success = True
        try:
            await aiosmtplib.send(
                msg,
                hostname=self._smtp.smtp_server,
                port=self._smtp.smtp_port,
                username=self._smtp.smtp_username,
                password=self._smtp.smtp_password,
                start_tls=True,
                recipients=self._receivers,  # ← список
                timeout=20,
            )
            logger.info("Email уведомление успешно отправлено")
            return success
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления через email: {e}")
            success = False
            return success
