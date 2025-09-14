"""Date utilities for UTC timestamp handling and bar filtering."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone


def to_ts_utc(s: str) -> int:
    """Convert date string to UTC timestamp."""
    x = s.strip()
    if "T" in x:
        if x.endswith("Z"):
            x = x[:-1] + "+00:00"
        dt = datetime.fromisoformat(x)
    else:
        dt = datetime.fromisoformat(x + "T00:00:00")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.astimezone(timezone.utc).timestamp())


def iso_utc(ts: int | None) -> str:
    """Convert timestamp to ISO UTC string."""
    if ts is None:
        return "None"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def filter_bars_by_date(
    bars: Iterable[tuple[int, float, float, float, float, int]],
    start: str | None,
    end: str | None,
) -> tuple[list[tuple[int, float, float, float, float, int]], int | None, int | None]:
    """Filter bars by date range and return filtered bars with start/end timestamps."""
    st = to_ts_utc(start) if start else None
    et = to_ts_utc(end) if end else None
    if et and end and len(end) == 10:
        et += 86399  # конец дня включительно
    fb = [b for b in bars if (st is None or b[0] >= st) and (et is None or b[0] <= et)]
    return fb, st, et
