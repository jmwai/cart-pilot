# Test Suite for Shopping Orchestrator

## Overview

Comprehensive test suite for all agent tools using pytest, SQLAlchemy mocking, and comprehensive coverage.

## Installation

Install test dependencies:

```bash
cd backend
pip install -r requirements-test.txt
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Suite
```bash
# Cart Agent tests
pytest tests/unit/test_cart_tools.py

# Checkout Agent tests
pytest tests/unit/test_checkout_tools.py
```

### Run with Coverage Report
```bash
pytest --cov=app --cov-report=html
```

Open `htmlcov/index.html` in your browser to view coverage report.

### Run Specific Test
```bash
pytest tests/unit/test_cart_tools.py::TestAddToCart::test_add_to_cart_success
```

### Run Fast Tests Only (Exclude Slow Tests)
```bash
pytest -m "not slow"
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and utilities
├── unit/                          # Unit tests for agent tools
│   ├── test_cart_tools.py         # Cart Agent tests (25 tests)
│   ├── test_checkout_tools.py     # Checkout Agent tests (22 tests)
│   ├── test_payment_tools.py      # Payment Agent tests (28 tests)
│   ├── test_customer_service_tools.py  # Customer Service tests (22 tests)
│   └── test_product_discovery_tools.py  # Product Discovery tests (15 tests)
├── integration/                   # Integration tests
│   ├── test_workflows.py          # End-to-end workflows
│   └── test_relationships.py      # Database relationships
└── fixtures/                      # Mock data generators
    └── sample_data.py
```

## Test Coverage

- **Target**: 80%+ code coverage
- **Current Implementation**: 
  - Cart Agent: Complete test suite (25 tests)
  - Checkout Agent: Complete test suite (22 tests)
  - Other agents: To be implemented

## Writing Tests

### Using Fixtures

```python
def test_add_to_cart(mock_db_session, sample_product):
    """Test using fixtures from conftest.py"""
    # Setup
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_product
    
    # Execute
    result = add_to_cart("prod_123", 2, "session_abc")
    
    # Assert
    assert result["quantity"] == 2
```

### Mocking SQLAlchemy Sessions

```python
def test_with_session_mock():
    with patch('app.cart_agent.tools.get_db_session') as mock_session:
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        
        # Setup query mocks
        mock_db.query.return_value.filter.return_value.first.return_value = product
        
        # Execute function
        result = function_under_test()
        
        # Assert
        assert result is not None
```

## Test Files Status

- ✅ `test_cart_tools.py` - Complete
- ✅ `test_checkout_tools.py` - Complete
- ⏳ `test_payment_tools.py` - To be implemented
- ⏳ `test_customer_service_tools.py` - To be implemented
- ⏳ `test_product_discovery_tools.py` - To be implemented

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Notes

- All tests use mocked database sessions
- No real database connection required
- Tests run in isolation
- Fast execution (all tests run in < 10 seconds)

