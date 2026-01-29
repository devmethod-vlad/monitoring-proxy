import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class EnvBaseSettings(BaseSettings):
    """Базовый класс для прокидывания настроек из .env"""

    model_config = SettingsConfigDict(env_file="..env", extra="ignore")


class AppSettings(EnvBaseSettings):
    """Настройки приложения"""

    title: str
    mode: str = "DEV"
    host: str
    port: int
    debug: bool = True
    root_path: str = ""
    model_config = SettingsConfigDict(env_prefix="app_")


class ScalingSettings(EnvBaseSettings):
    """Автовычисление ресурсов"""

    backend_workers: int | None = None
    celery_workers: int | None = None

    model_config = SettingsConfigDict(env_prefix="scale_")

    @computed_field
    def effective_backend_workers(self) -> int:
        """Вычисляемые от CPU воркеры граниан"""
        return self.backend_workers or (os.cpu_count() or 1)

    @computed_field
    def effective_celery_workers(self) -> int:
        """Вычисляемые от CPU воркеры celery"""
        return self.celery_workers or self.effective_backend_workers


class LoggingSettings(EnvBaseSettings):
    """Настройки логгера"""

    app_dir: str
    app_log_file: str
    celery_dir: str
    celery_log_file: str

    model_config = SettingsConfigDict(env_prefix="log_")


class SMTPSettings(EnvBaseSettings):
    """Настройки почты для уведомлений"""

    smtp_server: str
    smtp_port: int
    smtp_helo: str
    smtp_username: str
    smtp_password: str

    model_config = SettingsConfigDict(env_prefix="email_")


class TgSettings(EnvBaseSettings):
    """Настройки для уведомлений Telegram"""

    bot_token: str
    parse_mode: str = "HTML"
    max_chars: int = 3500

    model_config = SettingsConfigDict(env_prefix="telegram_")


class RedisSettings(EnvBaseSettings):
    """Настройки Redis"""

    dsn: RedisDsn | None = None
    port: int
    model_config = SettingsConfigDict(env_prefix="redis_")


class AlertExtractSettings(EnvBaseSettings):
    """Настройки для извлечения данных алертов"""

    context_before: int = 2
    context_after: int = 2
    context_time_range: str = "30m"
    search_window: str = "5m"
    max_matches: int = 3
    default_query_match: str = '{job="testapp"} |= "ERROR"'

    model_config = SettingsConfigDict(env_prefix="alert_")


class TemplateSettings(EnvBaseSettings):
    """Настройки шаблонизатора"""

    dir: str
    tg: str | None = None
    email: str | None = None

    model_config = SettingsConfigDict(env_prefix="template_")


class AlertReceiversSettings(EnvBaseSettings):
    """Настройки контактов для уведомлений"""

    # КРИТИЧНО: Храним как строки, а не списки!
    emails: str | None = None
    tg_ids: str | None = None

    model_config = SettingsConfigDict(env_prefix="receivers_")

    # Используем @property для получения списков
    @property
    def emails_list(self) -> list[str] | None:
        """Возвращает список email адресов"""
        if not self.emails:
            return None
        v = self.emails.strip().strip('"').strip("'")
        return [e.strip() for e in v.split(",") if e.strip()]

    @property
    def tg_ids_list(self) -> list[int] | None:
        """Возвращает список Telegram ID"""
        if not self.tg_ids:
            return None
        v = self.tg_ids.strip().strip('"').strip("'")
        return [int(x.strip()) for x in v.split(",") if x.strip()]


class LokiSettings(EnvBaseSettings):
    """Настройки для адаптера локи"""

    base_url: str
    timeout_s: int

    model_config = SettingsConfigDict(env_prefix="loki_")


class AvailableChannelsSettings(EnvBaseSettings):
    """Настройки доступных каналов для рассылки"""

    channels: str

    # Используем @property для получения списка
    @property
    def channels_list(self) -> list[str]:
        """Возвращает список каналов"""
        if not self.channels:
            return []
        v = self.channels.strip().strip('"').strip("'")
        return [ch.strip() for ch in v.split(",") if ch.strip()]

    model_config = SettingsConfigDict(env_prefix="available_")


class Settings(EnvBaseSettings):
    """Настройки сообщений"""

    app: AppSettings = AppSettings()
    telegram: TgSettings = TgSettings()
    receivers: AlertReceiversSettings = AlertReceiversSettings()
    channels: AvailableChannelsSettings = AvailableChannelsSettings()

    smtp: SMTPSettings = SMTPSettings()
    scaling: ScalingSettings = ScalingSettings()
    redis: RedisSettings = RedisSettings()
    templates: TemplateSettings = TemplateSettings()
    alert: AlertExtractSettings = AlertExtractSettings()
    loki: LokiSettings = LokiSettings()
    logging: LoggingSettings = LoggingSettings()


@lru_cache
def get_settings() -> Settings:
    """Кэшированная инициаилзация настроек"""
    return Settings()


settings = get_settings()
