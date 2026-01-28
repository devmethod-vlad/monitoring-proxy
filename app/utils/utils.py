from __future__ import annotations

import datetime as _dt
import re
from collections.abc import Iterable

_DURATION_RE = re.compile(r"^\s*(\d+)\s*(ms|s|m|h|d)\s*$", re.IGNORECASE)


def parse_duration_to_seconds(value: str) -> float:
    """Parse a tiny duration language into seconds.

    Supported units: ms, s, m, h, d

    Examples:
        "30s" -> 30
        "5m"  -> 300
        "1h"  -> 3600
    """
    m = _DURATION_RE.match(value or "")
    if not m:
        raise ValueError(f"Invalid duration: {value!r}. Use e.g. 30s, 5m, 1h, 2d")
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "ms":
        return n / 1000.0
    if unit == "s":
        return float(n)
    if unit == "m":
        return float(n) * 60
    if unit == "h":
        return float(n) * 3600
    if unit == "d":
        return float(n) * 86400
    raise ValueError(f"Unsupported duration unit: {unit}")


def utc_now() -> _dt.datetime:
    """Получение UTC"""
    return _dt.datetime.now(tz=_dt.UTC)


def rfc3339_to_datetime(value: str) -> _dt.datetime:
    """Parse RFC3339 timestamps used by Grafana payload (startsAt/endsAt)."""
    if not value:
        return utc_now()
    # Examples:
    #   2026-01-15T12:34:56Z
    #   2026-01-15T12:34:56.789Z
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return _dt.datetime.fromisoformat(value)
    except Exception:
        return utc_now()


def dt_to_ns(dt: _dt.datetime) -> int:
    """Datetime - наносекунды"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.UTC)
    return int(dt.timestamp() * 1_000_000_000)


def ns_to_dt(ns: int) -> _dt.datetime:
    """Наносекунды - datetime"""
    return _dt.datetime.fromtimestamp(ns / 1_000_000_000, tz=_dt.UTC)


def safe_join_lines(lines: Iterable[str], max_chars: int) -> str:
    """Join lines and truncate to max chars (for Telegram limits)."""
    s = "\n".join(lines)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."
