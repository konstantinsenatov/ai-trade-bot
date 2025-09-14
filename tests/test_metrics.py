"""Tests for backtest metrics and CSV export functionality."""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.backtest.engine import run_backtest  # noqa: E402
from bot.data.ohlcv_source import SyntheticOHLCV  # noqa: E402
from bot.strategy.mean_reversion import MeanReversion  # noqa: E402


@pytest.mark.xfail(reason="TASK-003: Metrics not implemented yet")
def test_backtest_metrics_keys():
    """Test that backtest returns required metric keys."""
    # Generate test data
    data_source = SyntheticOHLCV()
    bars = data_source.load("15m", 300)

    # Run backtest
    strategy = MeanReversion()
    metrics, equity = run_backtest(bars, strategy)

    # Check required keys exist
    required_keys = ["pf", "sharpe_like", "max_consec_losses"]
    for key in required_keys:
        assert key in metrics, f"Missing metric key: {key}"


@pytest.mark.xfail(reason="TASK-003: Metrics not implemented yet")
def test_backtest_metrics_values():
    """Test that metric values have correct types and ranges."""
    # Generate test data
    data_source = SyntheticOHLCV()
    bars = data_source.load("15m", 300)

    # Run backtest
    strategy = MeanReversion()
    metrics, equity = run_backtest(bars, strategy)

    # Check profit factor
    pf = metrics["pf"]
    assert pf >= 0 or pf == float("inf"), f"Invalid profit factor: {pf}"

    # Check sharpe-like
    sharpe_like = metrics["sharpe_like"]
    assert isinstance(sharpe_like, (int, float)), f"Invalid sharpe_like type: {type(sharpe_like)}"

    # Check max consecutive losses
    max_consec_losses = metrics["max_consec_losses"]
    assert max_consec_losses >= 0, f"Invalid max_consec_losses: {max_consec_losses}"


@pytest.mark.xfail(reason="TASK-003: CSV export not implemented yet")
def test_equity_csv_export():
    """Test that equity curve is exported to CSV file."""
    # Generate test data
    data_source = SyntheticOHLCV()
    bars = data_source.load("15m", 300)

    # Run backtest
    strategy = MeanReversion()
    metrics, equity = run_backtest(bars, strategy)

    # Check CSV file exists
    csv_path = Path("user_data/equity.csv")
    assert csv_path.exists(), "Equity CSV file not created"

    # Check CSV content
    with open(csv_path) as f:
        lines = f.readlines()

    # Should have header + data rows
    expected_rows = len(equity) + 1  # +1 for header
    assert len(lines) == expected_rows, f"Expected {expected_rows} rows, got {len(lines)}"

    # Check header
    assert lines[0].strip() == "ts,equity", f"Invalid CSV header: {lines[0].strip()}"


@pytest.mark.xfail(reason="TASK-003: CLI output not implemented yet")
def test_cli_metrics_output():
    """Test that CLI includes new metrics in JSON output."""
    # This test would need to be run via subprocess to test CLI
    # For now, just verify the structure exists
    assert True  # Placeholder for CLI testing


@pytest.mark.xfail(reason="TASK-003: Documentation not updated yet")
def test_readme_metrics_section():
    """Test that README contains metrics documentation."""
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md not found"

    content = readme_path.read_text()
    # Check for metrics section
    assert "Metrics" in content or "metrics" in content, "Metrics section not found in README"
