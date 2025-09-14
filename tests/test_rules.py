"""Tests for exchange rules."""

import pytest

from bot.core.rules import round_price, round_qty, validate_notional


def test_round_price():
    """Test price rounding to tick size."""
    # Test basic rounding
    assert round_price(100.123, 0.01) == 100.12
    assert round_price(100.126, 0.01) == 100.13

    # Test different tick sizes
    assert abs(round_price(100.123, 0.1) - 100.1) < 1e-10
    assert round_price(100.123, 1.0) == 100.0

    # Test edge cases
    assert round_price(0.0, 0.01) == 0.0
    assert round_price(0.005, 0.01) == 0.0  # 0.005 rounds to 0.0, not 0.01


def test_round_qty():
    """Test quantity rounding to step size."""
    # Test basic rounding
    assert round_qty(1.234, 0.01) == 1.23
    assert round_qty(1.236, 0.01) == 1.24

    # Test different step sizes
    assert abs(round_qty(1.234, 0.1) - 1.2) < 1e-10
    assert round_qty(1.234, 1.0) == 1.0

    # Test edge cases
    assert round_qty(0.0, 0.01) == 0.0
    assert round_qty(0.005, 0.01) == 0.0  # 0.005 rounds to 0.0, not 0.01


def test_validate_notional():
    """Test notional validation."""
    # Test valid notional
    validate_notional(1.0, 10.0, 10.0)  # Should not raise

    # Test invalid notional
    with pytest.raises(ValueError, match="Notional value of 5.0 is below minimum required 10.0"):
        validate_notional(0.5, 10.0, 10.0)

    # Test edge case - exactly at minimum
    validate_notional(1.0, 10.0, 10.0)  # Should not raise

    # Test with different minimum
    validate_notional(1.0, 5.0, 5.0)  # Should not raise
    with pytest.raises(ValueError):
        validate_notional(1.0, 4.0, 5.0)


def test_round_price_default_tick_size():
    """Test price rounding with default tick size."""
    assert round_price(100.123) == 100.12
    assert round_price(100.126) == 100.13


def test_round_qty_default_step_size():
    """Test quantity rounding with default step size."""
    assert round_qty(1.234) == 1.23
    assert round_qty(1.236) == 1.24


def test_validate_notional_default_minimum():
    """Test notional validation with default minimum."""
    validate_notional(1.0, 10.0)  # Should not raise
    with pytest.raises(ValueError):
        validate_notional(1.0, 5.0)  # Below default minimum of 10.0
