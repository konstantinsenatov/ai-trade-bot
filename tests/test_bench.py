"""Tests for batch backtest functionality."""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_bench_batch_run():
    """Test batch backtest with mini-grid."""
    script_path = project_root / "scripts" / "bench.py"
    output_path = project_root / "user_data" / "backtests_test.csv"

    # Clean up any existing test file
    if output_path.exists():
        output_path.unlink()

    # Run batch backtest with mini-grid
    env = os.environ.copy()
    env["DATA_SOURCE"] = "synthetic"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--modes",
            "onebar",
            "--bars",
            "60",
            "--fees",
            "0.001",
            "--thresholds",
            "0.01",
            "--seed",
            "42",
            "--out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    # Check return code
    assert result.returncode == 0, f"Batch script failed: {result.stderr}"

    # Check CSV file exists
    assert output_path.exists(), "CSV file was not created"

    # Check CSV content
    csv_content = output_path.read_text(encoding="utf-8")
    lines = csv_content.strip().split("\n")

    # Should have header + at least 1 data row
    assert len(lines) >= 2, f"Expected at least 2 lines (header + data), got {len(lines)}"

    # Check header
    header = lines[0]
    assert "mode" in header, "Missing 'mode' in CSV header"
    assert "trades" in header, "Missing 'trades' in CSV header"
    assert "final_equity" in header, "Missing 'final_equity' in CSV header"

    # Check data row
    data_row = lines[1]
    assert "onebar" in data_row, "Missing 'onebar' mode in data row"
    assert "60" in data_row, "Missing bars count in data row"
    assert "0.001" in data_row, "Missing fee in data row"
    assert "0.01" in data_row, "Missing threshold in data row"


def test_backtest_single_csv():
    """Test single backtest with CSV output."""
    script_path = project_root / "scripts" / "backtest.py"
    output_path = project_root / "user_data" / "single.csv"

    # Clean up any existing test file
    if output_path.exists():
        output_path.unlink()

    # Run single backtest with CSV output
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
            "50",
            "--out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    # Check return code
    assert result.returncode == 0, f"Single backtest script failed: {result.stderr}"

    # Check CSV file exists
    assert output_path.exists(), "CSV file was not created"

    # Check CSV content
    csv_content = output_path.read_text(encoding="utf-8")
    lines = csv_content.strip().split("\n")

    # Should have header + 1 data row
    assert len(lines) == 2, f"Expected exactly 2 lines (header + data), got {len(lines)}"

    # Check header
    header = lines[0]
    assert "mode" in header, "Missing 'mode' in CSV header"
    assert "trades" in header, "Missing 'trades' in CSV header"
    assert "final_equity" in header, "Missing 'final_equity' in CSV header"

    # Check data row
    data_row = lines[1]
    assert "close" in data_row, "Missing 'close' mode in data row"
    assert "50" in data_row, "Missing bars count in data row"


def test_backtest_append_csv():
    """Test single backtest with append mode."""
    script_path = project_root / "scripts" / "backtest.py"
    output_path = project_root / "user_data" / "append_test.csv"

    # Clean up any existing test file
    if output_path.exists():
        output_path.unlink()

    # First run - create file
    env = os.environ.copy()
    env["DATA_SOURCE"] = "synthetic"
    result1 = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--mode",
            "close",
            "--timeframe",
            "15m",
            "--bars",
            "30",
            "--out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result1.returncode == 0, f"First run failed: {result1.stderr}"

    # Second run - append
    result2 = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--mode",
            "onebar",
            "--timeframe",
            "15m",
            "--bars",
            "40",
            "--out",
            str(output_path),
            "--append",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result2.returncode == 0, f"Second run failed: {result2.stderr}"

    # Check CSV content
    csv_content = output_path.read_text(encoding="utf-8")
    lines = csv_content.strip().split("\n")

    # Should have header + 2 data rows
    assert len(lines) == 3, f"Expected exactly 3 lines (header + 2 data), got {len(lines)}"

    # Check both data rows
    data_row1 = lines[1]
    data_row2 = lines[2]

    assert "close" in data_row1, "Missing 'close' mode in first data row"
    assert "onebar" in data_row2, "Missing 'onebar' mode in second data row"
    assert "30" in data_row1, "Missing bars count in first data row"
    assert "40" in data_row2, "Missing bars count in second data row"


def test_csv_header_on_append_to_new_file():
    """Test that CSV header is written when appending to non-existent file."""
    script_path = project_root / "scripts" / "bench.py"
    output_path = project_root / "user_data" / "header_test.csv"

    # Clean up any existing test file
    if output_path.exists():
        output_path.unlink()

    # Run batch backtest with append to non-existent file
    env = os.environ.copy()
    env["DATA_SOURCE"] = "synthetic"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--modes",
            "onebar",
            "--bars",
            "30",
            "--fees",
            "0.001",
            "--thresholds",
            "0.01",
            "--seed",
            "42",
            "--out",
            str(output_path),
            "--append",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    # Check return code
    assert result.returncode == 0, f"Batch script failed: {result.stderr}"

    # Check CSV file exists
    assert output_path.exists(), "CSV file was not created"

    # Check CSV content
    csv_content = output_path.read_text(encoding="utf-8")
    lines = csv_content.strip().split("\n")

    # Should have header + 1 data row
    assert len(lines) == 2, f"Expected exactly 2 lines (header + data), got {len(lines)}"

    # Check header is present
    header = lines[0]
    assert "mode" in header, "Missing 'mode' in CSV header"
    assert "trades" in header, "Missing 'trades' in CSV header"
    assert "final_equity" in header, "Missing 'final_equity' in CSV header"

    # Check data row
    data_row = lines[1]
    assert "onebar" in data_row, "Missing 'onebar' mode in data row"
    assert "30" in data_row, "Missing bars count in data row"
