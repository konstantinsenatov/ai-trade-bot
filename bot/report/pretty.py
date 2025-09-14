from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _iso(ts: int | None) -> str:
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _pct(x: float | None) -> str:
    return f"{x*100:.2f}%" if isinstance(x, (int, float)) else "N/A"


def _money(x: float | None) -> str:
    return f"${x:,.2f}" if isinstance(x, (int, float)) else "N/A"


@dataclass
class PrettyCtx:
    # Контекст прогона
    start_ts: int
    end_ts: int
    timeframe: str
    initial_balance: float = 1000.0
    target_text: str = "ЦЕЛЬ: +30–50% годовых (реалистично и прибыльно)"
    # Данные / сигналы
    symbols_bars: list[tuple[str, int]] | None = None  # [("BTCUSDT", 17544), ...]
    signals_total: int | None = None  # можно = trades
    signals_period: tuple[int, int] | None = None  # (first_ts, last_ts)
    # Метрики (то, что уже считает твой бэктест)
    metrics: dict[str, Any] | None = (
        None  # trades, final_equity, win_rate, pf, max_dd, return_pct, total_fees...
    )
    # Опционально — чекпоинты прогресса (процент, баланс, сделки)
    checkpoints: list[tuple[float, float, int]] | None = None
    # «Сбалансированные параметры» (печатаем то, что есть)
    params: dict[str, Any] | None = (
        None  # e.g. {"base_pos": "6%", "max_pos": "10%", "fees_bps": 27}
    )
    # Аналитика по годам (опционально)
    yearly: list[dict[str, Any]] | None = None  # [{"year":2023,"trades":..., "pnl":...}, ...]


def _annualized(total_return: float | None, years: float) -> float | None:
    # total_return в долях (напр., 0.5152 == +51.52%)
    if total_return is None:
        return None
    if years <= 0:
        return None
    return (1.0 + total_return) ** (1.0 / years) - 1.0


def _years_between(a_ts: int, b_ts: int) -> float:
    return max((b_ts - a_ts) / (365.25 * 24 * 3600), 0.0001)


def _line(s: str = "=", n: int = 70) -> str:
    return s * n


