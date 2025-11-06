"""
Unit tests for ContentBuilder.
"""
import pytest
from unittest.mock import Mock, patch

from app.utils.content_builder import ContentBuilder
from app.utils.message_parser import ParsedMessage


class TestContentBuilder:
    """Tests for ContentBuilder class"""

    def test_init(self):
        """Test ContentBuilder initialization"""
        builder = ContentBuilder()
        assert builder.debug is False

    def test_init_debug(self):
        """Test ContentBuilder initialization with debug"""
        builder = ContentBuilder(debug=True)
        assert builder.debug is True

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.types.Content')
    def test_build_text_only(self, mock_content, mock_part):
        """Test building content with text only"""
        builder = ContentBuilder()
        parsed_message = ParsedMessage(
            text_query="test query",
            image_bytes=None,
            image_mime_type=None
        )

        mock_part.from_text.return_value = Mock()
        mock_content.return_value = Mock()

        result = builder.build(parsed_message)

        mock_part.from_text.assert_called_once_with(text="test query")
        mock_content.assert_called_once()

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.types.Content')
    def test_build_image_only(self, mock_content, mock_part):
        """Test building content with image only"""
        builder = ContentBuilder()
        parsed_message = ParsedMessage(
            text_query=None,
            image_bytes=b"fake_image_data",
            image_mime_type="image/jpeg"
        )

        mock_part.from_inline_data = Mock(return_value=Mock())
        mock_content.return_value = Mock()

        result = builder.build(parsed_message)

        mock_content.assert_called_once()

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.types.Content')
    def test_build_text_and_image(self, mock_content, mock_part):
        """Test building content with text and image"""
        builder = ContentBuilder()
        parsed_message = ParsedMessage(
            text_query="test query",
            image_bytes=b"fake_image_data",
            image_mime_type="image/jpeg"
        )

        mock_part.from_text.return_value = Mock()
        mock_part.from_inline_data = Mock(return_value=Mock())
        mock_content.return_value = Mock()

        result = builder.build(parsed_message)

        mock_part.from_text.assert_called_once()
        mock_content.assert_called_once()

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.types.Content')
    def test_build_empty(self, mock_content, mock_part):
        """Test building content with no text or image"""
        builder = ContentBuilder()
        parsed_message = ParsedMessage(
            text_query=None,
            image_bytes=None,
            image_mime_type=None
        )

        mock_part.from_text.return_value = Mock()
        mock_content.return_value = Mock()

        result = builder.build(parsed_message)

        # Should add empty text part
        mock_part.from_text.assert_called_once_with(text="")
        mock_content.assert_called_once()

    @patch('app.utils.content_builder.types.Part')
    def test_create_image_part_from_inline_data(self, mock_part):
        """Test creating image part using from_inline_data"""
        builder = ContentBuilder()
        mock_part.from_inline_data = Mock(return_value=Mock())

        result = builder._create_image_part(b"image_data", "image/jpeg")

        assert result is not None
        mock_part.from_inline_data.assert_called_once_with(
            data=b"image_data",
            mime_type="image/jpeg"
        )

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.inspect.signature')
    def test_create_image_part_inline_data_param(self, mock_signature, mock_part):
        """Test creating image part with inline_data parameter"""
        builder = ContentBuilder()
        # Mock that from_inline_data doesn't exist
        del mock_part.from_inline_data

        mock_sig = Mock()
        mock_sig.parameters = {'inline_data': Mock()}
        mock_signature.return_value = mock_sig

        mock_part.return_value = Mock()

        result = builder._create_image_part(b"image_data", "image/jpeg")

        assert result is not None

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.inspect.signature')
    def test_create_image_part_data_mime_type_params(self, mock_signature, mock_part):
        """Test creating image part with data and mime_type parameters"""
        builder = ContentBuilder()
        # Mock that from_inline_data doesn't exist
        del mock_part.from_inline_data

        mock_sig = Mock()
        mock_sig.parameters = {'data': Mock(), 'mime_type': Mock()}
        mock_signature.return_value = mock_sig

        mock_part.return_value = Mock()

        result = builder._create_image_part(b"image_data", "image/jpeg")

        assert result is not None

    @patch('app.utils.content_builder.types.Part')
    @patch('app.utils.content_builder.inspect.signature')
    def test_create_image_part_fallback_none(self, mock_signature, mock_part):
        """Test creating image part when no method works"""
        builder = ContentBuilder()

        # Mock that from_inline_data doesn't exist (hasattr returns False)
        # Mock that __init__ exists but has no matching parameters
        def hasattr_side_effect(obj, attr):
            if attr == 'from_inline_data':
                return False
            return True  # __init__ exists

        mock_sig = Mock()
        mock_sig.parameters = {}  # No matching parameters
        mock_signature.return_value = mock_sig

        with patch('builtins.hasattr', side_effect=hasattr_side_effect):
            result = builder._create_image_part(b"image_data", "image/jpeg")

        assert result is None

    @patch('app.utils.content_builder.types.Part')
    def test_create_image_part_exception(self, mock_part):
        """Test exception handling in create_image_part"""
        builder = ContentBuilder()
        mock_part.from_inline_data = Mock(side_effect=Exception("Test error"))

        result = builder._create_image_part(b"image_data", "image/jpeg")

        # Should return None on exception
        assert result is None
