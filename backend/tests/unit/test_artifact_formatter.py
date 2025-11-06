"""
Unit tests for ArtifactFormatter.
"""
import pytest

from app.utils.artifact_formatter import ArtifactFormatter


class TestFormatProducts:
    """Tests for format_products() method"""

    def test_format_products_basic(self):
        """Test basic product formatting"""
        products = [
            {
                "id": "prod_123",
                "name": "Test Product",
                "description": "A test product",
                "price_usd_units": 29.99,
                "product_image_url": "https://example.com/image.jpg",
                "distance": 0.5
            }
        ]
        result = ArtifactFormatter.format_products(products)

        assert len(result) == 1
        assert result[0]["id"] == "prod_123"
        assert result[0]["name"] == "Test Product"
        assert result[0]["price"] == 29.99
        assert result[0]["image_url"] == "https://example.com/image.jpg"
        assert result[0]["distance"] == 0.5

    def test_format_products_uses_picture_fallback(self):
        """Test that picture is used when product_image_url is missing"""
        products = [
            {
                "id": "prod_123",
                "name": "Test Product",
                "picture": "https://example.com/picture.jpg",
                "price_usd_units": 19.99
            }
        ]
        result = ArtifactFormatter.format_products(products)

        assert result[0]["image_url"] == "https://example.com/picture.jpg"

    def test_format_products_empty_image_url(self):
        """Test that empty string is used when no image available"""
        products = [
            {
                "id": "prod_123",
                "name": "Test Product",
                "price_usd_units": 19.99
            }
        ]
        result = ArtifactFormatter.format_products(products)

        assert result[0]["image_url"] == ""

    def test_format_products_no_price(self):
        """Test that price defaults to 0.0 when price_usd_units is missing"""
        products = [
            {
                "id": "prod_123",
                "name": "Test Product"
            }
        ]
        result = ArtifactFormatter.format_products(products)

        assert result[0]["price"] == 0.0
        assert result[0]["price_usd_units"] is None

    def test_format_products_multiple(self):
        """Test formatting multiple products"""
        products = [
            {"id": "prod_1", "name": "Product 1", "price_usd_units": 10.0},
            {"id": "prod_2", "name": "Product 2", "price_usd_units": 20.0}
        ]
        result = ArtifactFormatter.format_products(products)

        assert len(result) == 2
        assert result[0]["id"] == "prod_1"
        assert result[1]["id"] == "prod_2"

    def test_format_products_empty_list(self):
        """Test formatting empty product list"""
        result = ArtifactFormatter.format_products([])
        assert result == []


class TestFormatCart:
    """Tests for format_cart() method"""

    def test_format_cart_with_cart_key(self):
        """Test formatting cart from 'cart' key"""
        cart_state = {
            "cart": [
                {"cart_item_id": "item_1", "subtotal": 10.0},
                {"cart_item_id": "item_2", "subtotal": 20.0}
            ]
        }
        result = ArtifactFormatter.format_cart(cart_state)

        assert result is not None
        assert result["type"] == "cart"
        assert len(result["items"]) == 2
        assert result["total_items"] == 2
        assert result["subtotal"] == 30.0

    def test_format_cart_with_cart_items_key(self):
        """Test formatting cart from 'cart_items' key"""
        cart_state = {
            "cart_items": [
                {"cart_item_id": "item_1", "subtotal": 15.0}
            ]
        }
        result = ArtifactFormatter.format_cart(cart_state)

        assert result is not None
        assert result["type"] == "cart"
        assert len(result["items"]) == 1
        assert result["subtotal"] == 15.0

    def test_format_cart_empty(self):
        """Test that None is returned for empty cart"""
        cart_state = {"cart": []}
        result = ArtifactFormatter.format_cart(cart_state)
        assert result is None

    def test_format_cart_missing(self):
        """Test that None is returned when cart is missing"""
        cart_state = {}
        result = ArtifactFormatter.format_cart(cart_state)
        assert result is None

    def test_format_cart_invalid_type(self):
        """Test that None is returned for invalid cart type"""
        cart_state = {"cart": "not a list"}
        result = ArtifactFormatter.format_cart(cart_state)
        assert result is None


