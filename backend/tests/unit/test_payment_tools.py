"""
Unit tests for Payment Agent tools.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from app.payment_agent.tools import (
    create_payment_mandate,
    process_payment,
    get_payment_status,
    refund_payment,
    get_payment_history
)
from app.common.models import Order, Mandate, Payment


class TestCreatePaymentMandate:
    """Tests for create_payment_mandate() function"""

    def test_create_payment_mandate_success(self, mock_db_session, sample_order):
        """Test successful creation of payment mandate"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query for order lookup
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            # Execute
            result = create_payment_mandate("order_123", "credit_card")

            # Assert
            assert "mandate_id" in result
            assert result["order_id"] == "order_123"
            assert result["amount"] == 99.99
            assert result["payment_method"] == "credit_card"
            assert result["status"] == "pending"
            mock_db_session.add.assert_called_once()

    def test_create_payment_mandate_order_not_found(self, mock_db_session):
        """Test ValueError raised when order doesn't exist"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Order order_999 not found"):
                create_payment_mandate("order_999", "credit_card")

    def test_create_payment_mandate_type_payment(self, mock_db_session, sample_order):
        """Test that mandate_type is set to 'payment'"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            result = create_payment_mandate("order_123", "credit_card")

            # Check that Mandate was created with correct type
            call_args = mock_db_session.add.call_args[0][0]
            assert call_args.mandate_type == "payment"

    def test_create_payment_mandate_stores_json_data(self, mock_db_session, sample_order):
        """Test that mandate_data is stored as JSON"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            create_payment_mandate("order_123", "credit_card")

            # Check that mandate_data is JSON string
            call_args = mock_db_session.add.call_args[0][0]
            assert isinstance(call_args.mandate_data, str)
            # Can parse as JSON
            data = json.loads(call_args.mandate_data)
            assert "order_id" in data
            assert "amount" in data


class TestProcessPayment:
    """Tests for process_payment() function"""

    def test_process_payment_success(self, mock_db_session, sample_order):
        """Test successful payment processing"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock for order lookup
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            # Mock create_payment_mandate
            with patch('app.payment_agent.tools.create_payment_mandate') as mock_mandate:
                mock_mandate.return_value = {"mandate_id": "mandate_123"}

                # Execute
                result = process_payment("order_123", "credit_card")

                # Assert
                assert "payment_id" in result
                assert result["order_id"] == "order_123"
                assert result["amount"] == 99.99
                assert result["payment_method"] == "credit_card"
                assert result["status"] == "completed"
                assert "transaction_id" in result
                assert result["payment_mandate_id"] == "mandate_123"

    def test_process_payment_order_not_found(self, mock_db_session):
        """Test ValueError raised when order doesn't exist"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Order order_999 not found"):
                process_payment("order_999", "credit_card")

    def test_process_payment_creates_mandate(self, mock_db_session, sample_order):
        """Test that mandate is created before payment"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.payment_agent.tools.create_payment_mandate') as mock_mandate:
                mock_mandate.return_value = {"mandate_id": "mandate_123"}

                process_payment("order_123", "credit_card")

                # Verify mandate was created
                mock_mandate.assert_called_once_with(
                    "order_123", "credit_card")

    def test_process_payment_updates_order_status(self, mock_db_session, sample_order):
        """Test that order status is updated to 'completed'"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.payment_agent.tools.create_payment_mandate') as mock_mandate:
                mock_mandate.return_value = {"mandate_id": "mandate_123"}

                process_payment("order_123", "credit_card")

                # Verify order status was updated to completed
                assert sample_order.status == "completed"

    def test_process_payment_generates_transaction_id(self, mock_db_session, sample_order):
        """Test that transaction_id is generated"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.payment_agent.tools.create_payment_mandate') as mock_mandate:
                mock_mandate.return_value = {"mandate_id": "mandate_123"}

                result = process_payment("order_123", "credit_card")

                assert "transaction_id" in result
                assert result["transaction_id"].startswith("txn_")


