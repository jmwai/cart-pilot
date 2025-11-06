"""
Status message handler for dynamic status updates based on tool calls.

This module handles updating task status messages via A2A protocol
when tools are called during agent execution.
"""

import logging
from typing import Optional, Dict, Any

from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from app.utils.constants import TOOL_STATUS_MESSAGES

logger = logging.getLogger(__name__)


class StatusMessageHandler:
    """Handles dynamic status messages based on tool calls."""

    def __init__(self, status_messages: Dict[str, str], default_message: str = 'Processing your request...'):
        """Initialize status message handler.

        Args:
            status_messages: Dictionary mapping function names to status messages
            default_message: Default message to use if function not found
        """
        self.status_messages = status_messages
        self.default_message = default_message
        self.last_function_name: Optional[str] = None

    async def handle_function_call(
        self,
        function_call: any,
        updater: TaskUpdater,
        task: Any  # Task object from a2a.utils.new_task()
    ) -> Optional[str]:
        """Handle function call and update status if needed.

        Args:
            function_call: Function call object from ADK event
            updater: A2A TaskUpdater for sending status updates
            task: Current task object (from a2a.utils.new_task())

        Returns:
            Function name if status was updated, None otherwise
        """
        function_name = self._extract_function_name(function_call)

        if not function_name:
            return None

        # Update status message if function name found and different from last
        if function_name != self.last_function_name:
            if function_name in self.status_messages:
                status_message = self.status_messages[function_name]
                logger.info(
                    f"Updating status for function call: {function_name} -> {status_message}")
                # Send TaskStatusUpdateEvent via A2A streaming protocol
                await updater.update_status(
                    TaskState.working,  # A2A TaskState enum value
                    new_agent_text_message(  # Creates A2A Message with TextPart
                        status_message, task.context_id, task.id
                    ),
                )
                self.last_function_name = function_name
                return function_name
            else:
                # Log unknown function for future addition to mapping
                logger.debug(
                    f"Function '{function_name}' not in TOOL_STATUS_MESSAGES mapping")

        return None

    def _extract_function_name(self, function_call: any) -> Optional[str]:
        """Extract function name from function call object.

        Args:
            function_call: Function call object

        Returns:
            Function name or None if not found
        """
        # Try multiple ways to extract function name (defensive programming)
        if hasattr(function_call, 'name'):
            return function_call.name
        elif hasattr(function_call, 'function_name'):
            return function_call.function_name
        elif isinstance(function_call, dict):
            return function_call.get('name') or function_call.get('function_name')
        return None
