"""Tests for orders API endpoints."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.endpoints.orders import (
    _as_utc,
    _calculate_settlement_totals,
    _is_reservation_expired,
)
from app.core.validation import validate_drawer_session_status


class TestAsUtc:
    """Tests for _as_utc helper function."""

    def test_naive_datetime_gets_utc(self):
        """Naive datetime gets UTC timezone added."""
        naive = datetime(2024, 1, 1, 12, 0, 0)
        result = _as_utc(naive)
        assert result.tzinfo == timezone.utc

    def test_aware_datetime_unchanged(self):
        """Aware datetime is returned unchanged."""
        aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _as_utc(aware)
        assert result == aware


class TestIsReservationExpired:
    """Tests for reservation expiry check."""

    def test_returns_false_for_non_reserved(self):
        """Non-reserved orders return False."""
        order = MagicMock()
        order.reservation_status = "released"
        order.reservation_expires_at = datetime.now(timezone.utc)
        assert _is_reservation_expired(order) is False

    def test_returns_false_for_no_expiry(self):
        """Orders without expiry time return False."""
        order = MagicMock()
        order.reservation_status = "reserved"
        order.reservation_expires_at = None
        assert _is_reservation_expired(order) is False

    def test_returns_true_when_expired(self):
        """Orders past expiry time return True."""
        order = MagicMock()
        order.reservation_status = "reserved"
        order.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert _is_reservation_expired(order) is True

    def test_returns_false_when_not_expired(self):
        """Orders before expiry time return False."""
        order = MagicMock()
        order.reservation_status = "reserved"
        order.reservation_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        assert _is_reservation_expired(order) is False


class TestValidateDrawerSessionStatus:
    """Tests for drawer session validation."""

    def test_no_drawer_session_passes(self):
        """Orders without drawer session pass validation."""
        order = MagicMock()
        order.drawer_session_id = None
        db = MagicMock()
        # Should not raise
        validate_drawer_session_status(db, order, "add payment to")

    def test_closed_drawer_raises(self):
        """Closed drawer sessions raise HTTPException."""
        order = MagicMock()
        order.drawer_session_id = 1
        drawer = MagicMock()
        drawer.status = "closed"

        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = drawer
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            validate_drawer_session_status(db, order, "refund")
        assert exc_info.value.status_code == 400

    def test_open_drawer_passes(self):
        """Open drawer sessions pass validation."""
        order = MagicMock()
        order.drawer_session_id = 1
        drawer = MagicMock()
        drawer.status = "open"

        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = drawer
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        validate_drawer_session_status(db, order, "cancel")  # Should not raise


class TestCalculateSettlementTotals:
    """Tests for payment settlement calculation."""

    def test_zero_payments(self):
        """Orders with no payments calculate correctly."""
        order = MagicMock()
        order.total_amount = Decimal("100.00")
        order.payments = []

        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.scalar.return_value = 0.0
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        paid, change, remaining = _calculate_settlement_totals(db, order)
        assert paid == Decimal("0.00")
        assert change == Decimal("0.00")
        assert remaining == Decimal("100.00")

    def test_partial_payment(self):
        """Partial payments calculate correctly."""
        order = MagicMock()
        order.total_amount = Decimal("100.00")
        payment = MagicMock()
        payment.amount = Decimal("40.00")
        order.payments = [payment]

        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.scalar.return_value = 40.0
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        paid, change, remaining = _calculate_settlement_totals(db, order)
        assert paid == Decimal("40.00")
        assert change == Decimal("0.00")
        assert remaining == Decimal("60.00")

    def test_overpayment(self):
        """Overpayment calculates correct change."""
        order = MagicMock()
        order.total_amount = Decimal("100.00")
        payment = MagicMock()
        payment.amount = Decimal("120.00")
        order.payments = [payment]

        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.scalar.return_value = 120.0
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        paid, change, remaining = _calculate_settlement_totals(db, order)
        assert paid == Decimal("100.00")
        assert change == Decimal("20.00")
        assert remaining == Decimal("0.00")
