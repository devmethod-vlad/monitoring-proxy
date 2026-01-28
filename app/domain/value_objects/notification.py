from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    """Нормализованное сообщение"""

    title: str
    body: str
