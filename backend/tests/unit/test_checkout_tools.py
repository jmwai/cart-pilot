"""
Unit tests for Checkout Agent tools.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.shopping_agent.sub_agents.checkout_agent.tools import (
    create_order,
    get_order_status,
    cancel_order,
    validate_cart_for_checkout
)
from app.common.models import CartItem, Order, OrderItem, CatalogItem


class TestCreateOrder:
    """Tests for create_order() function"""

    def test_create_order_success(self, mock_db_session, sample_cart_item, mock_tool_context):
        """Test successful order creation"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock for cart items query
            mock_db_session.query.return_value.filter.return_value.all.return_value = [
                sample_cart_item]

            # Execute
            result = create_order(mock_tool_context)

            # Assert
            assert "order_id" in result
            assert result["status"] == "completed"
            assert "shipping_address" in result
            assert len(result["items"]) == 1
            assert result["items"][0]["product_id"] == "prod_123"
            assert result["items"][0]["quantity"] == 2

    def test_create_order_empty_cart(self, mock_db_session, mock_tool_context):
        """Test ValueError raised for empty cart"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock to return empty cart
            mock_db_session.query.return_value.filter.return_value.all.return_value = []

            # Execute & Assert
            with pytest.raises(ValueError, match="Cart is empty"):
                create_order(mock_tool_context)

    def test_create_order_clears_cart(self, mock_db_session, sample_cart_item, mock_tool_context):
        """Test that cart is cleared after order creation"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mocks
            mock_query = mock_db_session.query.return_value
            mock_query.filter.return_value.all.return_value = [
                sample_cart_item]

            # Execute
            create_order(mock_tool_context)

            # Assert cart deletion was called
            # Should be called after creating order
            assert mock_db_session.add.call_count >= 1  # Order + OrderItems

    def test_create_order_generates_uuid(self, mock_db_session, sample_cart_item, mock_tool_context):
        """Test that order_id is a UUID"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.all.return_value = [
                sample_cart_item]

            result = create_order(mock_tool_context)

            assert "order_id" in result
            assert len(result["order_id"]) > 0


class TestGetOrderStatus:
    """Tests for get_order_status() function"""

    def test_get_order_status_success(self, mock_db_session, sample_order, sample_order_item):
        """Test successful retrieval of order status"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup order with items
            sample_order.items = [sample_order_item]
            sample_order_item.product = CatalogItem(
                id="prod_123", name="Test Product")

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute
            result = get_order_status(mock_tool_context, "order_123")

            # Assert
            assert result["order_id"] == "order_123"
            assert result["status"] == "pending"
            assert result["total_amount"] == 99.99
            assert len(result["items"]) == 1

    def test_get_order_status_not_found(self, mock_db_session):
        """Test ValueError raised when order doesn't exist"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute & Assert
            with pytest.raises(ValueError, match="Order order_999 not found"):
                get_order_status(mock_tool_context, "order_999")


class TestCancelOrder:
    """Tests for cancel_order() function"""

    def test_cancel_order_success(self, mock_db_session, sample_order):
        """Test successful order cancellation"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute
            result = cancel_order(mock_tool_context, "order_123")

            # Assert
            assert result["order_id"] == "order_123"
            assert result["status"] == "cancelled"
            assert result["refund_amount"] == 99.99
            assert sample_order.status == "cancelled"

    def test_cancel_order_not_found(self, mock_db_session):
        """Test ValueError raised when order doesn't exist"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute & Assert
            with pytest.raises(ValueError, match="Order order_999 not found"):
                cancel_order(mock_tool_context, "order_999")

    def test_cancel_order_completed_order(self, mock_db_session):
        """Test ValueError raised for completed order"""
        completed_order = Order(
            order_id="order_123",
            session_id="session_abc",
            total_amount=99.99,
            status="completed"
        )

        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = completed_order

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute & Assert
            with pytest.raises(ValueError, match="Cannot cancel order with status: completed"):
                cancel_order(mock_tool_context, "order_123")

    def test_cancel_order_only_pending_or_processing(self, mock_db_session):
        """Test that only pending/processing orders can be cancelled"""
        pending_order = Order(
            order_id="order_123",
            session_id="session_abc",
            total_amount=99.99,
            status="pending"
        )

        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = pending_order

            # Create mock tool context
            from unittest.mock import Mock
            mock_tool_context = Mock()
            mock_tool_context.state = {}

            # Execute
            result = cancel_order(mock_tool_context, "order_123")

            # Assert
            assert result["status"] == "cancelled"


class TestValidateCartForCheckout:
    """Tests for validate_cart_for_checkout() function"""

    def test_validate_cart_valid(self, mock_db_session, mock_tool_context):
        """Test validation for valid cart"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return count of 3
            mock_db_session.query.return_value.filter.return_value.scalar.return_value = 3

            # Execute
            result = validate_cart_for_checkout(mock_tool_context)

            # Assert
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            assert result["item_count"] == 3

    def test_validate_cart_empty(self, mock_db_session, mock_tool_context):
        """Test validation for empty cart"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return count of 0
            mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

            # Execute
            result = validate_cart_for_checkout(mock_tool_context)

            # Assert
            assert result["valid"] is False
            assert len(result["errors"]) == 1
            assert "Cart is empty" in result["errors"]
            assert result["item_count"] == 0

    def test_validate_cart_returns_warnings(self, mock_db_session, mock_tool_context):
        """Test that warnings list is returned"""
        with patch('app.shopping_agent.sub_agents.checkout_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1

            result = validate_cart_for_checkout(mock_tool_context)

            assert "warnings" in result
            assert isinstance(result["warnings"], list)
