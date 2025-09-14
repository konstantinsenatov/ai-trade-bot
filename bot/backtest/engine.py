"""Backtesting engine."""

from typing import Any

from bot.core.exchange import PaperExchange
from bot.data.ohlcv_source import OHLCVBar
from bot.strategy.base import Strategy


def run_backtest(
    prices: list[OHLCVBar],
    strategy: Strategy,
    fee: float = 0.001,
) -> tuple[dict[str, Any], list[float]]:
    """Run backtest on historical data.

    Args:
        prices: List of OHLCV bars
        strategy: Trading strategy
        fee: Trading fee rate

    Returns:
        Tuple of (metrics dict, equity curve)
    """
    exchange = PaperExchange(taker_fee=fee)
    equity_curve = []
    trades: list[dict[str, Any]] = []

    initial_balance = exchange.balance

    for ts, o, h, low, c, v in prices:
        # Get strategy signal
        signal = strategy.on_bar(ts, o, h, low, c, v)

        # Execute trades at close price
        if signal == "buy" and exchange.position.quantity == 0:
            # Buy signal - go long
            quantity = 1.0  # Simple position sizing
            result = exchange.market_order("buy", quantity, c, ts)
            if result.success:
                trades.append(
                    {
                        "timestamp": ts,
                        "side": "buy",
                        "price": c,
                        "quantity": quantity,
                    }
                )

        elif signal == "sell" and exchange.position.quantity > 0:
            # Sell signal - close long position
            quantity = exchange.position.quantity
            result = exchange.market_order("sell", quantity, c, ts)
            if result.success:
                trades.append(
                    {
                        "timestamp": ts,
                        "side": "sell",
                        "price": c,
                        "quantity": quantity,
                    }
                )

        # Calculate current equity
        current_equity = exchange.balance + exchange.position.quantity * c
        equity_curve.append(current_equity)

    # Calculate metrics
    final_equity = equity_curve[-1] if equity_curve else initial_balance
    gross_pnl = final_equity - initial_balance
    total_fees = exchange.get_total_fees()
    net_pnl = gross_pnl - total_fees

    # Calculate win rate
    winning_trades = 0
    total_trades = len(trades) // 2  # Each trade has buy and sell

    for i in range(0, len(trades) - 1, 2):
        if i + 1 < len(trades):
            buy_trade = trades[i]
            sell_trade = trades[i + 1]
            if sell_trade["price"] > buy_trade["price"]:
                winning_trades += 1

    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

    # Calculate max drawdown
    max_dd = 0.0
    peak = initial_balance
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak
        max_dd = max(max_dd, drawdown)

    metrics = {
        "trades": len(trades),
        "gross_pnl": gross_pnl,
        "total_fees": total_fees,
        "net_pnl": net_pnl,
        "win_rate": win_rate,
        "max_dd": max_dd,
        "initial_balance": initial_balance,
        "final_equity": final_equity,
        "return_pct": (final_equity - initial_balance) / initial_balance * 100,
    }

    return metrics, equity_curve


def run_backtest_onebar(
    bars: list[OHLCVBar],
    strategy: Strategy,
    fee: float = 0.001,
) -> tuple[dict[str, Any], list[float]]:
    """Run one-bar backtest on historical data.

    In one-bar mode, signals are calculated using history < t (no look-ahead).
    If signal == "buy": enter at open[t], exit at close[t] of same bar.
    Commission is calculated both ways.

    Args:
        bars: List of OHLCV bars
        strategy: Trading strategy with signal() method
        fee: Trading fee rate

    Returns:
        Tuple of (metrics dict, equity curve)
    """
    equity_curve = [1000.0]  # Starting equity
    trades: list[dict[str, Any]] = []

    for t in range(1, len(bars)):
        # Get signal using history < t (no look-ahead)
        # Handle both tuple and OHLCVBar formats
        history = []
        for bar in bars[:t]:
            if isinstance(bar, tuple):
                history.append(bar)  # Already in correct format
            else:
                history.append((bar.timestamp, bar.open, bar.high, bar.low, bar.close))

        signal = strategy.signal(history)  # type: ignore

        if signal == "buy":
            # Enter at open[t], exit at close[t]
            current_bar = bars[t]
            if isinstance(current_bar, tuple):
                entry_price = current_bar[1]  # open
                exit_price = current_bar[4]  # close
            else:
                entry_price = current_bar.open
                exit_price = current_bar.close

            # Calculate PnL with commission both ways
            pnl = (exit_price - entry_price) / entry_price
            commission_cost = fee * 2  # Entry + exit
            net_pnl = pnl - commission_cost

            # Update equity
            new_equity = equity_curve[-1] * (1 + net_pnl)
            equity_curve.append(new_equity)

            trades.append(
                {
                    "timestamp": (
                        current_bar[0] if isinstance(current_bar, tuple) else current_bar.timestamp
                    ),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "net_pnl": net_pnl,
                    "commission": commission_cost,
                }
            )
        else:
            # No trade, equity stays same
            equity_curve.append(equity_curve[-1])

    # Calculate metrics
    if not trades:
        return {
            "trades": 0,
            "final_equity": equity_curve[-1],
            "pf": 0.0,
            "max_dd": 0.0,
        }, equity_curve

    # Profit Factor calculation
    profit_trades = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    loss_trades = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]

    profit_sum = sum(profit_trades) if profit_trades else 0
    loss_sum = abs(sum(loss_trades)) if loss_trades else 0

    pf = profit_sum / loss_sum if loss_sum > 0 else float("inf") if profit_sum > 0 else 0

    # Max drawdown
    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd

    metrics = {
        "trades": len(trades),
        "final_equity": equity_curve[-1],
        "pf": pf,
        "max_dd": max_dd,
    }

    return metrics, equity_curve
