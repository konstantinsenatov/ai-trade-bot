# bot/data/loader.py
from __future__ import annotations

import os
import sys
from typing import Protocol

OHLCV = tuple[int, float, float, float, float, int]


class Source(Protocol):
    def load(
        self, tf: str, bars: int | None = None, start: str | None = None, end: str | None = None
    ) -> list[OHLCV]: ...


def get_source(kind: str | None = None) -> Source:
    kind = (kind or os.getenv("DATA_SOURCE") or "synthetic").lower()
    if kind == "real":
        try:
            from bot.data.real_source import RealOHLCV  # если есть — используем

            return RealOHLCV()
        except Exception as e:
            print(f"[warn] RealOHLCV not available, fallback to synthetic: {e}", file=sys.stderr)
    from bot.data.ohlcv_source import SyntheticOHLCV

    return SyntheticOHLCV(seed=42)