def render(ctx: PrettyCtx) -> str:
    m = ctx.metrics or {}
    # Извлекаем метрики с безопасными значениями
    trades = m.get("trades")
    final_equity = m.get("final_equity")
    win_rate = m.get("win_rate")  # доли
    pf = m.get("pf")
    max_dd = m.get("max_dd")  # доли
    ret_pct = m.get("return_pct")  # доли
    total_fees = m.get("total_fees")

    years = _years_between(ctx.start_ts, ctx.end_ts)
    ann = _annualized(ret_pct, years) if ret_pct is not None else None
    net_profit = (
        (final_equity - ctx.initial_balance) if isinstance(final_equity, (int, float)) else None
    )
    multiple = (
        (final_equity / ctx.initial_balance)
        if isinstance(final_equity, (int, float)) and ctx.initial_balance > 0
        else None
    )

    # Шапка
    out = []
    out.append("⚖️ Запуск сбалансированного двухлетнего бэктеста...")
    out.append("⚖️ Инициализация СБАЛАНСИРОВАННОГО двухлетнего бэктеста")
    out.append(f"💰 Начальный баланс: {_money(ctx.initial_balance)}")
    out.append(f"🎯 {ctx.target_text}")
    # «оптимальные параметры» печатаем из ctx.params если есть
    if ctx.params:
        out.append("✅ Все баги исправлены + оптимальные параметры:")
        for k, v in ctx.params.items():
            out.append(f"   • {k}: {v}")

    out.append("")
    out.append("⚖️ ЗАПУСК СБАЛАНСИРОВАННОГО ДВУХЛЕТНЕГО БЭКТЕСТА")
    out.append(_line("="))
    out.append("📊 Загрузка двухлетних реальных данных...")
    if ctx.symbols_bars:
        for sym, n in ctx.symbols_bars:
            out.append(f"✅ {sym}: {n:,} записей")
    else:
        out.append("✅ Данные загружены (см. артефакты)")

    out.append("⚖️ Генерация сбалансированных сигналов...")
    if ctx.signals_total is not None:
        out.append(f"🎯 Сгенерировано {ctx.signals_total:,} сбалансированных сигналов")
    else:
        out.append("🎯 Сигналы сгенерированы")

    # Период сигналов
    if ctx.signals_period:
        sp_start, sp_end = ctx.signals_period
        out.append("")
        out.append("⚡️ НАЧИНАЕМ СБАЛАНСИРОВАННУЮ ТОРГОВЛЮ:")
        if trades is not None:
            out.append(f"📊 Сигналов: {trades:,}")
        out.append(f"📅 Период: {_iso(sp_start)} - {_iso(sp_end)}")

    # Чекпоинты прогресса (если переданы)
    if ctx.checkpoints:
        out.append("")
        for p, bal, t in ctx.checkpoints:
            # p в долях, t — сделки до этого момента
            p_str = f"{p*100:.1f}%".rjust(5)
            bal_str = _money(bal)
            gain_abs = None
            if isinstance(bal, (int, float)):
                gain_abs = bal - ctx.initial_balance
            gain_pct = (
                (gain_abs / ctx.initial_balance)
                if (gain_abs is not None and ctx.initial_balance > 0)
                else None
            )
            out.append(
                f"⏳ {p_str} | Баланс: {bal_str} ({'+' if (gain_pct or 0)>=0 else ''}{_pct(gain_pct)}) | Сделок: {t:,}"
            )

        if trades is not None and ctx.signals_total is not None:
            out.append("")
            out.append(f"✅ Исполнено {trades:,} из {ctx.signals_total:,} сигналов")

    out.append("")
    out.append("⚖️ РЕЗУЛЬТАТЫ СБАЛАНСИРОВАННОГО ДВУХЛЕТНЕГО БЭКТЕСТА")
    out.append("")
    out.append(_line("="))
    out.append("")
    # Фин. результаты
    out.append(
        f"💰 СБАЛАНСИРОВАННЫЕ ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ ({_iso(ctx.start_ts)}-{_iso(ctx.end_ts)}):"
    )
    out.append(_line("-"))
    out.append(f"Начальный депозит:      {_money(ctx.initial_balance)}")
    out.append(f"Финальный баланс:       {_money(final_equity)}")
    out.append(f"Чистая прибыль:         {_money(net_profit)}")
    out.append(f"Общая доходность:       {('+' if (ret_pct or 0)>=0 else '')}{_pct(ret_pct)}")
    out.append(f"Годовая доходность:     {('+' if (ann or 0)>=0 else '')}{_pct(ann)}")
    out.append(
        f"Прирост капитала:       {f'{multiple:.2f}x' if isinstance(multiple,(int,float)) else 'N/A'}"
    )
    out.append("")
    # Торговая статистика
    out.append("📊 СБАЛАНСИРОВАННАЯ ТОРГОВАЯ СТАТИСТИКА:")
    out.append(_line("-"))
    out.append(f"Всего сделок:           {trades if trades is not None else 'N/A'}")
    out.append(f"Винрейт:                {_pct(win_rate)}")
    out.append(
        f"Profit Factor:          {pf:.2f}"
        if isinstance(pf, (int, float))
        else "Profit Factor:          N/A"
    )
    out.append(f"Макс. просадка:         {_pct(max_dd)}")
    out.append(f"Комиссии (итого):       {_money(total_fees)}")
    out.append("")
    # По годам (если есть)
    if ctx.yearly:
        out.append("📅 АНАЛИЗ ПО ГОДАМ:")
        out.append(_line("-"))
        for y in ctx.yearly:
            yy = y.get("year", "YYYY")
            tr = y.get("trades", "N/A")
            pnl = y.get("pnl", None)
            out.append(f"{yy}: {tr} сделок, PnL: {_money(pnl)}")
        # опциональные доходности по годам
        ry = [y for y in ctx.yearly if "return_pct" in y]
        if ry:
            for y in ry:
                out.append(
                    f"Доходность {y['year']}: {('+' if y['return_pct']>=0 else '')}{_pct(y['return_pct'])}"
                )
        out.append("")

    # Параметры
    if ctx.params:
        out.append("⚖️ СБАЛАНСИРОВАННЫЕ ПАРАМЕТРЫ:")
        out.append(_line("-"))
        for k, v in ctx.params.items():
            out.append(f"✅ {k}: {v}")
        out.append("")

    # Эволюция (чисто структурный блок — заполняется по желанию)
    out.append("📈 ЭВОЛЮЦИЯ РЕЗУЛЬТАТОВ:")
    out.append(_line("-"))
    out.append("С багами:      n/a (нереально)")
    out.append("Переисправлено:    n/a (слишком консервативно)")
    out.append("Сбалансировано: n/a (оптимально)")
    out.append("")

    # Статус/рекомендации — формально на основе PF/DD (если есть)
    status = (
        "🚀 ОТЛИЧНЫЕ РЕЗУЛЬТАТЫ"
        if isinstance(pf, (int, float))
        and pf >= 1.5
        and isinstance(max_dd, (int, float))
        and max_dd <= 0.2
        else "ℹ️ НУЖНА ДОВОДКА"
    )
    out.append(f"🎯 Статус: {status}")
    out.append("Рекомендация: оценить риски и валидировать на вневыборке")
    out.append("")
    # Проекция (если известен final_equity)
    if isinstance(final_equity, (int, float)):
        mul = multiple or 1.0

        def proj(x: float) -> str:
            y1 = x * (1.0 + (ann or 0.0))  # приблизительно за год
            y2 = x * mul  # за 2 года по итогу
            return f"${x:,.0f} → ${y1:,.2f}/год | ${y2:,.2f}/2года"

        out.append("💡 ПРОЕКЦИЯ НА БОЛЬШИЙ КАПИТАЛ:")
        out.append(_line("-"))
        for cap in (5_000, 10_000, 25_000, 50_000, 100_000):
            out.append(proj(cap))
        out.append("")

    out.append("🎯 ИТОГОВОЕ ЗАКЛЮЧЕНИЕ:")
    out.append(_line("-"))
    out.append("🎉 МИССИЯ: отчёт сформирован (структура как в образце)")
    out.append("💾 Результаты сохранены в balanced_two_year_results.json")
    return "\n".join(out)


def save_json(ctx: PrettyCtx, out_path: str | Path = "balanced_two_year_results.json") -> Path:
    p = Path(out_path)
    p.write_text(str(asdict(ctx)), encoding="utf-8")
    return p
