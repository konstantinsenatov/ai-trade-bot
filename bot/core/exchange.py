"""Exchange interfaces and paper trading implementation."""

from dataclasses import dataclass
from typing import Literal, Protocol

from bot.core.rules import round_price, round_qty, validate_notional

Side = Literal["buy", "sell"]


@dataclass
class Order:
    """Order representation."""

    side: Side
    quantity: float
    price: float
    timestamp: int


@dataclass
class Fill:
    """Order fill representation."""

    order: Order
    quantity: float
    price: float
    fee: float
    timestamp: int


@dataclass
class Position:
    """Position representation."""

    quantity: float  # Positive for long, negative for short, 0 for flat
    avg_price: float
    unrealized_pnl: float = 0.0


@dataclass
class ExecutionResult:
    """Order execution result."""

    success: bool
    fill: Fill | None = None
    error: str | None = None


class Exchange(Protocol):
    """Exchange interface."""

    def market_order(
        self, side: Side, quantity: float, price: float, timestamp: int
    ) -> ExecutionResult:
        """Execute market order."""
        ...


class PaperExchange:
    """Paper trading exchange simulator."""

    def __init__(self, taker_fee: float = 0.001):
        """Initialize paper exchange.

        Args:
            taker_fee: Taker fee rate (default: 0.1%)
        """
        self.taker_fee = taker_fee
        self.position = Position(quantity=0.0, avg_price=0.0)
        self.fills: list[Fill] = []
        self.balance = 10000.0  # Starting balance

    def market_order(
        self, side: Side, quantity: float, price: float, timestamp: int
    ) -> ExecutionResult:
        """Execute market order.

        Args:
            side: Order side ('buy' or 'sell')
            quantity: Order quantity
            price: Execution price
            timestamp: Order timestamp

        Returns:
            Execution result
        """
        # Apply exchange rules: rounding and validation
        try:
            validate_notional(quantity, price)
            quantity = round_qty(quantity)
            price = round_price(price)
        except ValueError as e:
            return ExecutionResult(success=False, error=str(e))

        if quantity <= 0:
            return ExecutionResult(success=False, error="Invalid quantity")

        if side == "buy":
            cost = quantity * price
            fee = cost * self.taker_fee
            total_cost = cost + fee

            if total_cost > self.balance:
                return ExecutionResult(success=False, error="Insufficient balance")

            # Update position
            if self.position.quantity == 0:
                # Opening long position
                self.position.quantity = quantity
                self.position.avg_price = price
            else:
                # Adding to long position
                total_qty = self.position.quantity + quantity
                total_cost_basis = self.position.quantity * self.position.avg_price + cost
                self.position.quantity = total_qty
                self.position.avg_price = total_cost_basis / total_qty

            self.balance -= total_cost

        else:  # sell
            if self.position.quantity == 0:
                return ExecutionResult(success=False, error="No position to sell")

            if quantity > self.position.quantity:
                return ExecutionResult(success=False, error="Insufficient position")

            # Close position
            proceeds = quantity * price
            fee = proceeds * self.taker_fee
            net_proceeds = proceeds - fee

            self.position.quantity -= quantity
            self.balance += net_proceeds

        # Create fill
        order = Order(side=side, quantity=quantity, price=price, timestamp=timestamp)
        fee = quantity * price * self.taker_fee
        fill = Fill(order=order, quantity=quantity, price=price, fee=fee, timestamp=timestamp)
        self.fills.append(fill)

        return ExecutionResult(success=True, fill=fill)

    def get_pnl(self, current_price: float) -> float:
        """Calculate current PnL.

        Args:
            current_price: Current market price

        Returns:
            Total PnL (realized + unrealized)
        """
        realized_pnl = sum(
            fill.order.side == "sell" and fill.price - self.position.avg_price
            for fill in self.fills
            if fill.order.side == "sell"
        )

        unrealized_pnl = (
            (current_price - self.position.avg_price) * self.position.quantity
            if self.position.quantity > 0
            else 0.0
        )

        return realized_pnl + unrealized_pnl

    def get_total_fees(self) -> float:
        """Get total fees paid."""
        return sum(fill.fee for fill in self.fills)
