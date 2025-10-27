"""
Unit tests for Customer Service Agent tools.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.customer_service_agent.tools import (
    create_inquiry,
    get_inquiry_status,
    search_faq,
    initiate_return,
    get_order_inquiries
)
from app.common.models import CustomerInquiry, Order


class TestCreateInquiry:
    """Tests for create_inquiry() function"""

    def test_create_inquiry_success(self, mock_db_session):
        """Test successful creation of inquiry"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Execute
            result = create_inquiry(
                "return", "I want to return my order", "session_abc", "order_123")

            # Assert
            assert "inquiry_id" in result
            assert result["inquiry_type"] == "return"
            assert result["message"] == "I want to return my order"
            assert result["status"] == "open"
            assert result["order_id"] == "order_123"
            assert "response" in result
            mock_db_session.add.assert_called_once()

    def test_create_inquiry_invalid_type(self, mock_db_session):
        """Test ValueError raised for invalid inquiry_type"""
        with pytest.raises(ValueError, match="Inquiry type must be one of"):
            create_inquiry("invalid_type", "Test message", "session_abc")

    def test_create_inquiry_allows_null_order_id(self, mock_db_session):
        """Test that order_id can be None"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            result = create_inquiry(
                "question", "What is your policy?", "session_abc", None)

            assert result["order_id"] is None
            assert result["inquiry_type"] == "question"

    def test_create_inquiry_sets_status_open(self, mock_db_session):
        """Test that initial status is 'open'"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            result = create_inquiry("complaint", "Poor service", "session_abc")

            assert result["status"] == "open"

    def test_create_inquiry_generates_uuid(self, mock_db_session):
        """Test that inquiry_id is a UUID"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            result = create_inquiry("question", "Test?", "session_abc")

            assert "inquiry_id" in result
            assert len(result["inquiry_id"]) > 0

    def test_create_inquiry_stores_message(self, mock_db_session):
        """Test that message is stored correctly"""
        message = "I need help with my order"
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            result = create_inquiry("question", message, "session_abc")

            assert result["message"] == message

    def test_create_inquiry_valid_types(self, mock_db_session):
        """Test all valid inquiry types"""
        valid_types = ['return', 'refund',
                       'question', 'complaint', 'product_issue']

        for inquiry_type in valid_types:
            with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
                mock_session.return_value.__enter__.return_value = mock_db_session

                result = create_inquiry(
                    inquiry_type, f"Test {inquiry_type}", "session_abc")

                assert result["inquiry_type"] == inquiry_type


class TestGetInquiryStatus:
    """Tests for get_inquiry_status() function"""

    def test_get_inquiry_status_success(self, mock_db_session, sample_inquiry):
        """Test successful retrieval of inquiry status"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_inquiry

            # Execute
            result = get_inquiry_status("inquiry_123")

            # Assert
            assert result["inquiry_id"] == "inquiry_123"
            assert result["inquiry_type"] == "return"
            assert result["message"] == "I want to return my order"
            assert result["status"] == "open"
            assert result["order_id"] == "order_123"

    def test_get_inquiry_status_not_found(self, mock_db_session):
        """Test ValueError raised when inquiry doesn't exist"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Inquiry inquiry_999 not found"):
                get_inquiry_status("inquiry_999")

    def test_get_inquiry_status_formats_datetime(self, mock_db_session, sample_inquiry):
        """Test that created_at is formatted as ISO string"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_inquiry

            result = get_inquiry_status("inquiry_123")

            assert "created_at" in result
            if sample_inquiry.created_at:
                assert len(result["created_at"]) > 0


class TestSearchFaq:
    """Tests for search_faq() function"""

    def test_search_faq_success(self):
        """Test FAQ search returns results"""
        result = search_faq("return")

        assert isinstance(result, list)
        assert len(result) > 0
        assert "question" in result[0]
        assert "answer" in result[0]

    def test_search_faq_keyword_match(self):
        """Test that FAQ search matches keywords"""
        result = search_faq("return")

        # Should return FAQs related to returns
        assert any("return" in item["question"].lower() or "return" in item["answer"].lower()
                   for item in result)

    def test_search_faq_no_match(self):
        """Test that default FAQs are returned when no match"""
        result = search_faq("xyz_not_found_xyz")

        # Should return default FAQs
        assert len(result) > 0

    def test_search_faq_case_insensitive(self):
        """Test case-insensitive search"""
        result_lower = search_faq("return")
        result_upper = search_faq("RETURN")

        # Should return similar results
        assert len(result_lower) == len(result_upper)

    def test_search_faq_relevance_score(self):
        """Test that results include relevance scores"""
        result = search_faq("return")

        assert "relevance_score" in result[0]


