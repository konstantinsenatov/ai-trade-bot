#!/bin/bash
# === Автозапуск облачной оптимизации с TG-уведомлением ===
# Требования: gh CLI авторизован; в репо настроены secrets TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID

set -euo pipefail

echo "🔎 Репозиторий и gh CLI..."
REPO="${REPO:-$(git config --get remote.origin.url 2>/dev/null | sed -E 's#.*github.com[:/](.+/.+)\.git#\1#' || true)}"
REPO="${REPO:-konstantinsenatov/ai-trade-bot}"
echo "   → REPO=$REPO"
gh --version >/dev/null
gh auth status

echo "🔐 Проверяю Telegram secrets в $REPO..."
MISSING=0
for S in TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  if ! gh secret list -R "$REPO" | grep -q "^$S\b"; then
    echo "❌ Нет секрета: $S"
    MISSING=1
  else
    echo "✅ $S найден"
  fi
done
if [ "$MISSING" -ne 0 ]; then
  echo "⛔ Добавь secrets TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в Settings → Secrets and variables → Actions и перезапусти."
  exit 2
fi

echo "⏱ Вычисляю окно дат (UTC, последние 2 года)..."
START="$(python3 - <<'PY'
from datetime import datetime, timezone, timedelta
end = datetime.now(timezone.utc)
start = end - timedelta(days=730)
print(start.strftime("%Y-%m-%d"))
PY
)"
END="$(date -u +%F)"
echo "   → START=$START  END=$END"

echo "🧪 Быстрый sanity-check файлов..."
test -f .github/workflows/nightly-orchestrator.yml
test -f .github/workflows/bench-2y.yml
test -f scripts/bench.py
test -f scripts/backtest.py
test -f scripts/select_best.py

echo "🚀 Запускаю Nightly Orchestrator (dispatch bench-2y)..."
gh workflow run "Nightly Orchestrator" -R "$REPO" -f start_date="$START" -f end_date="$END"

echo "⏳ Жду регистрацию дочернего запуска bench-2y..."
sleep 6
# берём последний run bench-2y
BENCH_RUN_JSON="$(gh run list -R "$REPO" --workflow="bench-2y.yml" --limit 1 --json databaseId,url,status,conclusion 2>/dev/null || true)"
if [ -z "$BENCH_RUN_JSON" ] || [ "$BENCH_RUN_JSON" = "[]" ]; then
  echo "… bench-2y ещё не зарегистрировался, подожду ещё немного"
  sleep 10
  BENCH_RUN_JSON="$(gh run list -R "$REPO" --workflow="bench-2y.yml" --limit 1 --json databaseId,url,status,conclusion)"
fi

BENCH_ID="$(echo "$BENCH_RUN_JSON" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["databaseId"])')"
BENCH_URL="$(echo "$BENCH_RUN_JSON" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["url"])')"
echo "🔗 Bench run: $BENCH_URL (id=$BENCH_ID)"

echo "👀 Стримлю логи bench-2y до завершения..."
# не падать по завершении со статусом !=0, нам важно добежать до уведомлений
gh run watch "$BENCH_ID" -R "$REPO" --interval 10 --exit-status || true

echo "📥 Скачиваю артефакты..."
STAMP="${START}_${END}"
OUTDIR="artifacts/_downloads/${STAMP}"
mkdir -p "$OUTDIR"
gh run download "$BENCH_ID" -R "$REPO" -D "$OUTDIR" || true

echo "🧾 Итог:"
echo "   Bench run: $BENCH_URL"
echo "   Артефакты: $OUTDIR"
JSON_GLOB="$(ls -1 "$OUTDIR"/*/balanced_two_year_results.json 2>/dev/null | head -n1 || true)"
BEST_GLOB="$(ls -1 "$OUTDIR"/*/best_params.json 2>/dev/null | head -n1 || true)"
[ -n "$BEST_GLOB" ] && { echo "— best_params.json:"; cat "$BEST_GLOB"; } || echo "— best_params.json: не найден (проверь шаг select_best)"
[ -n "$JSON_GLOB" ] && { echo "— balanced_two_year_results.json (первые 40 строк):"; head -n 40 "$JSON_GLOB"; } || echo "— balanced_two_year_results.json: не найден"

echo "📲 Уведомление в Telegram отправит сам workflow (успех/ошибка). Готово."
