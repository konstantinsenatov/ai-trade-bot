#!/usr/bin/env python3
"""Small grid search for Onebar strategy optimization."""

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.data.loader import load_data  # noqa: E402


def run_backtest_with_params(
    zs_threshold: float,
    adx_max: float,
    atrpct_min: float,
    min_bars_cooldown: int,
    pair: str = "BTC/USDT",
    timeframe: str = "15m",
    limit: int = 3000,
    verbose: bool = False
) -> Dict:
    """Run backtest with specific parameters and return metrics."""
    
    cmd = [
        "python3", "scripts/backtest.py",
        "--mode", "onebar",
        "--strategy", "optimized",
        "--data-source", "real",
        "--pair", pair,
        "--timeframe", timeframe,
        "--limit", str(limit),
        "--zs-threshold", str(zs_threshold),
        "--adx-max", str(adx_max),
        "--atrpct-min", str(atrpct_min),
        "--min-bars-cooldown", str(min_bars_cooldown),
        "--out", f"artifacts/bench/temp_{zs_threshold}_{adx_max}_{atrpct_min}_{min_bars_cooldown}.csv"
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        runtime_s = time.time() - start_time
        
        if result.returncode != 0:
            print(f"Error running backtest: {result.stderr}")
            return {
                "zs_threshold": zs_threshold,
                "adx_max": adx_max,
                "atrpct_min": atrpct_min,
                "min_bars_cooldown": min_bars_cooldown,
                "equity": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "pf": 0.0,
                "max_dd": 1.0,
                "runtime_s": runtime_s,
                "error": result.stderr
            }
        
        # Parse JSON output from stdout using regex
        json_match = re.search(r'\{[^{}]*"final_equity"[^{}]*\}', result.stdout, re.DOTALL)
        json_line = json_match.group(0) if json_match else None
        
        if not json_line:
            print(f"No JSON output found in: {result.stdout}")
            return {
                "zs_threshold": zs_threshold,
                "adx_max": adx_max,
                "atrpct_min": atrpct_min,
                "min_bars_cooldown": min_bars_cooldown,
                "equity": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "pf": 0.0,
                "max_dd": 1.0,
                "runtime_s": runtime_s,
                "error": "No JSON output"
            }
        
        try:
            metrics = json.loads(json_line)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"JSON line: {json_line}")
            return {
                "zs_threshold": zs_threshold,
                "adx_max": adx_max,
                "atrpct_min": atrpct_min,
                "min_bars_cooldown": min_bars_cooldown,
                "equity": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "pf": 0.0,
                "max_dd": 1.0,
                "runtime_s": runtime_s,
                "error": f"JSON decode error: {e}"
            }
        
        return {
            "zs_threshold": zs_threshold,
            "adx_max": adx_max,
            "atrpct_min": atrpct_min,
            "min_bars_cooldown": min_bars_cooldown,
            "equity": metrics.get("final_equity", 0.0),
            "trades": metrics.get("trades", 0),
            "win_rate": metrics.get("win_rate", 0.0),
            "pf": metrics.get("pf", 0.0),
            "max_dd": metrics.get("max_dd", 1.0),
            "runtime_s": runtime_s
        }
        
    except subprocess.TimeoutExpired:
        print(f"Timeout running backtest for params: {zs_threshold}, {adx_max}, {atrpct_min}, {min_bars_cooldown}")
        return {
            "zs_threshold": zs_threshold,
            "adx_max": adx_max,
            "atrpct_min": atrpct_min,
            "min_bars_cooldown": min_bars_cooldown,
            "equity": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "pf": 0.0,
            "max_dd": 1.0,
            "runtime_s": 60.0,
            "error": "Timeout"
        }
    except Exception as e:
        print(f"Exception running backtest: {e}")
        return {
            "zs_threshold": zs_threshold,
            "adx_max": adx_max,
            "atrpct_min": atrpct_min,
            "min_bars_cooldown": min_bars_cooldown,
            "equity": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "pf": 0.0,
            "max_dd": 1.0,
            "runtime_s": 0.0,
            "error": str(e)
        }