class TestInitiateReturn:
    """Tests for initiate_return() function"""

    def test_initiate_return_success(self, mock_db_session, sample_order):
        """Test successful return initiation"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup order lookup
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            # Mock create_inquiry
            with patch('app.customer_service_agent.tools.create_inquiry') as mock_inquiry:
                mock_inquiry.return_value = {"inquiry_id": "inquiry_123"}

                # Execute
                result = initiate_return(
                    "order_123", "Didn't fit", "session_abc")

                # Assert
                assert "return_id" in result
                assert result["order_id"] == "order_123"
                assert result["status"] == "initiated"
                assert result["reason"] == "Didn't fit"
                assert "instructions" in result
                assert result["inquiry_id"] == "inquiry_123"

    def test_initiate_return_order_not_found(self, mock_db_session):
        """Test ValueError raised when order doesn't exist"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return None
            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            # Execute & Assert
            with pytest.raises(ValueError, match="Order order_999 not found"):
                initiate_return("order_999", "Test reason", "session_abc")

    def test_initiate_return_creates_inquiry(self, mock_db_session, sample_order):
        """Test that return creates an inquiry"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.customer_service_agent.tools.create_inquiry') as mock_inquiry:
                mock_inquiry.return_value = {"inquiry_id": "inquiry_123"}

                initiate_return("order_123", "Reason", "session_abc")

                # Verify inquiry was created
                mock_inquiry.assert_called_once_with(
                    "return", "Reason", "session_abc", "order_123")

    def test_initiate_return_generates_return_id(self, mock_db_session, sample_order):
        """Test that return_id is generated"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.customer_service_agent.tools.create_inquiry') as mock_inquiry:
                mock_inquiry.return_value = {"inquiry_id": "inquiry_123"}

                result = initiate_return("order_123", "Reason", "session_abc")

                assert "return_id" in result
                assert len(result["return_id"]) > 0

    def test_initiate_return_returns_instructions(self, mock_db_session, sample_order):
        """Test that return instructions are included"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = sample_order

            with patch('app.customer_service_agent.tools.create_inquiry') as mock_inquiry:
                mock_inquiry.return_value = {"inquiry_id": "inquiry_123"}

                result = initiate_return("order_123", "Reason", "session_abc")

                assert "instructions" in result
                assert len(result["instructions"]) > 0


class TestGetOrderInquiries:
    """Tests for get_order_inquiries() function"""

    def test_get_order_inquiries_success(self, mock_db_session, sample_inquiry):
        """Test successful retrieval of order inquiries"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query
            mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
                sample_inquiry]

            # Execute
            result = get_order_inquiries("order_123")

            # Assert
            assert len(result) == 1
            assert result[0]["inquiry_id"] == "inquiry_123"
            assert result[0]["inquiry_type"] == "return"
            assert result[0]["status"] == "open"

    def test_get_order_inquiries_empty(self, mock_db_session):
        """Test empty inquiries list"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Setup mock query to return empty list
            mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

            # Execute
            result = get_order_inquiries("order_123")

            # Assert
            assert result == []

    def test_get_order_inquiries_ordered_desc(self, mock_db_session, sample_inquiry):
        """Test that inquiries are ordered by created_at DESC"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_query = mock_db_session.query.return_value
            mock_query.filter.return_value.order_by.return_value.all.return_value = [
                sample_inquiry]

            get_order_inquiries("order_123")

            # Verify order_by was called
            mock_query.filter.return_value.order_by.assert_called_once()

    def test_get_order_inquiries_filter_by_order(self, mock_db_session, sample_inquiry):
        """Test that only inquiries for specified order are returned"""
        with patch('app.customer_service_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_query = mock_db_session.query.return_value
            mock_query.filter.return_value.order_by.return_value.all.return_value = [
                sample_inquiry]

            get_order_inquiries("order_123")

            # Verify filter was called
            mock_query.filter.assert_called_once()
