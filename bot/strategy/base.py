"""Base strategy interface."""

from abc import ABC, abstractmethod


class Strategy(ABC):
    """Abstract base strategy class."""

    @abstractmethod
    def on_bar(self, ts: int, o: float, h: float, low: float, c: float, v: int) -> str | None:
        """Process new bar data.

        Args:
            ts: Timestamp
            o: Open price
            h: High price
            low: Low price
            c: Close price
            v: Volume

        Returns:
            'buy', 'sell', or None
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Get strategy name."""
        pass
