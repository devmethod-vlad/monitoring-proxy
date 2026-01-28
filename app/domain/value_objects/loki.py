from dataclasses import dataclass
from typing import Literal

Direction = Literal["FORWARD", "BACKWARD"]


@dataclass(frozen=True)
class LokiEntry:
    """Cущность лога Loki"""

    ts_ns: int
    line: str
    stream: dict[str, str]


@dataclass(frozen=True)
class MatchContext:
    """ДТО запроса"""

    ts_ns: int
    ts_iso: str
    line: str
    before: list[str]
    after: list[str]