class TestFormatOrderSummary:
    """Tests for format_order_summary() method"""

    def test_format_order_summary_success(self):
        """Test successful order summary formatting"""
        summary_state = {
            "pending_order_summary": {
                "items": [{"product_id": "prod_1", "quantity": 2}],
                "total_amount": 50.0,
                "shipping_address": "123 Main St",
                "item_count": 1
            }
        }
        result = ArtifactFormatter.format_order_summary(summary_state)

        assert result is not None
        assert result["type"] == "order_summary"
        assert result["total_amount"] == 50.0
        assert result["shipping_address"] == "123 Main St"
        assert result["item_count"] == 1

    def test_format_order_summary_missing(self):
        """Test that None is returned when summary is missing"""
        summary_state = {}
        result = ArtifactFormatter.format_order_summary(summary_state)
        assert result is None

    def test_format_order_summary_none(self):
        """Test that None is returned when summary is None"""
        summary_state = {"pending_order_summary": None}
        result = ArtifactFormatter.format_order_summary(summary_state)
        assert result is None

    def test_format_order_summary_invalid_type(self):
        """Test that None is returned for invalid summary type"""
        summary_state = {"pending_order_summary": "not a dict"}
        result = ArtifactFormatter.format_order_summary(summary_state)
        assert result is None

    def test_format_order_summary_defaults(self):
        """Test that defaults are used for missing fields"""
        summary_state = {
            "pending_order_summary": {}
        }
        result = ArtifactFormatter.format_order_summary(summary_state)

        assert result is not None
        assert result["items"] == []
        assert result["total_amount"] == 0.0
        assert result["shipping_address"] == ""
        assert result["item_count"] == 0


class TestFormatOrder:
    """Tests for format_order() method"""

    def test_format_order_success(self):
        """Test successful order formatting"""
        order_state = {
            "current_order": {
                "order_id": "order_123",
                "status": "completed",
                "items": [{"product_id": "prod_1"}],
                "total_amount": 100.0,
                "shipping_address": "456 Oak Ave",
                "created_at": "2024-01-01T00:00:00"
            }
        }
        result = ArtifactFormatter.format_order(order_state)

        assert result is not None
        assert result["type"] == "order"
        assert result["order_id"] == "order_123"
        assert result["status"] == "completed"
        assert result["total_amount"] == 100.0

    def test_format_order_missing(self):
        """Test that None is returned when order is missing"""
        order_state = {}
        result = ArtifactFormatter.format_order(order_state)
        assert result is None

    def test_format_order_defaults(self):
        """Test that defaults are used for missing fields"""
        order_state = {
            "current_order": {"order_id": "order_123"}
        }
        result = ArtifactFormatter.format_order(order_state)

        assert result is not None
        assert result["status"] == ""
        assert result["items"] == []
        assert result["total_amount"] == 0.0


class TestFormatPaymentMethods:
    """Tests for format_payment_methods() method"""

    def test_format_payment_methods_success(self):
        """Test successful payment methods formatting"""
        payment_state = {
            "available_payment_methods": [
                {"id": "pm_1", "type": "credit_card", "display_name": "Visa"}
            ]
        }
        result = ArtifactFormatter.format_payment_methods(payment_state)

        assert result is not None
        assert result["type"] == "payment_methods"
        assert len(result["payment_methods"]) == 1
        assert result["payment_methods"][0]["id"] == "pm_1"

    def test_format_payment_methods_missing(self):
        """Test that None is returned when payment methods are missing"""
        payment_state = {}
        result = ArtifactFormatter.format_payment_methods(payment_state)
        assert result is None

    def test_format_payment_methods_empty_list(self):
        """Test that None is returned for empty list"""
        payment_state = {"available_payment_methods": []}
        result = ArtifactFormatter.format_payment_methods(payment_state)
        assert result is None

    def test_format_payment_methods_invalid_type(self):
        """Test that None is returned for invalid type"""
        payment_state = {"available_payment_methods": "not a list"}
        result = ArtifactFormatter.format_payment_methods(payment_state)
        assert result is None


class TestFormatPaymentMethodSelection:
    """Tests for format_payment_method_selection() method"""

    def test_format_payment_method_selection_success(self):
        """Test successful payment method selection formatting"""
        selection_state = {
            "selected_payment_method": {"id": "pm_visa_1234", "type": "credit_card"},
            "available_payment_methods": [
                {"id": "pm_visa_1234", "display_name": "Visa"}
            ]
        }
        result = ArtifactFormatter.format_payment_method_selection(
            selection_state)

        assert result is not None
        assert result["type"] == "payment_method_selection"
        assert result["selected_payment_method_id"] == "pm_visa_1234"
        assert len(result["payment_methods"]) == 1

    def test_format_payment_method_selection_missing(self):
        """Test that None is returned when selection is missing"""
        selection_state = {}
        result = ArtifactFormatter.format_payment_method_selection(
            selection_state)
        assert result is None

    def test_format_payment_method_selection_invalid_type(self):
        """Test that None is returned for invalid selection type"""
        selection_state = {
            "selected_payment_method": "not a dict",
            "available_payment_methods": []
        }
        result = ArtifactFormatter.format_payment_method_selection(
            selection_state)
        assert result is None

    def test_format_payment_method_selection_defaults(self):
        """Test that defaults are used for missing fields"""
        selection_state = {
            "selected_payment_method": {"id": "pm_1"},
            "available_payment_methods": []
        }
        result = ArtifactFormatter.format_payment_method_selection(
            selection_state)

        assert result is not None
        assert result["selected_payment_method_id"] == "pm_1"
        assert result["payment_methods"] == []
