"""
Agent Executor for Shopping Assistant - A2A Protocol

This module implements the executor that bridges A2A protocol to ADK agents.
It handles incoming A2A requests and executes them using the ADK shopping agent.
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

from app.shopping_agent import root_agent as shopping_agent


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

            # Create or get session - preserve existing state if session exists
            session_id = task.context_id  # Use context_id as session_id

            # Always try to get existing session first to preserve state
            session = None
            try:
                session = await self.runner.session_service.get_session(
                    app_name=self.agent.name,
                    user_id=user_id,
                    session_id=session_id
                )
                # Log existing state for debugging
                if session and hasattr(session, 'state'):
                    state_keys = list(session.state.keys()
                                      ) if session.state else []
                    print(
                        f"DEBUG: Retrieved existing session {session_id} with state keys: {state_keys}")
            except Exception as e:
                # Session doesn't exist, create new one
                print(
                    f"DEBUG: Session {session_id} not found, creating new one: {e}")
                session = await self.runner.session_service.create_session(
                    app_name=self.agent.name,
                    user_id=user_id,
                    state={},
                    session_id=session_id,
                )

            # Verify session was created/retrieved
            if not session:
                raise ValueError(
                    f"Failed to create or retrieve session with id: {session_id}")

            # Create ADK content message
            content = types.Content(
                role='user', parts=[types.Part.from_text(text=query)]
            )

            # Track accumulated text and artifacts
            accumulated_text = ''
            products_sent = False
            cart_sent = False
            order_sent = False

            # Helper function to format products
            def format_products(products_list):
                formatted = []
                for product in products_list:
                    price_usd_units = product.get("price_usd_units")
                    price = 0.0
                    if price_usd_units:
                        price = float(price_usd_units) / 100.0
                    image_url = product.get(
                        "product_image_url") or product.get("picture") or ""
                    formatted.append({
                        "id": product.get("id", ""),
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "image_url": image_url,
                        "price": price,
                        "price_usd_units": price_usd_units,
                        "distance": product.get("distance", 0.0)
                    })
                return formatted

            # Helper function to format cart
            def format_cart(cart_state):
                cart_data = cart_state.get(
                    "cart") or cart_state.get("cart_items")
                if not cart_data:
                    return None
                if isinstance(cart_data, list):
                    return {
                        "type": "cart",
                        "items": cart_data,
                        "total_items": len(cart_data),
                        "subtotal": sum(item.get("subtotal", 0.0) for item in cart_data)
                    }
                return None

            # Helper function to format order
            def format_order(order_state):
                order_data = order_state.get("current_order")
                if not order_data:
                    return None
                return {
                    "type": "order",
                    "order_id": order_data.get("order_id", ""),
                    "status": order_data.get("status", ""),
                    "items": order_data.get("items", []),
                    "total_amount": order_data.get("total_amount", 0.0),
                    "shipping_address": order_data.get("shipping_address", ""),
                    "created_at": order_data.get("created_at", ""),
                }

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
                            # Function calls are handled internally by ADK
                            pass

                # Check for state updates (products, cart) periodically
                # Check state after every event, but only send if available and not already sent
                if not event.is_final_response():
                    try:
                        current_session = await self.runner.session_service.get_session(
                            app_name=self.agent.name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        session_state = current_session.state if hasattr(
                            current_session, 'state') else {}

                        # Stream products if available and not already sent
                        if not products_sent and "current_results" in session_state:
                            current_results = session_state.get(
                                "current_results", [])
                            if current_results:
                                formatted_products = format_products(
                                    current_results)
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
                                    products_sent = True

                        # Stream cart if available and not already sent
                        if not cart_sent and ("cart" in session_state or "cart_items" in session_state):
                            cart_artifact_data = format_cart(session_state)
                            if cart_artifact_data:
                                await updater.add_artifact(
                                    [Part(root=DataPart(
                                        data=cart_artifact_data,
                                        mimeType="application/json"
                                    ))],
                                    name="cart"
                                )
                                cart_sent = True

                        # Stream order if available and not already sent
                        if not order_sent and "current_order" in session_state:
                            order_artifact_data = format_order(session_state)
                            if order_artifact_data:
                                await updater.add_artifact(
                                    [Part(root=DataPart(
                                        data=order_artifact_data,
                                        mimeType="application/json"
                                    ))],
                                    name="order"
                                )
                                order_sent = True
                    except Exception as state_error:
                        # Don't fail the entire request if state check fails
                        # Log error but continue processing
                        pass

            # After agent execution, ensure all artifacts are sent
            # Get final session state
            updated_session = await self.runner.session_service.get_session(
                app_name=self.agent.name,
                user_id=user_id,
                session_id=session_id
            )

            session_state = updated_session.state if hasattr(
                updated_session, 'state') else {}

            # Ensure products are sent if not already sent
            if not products_sent:
                current_results = session_state.get("current_results", [])
                if current_results:
                    formatted_products = format_products(current_results)
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

            # Ensure cart is sent if not already sent
            if not cart_sent:
                cart_artifact_data = format_cart(session_state)
                if cart_artifact_data:
                    await updater.add_artifact(
                        [Part(root=DataPart(
                            data=cart_artifact_data,
                            mimeType="application/json"
                        ))],
                        name="cart"
                    )

            # Ensure order is sent if not already sent
            if not order_sent:
                order_artifact_data = format_order(session_state)
                if order_artifact_data:
                    await updater.add_artifact(
                        [Part(root=DataPart(
                            data=order_artifact_data,
                            mimeType="application/json"
                        ))],
                        name="order"
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
