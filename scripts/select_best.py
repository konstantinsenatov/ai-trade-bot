#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

IN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/backtests/batch_2y.csv")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("artifacts/reports/best_params.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def f2(x):
    if x is None or x == "":
        return None
    try:
        v = float(x)
        return v / 100.0 if v > 2.0 else v  # если проценты в 0-100, приводим к 0-1
    except Exception:
        return None


def norm_row(r):
    return {
        "mode": r.get("mode") or r.get("Mode"),
        "fee": f2(r.get("fee") or r.get("Fee")),
        "threshold": f2(r.get("threshold") or r.get("Threshold")),
        "trades": int(float(r.get("trades") or 0)),
        "final_equity": float(r.get("equity") or r.get("final_equity") or 0.0),
        "win_rate": f2(r.get("winrate") or r.get("win_rate")),
        "pf": f2(r.get("pf")),
        "max_dd": f2(r.get("dd") or r.get("max_dd")),
        "return_pct": f2(r.get("return%") or r.get("return_pct")),
        "timeframe": r.get("timeframe") or "1h",
    }


rows = []
with open(IN, encoding="utf-8") as f:
    for raw in csv.DictReader(f):
        rows.append(norm_row(raw))

# здравые фильтры
cands = [
    r for r in rows if r["trades"] >= 50 and (r["pf"] or 0) >= 1.3 and (r["max_dd"] or 1) <= 0.25
]

if not cands:  # fallback — топ по pf
    cands = sorted(rows, key=lambda x: (x["pf"] or 0), reverse=True)[:5]

# скоринг: pf*(1-max_dd), затем return_pct
best = sorted(
    cands,
    key=lambda x: ((x["pf"] or 0) * (1 - (x["max_dd"] or 0)), (x["return_pct"] or 0)),
    reverse=True,
)[0]

OUT.write_text(json.dumps(best, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Best params → {OUT}")
