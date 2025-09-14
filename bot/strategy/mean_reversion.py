"""Mean reversion strategy implementation."""

from collections import deque

from bot.strategy.base import Strategy
from bot.utils.freshness import is_stale
from bot.utils.timeframes import tf_to_seconds


class MeanReversion(Strategy):
    """Simple mean reversion strategy using SMA."""

    def __init__(self, window: int = 20, threshold: float = 0.005, timeframe: str = "15m"):
        """Initialize mean reversion strategy.

        Args:
            window: SMA window size
            threshold: Threshold for mean reversion signals (0.5% default)
            timeframe: Timeframe string for freshness check
        """
        self.window = window
        self.threshold = threshold
        self.timeframe = timeframe
        self.tf_seconds = tf_to_seconds(timeframe)
        self.prices: deque[float] = deque(maxlen=window)

    def on_bar(self, ts: int, o: float, h: float, low: float, c: float, v: int) -> str | None:
        """Process new bar data.

        Args:
            ts: Timestamp
            o: Open price
            h: High price
            low: Low price
            c: Close price
            v: Volume

        Returns:
            'buy', 'sell', or None
        """
        # Check if data is stale
        now_ts = ts + self.tf_seconds  # Simulate current time
        if is_stale(ts, now_ts, self.tf_seconds):
            return None  # Don't trade on stale data

        self.prices.append(c)

        # Need at least window bars for SMA
        if len(self.prices) < self.window:
            return None

        # Calculate SMA
        sma = sum(self.prices) / len(self.prices)

        # Mean reversion signals
        if c < sma * (1 - self.threshold):
            return "buy"
        elif c > sma * (1 + self.threshold):
            return "sell"
        else:
            return None

    def name(self) -> str:
        """Get strategy name."""
        return f"MeanReversion_{self.window}_{self.threshold}"

    def signal(self, history: list[tuple[int, float, float, float, float]]) -> str | None:
        """Calculate signal using historical data (for one-bar backtest).

        Args:
            history: List of (timestamp, open, high, low, close) tuples

        Returns:
            'buy', 'sell', or None
        """
        if len(history) < self.window:
            return None

        # Calculate SMA using past closes (no look-ahead)
        closes = [bar[4] for bar in history]  # close is index 4
        sma = sum(closes) / len(closes)

        # Use the last close for signal calculation
        last_close = closes[-1]

        # Mean reversion signals
        if last_close < sma * (1 - self.threshold):
            return "buy"
        elif last_close > sma * (1 + self.threshold):
            return "sell"
        else:
            return None
