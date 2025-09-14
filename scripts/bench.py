#!/usr/bin/env python3
"""Batch backtest script with CSV output."""

import argparse
import csv
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.backtest.engine import run_backtest, run_backtest_onebar  # noqa: E402
from bot.data.loader import get_source  # noqa: E402
from bot.strategy.mean_reversion import MeanReversion  # noqa: E402
from utils.dates import filter_bars_by_date  # noqa: E402


def parse_comma_separated(value: str) -> list[str]:
    """Parse comma-separated string into list."""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_float_list(value: str) -> list[float]:
    """Parse comma-separated string into list of floats."""
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def run_single_backtest(
    mode: str,
    bars: int,
    fee: float,
    threshold: float,
    seed: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, float | int | str]:
    """Run a single backtest and return unified metrics."""
    # Load data using factory
    source_kind = os.getenv("DATA_SOURCE", "real")
    src = get_source(source_kind)

    # bars_to_use: если задан диапазон — не резать
    bars_to_use = 0 if (start_date or end_date) else bars
    bars_data = src.load(tf="15m", bars=bars_to_use, start=start_date, end=end_date)

    # Filter by date range if specified
    if start_date or end_date:
        bars_data, _, _ = filter_bars_by_date(bars_data, start_date, end_date)

    # Initialize strategy
    strategy = MeanReversion(window=20, threshold=threshold, timeframe="15m")

    # Run backtest based on mode
    if mode == "onebar":
        metrics, _ = run_backtest_onebar(bars_data, strategy, fee=fee)
    else:
        metrics, _ = run_backtest(bars_data, strategy, fee=fee)

    # Unify metrics to standard format
    unified = {
        "mode": mode,
        "bars": bars,
        "fee": fee,
        "threshold": threshold,
        "seed": seed,
        "trades": metrics.get("trades", 0),
        "final_equity": metrics.get("final_equity", 0.0),
        "win_rate": metrics.get("win_rate", ""),
        "pf": metrics.get("pf", ""),
        "max_dd": metrics.get("max_dd", 0.0),
        "return_pct": metrics.get("return_pct", ""),
        "total_fees": metrics.get("total_fees", ""),
    }

    return unified


def save_csv(results: list[dict], output_path: Path, append: bool = False) -> None:
    """Save results to CSV file."""
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # CSV headers
    headers = [
        "mode",
        "bars",
        "fee",
        "threshold",
        "seed",
        "trades",
        "final_equity",
        "win_rate",
        "pf",
        "max_dd",
        "return_pct",
        "total_fees",
    ]

    # Write CSV
    mode = "a" if append else "w"
    file_exists = output_path.exists()

    with open(output_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        # Write header if file doesn't exist or not appending
        if not file_exists or not append:
            writer.writeheader()
        writer.writerows(results)


def print_summary_table(results: list[dict]) -> None:
    """Print human-readable summary table."""
    if not results:
        print("No results to display.")
        return

    # Calculate column widths
    headers = [
        "Mode",
        "Bars",
        "Fee",
        "Threshold",
        "Trades",
        "Final Equity",
        "Win Rate",
        "PF",
        "Max DD",
    ]
    widths = [len(h) for h in headers]

    for result in results:
        widths[0] = max(widths[0], len(str(result["mode"])))
        widths[1] = max(widths[1], len(str(result["bars"])))
        widths[2] = max(widths[2], len(f"{result['fee']:.3f}"))
        widths[3] = max(widths[3], len(f"{result['threshold']:.3f}"))
        widths[4] = max(widths[4], len(str(result["trades"])))
        widths[5] = max(widths[5], len(f"{result['final_equity']:.2f}"))
        widths[6] = max(
            widths[6], len(str(result["win_rate"]) if result["win_rate"] != "" else "N/A")
        )
        widths[7] = max(widths[7], len(str(result["pf"]) if result["pf"] != "" else "N/A"))
        widths[8] = max(widths[8], len(f"{result['max_dd']:.3f}"))

    # Print header
    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))

    # Print data rows
    for result in results:
        win_rate_str = f"{result['win_rate']:.3f}" if result["win_rate"] != "" else "N/A"
        pf_str = f"{result['pf']:.3f}" if result["pf"] != "" else "N/A"

        row = [
            str(result["mode"]),
            str(result["bars"]),
            f"{result['fee']:.3f}",
            f"{result['threshold']:.3f}",
            str(result["trades"]),
            f"{result['final_equity']:.2f}",
            win_rate_str,
            pf_str,
            f"{result['max_dd']:.3f}",
        ]

        row_line = " | ".join(f"{cell:<{w}}" for cell, w in zip(row, widths))
        print(row_line)


def main() -> int:
    """Run batch backtest and save results to CSV."""
    parser = argparse.ArgumentParser(description="Run batch backtest with CSV output")
    parser.add_argument(
        "--modes",
        default="close,onebar",
        help="Comma-separated modes: close,onebar (default: close,onebar)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Number of bars to load (default: 500)",
    )
    parser.add_argument(
        "--fees",
        default="0.001",
        help="Comma-separated fee rates (default: 0.001)",
    )
    parser.add_argument(
        "--thresholds",
        default="0.005",
        help="Comma-separated thresholds (default: 0.005)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--out",
        default="user_data/backtests.csv",
        help="Output CSV path (default: user_data/backtests.csv)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to CSV instead of overwriting",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date: YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date: YYYY-MM-DD",
    )

    args = parser.parse_args()

    # Parse arguments
    modes = parse_comma_separated(args.modes)
    fees = parse_float_list(args.fees)
    thresholds = parse_float_list(args.thresholds)

    # Modify output path if date range is specified
    output_path = Path(args.out)
    if args.start or args.end:
        if args.start and args.end:
            suffix = f"_range{args.start}_{args.end}"
        elif args.start:
            suffix = f"_from{args.start}"
        elif args.end:
            suffix = f"_to{args.end}"
        else:
            suffix = "_2y"  # fallback for 2-year range

        # Add suffix before file extension
        stem = output_path.stem
        ext = output_path.suffix
        output_path = output_path.parent / f"{stem}{suffix}{ext}"

    # Validate modes
    valid_modes = {"close", "onebar"}
    invalid_modes = set(modes) - valid_modes
    if invalid_modes:
        print(f"Error: Invalid modes {invalid_modes}. Valid modes: {valid_modes}")
        return 1

    # Run batch backtests
    results = []
    total_combinations = len(modes) * len(fees) * len(thresholds)
    current = 0

    print(f"Running {total_combinations} backtest combinations...")
    print(
        f"Parameters: modes={modes}, fees={fees}, thresholds={thresholds}, bars={args.bars}, seed={args.seed}"
    )

    for mode in modes:
        for fee in fees:
            for threshold in thresholds:
                current += 1
                print(
                    f"Running {current}/{total_combinations}: {mode}, fee={fee:.3f}, threshold={threshold:.3f}"
                )

                try:
                    # Если задан start/end — не передавай bars (или выставь bars=0)
                    bars_to_use = 0 if (args.start or args.end) else args.bars
                    result = run_single_backtest(
                        mode, bars_to_use, fee, threshold, args.seed, args.start, args.end
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error running backtest: {e}")
                    return 1

    # Save results
    save_csv(results, output_path, args.append)
    print(f"\nResults saved to: {output_path}")

    # Print summary table
    print("\n=== Batch Backtest Summary ===")
    print_summary_table(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
