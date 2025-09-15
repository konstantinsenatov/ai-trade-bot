# AI Trade Bot

An AI-driven development automation system with integrated trading bot capabilities and cloud optimization pipeline.

## Bot module layout

The `bot/` module provides a lightweight trading bot framework:

### Core Components (`bot/core/`)
- **exchange.py**: Paper trading exchange simulator with order execution
- **risk.py**: Risk management wrappers around existing `core.risk` module

### Data Sources (`bot/data/`)
- **ohlcv_source.py**: OHLCV data interface with synthetic data generator

### Strategies (`bot/strategy/`)
- **base.py**: Abstract strategy interface
- **mean_reversion.py**: Simple mean reversion strategy using SMA

### Backtesting (`bot/backtest/`)
- **engine.py**: Minimal backtesting engine without pandas dependencies

### Utilities (`bot/utils/`)
- **timeframes.py**: Timeframe string to seconds conversion

### CLI Tools (`scripts/`)
- **backtest.py**: Command-line backtesting tool

## Quick Start

```bash
# Run backtest
make backtest

# One-bar backtest mode
python scripts/backtest.py --mode onebar

# Run all tests
make all
```

## One-bar backtest mode

The bot supports a special "one-bar" backtest mode that simulates realistic trading conditions:

- **No look-ahead bias**: Signals are calculated using only historical data (< t)
- **Same-bar execution**: If signal == "buy", enter at open[t] and exit at close[t]
- **Commission handling**: Trading fees are applied both ways (entry + exit)
- **Profit Factor**: Calculated as sum(profits) / abs(sum(losses))

```bash
# Run one-bar backtest
python scripts/backtest.py --mode onebar

# Compare with regular mode
python scripts/backtest.py --mode close
```

## Quick backtest with params

The CLI supports various parameters for customizing backtest runs:

```bash
# One-bar mode with custom parameters
python scripts/backtest.py --mode onebar --bars 300 --fee 0.002

# Close mode with different threshold
python scripts/backtest.py --mode close --bars 500 --threshold 0.01

# All parameters
python scripts/backtest.py --mode onebar --bars 1000 --fee 0.0015 --threshold 0.003
```

**Available parameters:**
- `--mode`: `close` (default) or `onebar`
- `--bars`: Number of bars to load (default: 500)
- `--fee`: Trading fee rate (default: 0.001)
- `--threshold`: Mean reversion threshold (default: 0.005)

**Output format:**
The CLI shows both JSON and human-readable table format:
```
{
  "final_equity": 453.83,
  "max_dd": 0.558,
  "pf": 0.588,
  "trades": 342
}

=== Backtest Results (mode=onebar) ===
Final Equity:   453.83
Max Dd:         0.558
Pf:             0.588
Trades:         342
```

## Batch backtest (CSV)

The system supports batch backtesting with CSV output for systematic parameter testing:

### Batch backtest script (`scripts/bench.py`)

Run multiple backtests with different parameter combinations:

```bash
# Simple batch with two modes
python scripts/bench.py --modes close,onebar --bars 300 --fees 0.001,0.002 --thresholds 0.005,0.01

# Custom parameters
python scripts/bench.py --modes onebar --bars 500 --fees 0.001,0.002,0.003 --thresholds 0.005,0.01,0.02 --seed 123 --out user_data/my_backtests.csv

# Append to existing CSV
python scripts/bench.py --modes close --bars 200 --fees 0.001 --thresholds 0.005 --append --out user_data/backtests.csv
```

**Available parameters:**
- `--modes`: Comma-separated modes (`close,onebar`, default: `close,onebar`)
- `--bars`: Number of bars to load (default: 500)
- `--fees`: Comma-separated fee rates (default: `0.001`)
- `--thresholds`: Comma-separated thresholds (default: `0.005`)
- `--seed`: Random seed (default: 42)
- `--out`: Output CSV path (default: `user_data/backtests.csv`)
- `--append`: Append to CSV instead of overwriting

### Single backtest with CSV output

Add CSV output to individual backtest runs:

```bash
# Single run and save to CSV
python scripts/backtest.py --mode onebar --bars 300 --fee 0.002 --threshold 0.005 --out user_data/runs.csv

# Append to existing CSV
python scripts/backtest.py --mode close --bars 200 --fee 0.001 --threshold 0.01 --out user_data/runs.csv --append
```

### CSV Format

All CSV files use the same standardized format with the following columns:

| Column | Description | Type |
|--------|-------------|------|
| `mode` | Backtest mode (`close` or `onebar`) | string |
| `bars` | Number of bars used | integer |
| `fee` | Trading fee rate | float |
| `threshold` | Mean reversion threshold | float |
| `seed` | Random seed | integer |
| `trades` | Number of trades executed | integer |
| `final_equity` | Final equity value | float |
| `win_rate` | Win rate (close mode only) | float |
| `pf` | Profit Factor (onebar mode only) | float |
| `max_dd` | Maximum drawdown | float |
| `return_pct` | Return percentage (close mode only) | float |
| `total_fees` | Total fees paid (close mode only) | float |

**Note:** Fields specific to certain modes are left empty for incompatible modes.

## Nightly batch (CSV+artifact+TG)

The system runs automated batch backtests nightly with CSV artifact generation and Telegram notifications:

### Automated nightly batch

**Schedule:** Daily at 03:00 UTC via GitHub Actions

**Default parameters:**
- Modes: `close,onebar`
- Bars: `500`
- Fees: `0.001,0.002`
- Thresholds: `0.003,0.005,0.01`
- Seed: `42`
- Output: `user_data/backtests.csv` (append mode)

### Manual batch execution

