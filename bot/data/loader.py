# bot/data/loader.py
from __future__ import annotations

import os
import sys
from typing import Protocol, Any

OHLCV = tuple[int, float, float, float, float, int]


class Source(Protocol):
    def load(
        self, tf: str, bars: int | None = None, start: str | None = None, end: str | None = None
    ) -> list[OHLCV]: ...


def load_data(source: str = "historical", **kwargs) -> list[OHLCV]:
    """Load data from specified source.
    
    Args:
        source: Data source ("historical", "real", "synthetic")
        **kwargs: Additional parameters for data loading
        
    Returns:
        List of OHLCV bars
        
    Raises:
        ValueError: If unknown data source is specified
    """
    if source == "historical":
        from bot.data import historical_source
        return historical_source.load(**kwargs)
    elif source == "real":
        from bot.data import real_source
        # Convert DataFrame to OHLCV format
        df = real_source.fetch_binance_ohlcv(**kwargs)
        return [
            (
                int(row["timestamp"].timestamp()),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                int(row["volume"])
            )
            for _, row in df.iterrows()
        ]
    elif source == "synthetic":
        from bot.data.ohlcv_source import SyntheticOHLCV
        synthetic = SyntheticOHLCV(seed=42)
        return synthetic.load(**kwargs)
    else:
        raise ValueError(f"Unknown data source: {source}")


def get_source(kind: str | None = None) -> Source:
    """Get data source instance (legacy method for backward compatibility)."""
    kind = (kind or os.getenv("DATA_SOURCE") or "synthetic").lower()
    if kind == "real":
        try:
            from bot.data.real_source import RealOHLCV  # если есть — используем

            return RealOHLCV()
        except Exception as e:
            print(f"[warn] RealOHLCV not available, fallback to synthetic: {e}", file=sys.stderr)
    from bot.data.ohlcv_source import SyntheticOHLCV

    return SyntheticOHLCV(seed=42)
