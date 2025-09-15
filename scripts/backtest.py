#!/usr/bin/env python3
"""Backtest CLI script."""

import argparse
import csv
import json
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.backtest.engine import run_backtest, run_backtest_onebar  # noqa: E402
from bot.data.loader import get_source, load_data  # noqa: E402
from bot.report.pretty import PrettyCtx, render, save_json  # noqa: E402
from bot.strategy.mean_reversion import MeanReversion  # noqa: E402
from bot.strategy.mean_reversion_optimized import MeanReversionOptimized  # noqa: E402
from utils.dates import filter_bars_by_date, iso_utc  # noqa: E402

# UTF-8 support
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def log_stage(stage: str, verbose: bool = False) -> None:
    """Log stage with timestamp."""
    if verbose:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {stage}", flush=True)


def log_timing(stage: str, duration: float, verbose: bool = False) -> None:
    """Log stage timing."""
    if verbose:
        print(f"[timing] {stage}: {duration:.2f}s", flush=True)


def progress_callback(current: int, total: int, verbose: bool = False) -> None:
    """Progress callback for engine."""
    if verbose and current % 1000 == 0:
        percentage = (current / total) * 100
        print(f"[progress] processed {current:,}/{total:,} bars ({percentage:.1f}%)", flush=True)


def watchdog_timer(stop_event: threading.Event, verbose: bool = False) -> None:
    """Watchdog timer to detect silent hangs."""
    last_log_time = time.time()
    while not stop_event.is_set():
        time.sleep(30)  # Check every 30 seconds
        if time.time() - last_log_time > 120:  # 2 minutes without activity
            if verbose:
                print("[watchdog] still working...", flush=True)
            last_log_time = time.time()


def format_metrics_table(metrics: dict, mode: str) -> str:
    """Format metrics as a human-readable table."""
    lines = [f"=== Backtest Results (mode={mode}) ==="]

    # Format numeric values with appropriate precision
    for key, value in sorted(metrics.items()):
        if isinstance(value, float):
            if value == float("inf"):
                formatted_value = "inf"
            elif abs(value) < 0.001:
                formatted_value = f"{value:.6f}"
            elif abs(value) < 1:
                formatted_value = f"{value:.3f}"
            else:
                formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)

        # Format key names nicely
        display_key = key.replace("_", " ").title()
        lines.append(f"{display_key:<15} {formatted_value}")

    return "\n".join(lines)


