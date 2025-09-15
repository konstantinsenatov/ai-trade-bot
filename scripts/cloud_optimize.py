#!/usr/bin/env python3
"""Cloud optimization entrypoint with sharding support."""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.bench_small import run_grid_search, filter_and_sort_results, save_results_csv  # noqa: E402


def get_parameter_grid() -> List[Tuple[float, float, float, int]]:
    """Get the full parameter grid as a list of tuples."""
    # Standard parameters
    zs_thresholds = [1.2, 1.5, 1.8, 2.0]
    adx_max_values = [20, 25, 30]
    atrpct_min_values = [0.003, 0.004, 0.005]
    min_bars_cooldowns = [3, 5]
    
    # Soft parameters (for fallback)
    zs_thresholds_soft = [1.0, 1.2, 1.5]
    adx_max_values_soft = [25, 30, 35]
    atrpct_min_values_soft = [0.002, 0.003, 0.004]
    min_bars_cooldowns_soft = [3, 5]
    
    # Generate all combinations
    standard_grid = []
    for zs in zs_thresholds:
        for adx in adx_max_values:
            for atr in atrpct_min_values:
                for cd in min_bars_cooldowns:
                    standard_grid.append((zs, adx, atr, cd))
    
    soft_grid = []
    for zs in zs_thresholds_soft:
        for adx in adx_max_values_soft:
            for atr in atrpct_min_values_soft:
                for cd in min_bars_cooldowns_soft:
                    soft_grid.append((zs, adx, atr, cd))
    
    return standard_grid, soft_grid


def run_shard_grid_search(
    shard_index: int,
    shard_count: int,
    pair: str,
    timeframe: str,
    limit: int,
    top_n: int,
    seed: int
) -> List[Dict]:
    """Run grid search for a specific shard."""
    
    standard_grid, soft_grid = get_parameter_grid()
    
    # Determine which grid to use for this shard
    # Try standard grid first
    shard_params = []
    for i, params in enumerate(standard_grid):
        if i % shard_count == shard_index:
            shard_params.append(params)
    
    print(f"🔍 Shard {shard_index}/{shard_count}: Testing {len(shard_params)} standard combinations", flush=True)
    
    # Run tests for this shard
    results = []
    for i, (zs_threshold, adx_max, atrpct_min, min_bars_cooldown) in enumerate(shard_params):
        print(f"[{i+1}/{len(shard_params)}] Testing: zs={zs_threshold}, adx={adx_max}, atr={atrpct_min}, cd={min_bars_cooldown}", flush=True)
        
        # Import here to avoid circular imports
        from scripts.bench_small import run_backtest_with_params
        
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
        print(f"  → trades={trades}, equity={equity:.2f}, pf={pf:.3f}, dd={max_dd:.3f}", flush=True)
        
        if "error" in result:
            print(f"  ❌ Error: {result['error']}", flush=True)
    
    # Check if we got any trades
    total_trades = sum(r["trades"] for r in results)
    if total_trades == 0:
        print("⚠️  No trades found in standard grid. Trying soft parameters...", flush=True)
        
        # Try soft grid for this shard
        soft_shard_params = []
        for i, params in enumerate(soft_grid):
            if i % shard_count == shard_index:
                soft_shard_params.append(params)
        
        print(f"🔍 Shard {shard_index}/{shard_count}: Testing {len(soft_shard_params)} soft combinations", flush=True)
        
        soft_results = []
        for i, (zs_threshold, adx_max, atrpct_min, min_bars_cooldown) in enumerate(soft_shard_params):
            print(f"[{i+1}/{len(soft_shard_params)}] Testing: zs={zs_threshold}, adx={adx_max}, atr={atrpct_min}, cd={min_bars_cooldown}", flush=True)
            
            result = run_backtest_with_params(
                zs_threshold, adx_max, atrpct_min, min_bars_cooldown,
                pair, timeframe, limit, verbose=False
            )
            
            soft_results.append(result)
            
            # Print quick result
            trades = result["trades"]
            equity = result["equity"]
            pf = result["pf"]
            max_dd = result["max_dd"]
            print(f"  → trades={trades}, equity={equity:.2f}, pf={pf:.3f}, dd={max_dd:.3f}", flush=True)
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}", flush=True)
        
        results.extend(soft_results)
    
    return results


def main() -> int:
    """Main function for cloud optimization."""
    
    parser = argparse.ArgumentParser(description="Cloud Optimization Entrypoint")
    parser.add_argument("--pair", type=str, default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", type=str, default="15m", help="Timeframe (default: 15m)")
    parser.add_argument("--limit", type=int, default=3000, help="Number of bars to fetch (default: 3000)")
    parser.add_argument("--top", type=int, default=5, help="Number of top results to save/print (default: 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic results (default: 42)")
    parser.add_argument("--shard-index", type=int, help="Shard index (0-based)")
    parser.add_argument("--shard-count", type=int, help="Total number of shards")
    
    args = parser.parse_args()
    
    # Validate shard arguments
    if args.shard_index is None or args.shard_count is None:
        print("❌ Both --shard-index and --shard-count are required", flush=True)
        return 1
    
    if args.shard_index < 0 or args.shard_index >= args.shard_count:
        print(f"❌ Invalid shard-index: {args.shard_index}. Must be 0 <= index < {args.shard_count}", flush=True)
        return 1
    
    # Create timestamp for this run
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"artifacts/bench/cloud/{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print("☁️  Cloud Optimization Entrypoint", flush=True)
    print("=" * 50, flush=True)
    print(f"📊 Pair: {args.pair}", flush=True)
    print(f"📊 Timeframe: {args.timeframe}", flush=True)
    print(f"📊 Bars: {args.limit}", flush=True)
    print(f"📊 Top-N: {args.top}", flush=True)
    print(f"📊 Seed: {args.seed}", flush=True)
    print(f"📊 Shard: {args.shard_index}/{args.shard_count}", flush=True)
    print(f"📊 Run Dir: {run_dir}", flush=True)
    print()
    
    # Run shard grid search
    results = run_shard_grid_search(
        args.shard_index, args.shard_count, args.pair, args.timeframe, 
        args.limit, args.top, args.seed
    )
    
    # Filter and sort results
    filtered_results = filter_and_sort_results(results)
    
    # Save shard results
    shard_results_file = run_dir / f"shard_{args.shard_index}_results.csv"
    save_results_csv(filtered_results, f"shard_{args.shard_index}_results.csv", args.top, run_dir)
    
    # Save shard top-N results
    shard_top_file = run_dir / f"shard_{args.shard_index}_top{args.top}.csv"
    if filtered_results:
        top_n_results = filtered_results[:args.top]
        save_results_csv(top_n_results, f"shard_{args.shard_index}_top{args.top}.csv", args.top, run_dir)
    
    # Print summary
    print(f"📊 Shard {args.shard_index} Summary:", flush=True)
    print(f"  Total combinations tested: {len(results)}", flush=True)
    print(f"  Valid configurations: {len(filtered_results)}", flush=True)
    print(f"  Results saved to: {shard_results_file}", flush=True)
    if filtered_results:
        print(f"  Top-{args.top} saved to: {shard_top_file}", flush=True)
        best = filtered_results[0]
        print(f"  Best config: zs={best['zs_threshold']}, adx={best['adx_max']}, atr={best['atrpct_min']}, cd={best['min_bars_cooldown']}", flush=True)
    print()
    
    # Print cloud run directory for GitHub Actions
    print(f"CLOUD_RUN_DIR: {run_dir}", flush=True)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
