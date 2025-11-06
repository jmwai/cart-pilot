"""
Content builder for creating ADK Content objects from parsed messages.

This module handles converting parsed A2A messages into ADK Content format,
with support for multimodal content (text + images).
"""

import inspect
import logging
from typing import Optional

from google.genai import types

from app.utils.message_parser import ParsedMessage

logger = logging.getLogger(__name__)


class ContentBuilder:
    """Builds ADK Content from parsed messages."""

    def __init__(self, debug: bool = False):
        """Initialize content builder.

        Args:
            debug: Enable debug logging (default: False)
        """
        self.debug = debug

    def build(self, parsed_message: ParsedMessage) -> types.Content:
        """Build ADK Content from parsed message.

        Args:
            parsed_message: Parsed message containing text and/or image data

        Returns:
            ADK Content object with appropriate parts
        """
        parts = []

        # Add text part if exists
        if parsed_message.text_query:
            parts.append(types.Part.from_text(text=parsed_message.text_query))

        # Add image part if exists
        if parsed_message.image_bytes:
            image_part = self._create_image_part(
                parsed_message.image_bytes,
                parsed_message.image_mime_type
            )
            if image_part:
                parts.append(image_part)

        # Ensure at least one part exists
        if not parts:
            parts.append(types.Part.from_text(text=""))

        content = types.Content(role='user', parts=parts)

        if self.debug:
            logger.info(
                f"DEBUG: Created Content with {len(parts)} parts (text: {bool(parsed_message.text_query)}, image: {bool(parsed_message.image_bytes)})")

        return content

    def _create_image_part(
        self,
        image_bytes: bytes,
        mime_type: Optional[str]
    ) -> Optional[types.Part]:
        """Create image part, handling multiple ADK formats.

        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Part object with image data, or None if creation fails
        """
        try:
            # Method 1: Try from_inline_data if it exists
            if hasattr(types.Part, 'from_inline_data'):
                part = types.Part.from_inline_data(
                    data=image_bytes,
                    mime_type=mime_type
                )
                if self.debug:
                    logger.info(
                        f"DEBUG: Added image to Content using from_inline_data, size: {len(image_bytes)} bytes")
                return part

            # Method 2: Try creating Part with inline_data parameter
            if hasattr(types.Part, '__init__'):
                sig = inspect.signature(types.Part.__init__)
                params = list(sig.parameters.keys())

                if self.debug:
                    logger.info(f"DEBUG: Part.__init__ parameters: {params}")

                # Try common parameter names
                if 'inline_data' in params:
                    return types.Part(
                        inline_data={'data': image_bytes, 'mime_type': mime_type})
                elif 'data' in params and 'mime_type' in params:
                    return types.Part(
                        data=image_bytes, mime_type=mime_type)

            # Fallback: Cannot create image part
            if self.debug:
                logger.warning(
                    f"DEBUG: Cannot create image Part - storing in state only")
            return None

        except Exception as e:
            logger.warning(f"Failed to create image part: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            # Don't raise - image will be read from state
            if self.debug:
                logger.info(
                    f"DEBUG: Continuing without image in Content - image will be read from state")
            return None
