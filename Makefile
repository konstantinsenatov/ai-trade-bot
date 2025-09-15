.PHONY: venv fmt smoke-hist smoke-real bench-small

venv:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

install:
	pip install -U pip && pip install -r requirements.txt

lint:
	ruff check . && black --check .

fmt:
	ruff check --fix . || true
	black .

types:
	mypy .

test:
	pytest -q

backtest:
	python3 scripts/backtest.py

smoke-hist:
	python3 scripts/backtest.py --mode onebar --strategy optimized --data-source historical --smoke --out artifacts/backtests/onebar_hist_smoke.csv

smoke-real:
	python3 scripts/backtest.py --mode onebar --strategy optimized --data-source real --pair BTC/USDT --timeframe 15m --limit 1500 --smoke --out artifacts/backtests/onebar_real_smoke.csv

bench-small:
	python3 scripts/bench_small.py

cloud-opt-local:
	python3 scripts/cloud_optimize.py --pair "BTC/USDT" --timeframe "15m" --limit 3000 --shard-index 0 --shard-count 1 --top 5

all: install lint types test
