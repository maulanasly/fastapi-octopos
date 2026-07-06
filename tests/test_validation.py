"""Tests for shared validation helpers."""
from datetime import timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.validation import validate_drawer_session_status


class TestValidateDrawerSessionStatus:
    """Tests for drawer session validation helper."""

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
        assert "refund" in exc_info.value.detail.lower()

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

    def test_error_message_includes_action(self):
        """Error message includes the action description."""
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
            validate_drawer_session_status(db, order, "process refund on")
        assert "process refund on" in exc_info.value.detail
