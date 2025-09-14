"""OHLCV data sources."""

import hashlib
import random
from typing import Protocol

# OHLCV tuple: (timestamp, open, high, low, close, volume)
OHLCVBar = tuple[int, float, float, float, float, int]


class OHLCVSource(Protocol):
    """OHLCV data source interface."""

    def load(
        self, tf: str, bars: int | None = None, start: str | None = None, end: str | None = None
    ) -> list[OHLCVBar]:
        """Load OHLCV data.

        Args:
            tf: Timeframe (e.g., '15m', '1h')
            bars: Number of bars to load
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format

        Returns:
            List of OHLCV bars
        """
        ...


class SyntheticOHLCV:
    """Synthetic OHLCV data generator."""

    def __init__(self, seed: int = 42, symbol: str = "BTCUSDT"):
        """Initialize synthetic data generator.

        Args:
            seed: Random seed for deterministic generation
            symbol: Trading symbol for deterministic generation
        """
        self.seed = seed
        self.symbol = symbol

    def load(
        self, tf: str, bars: int | None = None, start: str | None = None, end: str | None = None
    ) -> list[OHLCVBar]:
        """Generate synthetic OHLCV data.

        Args:
            tf: Timeframe (e.g., '15m', '1h')
            bars: Number of bars to generate (fallback if no start/end)
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format

        Returns:
            List of OHLCV bars
        """
        # Timeframe to seconds mapping
        tf_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}

        if tf not in tf_seconds:
            raise ValueError(f"Unsupported timeframe: {tf}")

        tf_sec = tf_seconds[tf]

        # If start and end are provided, generate exactly for that range
        if start and end:
            # Import here to avoid circular imports
            from utils.dates import to_ts_utc

            start_ts = to_ts_utc(start)
            end_ts = to_ts_utc(end)

            # Calculate number of bars needed
            n = int((end_ts - start_ts) // tf_sec) + 1

            # Create deterministic seed for this specific range
            seed_str = f"{self.symbol}-{tf}-{start_ts}-{end_ts}-{self.seed}"
            range_seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
            random.seed(range_seed)

            # Generate exactly n bars on the grid
            bars_data = []
            base_price = 100.0
            current_price = base_price

            for i in range(n):
                timestamp = start_ts + i * tf_sec

                # Random walk with some mean reversion
                change_pct = random.gauss(0, 0.02)  # 2% volatility
                if abs(current_price - base_price) > base_price * 0.1:
                    # Mean reversion when price deviates too much
                    change_pct *= -0.5

                new_price = current_price * (1 + change_pct)

                # Ensure price stays positive
                new_price = max(new_price, base_price * 0.5)

                # Generate OHLC from price movement
                open_price = current_price
                close_price = new_price

                # High and low with some intraday volatility
                intraday_vol = abs(change_pct) * 0.5
                high_price = max(open_price, close_price) * (1 + intraday_vol)
                low_price = min(open_price, close_price) * (1 - intraday_vol)

                # Generate volume (random but correlated with price movement)
                base_volume = 1000
                volume_multiplier = 1 + abs(change_pct) * 2
                volume = int(base_volume * volume_multiplier * random.uniform(0.5, 1.5))

                bars_data.append(
                    (timestamp, open_price, high_price, low_price, close_price, volume)
                )

                current_price = new_price

            return bars_data

        # Fallback: generate by bars count (original behavior)
        else:
            # Reset seed for deterministic results
            random.seed(self.seed)

            # Default bars if None
            if bars is None:
                bars = 500

            # Generate synthetic data using random walk
            base_price = 100.0
            current_price = base_price
            timestamp = 1609459200  # 2021-01-01 00:00:00 UTC

            bars_data = []

            for i in range(bars):
                # Random walk with some mean reversion
                change_pct = random.gauss(0, 0.02)  # 2% volatility
                if abs(current_price - base_price) > base_price * 0.1:
                    # Mean reversion when price deviates too much
                    change_pct *= -0.5

                new_price = current_price * (1 + change_pct)

                # Ensure price stays positive
                new_price = max(new_price, base_price * 0.5)

                # Generate OHLC from price movement
                open_price = current_price
                close_price = new_price

                # High and low with some intraday volatility
                intraday_vol = abs(change_pct) * 0.5
                high_price = max(open_price, close_price) * (1 + intraday_vol)
                low_price = min(open_price, close_price) * (1 - intraday_vol)

                # Generate volume (random but correlated with price movement)
                base_volume = 1000
                volume_multiplier = 1 + abs(change_pct) * 2
                volume = int(base_volume * volume_multiplier * random.uniform(0.5, 1.5))

                bars_data.append(
                    (timestamp, open_price, high_price, low_price, close_price, volume)
                )

                current_price = new_price
                timestamp += tf_sec

            return bars_data
