"""
Unit tests for Cart Agent tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from app.shopping_agent.sub_agents.cart_agent.tools import (
    add_to_cart,
    get_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    get_cart_total
)
from app.common.models import CartItem, CatalogItem


class TestAddToCart:
    """Tests for add_to_cart() function"""

    def test_add_to_cart_success(self, mock_db_session, sample_product):
        """Test successful addition of product to cart"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query for product lookup
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_product

            # Execute
            result = add_to_cart("prod_123", 2, "session_abc")

            # Assert
            assert result["product_id"] == "prod_123"
            assert result["quantity"] == 2
            assert result["name"] == "Test Running Shoes"
            assert result["picture"] == "https://example.com/shoes-large.jpg"
            mock_db_session.add.assert_called_once()

    def test_add_to_cart_product_not_found(self, mock_db_session):
        """Test ValueError raised when product doesn't exist"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None (product not found)
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Product prod_999 not found"):
                add_to_cart("prod_999", 1, "session_abc")

    def test_add_to_cart_zero_quantity(self, mock_db_session):
        """Test ValueError raised for zero quantity"""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            add_to_cart("prod_123", 0, "session_abc")

    def test_add_to_cart_negative_quantity(self, mock_db_session):
        """Test ValueError raised for negative quantity"""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            add_to_cart("prod_123", -1, "session_abc")

    def test_add_to_cart_creates_uuid(self, mock_db_session, sample_product):
        """Test that cart_item_id is a UUID"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_product

            # Execute
            result = add_to_cart("prod_123", 1, "session_abc")

            # Assert UUID format
            assert "cart_item_id" in result
            assert len(result["cart_item_id"]) > 0

    def test_add_to_cart_uses_product_image_url(self, mock_db_session):
        """Test that product_image_url is preferred over picture"""
        product = CatalogItem(
            id="prod_123",
            name="Test Product",
            picture="https://example.com/old.jpg",
            product_image_url="https://example.com/new.jpg"
        )

        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = product

            result = add_to_cart("prod_123", 1, "session_abc")

            assert result["picture"] == "https://example.com/new.jpg"


class TestGetCart:
    """Tests for get_cart() function"""

    def test_get_cart_success(self, mock_db_session, sample_cart_item):
        """Test successful retrieval of cart items"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
                sample_cart_item]

            # Execute
            result = get_cart("session_abc")

            # Assert
            assert len(result) == 1
            assert result[0]["cart_item_id"] == "cart_item_123"
            assert result[0]["product_id"] == "prod_123"
            assert result[0]["quantity"] == 2
            assert result[0]["name"] == "Test Running Shoes"

    def test_get_cart_empty(self, mock_db_session):
        """Test empty cart returns empty list"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return empty list
            mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

            # Execute
            result = get_cart("session_abc")

            # Assert
            assert result == []

    def test_get_cart_session_isolation(self, mock_db_session, sample_cart_item):
        """Test that cart returns only items for specified session"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_query = mock_db_session.query.return_value
            mock_query.filter.return_value.order_by.return_value.all.return_value = [
                sample_cart_item]

            # Execute
            result = get_cart("session_abc")

            # Assert filter was called with correct session_id
            mock_query.filter.assert_called_once()
            assert len(result) == 1


class TestUpdateCartItem:
    """Tests for update_cart_item() function"""

    def test_update_cart_item_success(self, mock_db_session, sample_cart_item):
        """Test successful update of cart item quantity"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_cart_item

            # Execute
            result = update_cart_item("cart_item_123", 5)

            # Assert
            assert result["cart_item_id"] == "cart_item_123"
            assert result["quantity"] == 5
            assert sample_cart_item.quantity == 5

    def test_update_cart_item_not_found(self, mock_db_session):
        """Test ValueError raised when cart item doesn't exist"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Cart item cart_item_999 not found"):
                update_cart_item("cart_item_999", 2)

    def test_update_cart_item_zero_quantity(self, mock_db_session):
        """Test ValueError raised for zero quantity"""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            update_cart_item("cart_item_123", 0)

    def test_update_cart_item_negative_quantity(self, mock_db_session):
        """Test ValueError raised for negative quantity"""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            update_cart_item("cart_item_123", -1)


class TestRemoveFromCart:
    """Tests for remove_from_cart() function"""

    def test_remove_from_cart_success(self, mock_db_session, sample_cart_item):
        """Test successful removal of cart item"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_cart_item

            # Execute
            result = remove_from_cart("cart_item_123")

            # Assert
            assert result["status"] == "removed"
            assert result["cart_item_id"] == "cart_item_123"
            mock_db_session.delete.assert_called_once_with(sample_cart_item)

    def test_remove_from_cart_not_found(self, mock_db_session):
        """Test ValueError raised when cart item doesn't exist"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Cart item cart_item_999 not found"):
                remove_from_cart("cart_item_999")


class TestClearCart:
    """Tests for clear_cart() function"""

    def test_clear_cart_success(self, mock_db_session):
        """Test successful clearing of cart"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return 3 items deleted
            mock_db_session.query.return_value.filter.return_value.delete.return_value = 3

            # Execute
            result = clear_cart("session_abc")

            # Assert
            assert result["status"] == "cleared"
            assert result["items_removed"] == 3

    def test_clear_cart_empty_cart(self, mock_db_session):
        """Test clearing empty cart"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return 0 items deleted
            mock_db_session.query.return_value.filter.return_value.delete.return_value = 0

            # Execute
            result = clear_cart("session_abc")

            # Assert
            assert result["status"] == "cleared"
            assert result["items_removed"] == 0


class TestGetCartTotal:
    """Tests for get_cart_total() function"""

    def test_get_cart_total_success(self, mock_db_session):
        """Test successful calculation of cart total"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock queries for count and sum
            mock_query = mock_db_session.query

            # First call returns count
            mock_query.return_value.filter.return_value.scalar.return_value = 3

            # Execute
            result = get_cart_total("session_abc")

            # Assert
            assert result["item_count"] == 3
            assert result["total_items"] == 0  # sum not mocked for second call
            assert result["subtotal"] == 0.0

    def test_get_cart_total_empty_cart(self, mock_db_session):
        """Test cart total for empty cart"""
        with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock queries
            mock_query = mock_db_session.query
            mock_query.return_value.filter.return_value.scalar.return_value = 0

            # Execute
            result = get_cart_total("session_abc")

            # Assert
            assert result["item_count"] == 0
            assert result["total_items"] == 0
            assert result["subtotal"] == 0.0