def run_grid_search(
    pair: str = "BTC/USDT",
    timeframe: str = "15m", 
    limit: int = 3000,
    soft_mode: bool = False
) -> List[Dict]:
    """Run grid search with specified parameter ranges."""
    
    if soft_mode:
        # Softer parameters for when no trades are found
        zs_thresholds = [1.0, 1.2, 1.5]
        adx_max_values = [25, 30, 35]
        atrpct_min_values = [0.002, 0.003, 0.004]
        min_bars_cooldowns = [3, 5]
        print("🔄 Running SOFT grid search (no trades found in previous run)")
    else:
        # Standard parameters
        zs_thresholds = [1.2, 1.5, 1.8, 2.0]
        adx_max_values = [20, 25, 30]
        atrpct_min_values = [0.003, 0.004, 0.005]
        min_bars_cooldowns = [3, 5]
        print("🚀 Running STANDARD grid search")
    
    results = []
    total_combinations = len(zs_thresholds) * len(adx_max_values) * len(atrpct_min_values) * len(min_bars_cooldowns)
    current = 0
    
    print(f"📊 Total combinations to test: {total_combinations}")
    print(f"📈 Data source: real BTC/USDT 15m (2000 bars)")
    print()
    
    for zs_threshold in zs_thresholds:
        for adx_max in adx_max_values:
            for atrpct_min in atrpct_min_values:
                for min_bars_cooldown in min_bars_cooldowns:
                    current += 1
                    print(f"[{current}/{total_combinations}] Testing: zs={zs_threshold}, adx={adx_max}, atr={atrpct_min}, cd={min_bars_cooldown}")
                    
                    result = run_backtest_with_params(
                        zs_threshold, adx_max, atrpct_min, min_bars_cooldown, 
                        pair, timeframe, limit, verbose=False
                    )
                    
                    results.append(result)
                    
                    # Print quick result
                    trades = result["trades"]
                    equity = result["equity"]
                    pf = result["pf"]
                    max_dd = result["max_dd"]
                    print(f"  → trades={trades}, equity={equity:.2f}, pf={pf:.3f}, dd={max_dd:.3f}")
                    
                    if "error" in result:
                        print(f"  ❌ Error: {result['error']}")
                    
                    print()
    
    return results


def filter_and_sort_results(results: List[Dict]) -> List[Dict]:
    """Filter results to keep only 3-80 trades and sort by performance."""
    
    # Filter: keep only results with 3-80 trades
    filtered = [r for r in results if 3 <= r["trades"] <= 80]
    
    if not filtered:
        print("⚠️  No results with 3-80 trades found!")
        return []
    
    # Sort by: pf (desc), equity (desc), max_dd (asc)
    sorted_results = sorted(filtered, key=lambda x: (-x["pf"], -x["equity"], x["max_dd"]))
    
    return sorted_results


