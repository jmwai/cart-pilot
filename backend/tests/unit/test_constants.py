"""
Unit tests for constants.py.
"""
import pytest

from app.utils.constants import TOOL_STATUS_MESSAGES


class TestConstants:
    """Tests for constants module"""

    def test_tool_status_messages_exists(self):
        """Test that TOOL_STATUS_MESSAGES is defined"""
        assert TOOL_STATUS_MESSAGES is not None
        assert isinstance(TOOL_STATUS_MESSAGES, dict)

    def test_tool_status_messages_has_entries(self):
        """Test that TOOL_STATUS_MESSAGES has expected entries"""
        assert len(TOOL_STATUS_MESSAGES) > 0
        assert 'text_vector_search' in TOOL_STATUS_MESSAGES
        assert 'add_to_cart' in TOOL_STATUS_MESSAGES
        assert 'create_order' in TOOL_STATUS_MESSAGES

    def test_tool_status_messages_values_are_strings(self):
        """Test that all values in TOOL_STATUS_MESSAGES are strings"""
        for key, value in TOOL_STATUS_MESSAGES.items():
            assert isinstance(value, str)
            assert len(value) > 0
