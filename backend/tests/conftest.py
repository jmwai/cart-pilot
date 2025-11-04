"""
Shared pytest fixtures and test utilities.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Generator
import uuid

from sqlalchemy.orm import Session
from app.common.models import (
    CatalogItem, CartItem, Order, OrderItem,
    Mandate, Payment, CustomerInquiry
)


@pytest.fixture
def mock_db_session():
    """Create a mock SQLAlchemy session"""
    session = Mock(spec=Session)
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.add = Mock()
    session.delete = Mock()
    session.query = Mock()
    session.execute = Mock()
    return session


@pytest.fixture
def mock_get_db_session():
    """Mock the get_db_session context manager"""
    def _mock_session():
        mock_db = Mock(spec=Session)
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        yield mock_db
        mock_db.commit()

    return patch('app.common.db.get_db_session', side_effect=_mock_session)


@pytest.fixture
def sample_product():
    """Sample product data"""
    return CatalogItem(
        id="prod_123",
        name="Test Running Shoes",
        description="High-quality running shoes",
        picture="https://example.com/shoes.jpg",
        product_image_url="https://example.com/shoes-large.jpg",
        price_usd_units=49.99
    )


@pytest.fixture
def sample_cart_item(sample_product):
    """Sample cart item"""
    cart_item = CartItem(
        cart_item_id="cart_item_123",
        session_id="session_abc",
        product_id="prod_123",
        quantity=2
    )
    cart_item.product = sample_product
    cart_item.created_at = datetime.now()
    return cart_item


@pytest.fixture
def sample_order():
    """Sample order"""
    return Order(
        order_id="order_123",
        session_id="session_abc",
        total_amount=99.99,
        status="pending",
        shipping_address="123 Main St, New York, NY 10001"
    )


@pytest.fixture
def sample_order_item(sample_product):
    """Sample order item"""
    return OrderItem(
        order_item_id=1,
        order_id="order_123",
        product_id="prod_123",
        quantity=2,
        price=49.99
    )


@pytest.fixture
def sample_mandate():
    """Sample mandate"""
    return Mandate(
        mandate_id="mandate_123",
        mandate_type="payment",
        session_id="session_abc",
        mandate_data='{"order_id": "order_123", "amount": 99.99}',
        status="pending"
    )


@pytest.fixture
def sample_payment(sample_order, sample_mandate):
    """Sample payment"""
    return Payment(
        payment_id="payment_123",
        order_id="order_123",
        amount=99.99,
        payment_method="credit_card",
        payment_mandate_id="mandate_123",
        transaction_id="txn_abc123",
        status="completed"
    )


@pytest.fixture
def sample_inquiry(sample_order):
    """Sample customer inquiry"""
    inquiry = CustomerInquiry(
        inquiry_id="inquiry_123",
        session_id="session_abc",
        inquiry_type="return",
        message="I want to return my order",
        related_order_id="order_123",
        status="open"
    )
    inquiry.created_at = datetime.now()
    return inquiry


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext for ADK tools"""
    from google.adk.tools import ToolContext

    # Create mock session
    mock_session = Mock()
    mock_session.id = "session_abc"

    # Create mock invocation context
    mock_invocation_context = Mock()
    mock_invocation_context.session = mock_session

    # Create mock tool context
    tool_context = Mock(spec=ToolContext)
    tool_context.state = {}
    tool_context._invocation_context = mock_invocation_context

    return tool_context


# Mock data generators
class MockDataGenerator:
    """Utility class for generating mock data"""

    @staticmethod
    def generate_product(product_id: str = None) -> CatalogItem:
        """Generate a mock product"""
        return CatalogItem(
            id=product_id or f"prod_{uuid.uuid4().hex[:8]}",
            name=f"Product {uuid.uuid4().hex[:4]}",
            description="Test product description",
            picture="https://example.com/product.jpg",
            product_image_url="https://example.com/product-large.jpg"
        )

    @staticmethod
    def generate_cart_item(session_id: str, product_id: str = None, quantity: int = 1) -> CartItem:
        """Generate a mock cart item"""
        return CartItem(
            cart_item_id=f"cart_item_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            product_id=product_id or f"prod_{uuid.uuid4().hex[:8]}",
            quantity=quantity
        )

    @staticmethod
    def generate_order(session_id: str, status: str = "pending") -> Order:
        """Generate a mock order"""
        return Order(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            total_amount=99.99,
            status=status,
            shipping_address="123 Main St, New York, NY 10001"
        )


@pytest.fixture
def mock_data():
    """Provide access to mock data generator"""
    return MockDataGenerator()


# Helper functions for setting up query mocks
def setup_query_mock(mock_session, model_class, filter_result=None, first_result=None, all_result=None):
    """Helper to set up SQLAlchemy query mocks"""
    mock_query = Mock()
    mock_session.query.return_value = mock_query

    if filter_result is not None:
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter

        if first_result is not None:
            mock_filter.first.return_value = first_result

        if all_result is not None:
            mock_filter.order_by.return_value.all.return_value = all_result

        return mock_filter

    return mock_query
