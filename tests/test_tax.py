"""Tests for tax calculation logic."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.orders import _get_scope_subtotal, _is_tax_rule_active


class TestIsTaxRuleActive:
    """Tests for tax rule active status check."""

    def test_inactive_rule(self):
        """Inactive rules are not active."""
        rule = MagicMock()
        rule.is_active = False
        rule.starts_at = None
        rule.ends_at = None
        assert _is_tax_rule_active(rule, datetime.now(UTC)) is False

    def test_future_start_date(self):
        """Rules starting in the future are not active."""
        rule = MagicMock()
        rule.is_active = True
        rule.starts_at = datetime.now(UTC) + timedelta(days=1)
        rule.ends_at = None
        assert _is_tax_rule_active(rule, datetime.now(UTC)) is False

    def test_past_end_date(self):
        """Rules ended in the past are not active."""
        rule = MagicMock()
        rule.is_active = True
        rule.starts_at = None
        rule.ends_at = datetime.now(UTC) - timedelta(days=1)
        assert _is_tax_rule_active(rule, datetime.now(UTC)) is False

    def test_active_rule(self):
        """Active rules within date range are active."""
        rule = MagicMock()
        rule.is_active = True
        rule.starts_at = None
        rule.ends_at = None
        assert _is_tax_rule_active(rule, datetime.now(UTC)) is True


class TestGetScopeSubtotal:
    """Tests for scope subtotal calculation."""

    def test_order_scope(self):
        """Order scope sums all line totals."""
        rule = MagicMock()
        rule.tax_scope = "order"

        movement_inputs = [
            {"product_id": 1, "category_id": 1, "line_total": Decimal("10.00")},
            {"product_id": 2, "category_id": 1, "line_total": Decimal("20.00")},
        ]

        result = _get_scope_subtotal(rule, movement_inputs)
        assert result == Decimal("30.00")

    def test_product_scope(self):
        """Product scope sums only matching product lines."""
        rule = MagicMock()
        rule.tax_scope = "product"
        rule.product_id = 1

        movement_inputs = [
            {"product_id": 1, "category_id": 1, "line_total": Decimal("10.00")},
            {"product_id": 2, "category_id": 1, "line_total": Decimal("20.00")},
        ]

        result = _get_scope_subtotal(rule, movement_inputs)
        assert result == Decimal("10.00")

    def test_category_scope(self):
        """Category scope sums only matching category lines."""
        rule = MagicMock()
        rule.tax_scope = "category"
        rule.category_id = 1

        movement_inputs = [
            {"product_id": 1, "category_id": 1, "line_total": Decimal("10.00")},
            {"product_id": 2, "category_id": 2, "line_total": Decimal("20.00")},
            {"product_id": 3, "category_id": 1, "line_total": Decimal("15.00")},
        ]

        result = _get_scope_subtotal(rule, movement_inputs)
        assert result == Decimal("25.00")

    def test_invalid_scope_returns_zero(self):
        """Invalid scope returns zero."""
        rule = MagicMock()
        rule.tax_scope = "invalid"

        movement_inputs = [
            {"product_id": 1, "category_id": 1, "line_total": Decimal("10.00")},
        ]

        result = _get_scope_subtotal(rule, movement_inputs)
        assert result == Decimal("0.00")
