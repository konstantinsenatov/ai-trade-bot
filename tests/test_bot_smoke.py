"""Smoke tests for bot module."""

import math
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import bot modules after path setup
from bot.backtest.engine import run_backtest  # noqa: E402
from bot.core.exchange import PaperExchange  # noqa: E402
from bot.data.ohlcv_source import SyntheticOHLCV  # noqa: E402
from bot.strategy.mean_reversion import MeanReversion  # noqa: E402
from bot.utils.timeframes import tf_to_seconds  # noqa: E402


def test_import_all_modules():
    """Test that all key bot modules can be imported."""
    # This test passes if imports succeed
    assert True


def test_timeframes():
    """Test timeframe utilities."""
    assert tf_to_seconds("1m") == 60
    assert tf_to_seconds("5m") == 300
    assert tf_to_seconds("15m") == 900
    assert tf_to_seconds("1h") == 3600
    assert tf_to_seconds("4h") == 14400
    assert tf_to_seconds("1d") == 86400

    try:
        tf_to_seconds("invalid")
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_synthetic_data():
    """Test synthetic data generation."""
    source = SyntheticOHLCV(seed=42)
    bars = source.load(tf="15m", bars=300)

    assert len(bars) == 300
    assert all(len(bar) == 6 for bar in bars)  # OHLCV tuple

    # Check data types and ranges
    for ts, o, h, low, c, v in bars:
        assert isinstance(ts, int)
        assert isinstance(o, float)
        assert isinstance(h, float)
        assert isinstance(low, float)
        assert isinstance(c, float)
        assert isinstance(v, int)

        assert o > 0
        assert h > 0
        assert low > 0
        assert c > 0
        assert v > 0

        # OHLC consistency
        assert h >= max(o, c)
        assert low <= min(o, c)


def test_mean_reversion_strategy():
    """Test mean reversion strategy."""
    strategy = MeanReversion(window=20, threshold=0.005)

    # Test with some bars
    for i in range(25):
        signal = strategy.on_bar(
            ts=1609459200 + i * 900, o=100.0 + i, h=101.0 + i, low=99.0 + i, c=100.0 + i, v=1000
        )

        if i < 19:  # Before window is filled
            assert signal is None
        else:
            assert signal in [None, "buy", "sell"]


def test_paper_exchange():
    """Test paper exchange functionality."""
    exchange = PaperExchange(taker_fee=0.001)

    # Test buy order
    result = exchange.market_order("buy", 1.0, 100.0, 1609459200)
    assert result.success
    assert exchange.position.quantity == 1.0
    assert exchange.position.avg_price == 100.0

    # Test sell order
    result = exchange.market_order("sell", 1.0, 105.0, 1609459201)
    assert result.success
    assert exchange.position.quantity == 0.0

    # Check fees
    assert exchange.get_total_fees() > 0


def test_backtest_engine():
    """Test backtest engine."""
    # Generate data
    source = SyntheticOHLCV(seed=42)
    bars = source.load(tf="15m", bars=300)

    # Run backtest
    strategy = MeanReversion(window=20, threshold=0.005)
    metrics, equity_curve = run_backtest(bars, strategy, fee=0.001)

    # Check metrics structure
    required_keys = ["trades", "net_pnl", "win_rate", "max_dd"]
    for key in required_keys:
        assert key in metrics

    # Check equity curve
    assert len(equity_curve) == len(bars)

    # Check values are finite
    for key, value in metrics.items():
        assert not math.isnan(value) if isinstance(value, float) else True
        assert not math.isinf(value) if isinstance(value, float) else True

    # Check equity curve values
    for equity in equity_curve:
        assert not math.isnan(equity)
        assert not math.isinf(equity)
        assert equity > 0


def test_backtest_integration():
    """Test full backtest integration."""
    # This is the main integration test
    source = SyntheticOHLCV(seed=42)
    bars = source.load(tf="15m", bars=300)

    strategy = MeanReversion(window=20, threshold=0.005)
    metrics, equity_curve = run_backtest(bars, strategy, fee=0.001)

    # Verify we have reasonable results
    assert metrics["trades"] >= 0
    assert metrics["net_pnl"] is not None
    assert 0 <= metrics["win_rate"] <= 1
    assert metrics["max_dd"] >= 0
    assert len(equity_curve) == 300
