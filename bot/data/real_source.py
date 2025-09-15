"""Real data source using ccxt for fetching live market data."""

from __future__ import annotations

import os
import time
import pathlib
from typing import Optional

import pandas as pd
import ccxt


# Cache directory for storing downloaded data
CACHE_DIR = pathlib.Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(pair: str, timeframe: str, limit: int) -> pathlib.Path:
    """Generate cache file path for given parameters.
    
    Args:
        pair: Trading pair (e.g., "BTC/USDT")
        timeframe: Timeframe (e.g., "15m")
        limit: Number of bars to fetch
        
    Returns:
        Path to cache file
    """
    safe = pair.replace("/", "")
    return CACHE_DIR / f"binance_{safe}_{timeframe}_{limit}.parquet"


def fetch_binance_ohlcv(
    pair: str = "BTC/USDT", 
    timeframe: str = "15m", 
    limit: int = 1000, 
    use_cache: bool = True
) -> pd.DataFrame:
    """Fetch OHLCV data from Binance using ccxt.
    
    Args:
        pair: Trading pair (e.g., "BTC/USDT")
        timeframe: Timeframe (e.g., "15m", "1h", "1d")
        limit: Number of bars to fetch (max 1000)
        use_cache: Whether to use cached data if available
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
        
    Raises:
        Exception: If all retry attempts fail
    """
    cache_file = _cache_path(pair, timeframe, limit)
    
    # Return cached data if available and requested
    if use_cache and cache_file.exists():
        print(f"[cache] Loading cached data from {cache_file}")
        return pd.read_parquet(cache_file)
    
    # Initialize Binance exchange
    ex = ccxt.binance({"enableRateLimit": True})
    
    # Retry logic for API calls
    for attempt in range(3):
        try:
            print(f"[api] Fetching {limit} bars of {pair} {timeframe} from Binance (attempt {attempt + 1})")
            bars = ex.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
            break
        except Exception as e:
            print(f"[api] Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))
    
    # Convert to DataFrame
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    
    # Cache the data if requested
    if use_cache:
        print(f"[cache] Saving data to {cache_file}")
        df.to_parquet(cache_file, index=False)
    
    print(f"[api] Successfully fetched {len(df)} bars")
    return df


def get_available_pairs() -> list[str]:
    """Get list of available trading pairs from Binance.
    
    Returns:
        List of trading pair strings
    """
    try:
        ex = ccxt.binance({"enableRateLimit": True})
        markets = ex.load_markets()
        return [symbol for symbol in markets.keys() if "/USDT" in symbol]
    except Exception as e:
        print(f"[api] Failed to fetch available pairs: {e}")
        return ["BTC/USDT", "ETH/USDT", "BNB/USDT"]  # Fallback


def get_available_timeframes() -> list[str]:
    """Get list of available timeframes from Binance.
    
    Returns:
        List of timeframe strings
    """
    try:
        ex = ccxt.binance({"enableRateLimit": True})
        return list(ex.timeframes.keys())
    except Exception as e:
        print(f"[api] Failed to fetch available timeframes: {e}")
        return ["1m", "5m", "15m", "1h", "4h", "1d"]  # Fallback
