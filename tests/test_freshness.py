"""Tests for freshness check utilities."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.utils.freshness import is_stale  # noqa: E402


def test_fresh_data():
    """Test that fresh data is not considered stale."""
    # Fresh data: within tolerance
    last_ts = 1609459200  # 2021-01-01 00:00:00
    now_ts = last_ts + 900  # 15 minutes later (15m timeframe)
    tf_sec = 900  # 15 minutes

    assert not is_stale(last_ts, now_ts, tf_sec)


def test_stale_data():
    """Test that stale data is detected."""
    # Stale data: beyond tolerance
    last_ts = 1609459200  # 2021-01-01 00:00:00
    now_ts = last_ts + 2000  # Much later than expected
    tf_sec = 900  # 15 minutes

    assert is_stale(last_ts, now_ts, tf_sec)


def test_borderline_data():
    """Test borderline case with exact tolerance."""
    last_ts = 1609459200
    tf_sec = 900
    tol = 1.2
    expected_interval = tf_sec * tol  # 1080 seconds

    # Exactly at tolerance boundary
    now_ts = last_ts + int(expected_interval)
    assert not is_stale(last_ts, now_ts, tf_sec, tol)

    # Just over tolerance boundary
    now_ts = last_ts + int(expected_interval) + 1
    assert is_stale(last_ts, now_ts, tf_sec, tol)


def test_different_timeframes():
    """Test with different timeframes."""
    last_ts = 1609459200

    # 1 minute timeframe
    assert not is_stale(last_ts, last_ts + 60, 60)  # Fresh
    assert is_stale(last_ts, last_ts + 200, 60)  # Stale

    # 1 hour timeframe
    assert not is_stale(last_ts, last_ts + 3600, 3600)  # Fresh
    assert is_stale(last_ts, last_ts + 5000, 3600)  # Stale
