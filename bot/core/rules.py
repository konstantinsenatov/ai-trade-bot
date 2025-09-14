"""Exchange rules helpers."""


def round_price(price: float, tick_size: float = 0.01) -> float:
    """Round price to nearest tick size.

    Args:
        price: The price to round.
        tick_size: The minimum price movement (default is 0.01).

    Returns:
        The rounded price.
    """
    return round(price / tick_size) * tick_size


def round_qty(quantity: float, step_size: float = 0.01) -> float:
    """Round quantity to nearest step size.

    Args:
        quantity: The quantity to round.
        step_size: The minimum order size (default is 0.01).

    Returns:
        The rounded quantity.
    """
    return round(quantity / step_size) * step_size


def validate_notional(quantity: float, price: float, min_notional: float = 10.0) -> None:
    """Validate that the order's notional meets the minimum requirement.

    Args:
        quantity: The quantity being ordered.
        price: The price of the asset.
        min_notional: The minimum notional value required (default is 10).

    Raises:
        ValueError: If the order's notional is less than the minimum.
    """
    notional = quantity * price
    if notional < min_notional:
        raise ValueError(f"Notional value of {notional} is below minimum required {min_notional}")
