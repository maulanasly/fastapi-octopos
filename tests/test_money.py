"""Tests for money utility functions."""

from decimal import Decimal

import pytest

from app.core.money import money_to_float, quantize_money, to_decimal

pytestmark = pytest.mark.no_db


class TestToDecimal:
    """Tests for to_decimal function."""

    def test_float_conversion(self):
        """Float values are correctly converted to Decimal."""
        result = to_decimal(10.5)
        assert result == Decimal("10.5")

    def test_string_conversion(self):
        """String values are correctly converted to Decimal."""
        result = to_decimal("10.5")
        assert result == Decimal("10.5")

    def test_int_conversion(self):
        """Integer values are correctly converted to Decimal."""
        result = to_decimal(10)
        assert result == Decimal("10")

    def test_decimal_passthrough(self):
        """Decimal values are returned unchanged."""
        original = Decimal("10.123")
        result = to_decimal(original)
        assert result == original

    def test_none_returns_default(self):
        """None returns the default value."""
        result = to_decimal(None)
        assert result == Decimal("0")

    def test_none_returns_custom_default(self):
        """None returns custom default value."""
        result = to_decimal(None, default="5.55")
        assert result == Decimal("5.55")


class TestQuantizeMoney:
    """Tests for quantize_money function."""

    def test_rounds_to_two_decimals(self):
        """Values are rounded to 2 decimal places (half up)."""
        result = quantize_money("10.125")
        assert result == Decimal("10.13")

    def test_rounds_down(self):
        """Values are correctly quantized."""
        result = quantize_money("10.126")
        assert result == Decimal("10.13")

    def test_handles_none(self):
        """None is converted to 0 before quantization."""
        result = quantize_money(None)
        assert result == Decimal("0")

    def test_decimal_input(self):
        """Decimal inputs are properly quantized."""
        result = quantize_money(Decimal("10.555"))
        assert result == Decimal("10.56")

    def test_zero_passthrough(self):
        """Zero values remain as zero."""
        result = quantize_money(0)
        assert result == Decimal("0.00")

    def test_large_values(self):
        """Large monetary values are handled correctly."""
        result = quantize_money(Decimal("999999999999.999"))
        assert result == Decimal("1000000000000.00")


class TestMoneyToFloat:
    """Tests for money_to_float boundary conversion."""

    def test_returns_quantized_float(self):
        """Value is quantized to two decimals before float conversion."""
        assert money_to_float(Decimal("10.005")) == 10.01
        assert money_to_float("3.14159") == 3.14

    def test_none_returns_zero(self):
        """None defaults to zero."""
        assert money_to_float(None) == 0.0

    def test_negative_values(self):
        """Negative amounts round correctly."""
        assert money_to_float("-7.125") == -7.13
