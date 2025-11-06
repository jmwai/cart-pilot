"""
Unit tests for StatusMessageHandler.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.utils.status_message_handler import StatusMessageHandler
from app.utils.constants import TOOL_STATUS_MESSAGES
from a2a.types import TaskState


class TestStatusMessageHandler:
    """Tests for StatusMessageHandler class"""

    def test_init(self):
        """Test StatusMessageHandler initialization"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        assert handler.status_messages == TOOL_STATUS_MESSAGES
        assert handler.default_message == 'Processing your request...'
        assert handler.last_function_name is None

    def test_init_custom_default(self):
        """Test initialization with custom default message"""
        handler = StatusMessageHandler({}, default_message='Custom message')
        assert handler.default_message == 'Custom message'

    @pytest.mark.asyncio
    async def test_handle_function_call_with_name_attr(self):
        """Test handling function call with name attribute"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_task.context_id = "ctx_123"
        mock_task.id = "task_123"

        mock_function_call = Mock()
        mock_function_call.name = "add_to_cart"

        with patch('app.utils.status_message_handler.new_agent_text_message') as mock_msg:
            mock_msg.return_value = Mock()
            result = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)

            assert result == "add_to_cart"
            assert handler.last_function_name == "add_to_cart"
            mock_updater.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_function_call_with_function_name_attr(self):
        """Test handling function call with function_name attribute"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_task.context_id = "ctx_123"
        mock_task.id = "task_123"

        mock_function_call = Mock()
        mock_function_call.function_name = "get_cart"
        del mock_function_call.name  # Remove name attribute

        with patch('app.utils.status_message_handler.new_agent_text_message') as mock_msg:
            mock_msg.return_value = Mock()
            result = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)

            assert result == "get_cart"
            assert handler.last_function_name == "get_cart"

    @pytest.mark.asyncio
    async def test_handle_function_call_dict(self):
        """Test handling function call as dict"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_task.context_id = "ctx_123"
        mock_task.id = "task_123"

        function_call_dict = {"name": "text_vector_search"}

        with patch('app.utils.status_message_handler.new_agent_text_message') as mock_msg:
            mock_msg.return_value = Mock()
            result = await handler.handle_function_call(function_call_dict, mock_updater, mock_task)

            assert result == "text_vector_search"
            assert handler.last_function_name == "text_vector_search"

    @pytest.mark.asyncio
    async def test_handle_function_call_unknown_function(self):
        """Test handling unknown function (not in mapping)"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_task.context_id = "ctx_123"
        mock_task.id = "task_123"

        mock_function_call = Mock()
        mock_function_call.name = "unknown_function"

        result = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)

        assert result is None
        assert handler.last_function_name is None
        mock_updater.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_function_call_no_function_name(self):
        """Test handling function call with no function name"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_function_call = Mock()
        del mock_function_call.name
        del mock_function_call.function_name

        result = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)

        assert result is None
        mock_updater.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_function_call_same_function_twice(self):
        """Test that same function doesn't trigger update twice"""
        handler = StatusMessageHandler(TOOL_STATUS_MESSAGES)
        mock_updater = Mock()
        mock_updater.update_status = AsyncMock()

        mock_task = Mock()
        mock_task.context_id = "ctx_123"
        mock_task.id = "task_123"

        mock_function_call = Mock()
        mock_function_call.name = "add_to_cart"

        with patch('app.utils.status_message_handler.new_agent_text_message') as mock_msg:
            mock_msg.return_value = Mock()
            # First call
            result1 = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)
            assert result1 == "add_to_cart"

            # Second call with same function
            result2 = await handler.handle_function_call(mock_function_call, mock_updater, mock_task)
            assert result2 is None  # Should not update again

            # Should only be called once
            assert mock_updater.update_status.call_count == 1

    def test_extract_function_name_name_attr(self):
        """Test extracting function name from name attribute"""
        handler = StatusMessageHandler({})
        mock_call = Mock()
        mock_call.name = "test_function"

        result = handler._extract_function_name(mock_call)
        assert result == "test_function"

    def test_extract_function_name_function_name_attr(self):
        """Test extracting function name from function_name attribute"""
        handler = StatusMessageHandler({})
        mock_call = Mock()
        mock_call.function_name = "test_function"
        del mock_call.name

        result = handler._extract_function_name(mock_call)
        assert result == "test_function"

    def test_extract_function_name_dict(self):
        """Test extracting function name from dict"""
        handler = StatusMessageHandler({})
        function_call_dict = {"name": "test_function"}

        result = handler._extract_function_name(function_call_dict)
        assert result == "test_function"

    def test_extract_function_name_dict_function_name_key(self):
        """Test extracting function name from dict with function_name key"""
        handler = StatusMessageHandler({})
        function_call_dict = {"function_name": "test_function"}

        result = handler._extract_function_name(function_call_dict)
        assert result == "test_function"

    def test_extract_function_name_none(self):
        """Test extracting function name when not found"""
        handler = StatusMessageHandler({})
        mock_call = Mock()
        del mock_call.name
        del mock_call.function_name

        result = handler._extract_function_name(mock_call)
        assert result is None
