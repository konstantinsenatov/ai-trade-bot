install:
	pip install -U pip && pip install -r requirements.txt

lint:
	ruff check . && black --check .

fmt:
	black .

types:
	mypy .

test:
	pytest -q

backtest:
	python3 scripts/backtest.py

all: install lint types test
