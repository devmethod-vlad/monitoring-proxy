class BaseAppError(Exception):
    """Базовая ошибка в инфраструктурном слое сервиса."""

    status_code: int = 400
    loc: list[str] = ["error"]
    field: str | None = None
    error_code: str = "app_error"

    def __init__(self, msg: str | None = None, *, ctx: dict | None = None):
        super().__init__(msg or self.__doc__ or "Application error")
        self.msg = msg or self.__doc__ or "Application error"
        self.ctx = ctx or {}
