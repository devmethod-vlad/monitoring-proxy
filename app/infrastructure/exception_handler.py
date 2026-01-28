from typing import Any

from litestar import MediaType, Request, Response
from pydantic import ValidationError

from app.domain.exceptions import DomainException
from app.infrastructure.exceptions import BaseAppError


def build_error_for_litestar(
    status_code: int,
    loc: str | list[str],
    field: str | None = None,
    error_code: str = "error",
    msg: str = "Ошибка",
    ctx: dict | None = None,
) -> Response:
    """Формирование ответа обработчика ошибок."""
    error = {"msg": msg, "code": error_code, "ctx": ctx}

    loc = loc.split(":") if isinstance(loc, str) else loc
    loc += ["non_field_error" if field is None else field]

    content: dict[str, Any] = dict()

    def deep_insert(keys: list[str], value: Any) -> None:
        d = content
        for subkey in keys[:-1]:
            d = d.setdefault(subkey, dict())
        d[keys[-1]] = value

    deep_insert(loc, error)
    return Response(status_code=status_code, content=content)


def parse_validation_error(
    exc: ValidationError,
) -> dict[str | int, Any]:
    """Кастомный обработчик ошибки ValidationError и RequestValidationError.

    Возвращает json с ошибками той же структуры, что и валидируемый объект.
    """
    result: dict[str | int, Any] = {}

    def deep_insert(keys: tuple[str | int, ...], value: Any) -> None:
        d = result
        for subkey in keys[:-1]:
            d = d.setdefault(subkey, {})
        d[keys[-1]] = value

    for error in exc.errors():
        keys: tuple[str | int, ...] = (
            error["loc"][1:] if error["loc"][0] in ["__root__"] else error["loc"]
        )
        deep_insert(keys, {"msg": error["msg"], "code": error["type"], "ctx": error.get("ctx")})
    return result


async def litestar_error_handler(request: Request, exc: BaseAppError) -> Response:
    """Обработчик инфраструктурной ощибки для Litestar."""
    return build_error_for_litestar(
        status_code=exc.status_code,
        loc=exc.loc,
        field=exc.field,
        error_code=exc.error_code,
        msg=exc.msg,
        ctx=exc.ctx,
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> Response:
    """Обработка валидации для litestar"""
    return Response(
        media_type=MediaType.TEXT,
        status_code=422,
        content=parse_validation_error(exc),
    )


async def litestar_domain_exception_handler(request: Request, exc: DomainException) -> Response:
    """Обработчик доменной ошибки Litestar."""
    return build_error_for_litestar(
        status_code=exc.status_code,
        loc=exc.loc,
        field=exc.field,
        error_code=exc.error_code,
        msg=exc.msg,
        ctx=exc.ctx,
    )


exception_handler = {
    DomainException: litestar_domain_exception_handler,
    BaseAppError: litestar_error_handler,
    ValidationError: validation_exception_handler,
}
