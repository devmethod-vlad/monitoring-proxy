from granian import Granian
from granian.constants import Interfaces

from app.settings.settings import settings


def main() -> None:
    """Запуск сервера"""
    server = Granian(
        target="app.main:app",  # ← Строка, не объект!
        address=settings.app.host,  # ← Было: host
        port=settings.app.port,
        interface=Interfaces.ASGI,  # ← Добавьте это!
        workers=settings.scaling.effective_backend_workers,
        reload=settings.app.debug,
        log_level="info",
    )

    server.serve()


if __name__ == "__main__":
    main()
