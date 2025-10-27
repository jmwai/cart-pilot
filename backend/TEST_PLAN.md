# Unit Test Plan for Agent Tools

## Overview

Comprehensive unit test suite for all agent tools using pytest, SQLAlchemy mocking, and comprehensive coverage.

## Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures and test utilities
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_product_discovery_tools.py
│   │   ├── test_cart_tools.py
│   │   ├── test_checkout_tools.py
│   │   ├── test_payment_tools.py
│   │   └── test_customer_service_tools.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_workflows.py
│   │   └── test_relationships.py
│   └── fixtures/
│       ├── sample_data.py    # Mock data generators
│       └── db_mocks.py       # Database mocking utilities
├── pytest.ini                # Pytest configuration
└── requirements-test.txt     # Test dependencies
```

## Dependencies

Add to `requirements-test.txt`:
```txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
faker>=20.0.0
```

## Test Utilities (`tests/conftest.py`)

### Mock SQLAlchemy Session Fixture
```python
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from app.common.models import *

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
    return session

@pytest.fixture
def mock_get_db_session(mocker):
    """Mock the get_db_session context manager"""
    def _mock_session():
        mock_db = Mock(spec=Session)
        yield mock_db
        mock_db.commit()
    return _mock_session
```

## 1. Product Discovery Agent Tests

### Test File: `tests/unit/test_product_discovery_tools.py`

#### Tests for `text_vector_search()`
- [ ] **test_text_vector_search_success**: Returns products with distance scores
- [ ] **test_text_vector_search_empty_query**: Handles empty query gracefully
- [ ] **test_text_vector_search_no_results**: Returns empty list when no matches
- [ ] **test_text_vector_search_limit_10**: Limits results to 10 items
- [ ] **test_text_vector_search_embedding_called**: Verifies embedding function called
- [ ] **test_text_vector_search_sql_execution**: Verifies raw SQL executed with pgvector

#### Tests for `image_vector_search()`
- [ ] **test_image_vector_search_success**: Returns visually similar products
- [ ] **test_image_vector_search_invalid_bytes**: Handles invalid image data
- [ ] **test_image_vector_search_no_results**: Returns empty list when no matches
- [ ] **test_image_vector_search_limit_10**: Limits results to 10 items
- [ ] **test_image_vector_search_embedding_called**: Verifies image embedding called

#### Edge Cases
- [ ] **test_database_connection_error**: Handles database failures
- [ ] **test_embedding_service_error**: Handles Vertex AI API failures
- [ ] **test_sql_injection_protection**: Ensures query parameters sanitized

**Estimated Tests**: 15

---

## 2. Cart Agent Tests

### Test File: `tests/unit/test_cart_tools.py`

#### Tests for `add_to_cart()`
- [ ] **test_add_to_cart_success**: Adds product to cart successfully
- [ ] **test_add_to_cart_product_not_found**: Raises ValueError for invalid product_id
- [ ] **test_add_to_cart_zero_quantity**: Raises ValueError for quantity <= 0
- [ ] **test_add_to_cart_negative_quantity**: Raises ValueError for negative quantity
- [ ] **test_add_to_cart_session_persistence**: Cart item linked to correct session
- [ ] **test_add_to_cart_creates_uuid**: Generates unique cart_item_id
- [ ] **test_add_to_cart_product_relationship**: Loads product details via relationship

#### Tests for `get_cart()`
- [ ] **test_get_cart_success**: Returns all cart items for session
- [ ] **test_get_cart_empty**: Returns empty list for empty cart
- [ ] **test_get_cart_ordered_by_added_at**: Items ordered by added_at DESC
- [ ] **test_get_cart_product_info**: Includes product name and picture
- [ ] **test_get_cart_session_isolation**: Only returns items for specified session

#### Tests for `update_cart_item()`
- [ ] **test_update_cart_item_success**: Updates quantity successfully
- [ ] **test_update_cart_item_not_found**: Raises ValueError for invalid cart_item_id
- [ ] **test_update_cart_item_zero_quantity**: Raises ValueError for quantity <= 0
- [ ] **test_update_cart_item_negative_quantity**: Raises ValueError for negative quantity

#### Tests for `remove_from_cart()`
- [ ] **test_remove_from_cart_success**: Removes item successfully
- [ ] **test_remove_from_cart_not_found**: Raises ValueError for invalid cart_item_id
- [ ] **test_remove_from_cart_commits**: Verifies commit() called

#### Tests for `clear_cart()`
- [ ] **test_clear_cart_success**: Removes all items for session
- [ ] **test_clear_cart_empty_cart**: Handles empty cart gracefully
- [ ] **test_clear_cart_returns_count**: Returns correct items_removed count
- [ ] **test_clear_cart_session_isolation**: Only clears items for specified session

#### Tests for `get_cart_total()`
- [ ] **test_get_cart_total_success**: Returns item count and totals
- [ ] **test_get_cart_total_empty_cart**: Returns zeros for empty cart
- [ ] **test_get_cart_total_multiple_items**: Calculates correct totals
- [ ] **test_get_cart_total_session_isolation**: Only counts items for specified session

**Estimated Tests**: 25

---

## 3. Checkout Agent Tests

### Test File: `tests/unit/test_checkout_tools.py`

#### Tests for `create_order()`
- [ ] **test_create_order_success**: Creates order with order items
- [ ] **test_create_order_empty_cart**: Raises ValueError for empty cart
- [ ] **test_create_order_clears_cart**: Removes cart items after order creation
- [ ] **test_create_order_generates_uuid**: Creates unique order_id
- [ ] **test_create_order_sets_status_pending**: Sets initial status to 'pending'
- [ ] **test_create_order_creates_order_items**: Creates order items for each cart item
- [ ] **test_create_order_total_amount**: Calculates total amount correctly
- [ ] **test_create_order_shipping_address**: Stores shipping address
- [ ] **test_create_order_product_relationship**: Links to products correctly

#### Tests for `get_order_status()`
- [ ] **test_get_order_status_success**: Returns order details with items
- [ ] **test_get_order_status_not_found**: Raises ValueError for invalid order_id
- [ ] **test_get_order_status_includes_items**: Returns order items
- [ ] **test_get_order_status_includes_product_info**: Includes product details
- [ ] **test_get_order_status_formats_datetime**: Formats created_at as ISO string

#### Tests for `cancel_order()`
- [ ] **test_cancel_order_success**: Cancels pending order
- [ ] **test_cancel_order_not_found**: Raises ValueError for invalid order_id
- [ ] **test_cancel_order_completed_order**: Raises ValueError for completed order
- [ ] **test_cancel_order_refunded_order**: Raises ValueError for refunded order
- [ ] **test_cancel_order_only_pending_or_processing**: Validates status before cancel
- [ ] **test_cancel_order_returns_refund_amount**: Returns correct refund amount

#### Tests for `validate_cart_for_checkout()`
- [ ] **test_validate_cart_valid**: Returns valid=True for non-empty cart
- [ ] **test_validate_cart_empty**: Returns valid=False for empty cart
- [ ] **test_validate_cart_returns_errors**: Returns errors list
- [ ] **test_validate_cart_returns_warnings**: Returns warnings list
- [ ] **test_validate_cart_item_count**: Returns correct item_count

**Estimated Tests**: 22

---

## 4. Payment Agent Tests

### Test File: `tests/unit/test_payment_tools.py`

#### Tests for `create_payment_mandate()`
- [ ] **test_create_payment_mandate_success**: Creates mandate successfully
- [ ] **test_create_payment_mandate_order_not_found**: Raises ValueError for invalid order_id
- [ ] **test_create_payment_mandate_type_payment**: Sets mandate_type to 'payment'
- [ ] **test_create_payment_mandate_status_pending**: Sets initial status to 'pending'
- [ ] **test_create_payment_mandate_data_json**: Stores mandate_data as JSON
- [ ] **test_create_payment_mandate_generates_uuid**: Creates unique mandate_id
- [ ] **test_create_payment_mandate_session_id**: Links to order's session_id

#### Tests for `process_payment()`
- [ ] **test_process_payment_success**: Processes payment successfully
- [ ] **test_process_payment_order_not_found**: Raises ValueError for invalid order_id
- [ ] **test_process_payment_creates_mandate**: Creates payment mandate first
- [ ] **test_process_payment_creates_payment_record**: Creates payment record
- [ ] **test_process_payment_updates_order_status**: Sets order status to 'completed'
- [ ] **test_process_payment_updates_mandate_status**: Sets mandate status to 'approved'
- [ ] **test_process_payment_generates_transaction_id**: Creates unique transaction_id
- [ ] **test_process_payment_amount**: Stores correct payment amount
- [ ] **test_process_payment_method**: Stores payment method

#### Tests for `get_payment_status()`
- [ ] **test_get_payment_status_success**: Returns payment details
- [ ] **test_get_payment_status_not_found**: Raises ValueError for invalid payment_id
- [ ] **test_get_payment_status_includes_mandate_id**: Returns mandate_id
- [ ] **test_get_payment_status_includes_transaction_id**: Returns transaction_id
- [ ] **test_get_payment_status_formats_datetime**: Formats processed_at as ISO string

#### Tests for `refund_payment()`
- [ ] **test_refund_payment_success**: Processes refund successfully
- [ ] **test_refund_payment_not_found**: Raises ValueError for invalid payment_id
- [ ] **test_refund_payment_updates_payment_status**: Sets payment status to 'refunded'
- [ ] **test_refund_payment_updates_order_status**: Sets order status to 'refunded'
- [ ] **test_refund_payment_returns_refund_amount**: Returns correct refund amount
- [ ] **test_refund_payment_generates_refund_id**: Creates unique refund_id

#### Tests for `get_payment_history()`
- [ ] **test_get_payment_history_success**: Returns payment history for session
- [ ] **test_get_payment_history_empty**: Returns empty list for no payments
- [ ] **test_get_payment_history_ordered_desc**: Orders by created_at DESC
- [ ] **test_get_payment_history_joins_orders**: Includes order_id from joined table
- [ ] **test_get_payment_history_session_isolation**: Only returns payments for specified session

**Estimated Tests**: 28

---

## 5. Customer Service Agent Tests

### Test File: `tests/unit/test_customer_service_tools.py`

#### Tests for `create_inquiry()`
- [ ] **test_create_inquiry_success**: Creates inquiry successfully
- [ ] **test_create_inquiry_invalid_type**: Raises ValueError for invalid inquiry_type
- [ ] **test_create_inquiry_allows_null_order_id**: Handles optional order_id
- [ ] **test_create_inquiry_sets_status_open**: Sets initial status to 'open'
- [ ] **test_create_inquiry_generates_uuid**: Creates unique inquiry_id
- [ ] **test_create_inquiry_stores_message**: Stores inquiry message
- [ ] **test_create_inquiry_returns_response**: Returns user-friendly response

#### Tests for `get_inquiry_status()`
- [ ] **test_get_inquiry_status_success**: Returns inquiry details
- [ ] **test_get_inquiry_status_not_found**: Raises ValueError for invalid inquiry_id
- [ ] **test_get_inquiry_status_includes_order_id**: Returns related order_id
- [ ] **test_get_inquiry_status_formats_datetime**: Formats created_at as ISO string

#### Tests for `search_faq()`
- [ ] **test_search_faq_success**: Returns FAQ results
- [ ] **test_search_faq_keyword_match**: Returns matching FAQs by keyword
- [ ] **test_search_faq_no_match**: Returns default FAQs when no match
- [ ] **test_search_faq_case_insensitive**: Case-insensitive search
- [ ] **test_search_faq_relevance_score**: Returns relevance scores

#### Tests for `initiate_return()`
- [ ] **test_initiate_return_success**: Initiates return process
- [ ] **test_initiate_return_order_not_found**: Raises ValueError for invalid order_id
- [ ] **test_initiate_return_creates_inquiry**: Creates return inquiry
- [ ] **test_initiate_return_generates_return_id**: Creates unique return_id
- [ ] **test_initiate_return_returns_instructions**: Returns return instructions
- [ ] **test_initiate_return_stores_reason**: Stores return reason

#### Tests for `get_order_inquiries()`
- [ ] **test_get_order_inquiries_success**: Returns inquiries for order
- [ ] **test_get_order_inquiries_empty**: Returns empty list for no inquiries
- [ ] **test_get_order_inquiries_ordered_desc**: Orders by created_at DESC
- [ ] **test_get_order_inquiries_filter_by_order**: Only returns inquiries for specified order

**Estimated Tests**: 22

---

## Total Estimated Tests: 112+

## Test Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## Mocking Strategy

### SQLAlchemy Query Mocking
```python
def test_add_to_cart_success(mock_db_session):
    # Setup
    product = CatalogItem(id="prod_123", name="Test Product")
    mock_db_session.query.return_value.filter.return_value.first.return_value = product
    
    # Execute
    result = add_to_cart("prod_123", 2, "session_abc")
    
    # Assert
    assert result["product_id"] == "prod_123"
    assert result["quantity"] == 2
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
```

### Relationship Testing
```python
def test_get_cart_with_product_relationship(mock_db_session):
    # Setup
    cart_item = CartItem(cart_item_id="item_1", product_id="prod_123", quantity=2)
    cart_item.product = CatalogItem(id="prod_123", name="Test Product")
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [cart_item]
    
    # Execute
    result = get_cart("session_abc")
    
    # Assert
    assert len(result) == 1
    assert result[0]["name"] == "Test Product"
```

## Test Execution

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test Suite
```bash
pytest tests/unit/test_cart_tools.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Fast Tests Only
```bash
pytest -m "not slow"
```

## Success Criteria

- ✅ All 112+ tests passing
- ✅ 80%+ code coverage
- ✅ All edge cases handled
- ✅ Error paths tested
- ✅ Relationship queries tested
- ✅ Transaction handling verified
- ✅ Mock isolation verified

## Implementation Order

1. **Phase 1**: Setup test infrastructure (conftest.py, fixtures)
2. **Phase 2**: Product Discovery Agent tests
3. **Phase 3**: Cart Agent tests
4. **Phase 4**: Checkout Agent tests
5. **Phase 5**: Payment Agent tests
6. **Phase 6**: Customer Service Agent tests
7. **Phase 7**: Integration tests
8. **Phase 8**: Coverage and polish

## Notes

- Use Faker for generating test data
- Mock all external dependencies (Vertex AI, database)
- Test both success and failure paths
- Verify SQLAlchemy relationships work correctly
- Ensure transaction handling is tested
- Mock time-sensitive operations (datetime.now)

