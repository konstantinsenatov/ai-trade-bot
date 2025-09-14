"""Data source factory for OHLCV data loading."""

from __future__ import annotations
from typing import Protocol

OHLCV = tuple[int, float, float, float, float, int]

class Source(Protocol):
    """Protocol for OHLCV data sources."""
    def load(self, tf: str, bars: int | None = None, start: str | None = None, end: str | None = None) -> list[OHLCV]: ...

def get_source(kind: str = "real"):
    """Get data source by kind."""
    if kind == "real":
        # TODO: УКАЖИ корректный путь к реальному загрузчику!
        try:
            from bot.data.real_source import RealOHLCV  # ← поправь под свой модуль
        except Exception as e:
            raise ImportError(
                "RealOHLCV не найден. Укажи путь к реальному загрузчику в bot/data/loader.py"
            ) from e
        return RealOHLCV()
    elif kind == "synthetic":
        from bot.data.ohlcv_source import SyntheticOHLCV
        return SyntheticOHLCV(seed=42)
    else:
        raise ValueError(f"Unknown source kind: {kind}")