Run the nightly batch manually with custom parameters:

1. Go to **Actions** → **Nightly Batch Backtest**
2. Click **Run workflow**
3. Optionally modify parameters:
   - **Modes:** `close,onebar` (default)
   - **Bars:** `500` (default)
   - **Fees:** `0.001,0.002` (default)
   - **Thresholds:** `0.003,0.005,0.01` (default)
   - **Seed:** `42` (default)
4. Click **Run workflow**

### Artifacts and notifications

**CSV Artifact:**
- Name: `batch-backtest-results`
- Path: `user_data/backtests.csv`
- Retention: 14 days
- Download from: **Actions** → **Nightly Batch Backtest** → **Artifacts**

**Telegram Notification Example:**
```
📊 Nightly Batch Backtest Complete

Ran 12 combinations
Best results: close: 9989 equity, 7 trades, 0.0% win rate, -0.1% return | onebar: 682 equity, 100 trades, 0.40 PF

Artifact: user_data/backtests.csv
```

### Reading backtest results

**Close mode metrics:**
- `trades`: Number of trades executed
- `win_rate`: Percentage of profitable trades
- `return_pct`: Total return percentage
- `final_equity`: Final portfolio value
- `total_fees`: Total trading fees paid
- `max_dd`: Maximum drawdown

**Onebar mode metrics:**
- `trades`: Number of trades executed
- `pf`: Profit Factor (sum of profits / abs(sum of losses))
- `final_equity`: Final portfolio value
- `max_dd`: Maximum drawdown
- `win_rate`: May be empty (not calculated in onebar mode)

**Analysis tips:**
- Sort CSV by `final_equity` (descending) for best performers
- Sort CSV by `pf` (descending) for onebar mode best performers
- Compare `max_dd` across different parameter combinations
- Use `--append` to accumulate results over multiple runs

## Nightly runs & stop conditions

### Manual workflow execution
To run the orchestrator manually in GitHub Actions:
1. Go to **Actions** → **Nightly Orchestrator**
2. Click **Run workflow**
3. Select branch and click **Run workflow**

### Schedule
The orchestrator runs automatically every day at **02:00 UTC** via cron schedule.

### Stopping the orchestrator
Several ways to stop the orchestrator:

1. **Cancel current run**: Go to Actions → Nightly Orchestrator → Cancel run
2. **Disable schedule**: Comment out or remove the `schedule` section in `.github/workflows/nightly-orchestrator.yml`
3. **Create stop file**: Create `.orchestrator_stop` file in repository root

### Environment variables
- `ORCH_MAX_ITERS`: Maximum iterations per task (default: 3)
- `TASKS_PER_RUN`: Maximum tasks to complete per run (default: 1)
- `WALL_TIMEOUT_MIN`: Maximum runtime in minutes, 0 = no limit (default: 0)

### Logs
- **GitHub Actions**: Check artifacts → `orchestrator-logs` (retained for 7 days)
- **Local**: Check `logs/` directory for `run-YYYYMMDD_HHMMSS.log` files

### Диагностика раннего завершения
Возможные причины быстрого завершения (~20s):
- `.orchestrator_stop` обнаружен
- нет незакрытых задач в TODO.md
- pre-flight passed/failed
- `invalid_diff` - некорректный diff от GPT

Смотреть:
- **Actions** → **Artifacts** → `orchestrator-logs`
- **Job Summary** (верх блока)

#### Диагностика invalid_diff
Если ран упал по причине `invalid_diff`:
- Скачайте артефакт `failed-diff` и посмотрите, что сгенерировал GPT
- Оркестратор автоматически делает до 2 повторных запросов
- Проверьте формат diff: должен начинаться с `diff --git` и содержать `+++`/`---`

## Cloud Optimization (GitHub Actions)

The system includes a cloud-based optimization pipeline that runs parameter grid searches across multiple shards for maximum efficiency.

### Manual Execution

**GitHub UI:**
1. Go to **Actions** → **Cloud Optimization**
2. Click **Run workflow**
3. Configure parameters:
   - **pair**: Trading pair (default: BTC/USDT)
   - **timeframe**: Timeframe (default: 15m)
   - **limit**: Number of bars (default: 3000)
   - **shards**: Number of parallel shards 1-8 (default: 4)
   - **top**: Top-N results to save (default: 5)

**GitHub CLI:**
```bash
gh workflow run "Cloud Optimization" --ref main \
  -f pair="BTC/USDT" \
  -f timeframe="15m" \
  -f limit=3000 \
  -f shards=4 \
  -f top=5
```

### Artifacts

**Individual Shards:**
- `optimization-<timestamp>-shard-<N>`: Results from each shard
- Contains: `shard_N_results.csv`, `shard_N_top5.csv`

**Aggregated Results:**
- `optimization-aggregate`: Combined results from all shards
- Contains: `combined_results.csv`, `summary.md`

### Local Testing

```bash
# Test single shard locally
make cloud-opt-local

# Or directly:
python3 scripts/cloud_optimize.py \
  --pair "BTC/USDT" \
  --timeframe "15m" \
  --limit 3000 \
  --shard-index 0 \
  --shard-count 1 \
  --top 5
```

### Scheduling

The optimization runs automatically:
- **Daily**: 02:00 UTC via cron schedule
- **Parameters**: Default BTC/USDT 15m, 3000 bars, 4 shards

## Architecture

The bot module is designed to be:
- **Lightweight**: No heavy dependencies (pandas, ccxt)
- **Typed**: Full Python 3.11+ type annotations
- **Testable**: Comprehensive test coverage
- **Extensible**: Clean interfaces for adding new strategies and data sources