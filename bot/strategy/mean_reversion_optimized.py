"""Optimized mean reversion strategy with advanced filters."""

import math
from collections import deque
from typing import Optional

import numpy as np

from bot.strategy.base import Strategy
from bot.utils.freshness import is_stale
from bot.utils.timeframes import tf_to_seconds


class MeanReversionOptimized(Strategy):
    """Optimized mean reversion strategy with multiple filters to reduce trade frequency."""

    def __init__(
        self,
        window: int = 20,
        threshold: float = 0.005,
        timeframe: str = "15m",
        zscore_threshold: float = 2.0,
        adx_threshold: float = 25.0,
        atr_threshold: float = 0.005,
    ):
        """Initialize optimized mean reversion strategy.

        Args:
            window: SMA window size
            threshold: Threshold for mean reversion signals (0.5% default)
            timeframe: Timeframe string for freshness check
            zscore_threshold: Z-score threshold for entry (2.0 = 2 standard deviations)
            adx_threshold: ADX threshold for trend filter (25 = range-bound market)
            atr_threshold: ATR percentage threshold for volatility filter (0.5%)
        """
        self.window = window
        self.threshold = threshold
        self.timeframe = timeframe
        self.tf_seconds = tf_to_seconds(timeframe)
        
        # Filter parameters
        self.zscore_threshold = zscore_threshold
        self.adx_threshold = adx_threshold
        self.atr_threshold = atr_threshold
        
        # Data storage
        self.prices: deque[float] = deque(maxlen=window)
        self.highs: deque[float] = deque(maxlen=window)
        self.lows: deque[float] = deque(maxlen=window)
        self.volumes: deque[int] = deque(maxlen=window)

    def _calculate_zscore(self, prices: list[float]) -> float:
        """Calculate Z-score for the last price.
        
        Args:
            prices: List of prices
            
        Returns:
            Z-score of the last price
        """
        if len(prices) < 2:
            return 0.0
        
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if std_price == 0:
            return 0.0
            
        return abs((prices[-1] - mean_price) / std_price)

    def _calculate_adx(self, highs: list[float], lows: list[float], closes: list[float]) -> float:
        """Calculate ADX (Average Directional Index) for trend filter.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            
        Returns:
            ADX value (0-100)
        """
        if len(highs) < 14:  # Need at least 14 periods for ADX
            return 50.0  # Default to trending market
        
        try:
            # Calculate True Range (TR)
            tr_values = []
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values.append(tr)
            
            # Calculate Directional Movement
            dm_plus = []
            dm_minus = []
            
            for i in range(1, len(highs)):
                high_diff = highs[i] - highs[i-1]
                low_diff = lows[i-1] - lows[i]
                
                if high_diff > low_diff and high_diff > 0:
                    dm_plus.append(high_diff)
                else:
                    dm_plus.append(0)
                    
                if low_diff > high_diff and low_diff > 0:
                    dm_minus.append(low_diff)
                else:
                    dm_minus.append(0)
            
            # Calculate smoothed values (simplified)
            if len(tr_values) >= 14:
                tr_smooth = np.mean(tr_values[-14:])
                dm_plus_smooth = np.mean(dm_plus[-14:])
                dm_minus_smooth = np.mean(dm_minus[-14:])
                
                if tr_smooth > 0:
                    di_plus = (dm_plus_smooth / tr_smooth) * 100
                    di_minus = (dm_minus_smooth / tr_smooth) * 100
                    
                    dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100
                    return dx
                    
        except Exception:
            pass
            
        return 50.0  # Default to trending market

    def _calculate_atr_percentage(self, highs: list[float], lows: list[float], closes: list[float]) -> float:
        """Calculate ATR as percentage of price for volatility filter.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            
        Returns:
            ATR as percentage of current price
        """
        if len(highs) < 14:
            return 0.01  # Default 1%
            
        try:
            # Calculate True Range
            tr_values = []
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values.append(tr)
            
            # Calculate ATR (14-period average)
            atr = np.mean(tr_values[-14:])
            current_price = closes[-1]
            
            return atr / current_price if current_price > 0 else 0.01
            
        except Exception:
            return 0.01  # Default 1%

    def on_bar(self, ts: int, o: float, h: float, low: float, c: float, v: int) -> Optional[str]:
        """Process new bar data with advanced filters.

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
        now_ts = ts + self.tf_seconds
        if is_stale(ts, now_ts, self.tf_seconds):
            return None

        # Store data
        self.prices.append(c)
        self.highs.append(h)
        self.lows.append(low)
        self.volumes.append(v)

        # Need at least window bars for calculations
        if len(self.prices) < self.window:
            return None

        # Convert to lists for calculations
        prices_list = list(self.prices)
        highs_list = list(self.highs)
        lows_list = list(self.lows)

        # Filter 1: Z-score threshold - only trade on significant deviations
        zscore = self._calculate_zscore(prices_list)
        if zscore < self.zscore_threshold:
            return None  # Not significant enough deviation

        # Filter 2: ADX trend filter - only trade in range-bound markets
        adx = self._calculate_adx(highs_list, lows_list, prices_list)
        if adx > self.adx_threshold:
            return None  # Market is trending, avoid mean reversion

        # Filter 3: ATR volatility filter - only trade in sufficient volatility
        atr_pct = self._calculate_atr_percentage(highs_list, lows_list, prices_list)
        if atr_pct < self.atr_threshold:
            return None  # Insufficient volatility

        # Calculate SMA for mean reversion signal
        sma = sum(prices_list) / len(prices_list)

        # Mean reversion signals (only if all filters pass)
        if c < sma * (1 - self.threshold):
            return "buy"
        elif c > sma * (1 + self.threshold):
            return "sell"
        else:
            return None

    def name(self) -> str:
        """Get strategy name."""
        return f"MeanReversionOpt_{self.window}_{self.threshold}_z{self.zscore_threshold}_adx{self.adx_threshold}_atr{self.atr_threshold}"

    def signal(self, history: list[tuple[int, float, float, float, float]]) -> Optional[str]:
        """Calculate signal using historical data with filters.

        Args:
            history: List of (timestamp, open, high, low, close) tuples

        Returns:
            'buy', 'sell', or None
        """
        if len(history) < self.window:
            return None

        # Extract data
        highs = [bar[2] for bar in history]  # high is index 2
        lows = [bar[3] for bar in history]   # low is index 3
        closes = [bar[4] for bar in history]  # close is index 4

        # Filter 1: Z-score threshold
        zscore = self._calculate_zscore(closes)
        if zscore < self.zscore_threshold:
            return None

        # Filter 2: ADX trend filter
        adx = self._calculate_adx(highs, lows, closes)
        if adx > self.adx_threshold:
            return None

        # Filter 3: ATR volatility filter
        atr_pct = self._calculate_atr_percentage(highs, lows, closes)
        if atr_pct < self.atr_threshold:
            return None

        # Calculate SMA
        sma = sum(closes) / len(closes)
        last_close = closes[-1]

        # Mean reversion signals
        if last_close < sma * (1 - self.threshold):
            return "buy"
        elif last_close > sma * (1 + self.threshold):
            return "sell"
        else:
            return None