def save_single_result_csv(
    metrics: dict,
    mode: str,
    bars: int,
    fee: float,
    threshold: float,
    output_path: Path,
    append: bool = False,
) -> None:
    """Save single backtest result to CSV."""
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Unify metrics to standard format
    unified = {
        "mode": mode,
        "bars": bars,
        "fee": fee,
        "threshold": threshold,
        "seed": 42,  # Fixed seed for consistency
        "trades": metrics.get("trades", 0),
        "final_equity": metrics.get("final_equity", 0.0),
        "win_rate": metrics.get("win_rate", ""),
        "pf": metrics.get("pf", ""),
        "max_dd": metrics.get("max_dd", 0.0),
        "return_pct": metrics.get("return_pct", ""),
        "total_fees": metrics.get("total_fees", ""),
    }

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
    mode_str = "a" if append else "w"
    file_exists = output_path.exists()

    with open(output_path, mode_str, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        # Write header if file doesn't exist or not appending
        if not file_exists or not append:
            writer.writeheader()
        writer.writerow(unified)


def main() -> int:
    """Run backtest and print results."""
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument(
        "--mode",
        choices=["close", "onebar"],
        default="close",
        help="Backtest mode: 'close' for regular mode, 'onebar' for one-bar mode",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="15m",
        help="Timeframe for data loading (default: 15m)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Number of bars to load from synthetic data (default: 500)",
    )
    parser.add_argument(
        "--fee",
        type=float,
        default=0.001,
        help="Trading fee rate (default: 0.001)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.005,
        help="Mean reversion threshold (default: 0.005)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date: YYYY-MM-DD or YYYY-MM-DDTHH:MM",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date: YYYY-MM-DD or YYYY-MM-DDTHH:MM",
    )
    parser.add_argument(
        "--out",
        help="Output CSV path (optional)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to CSV instead of overwriting",
    )
    parser.add_argument(
        "--strategy",
        choices=["basic", "optimized"],
        default="basic",
        help="Strategy type: 'basic' for original, 'optimized' for filtered version",
    )
    parser.add_argument(
        "--zscore-threshold",
        type=float,
        default=2.0,
        help="Z-score threshold for optimized strategy (default: 2.0)",
    )
    parser.add_argument(
        "--adx-threshold",
        type=float,
        default=25.0,
        help="ADX threshold for trend filter (default: 25.0)",
    )
    parser.add_argument(
        "--atr-threshold",
        type=float,
        default=0.005,
        help="ATR percentage threshold for volatility filter (default: 0.005)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Generate beautiful structural report with emojis",
    )
    parser.add_argument(
        "--pretty-symbols",
        type=str,
        help="Symbols for pretty report: SYMBOL:COUNT,... (optional)",
    )
    parser.add_argument(
        "--data-source",
        choices=["historical", "real", "synthetic"],
        default="historical",
        help="Data source: 'historical' for historical data, 'real' for Binance API, 'synthetic' for generated data",
    )
    parser.add_argument(
        "--pair",
        type=str,
        default="BTC/USDT",
        help="Trading pair for real data source (default: BTC/USDT)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of bars to fetch from real data source (default: 1000)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick run on small number of bars (default: 2000 bars)",
    )
    parser.add_argument(
        "--max-bars",
        type=int,
        help="Limit number of bars for backtest (overrides --smoke)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging of stages and progress",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable cProfile profiling and save stats to artifacts/profile_<timestamp>.prof",
    )
    args = parser.parse_args()

    # Start watchdog timer if verbose
    stop_event = threading.Event()
    watchdog_thread = None
    if args.verbose:
        watchdog_thread = threading.Thread(target=watchdog_timer, args=(stop_event, args.verbose))
        watchdog_thread.daemon = True
        watchdog_thread.start()

    # Determine max bars limit
    max_bars = None
    if args.max_bars:
        max_bars = args.max_bars
    elif args.smoke:
        max_bars = 2000

    # Load data with timing
    log_stage("Loading data", args.verbose)
    start_time = time.time()
    
    if args.data_source == "real":
        # For real data, use specific parameters
        bars: list[tuple[int, float, float, float, float, int]] = load_data(
            source="real",
            pair=args.pair,
            timeframe=args.timeframe,
            limit=args.limit
        )
    else:
        # For historical/synthetic data, use legacy method
        source_kind = os.getenv("DATA_SOURCE", args.data_source)
        src = get_source(source_kind)
        
        # bars_to_use: если задан диапазон — не резать
        bars_to_use = 0 if (args.start or args.end) else getattr(args, "bars", None)
        bars: list[tuple[int, float, float, float, float, int]] = src.load(
            tf=args.timeframe, bars=bars_to_use, start=args.start, end=args.end
        )

    log_timing("Data loading", time.time() - start_time, args.verbose)

    # Apply max bars limit
    original_bars = len(bars)
    if max_bars and len(bars) > max_bars:
        bars = bars[-max_bars:]  # Take last N bars
        log_stage(f"Trimmed data from {original_bars:,} to {len(bars):,} bars", args.verbose)

    # фильтрация + логирование
    log_stage("Filtering data by date range", args.verbose)
    filter_start = time.time()
    before = len(bars)
    filtered_bars, st, et = filter_bars_by_date(bars, args.start, args.end)
    bars = filtered_bars  # type: ignore[assignment]
    after = len(bars)
    log_timing("Date filtering", time.time() - filter_start, args.verbose)
    
    print(
        f"[range] start={iso_utc(st)} end={iso_utc(et)} bars_before={before} bars_after={after}",
        flush=True,
    )

    # fail-fast если диапазон указан и баров нет
    if (args.start or args.end) and not bars:
        print(
            f"[ERR] No bars in range {iso_utc(st)}..{iso_utc(et)} timeframe={args.timeframe}",
            flush=True,
        )
        sys.exit(2)

    # Initialize strategy
    log_stage("Initializing strategy", args.verbose)
    strategy_start = time.time()
    
    if args.strategy == "optimized":
        strategy = MeanReversionOptimized(
            window=20,
            threshold=args.threshold,
            timeframe="15m",
            zscore_threshold=args.zscore_threshold,
            adx_threshold=args.adx_threshold,
            atr_threshold=args.atr_threshold,
        )
    else:
        strategy = MeanReversion(window=20, threshold=args.threshold, timeframe="15m")
    
    log_timing("Strategy initialization", time.time() - strategy_start, args.verbose)

    # Run backtest with profiling if requested
    log_stage(f"Running {args.mode} backtest on {len(bars):,} bars", args.verbose)
    engine_start = time.time()
    
    if args.profile:
        import cProfile
        import pstats
        
        profiler = cProfile.Profile()
        profiler.enable()
    
    try:
        # Create progress callback if verbose
        progress_cb = None
        if args.verbose:
            progress_cb = lambda i, n: progress_callback(i, n, args.verbose)
        
        # Run backtest based on mode
        if args.mode == "onebar":
            metrics, equity_curve = run_backtest_onebar(
                bars, strategy, fee=args.fee, verbose=args.verbose, progress_cb=progress_cb
            )
        else:
            metrics, equity_curve = run_backtest(
                bars, strategy, fee=args.fee, verbose=args.verbose, progress_cb=progress_cb
            )
            
    except Exception as e:
        if args.profile:
            profiler.disable()
        stop_event.set()
        print(f"[ERROR] Backtest failed: {e}", flush=True)
        sys.exit(2)
    finally:
        if args.profile:
            profiler.disable()
            # Save profile
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_path = Path(f"artifacts/profile_{timestamp}.prof")
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profiler.dump_stats(str(profile_path))
            print(f"[profile] Saved to: {profile_path}")
            print(f"[profile] View with: python -m pstats {profile_path}")
    
    log_timing("Backtest engine", time.time() - engine_start, args.verbose)
    
    # Stop watchdog
    stop_event.set()

    # Print results as JSON
    print(json.dumps(metrics, indent=2, sort_keys=True))

    # Print human-readable table
    print()
    print(format_metrics_table(metrics, args.mode))

    # Save to CSV if requested
    if args.out:
        log_stage("Saving results to CSV", args.verbose)
        save_start = time.time()
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_single_result_csv(
            metrics, args.mode, args.bars, args.fee, args.threshold, output_path, args.append
        )
        log_timing("CSV save", time.time() - save_start, args.verbose)
        print(f"\nResult saved to: {output_path}")
    
    # Print summary
    if args.verbose:
        print(f"\n[summary] Data: {original_bars:,} → {len(bars):,} bars")
        print(f"[summary] Strategy: {strategy.name()}")
        print(f"[summary] Mode: {args.mode}")
        print(f"[summary] Total time: {time.time() - start_time:.2f}s")

    # Generate pretty report if requested
    if args.pretty:
        # Prepare context for pretty report
        if args.pretty_symbols:
            # Parse symbols from command line
            symbols_bars = []
            for symbol_info in args.pretty_symbols.split(","):
                if ":" in symbol_info:
                    sym, count_str = symbol_info.split(":", 1)
                    symbols_bars.append((sym.strip(), int(count_str.strip())))
                else:
                    symbols_bars.append((symbol_info.strip(), len(bars)))
        else:
            # Default: use one symbol with actual bar count
            sym = getattr(args, "symbol", "SYMBOL")
            symbols_bars = [(sym, len(bars))]

        signals_total = metrics.get("trades")  # если «сигналы == сделки», иначе оставь None
        signals_period = (bars[0][0], bars[-1][0]) if bars else None

        # чекпоинты (если нет equity_curve)
        checkpoints = []
        if metrics.get("trades"):
            T = metrics["trades"]
            for k in (0.189, 0.378, 0.567, 0.756, 0.945):
                checkpoints.append((k, 0.0, int(T * k)))  # баланс=0.0, чтобы сохранить структуру

        params = {
            "Базовый размер позиции": "6%",
            "Максимальный размер": "10%",
            "Торговые расходы": (
                f"{int(round((args.fee or 0.0)*10000))} bps" if hasattr(args, "fee") else "N/A"
            ),
        }

        ctx = PrettyCtx(
            start_ts=st or 0,  # у тебя уже есть UTC-границы
            end_ts=et or 0,
            timeframe=args.timeframe,
            initial_balance=1000.0,
            symbols_bars=symbols_bars,
            signals_total=signals_total,
            signals_period=signals_period,
            metrics=metrics,
            checkpoints=checkpoints,
            params=params,
        )

        summary = render(ctx)
        print("\n" + summary)

        # Save JSON to both locations
        save_json(ctx, "balanced_two_year_results.json")
        out_dir = Path("artifacts/reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        save_json(ctx, out_dir / "balanced_two_year_results.json")

        # Add to GitHub Step Summary if available
        summ = os.environ.get("GITHUB_STEP_SUMMARY")
        if summ:
            with open(summ, "a", encoding="utf-8") as f:
                f.write("```\n" + summary + "\n```\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
