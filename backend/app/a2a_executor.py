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
            cart_data = None

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

            # After agent execution, get updated session to access state
            updated_session = await self.runner.session_service.get_session(
                app_name=self.agent.name,
                user_id=user_id,
                session_id=session.id
            )

            # Extract products from session state
            session_state = updated_session.state if hasattr(
                updated_session, 'state') else {}
            current_results = session_state.get("current_results", [])

            # Format products with all required fields
            formatted_products = []
            if current_results:
                for product in current_results:
                    # Calculate price in dollars from price_usd_units (cents)
                    price_usd_units = product.get("price_usd_units")
                    price = 0.0
                    if price_usd_units:
                        price = float(price_usd_units) / 100.0

                    # Ensure image URL is always present
                    image_url = product.get(
                        "product_image_url") or product.get("picture") or ""

                    formatted_products.append({
                        "id": product.get("id", ""),
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "image_url": image_url,
                        "price": price,
                        "price_usd_units": price_usd_units,
                        "distance": product.get("distance", 0.0)
                    })

            # Check for cart data (from cart agent output or state)
            # Cart might be in state or need to be fetched
            if "cart" in session_state:
                cart_data = session_state.get("cart")
            elif "cart_items" in session_state:
                cart_data = session_state.get("cart_items")

            # Add text response as artifact
            await updater.add_artifact(
                [Part(root=TextPart(text=response_text))],
                name=self.artifact_name,
            )

            # Add products as DataPart artifact if found
            if formatted_products:
                product_data = {
                    "type": "product_list",
                    "products": formatted_products
                }
                await updater.add_artifact(
                    [Part(root=DataPart(
                        data=product_data,
                        mimeType="application/json"
                    ))],
                    name="products"
                )

            # Add cart as DataPart artifact if found
            if cart_data:
                cart_artifact_data = {
                    "type": "cart",
                    "items": cart_data if isinstance(cart_data, list) else [],
                    "total_items": len(cart_data) if isinstance(cart_data, list) else 0,
                    "subtotal": sum(item.get("subtotal", 0.0) for item in cart_data) if isinstance(cart_data, list) else 0.0
                }
                await updater.add_artifact(
                    [Part(root=DataPart(
                        data=cart_artifact_data,
                        mimeType="application/json"
                    ))],
                    name="cart"
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
