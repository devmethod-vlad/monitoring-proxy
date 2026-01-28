class DomainException(Exception):
    """Базовая доменная ошибка."""

    status_code: int = 409
    error_code: str = "domain_error"
    loc: list[str] = ["domain"]
    field: str | None = None

    def __init__(self, msg: str | None = None, *, ctx: dict | None = None):
        super().__init__(msg or self.__doc__ or "Domain error")
        self.msg = msg or self.__doc__ or "Domain error"
        self.ctx = ctx or {}


class ExtractionException(DomainException):
    """Ошибка извлечения информации из Loki"""

    status_code: int = 400
    error_code = "extraction_error"


class TemplateRenderingException(DomainException):
    """Ошибка рендеринга шаблонов"""

    status_code: int = 429
    error_code = "template_rendering_error"
