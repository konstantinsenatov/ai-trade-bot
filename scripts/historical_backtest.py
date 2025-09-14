#!/usr/bin/env python3
"""
Historical backtest script for last 2 years of data.

This script runs backtests using realistic historical data simulation
based on actual market patterns over the last 2 years.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.backtest.engine import run_backtest, run_backtest_onebar
from bot.data.historical_source import HistoricalOHLCV
from bot.strategy.mean_reversion import MeanReversion


def format_metrics_table(metrics: dict, mode: str) -> str:
    """Format metrics as a human-readable table."""
    lines = [f"=== Historical Backtest Results (mode={mode}) ==="]
    
    # Define key metrics for each mode
    if mode == "close":
        key_metrics = ["trades", "final_equity", "win_rate", "max_dd", "return_pct", "total_fees"]
    else:  # onebar
        key_metrics = ["trades", "final_equity", "pf", "max_dd"]
    
    # Calculate column widths
    max_key_width = max(len(key) for key in key_metrics)
    
    for key in key_metrics:
        if key in metrics:
            value = metrics[key]
            if isinstance(value, float):
                if key in ["win_rate", "return_pct", "max_dd"]:
                    formatted_value = f"{value:.1%}"
                elif key in ["final_equity", "total_fees"]:
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = f"{value:.3f}"
            else:
                formatted_value = str(value)
            
            lines.append(f"{key.replace('_', ' ').title():<{max_key_width}}: {formatted_value}")
    
    return "\n".join(lines)


def run_historical_backtest(
    mode: str = "close",
    timeframe: str = "1h", 
    fee: float = 0.001,
    threshold: float = 0.005,
    symbol: str = "BTCUSDT"
) -> dict:
    """Run historical backtest for last 2 years."""
    
    print(f"Loading historical data for {symbol} ({timeframe})...")
    
    # Load historical data
    data_source = HistoricalOHLCV(symbol=symbol, timeframe=timeframe)
    bars = data_source.load(timeframe, bars=0)  # bars=0 means load all available (2 years)
    
    print(f"Loaded {len(bars)} bars of historical data")
    print(f"Date range: {bars[0][0]} to {bars[-1][0]}")
    
    # Convert timestamps to readable dates
    from datetime import datetime
    start_date = datetime.fromtimestamp(bars[0][0]).strftime("%Y-%m-%d %H:%M")
    end_date = datetime.fromtimestamp(bars[-1][0]).strftime("%Y-%m-%d %H:%M")
    print(f"Period: {start_date} to {end_date}")
    
    # Initialize strategy
    strategy = MeanReversion(threshold=threshold)
    
    # Run backtest
    print(f"Running {mode} backtest...")
    print(f"Parameters: fee={fee}, threshold={threshold}")
    
    if mode == "onebar":
        metrics, equity = run_backtest_onebar(bars, strategy, fee=fee)
    else:
        metrics, equity = run_backtest(bars, strategy, fee=fee)
    
    return metrics, equity, bars


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Historical backtest for last 2 years")
    parser.add_argument("--mode", choices=["close", "onebar"], default="close",
                       help="Backtest mode (default: close)")
    parser.add_argument("--timeframe", default="1h", 
                       help="Data timeframe (default: 1h)")
    parser.add_argument("--fee", type=float, default=0.001,
                       help="Trading fee (default: 0.001)")
    parser.add_argument("--threshold", type=float, default=0.005,
                       help="Strategy threshold (default: 0.005)")
    parser.add_argument("--symbol", default="BTCUSDT",
                       help="Trading symbol (default: BTCUSDT)")
    parser.add_argument("--save-data", action="store_true",
                       help="Save historical data to CSV")
    parser.add_argument("--out", type=str,
                       help="Output CSV file for results")
    
    args = parser.parse_args()
    
    try:
        # Run backtest
        metrics, equity, bars = run_historical_backtest(
            mode=args.mode,
            timeframe=args.timeframe,
            fee=args.fee,
            threshold=args.threshold,
            symbol=args.symbol
        )
        
        # Print JSON results
        print("\n" + "="*50)
        print("JSON Results:")
        print(json.dumps(metrics, indent=2))
        
        # Print human-readable table
        print("\n" + format_metrics_table(metrics, args.mode))
        
        # Save data if requested
        if args.save_data:
            data_source = HistoricalOHLCV(symbol=args.symbol, timeframe=args.timeframe)
            csv_path = data_source.save_to_csv(bars, f"historical_{args.symbol}_{args.timeframe}.csv")
            print(f"\nHistorical data saved to: {csv_path}")
        
        # Save results to CSV if requested
        if args.out:
            output_path = Path(args.out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['metric', 'value'])
                for key, value in metrics.items():
                    writer.writerow([key, value])
            
            print(f"\nResults saved to: {output_path}")
        
        print(f"\nHistorical backtest completed successfully!")
        print(f"Period: 2 years of {args.symbol} data")
        print(f"Total bars: {len(bars)}")
        
    except Exception as e:
        print(f"Error running historical backtest: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
