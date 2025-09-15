# === Облачная самооптимизация + TG-уведомления ===
# Требования: gh CLI авторизован; в Settings → Secrets → Actions заданы TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID

set -euo pipefail

REPO="${REPO:-$(git config --get remote.origin.url 2>/dev/null | sed -E 's#.*github.com[:/](.+/.+)\.git#\1#' || true)}"
REPO="${REPO:-konstantinsenatov/ai-trade-bot}"
echo "📦 Repo: $REPO"
gh --version >/dev/null
gh auth status

echo "🔐 Проверка TG secrets…"
MISS=0; for S in TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  gh secret list -R "$REPO" | grep -q "^$S\b" && echo "✅ $S" || { echo "❌ $S отсутствует"; MISS=1; }
done
[ "$MISS" -eq 0 ] || { echo "⛔ Добавь secrets и перезапусти."; exit 2; }

# Окно дат — последние 2 года (UTC). Можно переопределить переменными START/END.
START="${START:-$(python3 - <<'PY'
from datetime import datetime, timezone, timedelta
print((datetime.now(timezone.utc)-timedelta(days=730)).strftime("%Y-%m-%d"))
PY
)}"
END="${END:-$(date -u +%F)}"
echo "🗓 Окно: $START → $END (UTC)"

echo "🧪 Sanity-файлы…"
test -f .github/workflows/nightly-orchestrator.yml
test -f .github/workflows/bench-2y.yml
test -f scripts/bench.py
test -f scripts/backtest.py
test -f scripts/select_best.py

echo "🚀 Запуск Nightly Orchestrator (dispatch bench-2y)…"
gh workflow run "Nightly Orchestrator" -R "$REPO" -f start_date="$START" -f end_date="$END"

echo "⏳ Ожидание регистрации bench-2y…"
sleep 8
RUN_JSON="$(gh run list -R "$REPO" --workflow="bench-2y.yml" --limit 1 --json databaseId,url,status,conclusion 2>/dev/null || true)"
if [ -z "$RUN_JSON" ] || [ "$RUN_JSON" = "[]" ]; then
  echo "…подожду ещё"; sleep 12
  RUN_JSON="$(gh run list -R "$REPO" --workflow="bench-2y.yml" --limit 1 --json databaseId,url,status,conclusion)"
fi

RID="$(echo "$RUN_JSON" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["databaseId"])')"
RURL="$(echo "$RUN_JSON" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["url"])')"
echo "🔗 Bench run: $RURL (id=$RID)"

echo "👀 Стримлю логи до завершения…"
gh run watch "$RID" -R "$REPO" --interval 12 --exit-status || true

echo "📥 Скачиваю артефакты…"
STAMP="${START}_${END}"
OUTDIR="artifacts/_downloads/${STAMP}"
mkdir -p "$OUTDIR"
gh run download "$RID" -R "$REPO" -D "$OUTDIR" || true

echo "🧾 Итого:"
echo "  • Run: $RURL"
echo "  • Артефакты: $OUTDIR"
BEST="$(ls -1 "$OUTDIR"/*/best_params.json 2>/dev/null | head -n1 || true)"
PRETTY="$(ls -1 "$OUTDIR"/*/balanced_two_year_results.json 2>/dev/null | head -n1 || true)"
[ -n "$BEST" ] && { echo "— best_params.json:"; cat "$BEST"; } || echo "— best_params.json: нет"
[ -n "$PRETTY" ] && { echo "— balanced_two_year_results.json (head):"; head -n 40 "$PRETTY"; } || echo "— balanced_two_year_results.json: нет"

echo "📲 TG-уведомление отправляет сам workflow (успех/ошибка). Готово."
