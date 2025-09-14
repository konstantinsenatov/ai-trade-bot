import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.core.risk import apply_stop_loss_take_profit, calculate_position_size


def test_position_size_calculation():
    size = calculate_position_size(
        account_balance=1000, risk_per_trade=0.01, entry_price=123.45, stop_loss_price=122.0
    )
    # Calculate expected: 1000 * 0.01 / (123.45 - 122.0) = 10 / 1.45 = 6.896...
    expected = 1000 * 0.01 / (123.45 - 122.0)
    assert abs(size - expected) < 1e-6


def test_apply_sl_tp_basic():
    sl_tp = apply_stop_loss_take_profit(
        entry_price=100.0, side="buy", stop_loss_pct=0.02, take_profit_pct=0.04
    )
    assert sl_tp["stop_loss"] == 98.0
    assert sl_tp["take_profit"] == 104.0
