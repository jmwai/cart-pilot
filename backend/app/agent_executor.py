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

logger = logging.getLogger(__name__)

# Tool name -> Status message mapping for dynamic status updates
# Maps function names to user-friendly status messages sent via A2A TaskStatusUpdateEvent
TOOL_STATUS_MESSAGES = {
    # Product Discovery
    'text_vector_search': 'Searching for products...',
    'image_vector_search': 'Finding visually similar products...',

    # Cart Operations
    'add_to_cart': 'Adding item to cart...',
    'get_cart': 'Loading your cart...',
    'update_cart_item': 'Updating cart...',
    'remove_from_cart': 'Removing item from cart...',
    'clear_cart': 'Clearing cart...',
    'get_cart_total': 'Calculating cart total...',

    # Checkout
    'create_order': 'Processing your order...',
    'get_order_status': 'Checking order status...',
    'cancel_order': 'Canceling order...',
    'validate_cart_for_checkout': 'Validating cart...',

    # Customer Service
    'create_inquiry': 'Creating your inquiry...',
    'get_inquiry_status': 'Checking inquiry status...',
    'search_faq': 'Searching FAQ...',
    'initiate_return': 'Initiating return...',
    'get_order_inquiries': 'Retrieving order inquiries...',
}


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

        # Debug: Log message structure to understand how parts are accessed
        # Use both logger and print to ensure we see output
        print("=" * 80, flush=True)
        print("DEBUG: ====== START EXECUTE ======", flush=True)
        print(
            f"DEBUG: context.message type: {type(context.message)}", flush=True)

        # Try to serialize message to see its structure
        import json
        try:
            if hasattr(context.message, '__dict__'):
                msg_dict = context.message.__dict__
                print(
                    f"DEBUG: Message __dict__ keys: {list(msg_dict.keys())}", flush=True)
            # Try to convert to dict if possible
            if hasattr(context.message, 'model_dump'):
                msg_json = json.dumps(
                    context.message.model_dump(), default=str)
                print(
                    f"DEBUG: Message as JSON (first 500 chars): {msg_json[:500]}", flush=True)
        except Exception as e:
            print(f"DEBUG: Could not serialize message: {e}", flush=True)

        logger.info("DEBUG: ====== START EXECUTE ======")
        logger.info(f"DEBUG: context.message type: {type(context.message)}")

        # Try multiple ways to access parts
        message_parts = []
        if hasattr(context.message, 'parts'):
            message_parts = context.message.parts
            print(
                f"DEBUG: Found parts via context.message.parts: {len(message_parts) if message_parts else 0}", flush=True)
            logger.info(
                f"DEBUG: Found parts via context.message.parts: {len(message_parts) if message_parts else 0}")
            # Log each part
            for i, part in enumerate(message_parts):
                part_info = f"DEBUG: Part {i}: {type(part)}, dir: {[a for a in dir(part) if not a.startswith('_')][:10]}"
                print(part_info, flush=True)
                logger.info(part_info)
                # Try to serialize part
                try:
                    if hasattr(part, 'model_dump'):
                        part_json = json.dumps(part.model_dump(), default=str)
                        print(
                            f"DEBUG: Part {i} JSON: {part_json[:200]}", flush=True)
                except:
                    pass
        else:
            print(
                "DEBUG: context.message.parts not found, trying alternatives...", flush=True)
            logger.info(
                f"DEBUG: context.message.parts not found, trying alternatives...")
            # Check if message has a different structure
            if hasattr(context.message, 'message') and hasattr(context.message.message, 'parts'):
                message_parts = context.message.message.parts
                print(
                    f"DEBUG: Found parts via context.message.message.parts: {len(message_parts)}", flush=True)
                logger.info(
                    f"DEBUG: Found parts via context.message.message.parts: {len(message_parts)}")
            elif isinstance(context.message, dict) and 'parts' in context.message:
                message_parts = context.message['parts']
                print(
                    f"DEBUG: Found parts via dict access: {len(message_parts)}", flush=True)
                logger.info(
                    f"DEBUG: Found parts via dict access: {len(message_parts)}")
            else:
                # Try to inspect the message object more deeply
                print(
                    f"DEBUG: Inspecting message object: {dir(context.message)}", flush=True)
                if hasattr(context.message, '__dict__'):
                    print(
                        f"DEBUG: Message __dict__: {context.message.__dict__}", flush=True)
                # Try get_user_input to see what's there
                try:
                    user_input = context.get_user_input()
                    print(
                        f"DEBUG: get_user_input() returned: {user_input[:200] if user_input else 'None'}", flush=True)
                except Exception as e:
                    print(f"DEBUG: get_user_input() failed: {e}", flush=True)

        text_query = None
        image_bytes = None
        image_mime_type = None

        print(
            f"DEBUG: Processing message with {len(message_parts)} parts", flush=True)
        logger.info(
            f"DEBUG: Processing message with {len(message_parts)} parts")

        # Process message parts to extract text and file parts
        for i, part in enumerate(message_parts):
            # Try multiple ways to access part attributes (Pydantic models)
            part_kind = None
            part_text = None
            part_file = None

            # Method 1: Direct attribute access
            part_kind = getattr(part, 'kind', None)
            part_text = getattr(part, 'text', None)
            part_file = getattr(part, 'file', None)

            # Method 2: Try JSON serialization (we know this works from earlier logs)
            if part_kind is None or (part_text is None and part_file is None):
                try:
                    import json
                    if hasattr(part, 'json'):
                        part_json_str = part.json()
                        part_dict = json.loads(part_json_str)
                        print(
                            f"DEBUG: Part {i} JSON: {part_json_str[:200]}...", flush=True)
                    elif hasattr(part, 'dict'):
                        part_dict = part.dict()
                    elif hasattr(part, 'model_dump'):
                        part_dict = part.model_dump()
                    elif hasattr(part, '__dict__'):
                        part_dict = part.__dict__
                    else:
                        part_dict = {}

                    if part_kind is None:
                        part_kind = part_dict.get('kind')
                    if part_text is None:
                        part_text = part_dict.get('text')
                    if part_file is None:
                        part_file = part_dict.get('file')
                except Exception as e:
                    print(
                        f"DEBUG: Error accessing part as dict: {e}", flush=True)
                    import traceback
                    traceback.print_exc()

            part_debug = f"DEBUG: Part {i}: kind={part_kind}, has_text={part_text is not None}, has_file={part_file is not None}"
            print(part_debug, flush=True)
            logger.info(part_debug)

            # Handle text parts
            if part_kind == 'text' and part_text:
                text_query = part_text
                text_debug = f"DEBUG: Extracted text query: {text_query[:50] if len(text_query) > 50 else text_query}..."
                print(text_debug, flush=True)
                logger.info(text_debug)
            # Handle file parts (FilePart - only FileWithBytes supported for local uploads)
            elif part_kind == 'file' and part_file:
                file_obj = part_file

                # Try to get file attributes
                file_bytes = None
                file_mime_type = None

                # Method 1: Direct attribute access
                file_bytes = getattr(file_obj, 'bytes', None)
                file_mime_type = getattr(file_obj, 'mimeType', None) or getattr(
                    file_obj, 'mime_type', None)

                # Method 2: Try dict access
                if file_bytes is None:
                    try:
                        import json
                        if hasattr(file_obj, 'json'):
                            file_json_str = file_obj.json()
                            file_dict = json.loads(file_json_str)
                        elif hasattr(file_obj, 'dict'):
                            file_dict = file_obj.dict()
                        elif hasattr(file_obj, 'model_dump'):
                            file_dict = file_obj.model_dump()
                        elif hasattr(file_obj, '__dict__'):
                            file_dict = file_obj.__dict__
                        elif isinstance(file_obj, dict):
                            file_dict = file_obj
                        else:
                            file_dict = {}

                        file_bytes = file_dict.get('bytes')
                        file_mime_type = file_dict.get(
                            'mimeType') or file_dict.get('mime_type')
                        print(
                            f"DEBUG: File dict access - bytes present: {file_bytes is not None}, mime_type: {file_mime_type}", flush=True)
                    except Exception as e:
                        print(
                            f"DEBUG: Error accessing file as dict: {e}", flush=True)
                        import traceback
                        traceback.print_exc()

                file_debug = f"DEBUG: Found file part, has bytes={file_bytes is not None}, has uri={hasattr(file_obj, 'uri') or (isinstance(file_obj, dict) and 'uri' in file_obj)}"
                print(file_debug, flush=True)
                logger.info(file_debug)

                # Handle FileWithBytes (base64-encoded) - only local uploads supported
                if file_bytes:
                    import base64
                    try:
                        decode_debug = f"DEBUG: Decoding base64 image (base64 length: {len(file_bytes)})"
                        print(decode_debug, flush=True)
                        logger.info(decode_debug)

                        image_bytes = base64.b64decode(file_bytes)
                        image_mime_type = file_mime_type or 'image/jpeg'

                        decoded_debug = f"DEBUG: Decoded image - size: {len(image_bytes)} bytes, mime_type: {image_mime_type}"
                        print(decoded_debug, flush=True)
                        logger.info(decoded_debug)

                        # Validate MIME type
                        valid_types = ['image/jpeg', 'image/png', 'image/webp']
                        if image_mime_type not in valid_types:
                            raise ValueError(
                                f'Unsupported image type: {image_mime_type}. Supported types: {valid_types}')

                        # Validate size (max 10MB)
                        max_size = 10 * 1024 * 1024  # 10MB
                        if len(image_bytes) > max_size:
                            raise ValueError(
                                f'Image size ({len(image_bytes)} bytes) exceeds maximum ({max_size} bytes)')
                        print("DEBUG: Image validation passed", flush=True)
                        logger.info(f"DEBUG: Image validation passed")
                    except Exception as e:
                        error_debug = f"DEBUG: Error processing image: {e}"
                        print(error_debug, flush=True)
                        logger.error(error_debug)
                        import traceback
                        traceback.print_exc()
                        raise ValueError(f'Failed to process image file: {e}')
                elif hasattr(file_obj, 'uri') or (isinstance(file_obj, dict) and 'uri' in file_obj):
                    # FileWithUri not supported - only local file uploads
                    error_msg = 'Only local file uploads (FileWithBytes) are supported. FileWithUri is not supported.'
                    print(f"DEBUG: {error_msg}", flush=True)
                    raise ValueError(error_msg)
                else:
                    error_msg = f'File part found but no bytes or uri attribute. File object type: {type(file_obj)}, file_obj: {str(file_obj)[:200]}'
                    print(f"DEBUG: {error_msg}", flush=True)
                    logger.error(error_msg)

        # Get text query from context if not found in parts
        if not text_query:
            text_query = context.get_user_input() or ""

        extraction_complete = f"DEBUG: Extraction complete - text_query={'present' if text_query else 'None'}, image_bytes={'present' if image_bytes else 'None'}"
        print(extraction_complete, flush=True)
        logger.info(extraction_complete)

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
            initial_state = {}
            try:
                session = await self.runner.session_service.get_session(
                    app_name=self.agent.name,
                    user_id=user_id,
                    session_id=session_id
                )
                # Log existing state for debugging
                if session and hasattr(session, 'state'):
                    initial_state = session.state if session.state else {}
                    state_keys = list(initial_state.keys())
                    logger.info(
                        f"DEBUG: Retrieved existing session {session_id} with state keys: {state_keys}")
            except Exception as e:
                # Session doesn't exist or error occurred
                logger.info(
                    f"DEBUG: Session {session_id} get_session raised exception: {e}")

            # If session is None (either get_session returned None or raised exception), create new one
            if session is None:
                logger.info(
                    f"DEBUG: Session {session_id} not found, creating new one (app_name={self.agent.name}, user_id={user_id})")
                # Prepare initial state with image if available
                initial_state = {}
                if image_bytes:
                    initial_state["current_image_bytes"] = image_bytes
                    initial_state["current_image_mime_type"] = image_mime_type
                try:
                    session = await self.runner.session_service.create_session(
                        app_name=self.agent.name,
                        user_id=user_id,
                        state=initial_state,
                        session_id=session_id,
                    )
                    logger.info(
                        f"DEBUG: Successfully created session {session_id} with initial state keys: {list(initial_state.keys())}")
                except Exception as create_error:
                    logger.error(
                        f"DEBUG: Failed to create session {session_id}: {create_error}")
                    raise ValueError(
                        f"Failed to create session with id: {session_id} (app_name={self.agent.name}, user_id={user_id}): {create_error}")
            else:
                # Session exists - update state with image if available
                if image_bytes:
                    # Ensure session has state dictionary
                    if not hasattr(session, 'state') or session.state is None:
                        session.state = {}

                    # Store image bytes in state
                    session.state["current_image_bytes"] = image_bytes
                    session.state["current_image_mime_type"] = image_mime_type

                    logger.info(
                        f"DEBUG: Updated existing session {session_id} with image (size: {len(image_bytes)} bytes)")
                    logger.info(
                        f"DEBUG: Session state keys after update: {list(session.state.keys())}")

                    # Explicitly update session to ensure persistence
                    try:
                        if hasattr(self.runner.session_service, 'update_session'):
                            await self.runner.session_service.update_session(session)
                            logger.info(
                                f"DEBUG: Called update_session to persist state")
                    except Exception as update_error:
                        logger.warning(
                            f"DEBUG: update_session not available or failed: {update_error}")

                    # For InMemorySessionService, modifying session.state should persist
                    # but let's verify by re-fetching
                    try:
                        verify_session = await self.runner.session_service.get_session(
                            app_name=self.agent.name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        if verify_session and hasattr(verify_session, 'state'):
                            verify_keys = list(
                                verify_session.state.keys()) if verify_session.state else []
                            verify_image = verify_session.state.get(
                                "current_image_bytes") is not None
                            logger.info(
                                f"DEBUG: Verified session state - keys: {verify_keys}, image present: {verify_image}")
                    except Exception as verify_error:
                        logger.error(
                            f"DEBUG: Could not verify session state: {verify_error}")

            # Verify session was created/retrieved
            if not session:
                raise ValueError(
                    f"Failed to create or retrieve session with id: {session_id} (app_name={self.agent.name}, user_id={user_id})")

            # Create ADK content message with multimodal parts
            parts = []

            # Add text part if exists
            if text_query:
                parts.append(types.Part.from_text(text=text_query))

            # Add image part if exists - pass directly in Content, not state
            if image_bytes:
                # ADK supports inline_data for images
                # Try different methods to create image part
                try:
                    # Method 1: Try from_inline_data if it exists
                    if hasattr(types.Part, 'from_inline_data'):
                        parts.append(types.Part.from_inline_data(
                            data=image_bytes,
                            mime_type=image_mime_type
                        ))
                        print(
                            f"DEBUG: Added image to Content using from_inline_data, size: {len(image_bytes)} bytes", flush=True)
                        logger.info(
                            f"DEBUG: Added image to Content using from_inline_data")
                    # Method 2: Try creating Part with inline_data parameter
                    elif hasattr(types.Part, '__init__'):
                        # Try to inspect Part constructor
                        import inspect
                        sig = inspect.signature(types.Part.__init__)
                        params = list(sig.parameters.keys())
                        print(
                            f"DEBUG: Part.__init__ parameters: {params}", flush=True)

                        # Try common parameter names
                        if 'inline_data' in params:
                            parts.append(types.Part(
                                inline_data={'data': image_bytes, 'mime_type': image_mime_type}))
                        elif 'data' in params and 'mime_type' in params:
                            parts.append(types.Part(
                                data=image_bytes, mime_type=image_mime_type))
                        else:
                            # Fallback: Just store in state, don't add to Content
                            print(
                                f"DEBUG: Cannot create image Part - parameters: {params}. Storing in state only.", flush=True)
                            logger.warning(
                                f"DEBUG: Cannot create image Part - storing in state only")
                    else:
                        # Fallback: Just store in state
                        print(
                            f"DEBUG: Cannot create image Part - Part class doesn't support inline_data. Storing in state only.", flush=True)
                        logger.warning(
                            f"DEBUG: Cannot create image Part - storing in state only")
                except Exception as e:
                    print(
                        f"WARNING: Failed to create image part: {e}", flush=True)
                    logger.warning(f"Failed to create image part: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't raise - just store in state and continue
                    print(
                        f"DEBUG: Continuing without image in Content - image will be read from state", flush=True)

            # Ensure at least one part exists
            if not parts:
                parts.append(types.Part.from_text(text=""))

            content = types.Content(role='user', parts=parts)
            print(
                f"DEBUG: Created Content with {len(parts)} parts (text: {bool(text_query)}, image: {bool(image_bytes)})", flush=True)

            # Store image in state BEFORE Runner starts - this is critical!
            # The tool will read from state, so we must ensure it's persisted
            if image_bytes:
                # Ensure session has state dictionary
                if not hasattr(session, 'state') or session.state is None:
                    session.state = {}

                # Store image bytes in state
                session.state["current_image_bytes"] = image_bytes
                session.state["current_image_mime_type"] = image_mime_type
                print(
                    f"DEBUG: Stored image in state BEFORE Runner (size: {len(image_bytes)} bytes)", flush=True)

                # CRITICAL: Explicitly update session to ensure state persistence
                # For InMemorySessionService, modifying session.state should persist, but let's be explicit
                try:
                    if hasattr(self.runner.session_service, 'update_session'):
                        await self.runner.session_service.update_session(session)
                        print(
                            f"DEBUG: Called update_session to persist image", flush=True)

                    # Verify persistence by re-fetching
                    verify_session = await self.runner.session_service.get_session(
                        app_name=self.agent.name,
                        user_id=user_id,
                        session_id=session_id
                    )
                    if verify_session and hasattr(verify_session, 'state'):
                        verify_keys = list(
                            verify_session.state.keys()) if verify_session.state else []
                        verify_image = verify_session.state.get(
                            "current_image_bytes") is not None
                        print(
                            f"DEBUG: VERIFIED state persistence - keys: {verify_keys}, image present: {verify_image}", flush=True)

                        if not verify_image:
                            print(
                                f"DEBUG: ERROR - Image not persisted! Re-storing...", flush=True)
                            verify_session.state["current_image_bytes"] = image_bytes
                            verify_session.state["current_image_mime_type"] = image_mime_type
                            if hasattr(self.runner.session_service, 'update_session'):
                                await self.runner.session_service.update_session(verify_session)
                            print(
                                f"DEBUG: Re-stored image in state after verification", flush=True)
                except Exception as verify_error:
                    print(
                        f"DEBUG: ERROR during state verification: {verify_error}", flush=True)
                    import traceback
                    traceback.print_exc()

            # Track accumulated text and artifacts
            accumulated_text = ''
            products_sent = False
            cart_sent = False
            order_sent = False
            order_summary_sent = False  # Track if order summary artifact was sent

            # Track initial state to detect modifications
            initial_session = await self.runner.session_service.get_session(
                app_name=self.agent.name,
                user_id=user_id,
                session_id=session_id
            )
            initial_state = initial_session.state if hasattr(
                initial_session, 'state') else {}
            initial_products = initial_state.get("current_results", [])
            initial_cart = initial_state.get(
                "cart") or initial_state.get("cart_items", [])
            initial_order = initial_state.get("current_order")
            initial_order_summary = initial_state.get("pending_order_summary")

            # Helper function to format products
            def format_products(products_list):
                formatted = []
                for product in products_list:
                    price_usd_units = product.get("price_usd_units")
                    price = 0.0
                    if price_usd_units:
                        # price_usd_units is stored as dollars (not cents), use directly
                        # This matches how cart_agent/tools.py handles prices
                        price = float(price_usd_units)
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

            # Helper function to format order summary
            def format_order_summary(summary_state):
                summary_data = summary_state.get("pending_order_summary")
                if not summary_data or summary_data is None or not isinstance(summary_data, dict):
                    return None
                return {
                    "type": "order_summary",
                    "items": summary_data.get("items", []),
                    "total_amount": summary_data.get("total_amount", 0.0),
                    "shipping_address": summary_data.get("shipping_address", ""),
                    "item_count": summary_data.get("item_count", 0),
                }

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
            last_function_name = None  # Track last function to avoid duplicate status updates
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
                            # Extract function name and update status message via A2A TaskStatusUpdateEvent
                            function_call = part.function_call
                            function_name = None

                            # Try multiple ways to extract function name (defensive programming)
                            if hasattr(function_call, 'name'):
                                function_name = function_call.name
                            elif hasattr(function_call, 'function_name'):
                                function_name = function_call.function_name
                            elif isinstance(function_call, dict):
                                function_name = function_call.get(
                                    'name') or function_call.get('function_name')

                            # Update status message if function name found and different from last
                            if function_name and function_name != last_function_name:
                                if function_name in TOOL_STATUS_MESSAGES:
                                    status_message = TOOL_STATUS_MESSAGES[function_name]
                                    logger.info(
                                        f"Updating status for function call: {function_name} -> {status_message}")
                                    # Send TaskStatusUpdateEvent via A2A streaming protocol
                                    await updater.update_status(
                                        TaskState.working,  # A2A TaskState enum value
                                        new_agent_text_message(  # Creates A2A Message with TextPart
                                            status_message, task.context_id, task.id
                                        ),
                                    )
                                    last_function_name = function_name
                                else:
                                    # Log unknown function for future addition to mapping
                                    logger.debug(
                                        f"Function '{function_name}' not in TOOL_STATUS_MESSAGES mapping")
                                    # Optionally update with generic message for unknown functions
                                    # Uncomment below if desired:
                                    # await updater.update_status(
                                    #     TaskState.working,
                                    #     new_agent_text_message(
                                    #         self.status_message, task.context_id, task.id
                                    #     ),
                                    # )

                # Handle final response - ensure any remaining artifacts are sent
                if event.is_final_response():
                    try:
                        current_session = await self.runner.session_service.get_session(
                            app_name=self.agent.name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        session_state = current_session.state if hasattr(
                            current_session, 'state') else {}

                        # Send order summary if it was prepared but not yet sent
                        if not order_summary_sent and "pending_order_summary" in session_state:
                            current_order_summary = session_state.get(
                                "pending_order_summary")
                            # Only send if summary is new (different from initial) and not None
                            if current_order_summary and current_order_summary is not None and current_order_summary != initial_order_summary:
                                order_summary_artifact_data = format_order_summary(
                                    session_state)
                                if order_summary_artifact_data:
                                    await updater.add_artifact(
                                        [Part(root=DataPart(
                                            data=order_summary_artifact_data,
                                            mimeType="application/json"
                                        ))],
                                        name="order_summary"
                                    )
                                    order_summary_sent = True

                        # Send order if it was created but not yet sent
                        if not order_sent and "current_order" in session_state:
                            current_order = session_state.get("current_order")
                            if current_order and current_order != initial_order:
                                if not initial_order or current_order.get("order_id") != initial_order.get("order_id"):
                                    order_artifact_data = format_order(
                                        session_state)
                                    if order_artifact_data:
                                        await updater.add_artifact(
                                            [Part(root=DataPart(
                                                data=order_artifact_data,
                                                mimeType="application/json"
                                            ))],
                                            name="order"
                                        )
                                        order_sent = True
                    except Exception as final_state_error:
                        logger.error(
                            f"Error processing final response state: {final_state_error}")
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

                        # Stream products ONLY if they were modified during this request
                        if not products_sent and "current_results" in session_state:
                            current_results = session_state.get(
                                "current_results", [])
                            # Only send if products changed (new search performed)
                            if current_results and current_results != initial_products:
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

                        # Stream cart ONLY if it was modified during this request
                        if not cart_sent and ("cart" in session_state or "cart_items" in session_state):
                            current_cart = session_state.get(
                                "cart") or session_state.get("cart_items", [])
                            # Only send if cart changed during this request
                            if current_cart != initial_cart:
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

                        # Stream order summary ONLY if it was prepared during this request
                        if not order_summary_sent and "pending_order_summary" in session_state:
                            current_order_summary = session_state.get(
                                "pending_order_summary")
                            # Only send if summary is new (different from initial) or was just prepared
                            if current_order_summary and current_order_summary != initial_order_summary:
                                order_summary_artifact_data = format_order_summary(
                                    session_state)
                                if order_summary_artifact_data:
                                    await updater.add_artifact(
                                        [Part(root=DataPart(
                                            data=order_summary_artifact_data,
                                            mimeType="application/json"
                                        ))],
                                        name="order_summary"
                                    )
                                    order_summary_sent = True

                        # Stream order ONLY if it was created during this request
                        if not order_sent and "current_order" in session_state:
                            current_order = session_state.get("current_order")
                            # Only send if order is new (different from initial) or was just created
                            if current_order and current_order != initial_order:
                                # Additional check: ensure order_id is different (new order)
                                if not initial_order or current_order.get("order_id") != initial_order.get("order_id"):
                                    order_artifact_data = format_order(
                                        session_state)
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

            # Ensure products are sent if they were modified (not already sent)
            if not products_sent:
                current_results = session_state.get("current_results", [])
                # Only send if products changed during this request
                if current_results and current_results != initial_products:
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

            # Ensure cart is sent if it was modified (not already sent)
            if not cart_sent:
                current_cart = session_state.get(
                    "cart") or session_state.get("cart_items", [])
                # Only send if cart changed during this request
                if current_cart != initial_cart:
                    cart_artifact_data = format_cart(session_state)
                    if cart_artifact_data:
                        await updater.add_artifact(
                            [Part(root=DataPart(
                                data=cart_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="cart"
                        )

            # Ensure order summary is sent if it was prepared (not already sent)
            if not order_summary_sent:
                current_order_summary = session_state.get(
                    "pending_order_summary")
                # Only send if summary is new (different from initial) and not None
                if current_order_summary and current_order_summary is not None and current_order_summary != initial_order_summary:
                    order_summary_artifact_data = format_order_summary(
                        session_state)
                    if order_summary_artifact_data:
                        await updater.add_artifact(
                            [Part(root=DataPart(
                                data=order_summary_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="order_summary"
                        )

            # Ensure order is sent if it was created (not already sent)
            if not order_sent:
                current_order = session_state.get("current_order")
                # Only send if order is new (different from initial)
                if current_order and current_order != initial_order:
                    # Additional check: ensure order_id is different (new order)
                    if not initial_order or current_order.get("order_id") != initial_order.get("order_id"):
                        order_artifact_data = format_order(session_state)
                        if order_artifact_data:
                            await updater.add_artifact(
                                [Part(root=DataPart(
                                    data=order_artifact_data,
                                    mimeType="application/json"
                                ))],
                                name="order"
                            )

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
