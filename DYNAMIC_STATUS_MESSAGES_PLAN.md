# Plan: Dynamic Status Messages for Shopping Tasks

## Overview
Currently, users see a generic "Processing your shopping request..." message during all operations. This plan outlines how to provide context-specific status messages based on the actual task being performed (e.g., "Searching for products...", "Adding item to cart...", etc.).

## Current Implementation

### Status Message Flow (A2A Protocol Compliant)
1. **Initialization**: `ShoppingAgentExecutor.__init__()` sets `self.status_message = 'Processing your shopping request...'` (line 37)
2. **Status Update**: Single status update sent at start of execution (lines 334-339) using `updater.update_status()`
3. **Function Call Detection**: Function calls are detected in event loop (lines 643-645) but not used for status updates
4. **A2A Protocol**: Status updates are sent as `TaskStatusUpdateEvent` objects via the streaming protocol (`message/stream` method)
5. **Status Message Format**: Status messages are sent as `Message` objects containing `TextPart` via `new_agent_text_message()`

### A2A Protocol Compliance
According to the [A2A Specification](https://a2a-protocol.org/latest/specification/):
- **TaskStatusUpdateEvent**: Status updates are sent as part of the streaming protocol (Section 7.2.2)
- **TaskState Enum**: Status updates use `TaskState.working` to indicate task is in progress (Section 6.3)
- **Message Format**: Status messages are sent as `Message` objects with `TextPart` containing the status text (Section 6.4, 6.5.1)
- **Streaming**: Status updates are sent incrementally via `message/stream` method (Section 7.2)

### Available Tools by Sub-Agent

**Product Discovery Agent:**
- `text_vector_search(query: str)` - Text-based product search
- `image_vector_search()` - Image-based visual similarity search

**Cart Agent:**
- `add_to_cart(product_description: str, quantity: int)` - Add item to cart
- `get_cart()` - Retrieve cart contents
- `update_cart_item(cart_item_id: str, quantity: int)` - Update item quantity
- `remove_from_cart(cart_item_id: str)` - Remove item from cart
- `clear_cart()` - Clear entire cart
- `get_cart_total()` - Get cart total

**Checkout Agent:**
- `create_order()` - Create order from cart
- `get_order_status(order_id: Optional[str])` - Check order status
- `cancel_order(order_id: str)` - Cancel an order
- `validate_cart_for_checkout()` - Validate cart before checkout

**Customer Service Agent:**
- `create_inquiry(inquiry_type: str, message: str, order_id: Optional[str])` - Create support ticket
- `get_inquiry_status(inquiry_id: str)` - Check inquiry status
- `search_faq(query: str)` - Search FAQ database
- `initiate_return(order_id: str, reason: str)` - Initiate product return
- `get_order_inquiries(order_id: str)` - Get inquiries for an order

## Proposed Solution

### Phase 1: Create Status Message Mapping

**File**: `backend/app/agent_executor.py`

Create a mapping dictionary that maps function names to user-friendly status messages:

```python
# Tool name -> Status message mapping
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
```

### Phase 2: Extract Function Call Information

**File**: `backend/app/agent_executor.py` (in `execute()` method)

Modify the function call detection section (currently lines 643-645) to extract function name and update status via A2A protocol:

```python
elif hasattr(part, 'function_call'):
    function_call = part.function_call
    function_name = function_call.name if hasattr(function_call, 'name') else None
    
    # Update status message based on function being called
    # This sends a TaskStatusUpdateEvent via A2A streaming protocol
    if function_name and function_name in TOOL_STATUS_MESSAGES:
        status_message = TOOL_STATUS_MESSAGES[function_name]
        await updater.update_status(
            TaskState.working,  # A2A TaskState enum value
            new_agent_text_message(  # Creates A2A Message with TextPart
                status_message, task.context_id, task.id
            ),
        )
```

**A2A Protocol Details**:
- `updater.update_status()` sends a `TaskStatusUpdateEvent` (A2A Spec Section 7.2.2)
- The event contains `TaskState.working` and a `Message` object with `TextPart`
- This is sent via the streaming protocol (`message/stream`) to the client
- The client receives it as a `status-update` event kind

### Phase 3: Handle Edge Cases

**Considerations:**

1. **Multiple Function Calls**: If multiple functions are called in sequence, update status for each one
   - Track last function name to avoid duplicate status updates
   - Each function call should trigger a new TaskStatusUpdateEvent

2. **Unknown Functions**: If a function name isn't in the mapping, fall back to generic message or log for future addition
   - Use default `self.status_message` or a generic "Processing..." message
   - Log unknown function names for future mapping additions

3. **Function Call Completion**: Optionally update status back to generic message after function completes (or let next function call update it)
   - Current approach: Let next function call update status
   - Alternative: Reset to generic message after function completes (may be unnecessary)

4. **Sub-Agent Transfers**: When the main agent transfers to a sub-agent, we might want to show a different message, but function calls are more granular
   - Function-level messages are more specific and useful
   - Sub-agent transfers are handled internally by ADK and may not be directly observable

5. **A2A Protocol Considerations**:
   - Ensure status updates don't interfere with artifact streaming
   - Status updates should be non-blocking
   - Multiple status updates in quick succession should be handled gracefully

### Phase 4: Enhanced Messages with Context (Optional)

For some operations, we could include context from function arguments:

```python
# Enhanced messages with context
def get_status_message(function_name: str, function_args: dict) -> str:
    base_message = TOOL_STATUS_MESSAGES.get(function_name, 'Processing your request...')
    
    # Add context where helpful
    if function_name == 'text_vector_search' and 'query' in function_args:
        query = function_args['query']
        return f'Searching for "{query}"...'
    
    if function_name == 'add_to_cart' and 'product_description' in function_args:
        desc = function_args['product_description']
        return f'Adding "{desc}" to cart...'
    
    return base_message
```

**Note**: This requires extracting function arguments from the `function_call` object, which may have different structures depending on ADK version.

### Phase 5: A2A Protocol Compliance Verification

**Verification Points**:

1. **TaskStatusUpdateEvent Structure**: Ensure status updates conform to A2A spec Section 7.2.2
   - Event contains `state` (TaskState enum)
   - Event contains `message` (Message object with TextPart)
   - Event is sent via streaming protocol

2. **Message Format**: Verify `new_agent_text_message()` creates valid A2A Message objects
   - Message contains `TextPart` with status text
   - Message includes `contextId` and `taskId` for proper routing

3. **Streaming Protocol**: Confirm status updates are sent via `message/stream` method
   - Updates are sent incrementally as they occur
   - Client receives events in real-time
   - No blocking of the main execution flow

4. **TaskState Usage**: Ensure correct TaskState enum values are used
   - `TaskState.working` for in-progress operations
   - `TaskState.failed` for errors (already handled)
   - `TaskState.completed` when task finishes (already handled)

## Implementation Steps

1. **Add Status Message Mapping** (5 min)
   - Create `TOOL_STATUS_MESSAGES` dictionary in `agent_executor.py`
   - Place near top of class or as module-level constant

2. **Extract Function Call Info** (15 min)
   - Modify function call detection block (lines 643-645)
   - Extract `function_name` from `function_call` object
   - Look up message in mapping dictionary
   - Call `updater.update_status()` with new message

3. **Test Function Call Structure** (10 min)
   - Add debug logging to inspect `function_call` object structure from ADK events
   - Verify we can access `function_call.name` or equivalent attribute
   - Verify ADK event structure matches expected format
   - Document the structure for future reference
   - Ensure function calls appear in `event.content.parts` as expected

4. **Handle Edge Cases** (10 min)
   - Add fallback for unknown function names
   - Ensure status updates don't interfere with existing flow
   - Test with multiple sequential function calls

5. **Testing** (20 min)
   - Test each tool category:
     - Product search (text and image)
     - Cart operations (add, update, remove, clear)
     - Checkout (create order, check status)
     - Customer service (inquiry, return, FAQ)
   - Verify A2A TaskStatusUpdateEvent events are sent correctly
   - Verify status messages are received by client via streaming protocol
   - Ensure messages update appropriately during multi-step operations
   - Test that status updates don't interfere with artifact streaming

## Alternative Approaches Considered

### Option A: Intent-Based Messages (Rejected)
- Detect user intent from initial message
- Problem: Intent detection is less reliable than actual function calls
- Problem: User intent may not match actual operations performed

### Option B: Sub-Agent Based Messages (Rejected)
- Show messages based on which sub-agent is active
- Problem: Less granular - sub-agents perform multiple operations
- Problem: Harder to detect sub-agent transitions reliably

### Option C: State-Based Messages (Rejected)
- Infer operation from session state changes
- Problem: State changes happen after operations complete
- Problem: Multiple state changes can occur simultaneously

## Benefits

1. **Better User Experience**: Users see exactly what's happening
2. **Reduced Perceived Wait Time**: Specific messages feel more responsive
3. **Transparency**: Users understand what operations are being performed
4. **Debugging**: Easier to track what operations are executing

## Risks & Mitigations

1. **Risk**: Function call structure may vary between ADK versions
   - **Mitigation**: Add defensive checks and fallback to generic message
   - **Mitigation**: Log function call structure for debugging and version compatibility

2. **Risk**: Too many status updates could be distracting or cause performance issues
   - **Mitigation**: Only update when function name changes (track last function name)
   - **Mitigation**: Consider debouncing rapid status updates
   - **Mitigation**: Ensure status updates don't block the main execution flow

3. **Risk**: Status messages might not match actual operation duration
   - **Mitigation**: Messages are informational, not progress indicators
   - **Mitigation**: Use present tense ("Searching...") to indicate ongoing operation

4. **Risk**: A2A protocol compliance issues
   - **Mitigation**: Follow A2A spec Section 7.2.2 for TaskStatusUpdateEvent format
   - **Mitigation**: Ensure TaskState enum values are used correctly
   - **Mitigation**: Verify Message objects conform to Section 6.4 specification

## Future Enhancements

1. **Operation History**: Track completed operations for debugging/logging purposes
2. **Estimated Time**: Provide time estimates based on operation type (if A2A spec supports this)
3. **Cancellation**: Leverage A2A `tasks/cancel` method for long-running operations
4. **Multi-Language**: Support status messages in multiple languages (localization)
5. **Context-Aware Messages**: Include function arguments in status messages where helpful (see Phase 4)

## Files to Modify

1. `backend/app/agent_executor.py`
   - Add `TOOL_STATUS_MESSAGES` mapping (module-level constant)
   - Modify function call detection section (lines 643-645)
   - Add status update logic using `updater.update_status()`
   - Ensure A2A protocol compliance (TaskStatusUpdateEvent format)

2. **Testing & Verification**
   - Add debug logging for function call structure from ADK events
   - Verify TaskStatusUpdateEvent events are sent correctly
   - Verify A2A protocol compliance (Message format, TaskState enum)
   - Test streaming protocol behavior with multiple status updates

## Estimated Time

- **Implementation**: 40-60 minutes
- **Testing**: 20-30 minutes
- **Total**: 1-1.5 hours

## Success Criteria

1. ✅ Status messages update when function calls are detected
2. ✅ Messages are user-friendly and specific to the operation
3. ✅ Status updates conform to A2A TaskStatusUpdateEvent specification
4. ✅ TaskStatusUpdateEvent events are sent via A2A streaming protocol correctly
5. ✅ All major tool operations have appropriate messages
6. ✅ Fallback message exists for unknown operations
7. ✅ No performance degradation from status updates
8. ✅ Status updates don't interfere with artifact streaming
9. ✅ A2A protocol compliance maintained throughout implementation