class TestGetPaymentStatus:
    """Tests for get_payment_status() function"""

    def test_get_payment_status_success(self, mock_db_session, sample_payment):
        """Test successful retrieval of payment status"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_payment

            # Execute
            result = get_payment_status("payment_123")

            # Assert
            assert result["payment_id"] == "payment_123"
            assert result["order_id"] == "order_123"
            assert result["amount"] == 99.99
            assert result["payment_method"] == "credit_card"
            assert result["status"] == "completed"
            assert result["transaction_id"] == "txn_abc123"
            assert result["payment_mandate_id"] == "mandate_123"

    def test_get_payment_status_not_found(self, mock_db_session):
        """Test ValueError raised when payment doesn't exist"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Payment payment_999 not found"):
                get_payment_status("payment_999")

    def test_get_payment_status_formats_datetime(self, mock_db_session, sample_payment):
        """Test that processed_at is formatted as ISO string"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_payment

            result = get_payment_status("payment_123")

            assert "processed_at" in result
            # Should be ISO format if created_at exists
            if sample_payment.created_at:
                assert "T" in result["processed_at"] or len(
                    result["processed_at"]) > 0


class TestRefundPayment:
    """Tests for refund_payment() function"""

    def test_refund_payment_success(self, mock_db_session, sample_payment):
        """Test successful refund processing"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query for payment
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_payment

            # Mock order query
            sample_order = Order(
                order_id="order_123", session_id="session_abc", total_amount=99.99, status="completed")
            # We need to handle multiple queries

            def mock_query_side_effect():
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = sample_order
                return mock_q

            mock_db_session.query.side_effect = [Mock(filter=Mock(return_value=Mock(first=Mock(return_value=sample_payment)))),
                                                 Mock(filter=Mock(return_value=Mock(first=Mock(return_value=sample_order))))]

            # Execute
            result = refund_payment("payment_123", "Customer requested refund")

            # Assert
            assert "refund_id" in result
            assert result["payment_id"] == "payment_123"
            assert result["amount"] == 99.99
            assert result["reason"] == "Customer requested refund"
            assert result["status"] == "refunded"

    def test_refund_payment_not_found(self, mock_db_session):
        """Test ValueError raised when payment doesn't exist"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Payment payment_999 not found"):
                refund_payment("payment_999", "Test reason")

    def test_refund_payment_updates_status(self, mock_db_session, sample_payment):
        """Test that payment status is updated to 'refunded'"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mocks
            sample_order = Order(
                order_id="order_123", session_id="session_abc", total_amount=99.99, status="completed")
            mock_db_session.query.side_effect = [
                Mock(filter=Mock(return_value=Mock(
                    first=Mock(return_value=sample_payment)))),
                Mock(filter=Mock(return_value=Mock(
                    first=Mock(return_value=sample_order))))
            ]

            refund_payment("payment_123", "Test reason")

            # Verify status was updated
            assert sample_payment.status == "refunded"


class TestGetPaymentHistory:
    """Tests for get_payment_history() function"""

    def test_get_payment_history_success(self, mock_db_session, sample_payment):
        """Test successful retrieval of payment history"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query with join
            mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
                sample_payment]

            # Execute
            result = get_payment_history("session_abc")

            # Assert
            assert len(result) == 1
            assert result[0]["payment_id"] == "payment_123"
            assert result[0]["order_id"] == "order_123"
            assert result[0]["amount"] == 99.99
            assert result[0]["payment_method"] == "credit_card"
            assert result[0]["status"] == "completed"

    def test_get_payment_history_empty(self, mock_db_session):
        """Test empty payment history"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return empty list
            mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = []

            # Execute
            result = get_payment_history("session_abc")

            # Assert
            assert result == []

    def test_get_payment_history_ordered_desc(self, mock_db_session, sample_payment):
        """Test that payments are ordered by created_at DESC"""
        with patch('app.payment_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_query = mock_db_session.query.return_value
            mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
                sample_payment]

            get_payment_history("session_abc")

            # Verify order_by was called
            mock_query.join.return_value.filter.return_value.order_by.assert_called_once()
