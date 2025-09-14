"""Freshness check utilities for trading data."""


def is_stale(last_ts: int, now_ts: int, tf_sec: int, tol: float = 1.2) -> bool:
    """Check if the last candle timestamp is stale.

    Args:
        last_ts: Last candle timestamp
        now_ts: Current timestamp
        tf_sec: Timeframe in seconds
        tol: Tolerance multiplier (default 1.2 = 20% tolerance)

    Returns:
        True if stale, False if fresh
    """
    expected_interval = tf_sec * tol
    time_diff = now_ts - last_ts
    return time_diff > expected_interval