def save_results_csv(results: List[Dict], filename: str, top_n: int = 5, output_dir: Path = None) -> None:
    """Save results to CSV file."""
    
    if output_dir is None:
        output_dir = Path("artifacts/bench")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / filename
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'zs_threshold', 'adx_max', 'atrpct_min', 'min_bars_cooldown',
            'equity', 'trades', 'win_rate', 'pf', 'max_dd', 'runtime_s'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Create params_json field
            params_json = json.dumps({
                "zs_threshold": result["zs_threshold"],
                "adx_max": result["adx_max"],
                "atrpct_min": result["atrpct_min"],
                "min_bars_cooldown": result["min_bars_cooldown"]
            })
            result["params_json"] = params_json
            
            # Write row (excluding error field if present)
            row = {k: v for k, v in result.items() if k != "error"}
            writer.writerow(row)
    
    print(f"💾 Results saved to: {output_path}", flush=True)
    
    # Save Top-N results separately
    if results:
        top_n_results = results[:top_n]
        top_filename = filename.replace('.csv', f'_top{top_n}.csv')
        top_path = output_dir / top_filename
        
        with open(top_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in top_n_results:
                params_json = json.dumps({
                    "zs_threshold": result["zs_threshold"],
                    "adx_max": result["adx_max"],
                    "atrpct_min": result["atrpct_min"],
                    "min_bars_cooldown": result["min_bars_cooldown"]
                })
                result["params_json"] = params_json
                
                row = {k: v for k, v in result.items() if k != "error"}
                writer.writerow(row)
        
        print(f"💾 Top-{top_n} results saved to: {top_path}", flush=True)


def print_top_results(results: List[Dict], top_n: int = 5) -> None:
    """Print top N results in a formatted table."""
    
    if not results:
        print("❌ No results to display")
        return
    
    print(f"🏆 TOP {min(top_n, len(results))} RESULTS:")
    print()
    
    # Header
    print(f"{'Rank':<4} {'Trades':<6} {'PF':<8} {'Equity':<10} {'MaxDD':<8} {'Params'}")
    print("-" * 80)
    
    for i, result in enumerate(results[:top_n]):
        rank = i + 1
        trades = result["trades"]
        pf = result["pf"]
        equity = result["equity"]
        max_dd = result["max_dd"]
        
        params = f"zs={result['zs_threshold']}, adx={result['adx_max']}, atr={result['atrpct_min']}, cd={result['min_bars_cooldown']}"
        
        print(f"{rank:<4} {trades:<6} {pf:<8.3f} {equity:<10.2f} {max_dd:<8.3f} {params}")
    
    print()


def generate_markdown_table(results: List[Dict], top_n: int = 5) -> str:
    """Generate markdown table for top results."""
    
    if not results:
        return "No results available."
    
    md_lines = [
        "| Rank | Trades | PF | Equity | MaxDD | ZS | ADX | ATR | CD |",
        "|------|--------|----|---------|-------|----|----|----|----|"
    ]
    
    for i, result in enumerate(results[:top_n]):
        rank = i + 1
        trades = result["trades"]
        pf = result["pf"]
        equity = result["equity"]
        max_dd = result["max_dd"]
        zs = result["zs_threshold"]
        adx = result["adx_max"]
        atr = result["atrpct_min"]
        cd = result["min_bars_cooldown"]
        
        md_lines.append(f"| {rank} | {trades} | {pf:.3f} | {equity:.2f} | {max_dd:.3f} | {zs} | {adx} | {atr} | {cd} |")
    
    return "\n".join(md_lines)


def main() -> int:
    """Main function for grid search."""
    
    parser = argparse.ArgumentParser(description="Onebar Strategy Grid Search")
    parser.add_argument("--pair", type=str, default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", type=str, default="15m", help="Timeframe (default: 15m)")
    parser.add_argument("--limit", type=int, default=3000, help="Number of bars to fetch (default: 3000)")
    parser.add_argument("--out", type=str, default="artifacts/bench/bench_small.csv", help="Output CSV path (default: artifacts/bench/bench_small.csv)")
    parser.add_argument("--top", type=int, default=5, help="Number of top results to save/print (default: 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic results (default: 42)")
    
    args = parser.parse_args()
    
    print("🔍 Onebar Strategy Grid Search", flush=True)
    print("=" * 50, flush=True)
    print(f"📊 Pair: {args.pair}", flush=True)
    print(f"📊 Timeframe: {args.timeframe}", flush=True)
    print(f"📊 Bars: {args.limit}", flush=True)
    print(f"📊 Top-N: {args.top}", flush=True)
    print(f"📊 Seed: {args.seed}", flush=True)
    print()
    
    # Ensure output directory exists
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run standard grid search
    results = run_grid_search(args.pair, args.timeframe, args.limit, soft_mode=False)
    
    # Check if we got any trades
    total_trades = sum(r["trades"] for r in results)
    if total_trades == 0:
        print("⚠️  No trades found in standard grid search. Running soft mode...", flush=True)
        results = run_grid_search(args.pair, args.timeframe, args.limit, soft_mode=True)
    
    # Filter and sort results
    filtered_results = filter_and_sort_results(results)
    
    # Save results
    save_results_csv(filtered_results, args.out, args.top)
    
    # Print top results
    print_top_results(filtered_results, top_n=args.top)
    
    # Generate markdown table
    md_table = generate_markdown_table(filtered_results, top_n=args.top)
    print("📋 MARKDOWN TABLE:", flush=True)
    print()
    print(md_table, flush=True)
    print()
    
    # Print recommended config
    if filtered_results:
        best = filtered_results[0]
        recommended_args = f"--zs-threshold {best['zs_threshold']} --adx-max {best['adx_max']} --atrpct-min {best['atrpct_min']} --min-bars-cooldown {best['min_bars_cooldown']}"
        print("🎯 RECOMMENDED CONFIG:", flush=True)
        print(recommended_args, flush=True)
        print()
        print(f"RECOMMENDED_ARGS: {recommended_args}", flush=True)
    else:
        print("❌ No valid configurations found", flush=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
