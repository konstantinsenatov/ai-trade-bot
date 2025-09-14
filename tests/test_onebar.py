"""Tests for one-bar backtest mode."""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.backtest.engine import run_backtest_onebar  # noqa: E402
from bot.data.ohlcv_source import SyntheticOHLCV  # noqa: E402
from bot.strategy.mean_reversion import MeanReversion  # noqa: E402


def test_onebar_backtest():
    """Test one-bar backtest functionality."""
    # Generate 300 bars of synthetic data
    data_source = SyntheticOHLCV(seed=42)
    bars = data_source.load(tf="15m", bars=300)

    # Initialize MeanReversion strategy
    strategy = MeanReversion(window=20, threshold=0.005, timeframe="15m")

    # Run one-bar backtest
    metrics, equity = run_backtest_onebar(bars, strategy, fee=0.001)

    # Assertions
    assert len(equity) == 300, f"Expected 300 equity points, got {len(equity)}"
    assert metrics["trades"] >= 0, f"Expected trades >= 0, got {metrics['trades']}"
    assert "final_equity" in metrics, "Missing 'final_equity' key in metrics"
    assert "pf" in metrics, "Missing 'pf' key in metrics"
    assert "max_dd" in metrics, "Missing 'max_dd' key in metrics"

    # Check equity curve properties
    assert all(isinstance(x, float) for x in equity), "Equity curve should contain floats"
    assert equity[0] == 1000.0, f"Expected starting equity 1000.0, got {equity[0]}"
    assert equity[-1] == metrics["final_equity"], "Final equity should match metrics"


def test_onebar_no_trades():
    """Test one-bar backtest with no trades."""
    # Generate minimal data
    data_source = SyntheticOHLCV(seed=42)
    bars = data_source.load(tf="15m", bars=10)  # Too few bars for strategy

    # Initialize strategy with high threshold (no signals)
    strategy = MeanReversion(window=20, threshold=0.5, timeframe="15m")

    # Run one-bar backtest
    metrics, equity = run_backtest_onebar(bars, strategy, fee=0.001)

    # Should have no trades
    assert metrics["trades"] == 0, f"Expected 0 trades, got {metrics['trades']}"
    assert metrics["pf"] == 0.0, f"Expected pf=0.0, got {metrics['pf']}"
    assert metrics["max_dd"] == 0.0, f"Expected max_dd=0.0, got {metrics['max_dd']}"
    assert len(equity) == 10, f"Expected 10 equity points, got {len(equity)}"


def test_cli_onebar_output():
    """Test CLI output for onebar mode."""
    script_path = project_root / "scripts" / "backtest.py"

    # Run CLI with onebar mode and small dataset
    env = os.environ.copy()
    env["DATA_SOURCE"] = "synthetic"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--mode",
            "onebar",
            "--timeframe",
            "15m",
            "--bars",
            "50",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    output = result.stdout
    assert "Trades" in output, "Missing 'Trades' in CLI output"
    assert "Final Equity" in output, "Missing 'Final Equity' in CLI output"
    assert "mode=onebar" in output, "Missing mode indicator in CLI output"


def test_cli_close_output():
    """Test CLI output for close mode."""
    script_path = project_root / "scripts" / "backtest.py"

    # Run CLI with close mode
    env = os.environ.copy()
    env["DATA_SOURCE"] = "synthetic"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--mode",
            "close",
            "--timeframe",
            "15m",
            "--bars",
            "100",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    output = result.stdout
    assert "Trades" in output, "Missing 'Trades' in CLI output"
    assert "Win Rate" in output, "Missing 'Win Rate' in CLI output"
    assert "mode=close" in output, "Missing mode indicator in CLI output"
