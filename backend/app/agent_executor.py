"""
Agent Executor for Shopping Assistant - A2A Protocol

This module implements the executor that bridges A2A protocol to ADK agents.
It handles incoming A2A requests and executes them using the ADK shopping agent.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Part,
    TaskState,
    TextPart,
    DataPart,
)
from a2a.utils import new_agent_text_message, new_task
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.shopping_agent import root_agent as shopping_agent
from app.utils.constants import TOOL_STATUS_MESSAGES
from app.utils.artifact_formatter import ArtifactFormatter
from app.utils.message_parser import MessageParser
from app.utils.session_manager import SessionManager
from app.utils.content_builder import ContentBuilder
from app.utils.state_tracker import StateTracker
from app.utils.artifact_streamer import ArtifactStreamer
from app.utils.status_message_handler import StatusMessageHandler

logger = logging.getLogger(__name__)


class ShoppingAgentExecutor(AgentExecutor):
    """Executor that bridges A2A protocol to ADK agents."""

    def __init__(
        self,
        agent=None,
        status_message='Processing your shopping request...',
        artifact_name='response',
    ):
        """Initialize the shopping agent executor.

        Args:
            agent: The ADK agent instance (defaults to shopping_agent)
            status_message: Message to display while processing
            artifact_name: Name for the response artifact
        """
        self.agent = agent or shopping_agent
        self.status_message = status_message
        self.artifact_name = artifact_name

        # Initialize ADK Runner with in-memory services
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel the execution of a specific task."""
        raise NotImplementedError(
            'Cancellation is not implemented for ShoppingAgentExecutor.'
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a task received via A2A protocol."""
        # Parse message to extract text and image data
        # Set to True for debug logging
        message_parser = MessageParser(debug=False)
        parsed_message = message_parser.parse(context)

        text_query = parsed_message.text_query
        image_bytes = parsed_message.image_bytes
        image_mime_type = parsed_message.image_mime_type

        # Create or use existing task
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)

        # Create task updater for status updates
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        # Extract user ID from call context
        if context.call_context:
            user_id = context.call_context.user.user_name
        else:
            user_id = 'a2a_user'

        try:
            # Update status with custom message
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    self.status_message, task.context_id, task.id
                ),
            )

            # Create or get session - preserve existing state if session exists
            session_id = task.context_id  # Use context_id as session_id

            # Initialize session manager
            session_manager = SessionManager(
                runner=self.runner,
                agent_name=self.agent.name,
                debug=False
            )

            # Prepare initial state with image if available
            initial_state = {}
            if image_bytes:
                initial_state["current_image_bytes"] = image_bytes
                initial_state["current_image_mime_type"] = image_mime_type

            # Get or create session
            session = await session_manager.get_or_create_session(
                user_id=user_id,
                session_id=session_id,
                initial_state=initial_state if initial_state else None
            )

            # If session existed and we have an image, update it
            if image_bytes:
                await session_manager.update_session_state(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    updates={
                        "current_image_bytes": image_bytes,
                        "current_image_mime_type": image_mime_type
                    }
                )
                # Re-fetch session to get updated state
                session = await session_manager.get_session(user_id, session_id)

            # Create ADK content message with multimodal parts
            content_builder = ContentBuilder(debug=False)
            content = content_builder.build(parsed_message)

            # Store image in state BEFORE Runner starts - this is critical!
            # The tool will read from state, so we must ensure it's persisted
            if image_bytes:
                await session_manager.update_session_state(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    updates={
                        "current_image_bytes": image_bytes,
                        "current_image_mime_type": image_mime_type
                    }
                )
                # Re-fetch session to get updated state
                session = await session_manager.get_session(user_id, session_id)

            # Track accumulated text
            accumulated_text = ''

            # Track initial state to detect modifications
            initial_state = await session_manager.get_session_state(
                user_id=user_id,
                session_id=session_id
            )
            tracker = StateTracker(initial_state)
            initial_products = tracker.initial_products
            initial_cart = tracker.initial_cart
            initial_order = tracker.initial_order
            initial_order_summary = tracker.initial_order_summary

            # Initialize artifact formatter and streamer
            formatter = ArtifactFormatter()
            streamer = ArtifactStreamer(
                updater=updater,
                formatter=formatter,
                tracker=tracker
            )

            # Initialize status handler
            status_handler = StatusMessageHandler(
                status_messages=TOOL_STATUS_MESSAGES,
                default_message=self.status_message
            )

            # Process with ADK agent - stream events as they arrive
            # ADK Runner automatically persists state changes made through tool_context.state
            async for event in self.runner.run_async(
                user_id=user_id, session_id=session_id, new_message=content
            ):
                # Stream text chunks incrementally
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_chunk = part.text
                            accumulated_text += text_chunk
                            # Stream incremental text updates
                            await updater.add_artifact(
                                [Part(root=TextPart(text=text_chunk))],
                                name=self.artifact_name,
                            )
                        elif hasattr(part, 'function_call'):
                            # Handle function call and update status
                            await status_handler.handle_function_call(
                                part.function_call,
                                updater,
                                task
                            )

                # Handle final response - ensure any remaining artifacts are sent
                if event.is_final_response():
                    try:
                        current_session = await session_manager.get_session(
                            user_id=user_id,
                            session_id=session_id
                        )
                        session_state = current_session.state if hasattr(
                            current_session, 'state') else {}

                        # Stream any remaining artifacts
                        await streamer.stream_if_changed("order_summary", session_state)
                        await streamer.stream_if_changed("order", session_state)
                    except Exception as final_state_error:
                        logger.error(
                            f"Error processing final response state: {final_state_error}")
                        pass

                # Check for state updates (products, cart) periodically
                # Check state after every event, but only send if available and not already sent
                if not event.is_final_response():
                    try:
                        current_session = await session_manager.get_session(
                            user_id=user_id,
                            session_id=session_id
                        )
                        session_state = current_session.state if hasattr(
                            current_session, 'state') else {}

                        # Stream artifacts if state changed
                        await streamer.stream_if_changed("products", session_state)
                        await streamer.stream_if_changed("cart", session_state)
                        await streamer.stream_if_changed("order_summary", session_state)
                        await streamer.stream_if_changed("order", session_state)
                    except Exception as state_error:
                        # Don't fail the entire request if state check fails
                        # Log error but continue processing
                        pass

            # After agent execution, ensure all artifacts are sent
            session_state = await session_manager.get_session_state(
                user_id=user_id,
                session_id=session_id
            )
            await streamer.ensure_all_sent(session_state)

            # Complete the task - ensure this always happens
            try:
                logger.info("Completing task and sending completion event")
                await updater.complete()
                logger.info("Task completed successfully")
            except Exception as complete_error:
                logger.error(f"Error completing task: {complete_error}")
                # Still try to mark as complete even if there's an error
                try:
                    await updater.complete()
                except:
                    pass

        except Exception as e:
            # Handle errors gracefully
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Error: {e!s}', task.context_id, task.id
                ),
                final=True,
            )
