"""Timeframe utilities."""

from typing import Final

# Timeframe mappings
TIMEFRAME_SECONDS: Final[dict[str, int]] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


def tf_to_seconds(tf: str) -> int:
    """Convert timeframe string to seconds.

    Args:
        tf: Timeframe string (e.g., '1m', '5m', '15m', '1h', '4h', '1d')

    Returns:
        Number of seconds

    Raises:
        ValueError: If timeframe is not supported
    """
    if tf not in TIMEFRAME_SECONDS:
        raise ValueError(
            f"Unsupported timeframe: {tf}. Supported: {list(TIMEFRAME_SECONDS.keys())}"
        )
    return TIMEFRAME_SECONDS[tf]
