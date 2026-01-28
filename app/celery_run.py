from app.infrastructure.worker.celery import celery_app
from app.settings.settings import settings


def main() -> None:
    """Поднятие воркера celery"""
    celery_app.worker_main(
        [
            "worker",
            "--loglevel=INFO",
            f"--concurrency={settings.scaling.effective_celery_workers}",
            "--pool=prefork",
        ]
    )


if __name__ == "__main__":
    main()
