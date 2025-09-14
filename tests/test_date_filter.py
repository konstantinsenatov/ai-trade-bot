"""Test date filtering functionality."""

from datetime import datetime


def _to_ts(s: str) -> int:
    """Convert date string to timestamp."""
    if "T" in s:
        dt = datetime.fromisoformat(s)
    else:
        dt = datetime.fromisoformat(s + "T00:00:00")
    return int(dt.timestamp())


def filter_bars_by_date(bars, start_date=None, end_date=None):
    """Filter bars by date range."""
    start_ts = _to_ts(start_date) if start_date else None
    end_ts = _to_ts(end_date) if end_date else None
    if end_ts and end_date and len(end_date) == 10:
        end_ts += 86399  # end of day inclusive

    return [
        b for b in bars if (not start_ts or b[0] >= start_ts) and (not end_ts or b[0] <= end_ts)
    ]


def test_date_filter_basic():
    """Test basic date filtering functionality."""
    # Generate 5 bars with 1-day intervals
    base_ts = int(datetime(2023, 1, 1).timestamp())
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)  # 1 day = 86400 seconds
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # Test filtering from day 1 to day 3 (inclusive)
    start_date = "2023-01-02"  # day 1
    end_date = "2023-01-04"  # day 3

    filtered_bars = filter_bars_by_date(bars, start_date, end_date)

    # Should have exactly 3 bars (days 1, 2, 3)
    assert len(filtered_bars) == 3

    # Check that boundaries are included
    first_bar_ts = filtered_bars[0][0]
    last_bar_ts = filtered_bars[-1][0]

    start_ts = _to_ts(start_date)
    end_ts = _to_ts(end_date) + 86399  # end of day inclusive

    assert first_bar_ts >= start_ts
    assert last_bar_ts <= end_ts

    # Verify specific timestamps
    expected_timestamps = [
        base_ts + (1 * 86400),  # day 1
        base_ts + (2 * 86400),  # day 2
        base_ts + (3 * 86400),  # day 3
    ]

    actual_timestamps = [bar[0] for bar in filtered_bars]
    assert actual_timestamps == expected_timestamps


def test_date_filter_start_only():
    """Test filtering with only start date."""
    base_ts = int(datetime(2023, 1, 1).timestamp())
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # Filter from day 2 onwards
    filtered_bars = filter_bars_by_date(bars, start_date="2023-01-03")

    # Should have 3 bars (days 2, 3, 4)
    assert len(filtered_bars) == 3


def test_date_filter_end_only():
    """Test filtering with only end date."""
    base_ts = int(datetime(2023, 1, 1).timestamp())
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # Filter up to day 2
    filtered_bars = filter_bars_by_date(bars, end_date="2023-01-03")

    # Should have 3 bars (days 0, 1, 2)
    assert len(filtered_bars) == 3


def test_date_filter_no_filter():
    """Test that no filtering returns all bars."""
    base_ts = int(datetime(2023, 1, 1).timestamp())
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # No filtering
    filtered_bars = filter_bars_by_date(bars)

    # Should have all 5 bars
    assert len(filtered_bars) == 5


def test_date_filter_empty_result():
    """Test filtering that results in empty list."""
    base_ts = int(datetime(2023, 1, 1).timestamp())
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # Filter for dates outside the range
    filtered_bars = filter_bars_by_date(bars, start_date="2023-02-01")

    # Should have 0 bars
    assert len(filtered_bars) == 0


def test_date_filter_with_time():
    """Test filtering with datetime including time."""
    base_ts = int(datetime(2023, 1, 1, 12, 0, 0).timestamp())  # noon
    bars = []
    for i in range(5):
        ts = base_ts + (i * 86400)
        bars.append((ts, 100.0, 101.0, 99.0, 100.5, 1000))

    # Filter with specific time
    filtered_bars = filter_bars_by_date(
        bars, start_date="2023-01-01T12:00:00", end_date="2023-01-03T12:00:00"
    )

    # Should have 3 bars
    assert len(filtered_bars) == 3
