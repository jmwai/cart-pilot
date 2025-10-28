"""
Agent Executor for Shopping Assistant - A2A Protocol

This module implements the executor that bridges A2A protocol to ADK agents.
It handles incoming A2A requests and executes them using the ADK orchestrator.
"""

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

from app.orchestrator_agent import root_agent as shopping_orchestrator


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
            agent: The ADK agent instance (defaults to shopping_orchestrator)
            status_message: Message to display while processing
            artifact_name: Name for the response artifact
        """
        self.agent = agent or shopping_orchestrator
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
        if not context.message:
            raise ValueError('Message should be present in request context')

        # Get user input from context
        query = context.get_user_input()

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

            # Create or get session
            session = await self.runner.session_service.create_session(
                app_name=self.agent.name,
                user_id=user_id,
                state={},
                session_id=task.context_id,
            )

            # Create ADK content message
            content = types.Content(
                role='user', parts=[types.Part.from_text(text=query)]
            )

            # Process with ADK agent
            response_text = ''
            products = []

            async for event in self.runner.run_async(
                user_id=user_id, session_id=session.id, new_message=content
            ):
                if (
                    event.is_final_response()
                    and event.content
                    and event.content.parts
                ):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text + '\n'
                        elif hasattr(part, 'function_call'):
                            # Function calls are handled internally by ADK
                            pass

                # Check for tool results that might contain product data
                if hasattr(event, 'tool_result') and event.tool_result:
                    result_data = event.tool_result
                    # Handle different result formats
                    if isinstance(result_data, list) and len(result_data) > 0:
                        # Check if this looks like product data
                        first_item = result_data[0]
                        if isinstance(first_item, dict) and 'id' in first_item and 'name' in first_item:
                            products = result_data
                    elif isinstance(result_data, dict):
                        # Check if it's wrapped in a products key
                        if 'products' in result_data and isinstance(result_data['products'], list):
                            products = result_data['products']
                        # Or if the dict itself represents a product list structure
                        elif 'type' in result_data and result_data.get('type') == 'product_list':
                            products = result_data.get('products', [])

            # Add text response as artifact
            await updater.add_artifact(
                [Part(root=TextPart(text=response_text))],
                name=self.artifact_name,
            )

            # If we found products, add them as a separate DataPart artifact
            if products:
                import json
                product_data = {
                    "type": "product_list",
                    "products": products
                }
                await updater.add_artifact(
                    [Part(root=DataPart(
                        data=product_data,
                        mimeType="application/json"
                    ))],
                    name="products"
                )

            # Complete the task
            await updater.complete()

        except Exception as e:
            # Handle errors gracefully
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Error: {e!s}', task.context_id, task.id
                ),
                final=True,
            )
