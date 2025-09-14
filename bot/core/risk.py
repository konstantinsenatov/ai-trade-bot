"""Risk management wrappers."""


def calculate_position_size(
    account_balance: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """Calculate position size based on risk management.

    Args:
        account_balance: Account balance
        risk_per_trade: Risk per trade as fraction (e.g., 0.02 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price

    Returns:
        Position size
    """
    # Simple position sizing: risk amount / price difference
    risk_amount = account_balance * risk_per_trade
    price_diff = abs(entry_price - stop_loss_price)
    return risk_amount / price_diff if price_diff > 0 else 0.0


def apply_stop_loss_take_profit(
    entry_price: float,
    side: str,
    stop_loss_pct: float = 0.02,
    take_profit_pct: float = 0.04,
) -> dict[str, float]:
    """Apply stop loss and take profit levels.

    Args:
        entry_price: Entry price
        side: Trade side ('buy' or 'sell')
        stop_loss_pct: Stop loss percentage
        take_profit_pct: Take profit percentage

    Returns:
        Dictionary with stop_loss and take_profit prices
    """
    if side == "buy":
        stop_loss = entry_price * (1 - stop_loss_pct)
        take_profit = entry_price * (1 + take_profit_pct)
    else:  # sell
        stop_loss = entry_price * (1 + stop_loss_pct)
        take_profit = entry_price * (1 - take_profit_pct)

    return {"stop_loss": stop_loss, "take_profit": take_profit}
