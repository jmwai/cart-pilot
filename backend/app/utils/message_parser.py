"""
Message parser for extracting text and image data from A2A messages.

This module handles parsing A2A protocol messages to extract text queries
and image data, with support for multiple message formats.
"""

import base64
import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Any

from a2a.server.agent_execution import RequestContext

logger = logging.getLogger(__name__)


@dataclass
class ParsedMessage:
    """Container for parsed message data."""
    text_query: Optional[str] = None
    image_bytes: Optional[bytes] = None
    image_mime_type: Optional[str] = None


class MessageParser:
    """Parses A2A messages to extract text and image data."""

    # Valid image MIME types
    VALID_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

    # Maximum image size (10MB)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024

    def __init__(self, debug: bool = False):
        """Initialize message parser.

        Args:
            debug: Enable debug logging (default: False)
        """
        self.debug = debug

    def parse(self, context: RequestContext) -> ParsedMessage:
        """Extract text and image from A2A message.

        Args:
            context: A2A request context containing the message

        Returns:
            ParsedMessage containing text_query, image_bytes, and image_mime_type

        Raises:
            ValueError: If image processing fails or unsupported format detected
        """
        if not context.message:
            raise ValueError('Message should be present in request context')

        if self.debug:
            self._log_message_structure(context)

        # Extract message parts
        message_parts = self._extract_parts(context.message)

        if self.debug:
            logger.info(
                f"DEBUG: Processing message with {len(message_parts)} parts")

        text_query = None
        image_bytes = None
        image_mime_type = None

        # Process message parts to extract text and file parts
        for i, part in enumerate(message_parts):
            part_kind, part_text, part_file = self._extract_part_attributes(
                part, i)

            if self.debug:
                part_debug = f"DEBUG: Part {i}: kind={part_kind}, has_text={part_text is not None}, has_file={part_file is not None}"
                logger.info(part_debug)

            # Handle text parts
            if part_kind == 'text' and part_text:
                text_query = part_text
                if self.debug:
                    text_debug = f"DEBUG: Extracted text query: {text_query[:50] if len(text_query) > 50 else text_query}..."
                    logger.info(text_debug)

            # Handle file parts (FilePart - only FileWithBytes supported for local uploads)
            elif part_kind == 'file' and part_file:
                parsed_image = self._extract_image(part_file, i)
                if parsed_image:
                    image_bytes, image_mime_type = parsed_image

        # Get text query from context if not found in parts
        if not text_query:
            text_query = context.get_user_input() or ""

        if self.debug:
            extraction_complete = f"DEBUG: Extraction complete - text_query={'present' if text_query else 'None'}, image_bytes={'present' if image_bytes else 'None'}"
            logger.info(extraction_complete)

        return ParsedMessage(
            text_query=text_query,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type
        )

    def _extract_parts(self, message: Any) -> List[Any]:
        """Extract parts from message using multiple strategies.

        Args:
            message: A2A message object

        Returns:
            List of message parts
        """
        message_parts = []

        # Method 1: Direct parts attribute
        if hasattr(message, 'parts'):
            message_parts = message.parts
            if self.debug:
                logger.info(
                    f"DEBUG: Found parts via context.message.parts: {len(message_parts) if message_parts else 0}")

        # Method 2: Nested message.parts
        elif hasattr(message, 'message') and hasattr(message.message, 'parts'):
            message_parts = message.message.parts
            if self.debug:
                logger.info(
                    f"DEBUG: Found parts via context.message.message.parts: {len(message_parts)}")

        # Method 3: Dict access
        elif isinstance(message, dict) and 'parts' in message:
            message_parts = message['parts']
            if self.debug:
                logger.info(
                    f"DEBUG: Found parts via dict access: {len(message_parts)}")

        # Method 4: Deep inspection (debug only)
        elif self.debug:
            logger.info(f"DEBUG: Inspecting message object: {dir(message)}")
            if hasattr(message, '__dict__'):
                logger.info(f"DEBUG: Message __dict__: {message.__dict__}")

        return message_parts or []

    def _extract_part_attributes(self, part: Any, index: int) -> tuple[Optional[str], Optional[str], Optional[Any]]:
        """Extract kind, text, and file attributes from a part.

        Args:
            part: Message part object
            index: Part index for debugging

        Returns:
            Tuple of (kind, text, file)
        """
        part_kind = None
        part_text = None
        part_file = None

        # Method 1: Direct attribute access
        part_kind = getattr(part, 'kind', None)
        part_text = getattr(part, 'text', None)
        part_file = getattr(part, 'file', None)

        # Method 2: Try JSON serialization
        if part_kind is None or (part_text is None and part_file is None):
            try:
                part_dict = self._part_to_dict(part)

                if part_kind is None:
                    part_kind = part_dict.get('kind')
                if part_text is None:
                    part_text = part_dict.get('text')
                if part_file is None:
                    part_file = part_dict.get('file')

                if self.debug and part_dict:
                    part_json_str = json.dumps(part_dict, default=str)
                    logger.info(
                        f"DEBUG: Part {index} JSON: {part_json_str[:200]}...")
            except Exception as e:
                if self.debug:
                    logger.error(f"DEBUG: Error accessing part as dict: {e}")
                    import traceback
                    traceback.print_exc()

        return part_kind, part_text, part_file

    def _part_to_dict(self, part: Any) -> dict:
        """Convert part to dictionary using multiple strategies.

        Args:
            part: Part object

        Returns:
            Dictionary representation of part
        """
        if hasattr(part, 'json'):
            return json.loads(part.json())
        elif hasattr(part, 'dict'):
            return part.dict()
        elif hasattr(part, 'model_dump'):
            return part.model_dump()
        elif hasattr(part, '__dict__'):
            return part.__dict__
        else:
            return {}

    def _extract_image(self, file_obj: Any, index: int) -> Optional[tuple[bytes, str]]:
        """Extract and validate image from a file part.

        Args:
            file_obj: File part object
            index: Part index for debugging

        Returns:
            Tuple of (image_bytes, mime_type) or None if extraction fails

        Raises:
            ValueError: If image is invalid or unsupported format
        """
        file_bytes = None
        file_mime_type = None

        # Handle dict first (common case from A2A protocol)
        if isinstance(file_obj, dict):
            file_bytes = file_obj.get('bytes')
            file_mime_type = file_obj.get(
                'mimeType') or file_obj.get('mime_type')
            if self.debug:
                logger.info(
                    f"DEBUG: File dict access - bytes present: {file_bytes is not None}, mime_type: {file_mime_type}")
        else:
            # Method 1: Direct attribute access
            file_bytes = getattr(file_obj, 'bytes', None)
            file_mime_type = getattr(file_obj, 'mimeType', None) or getattr(
                file_obj, 'mime_type', None)

            # Method 2: Try dict access via _part_to_dict
            if file_bytes is None:
                try:
                    file_dict = self._part_to_dict(file_obj)
                    file_bytes = file_dict.get('bytes')
                    file_mime_type = file_dict.get(
                        'mimeType') or file_dict.get('mime_type')

                    if self.debug:
                        logger.info(
                            f"DEBUG: File dict access - bytes present: {file_bytes is not None}, mime_type: {file_mime_type}")
                except Exception as e:
                    if self.debug:
                        logger.error(
                            f"DEBUG: Error accessing file as dict: {e}")
                        import traceback
                        traceback.print_exc()

        if self.debug:
            file_debug = f"DEBUG: Found file part, has bytes={file_bytes is not None}, has uri={hasattr(file_obj, 'uri') or (isinstance(file_obj, dict) and 'uri' in file_obj)}"
            logger.info(file_debug)

        # Handle FileWithBytes (base64-encoded) - only local uploads supported
        if file_bytes:
            return self._process_image_bytes(file_bytes, file_mime_type, index)
        elif hasattr(file_obj, 'uri') or (isinstance(file_obj, dict) and 'uri' in file_obj):
            # FileWithUri not supported - only local file uploads
            error_msg = 'Only local file uploads (FileWithBytes) are supported. FileWithUri is not supported.'
            if self.debug:
                logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        else:
            error_msg = f'File part found but no bytes or uri attribute. File object type: {type(file_obj)}, file_obj: {str(file_obj)[:200]}'
            if self.debug:
                logger.error(error_msg)
            raise ValueError(error_msg)

    def _process_image_bytes(self, file_bytes: str, file_mime_type: Optional[str], index: int) -> tuple[bytes, str]:
        """Process base64-encoded image bytes.

        Args:
            file_bytes: Base64-encoded image string
            file_mime_type: MIME type of the image
            index: Part index for debugging

        Returns:
            Tuple of (decoded_bytes, mime_type)

        Raises:
            ValueError: If image is invalid or exceeds size limit
        """
        try:
            if self.debug:
                decode_debug = f"DEBUG: Decoding base64 image (base64 length: {len(file_bytes)})"
                logger.info(decode_debug)

            image_bytes = base64.b64decode(file_bytes)
            image_mime_type = file_mime_type or 'image/jpeg'

            if self.debug:
                decoded_debug = f"DEBUG: Decoded image - size: {len(image_bytes)} bytes, mime_type: {image_mime_type}"
                logger.info(decoded_debug)

            # Validate MIME type
            if image_mime_type not in self.VALID_IMAGE_TYPES:
                raise ValueError(
                    f'Unsupported image type: {image_mime_type}. Supported types: {self.VALID_IMAGE_TYPES}')

            # Validate size
            if len(image_bytes) > self.MAX_IMAGE_SIZE:
                raise ValueError(
                    f'Image size ({len(image_bytes)} bytes) exceeds maximum ({self.MAX_IMAGE_SIZE} bytes)')

            if self.debug:
                logger.info("DEBUG: Image validation passed")

            return image_bytes, image_mime_type

        except Exception as e:
            error_debug = f"DEBUG: Error processing image: {e}"
            if self.debug:
                logger.error(error_debug)
                import traceback
                traceback.print_exc()
            raise ValueError(f'Failed to process image file: {e}')

    def _log_message_structure(self, context: RequestContext) -> None:
        """Log message structure for debugging.

        Args:
            context: Request context
        """
        logger.info("DEBUG: ====== START EXECUTE ======")
        logger.info(f"DEBUG: context.message type: {type(context.message)}")

        # Try to serialize message to see its structure
        try:
            if hasattr(context.message, '__dict__'):
                msg_dict = context.message.__dict__
                logger.info(
                    f"DEBUG: Message __dict__ keys: {list(msg_dict.keys())}")

            if hasattr(context.message, 'model_dump'):
                msg_json = json.dumps(
                    context.message.model_dump(), default=str)
                logger.info(
                    f"DEBUG: Message as JSON (first 500 chars): {msg_json[:500]}")
        except Exception as e:
            logger.info(f"DEBUG: Could not serialize message: {e}")

        # Log each part
        message_parts = self._extract_parts(context.message)
        for i, part in enumerate(message_parts):
            part_info = f"DEBUG: Part {i}: {type(part)}, dir: {[a for a in dir(part) if not a.startswith('_')][:10]}"
            logger.info(part_info)
            try:
                if hasattr(part, 'model_dump'):
                    part_json = json.dumps(part.model_dump(), default=str)
                    logger.info(f"DEBUG: Part {i} JSON: {part_json[:200]}")
            except:
                pass
