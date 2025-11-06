# Plan: Order Confirmation Before Placement

## Overview
Currently, when a user requests checkout, the system immediately creates the order. This plan adds a confirmation step where users see order details (items, total, shipping address) and must confirm before the order is created.

## Current Implementation

### Current Checkout Flow
1. User: "I want to checkout" or "Place order"
2. Checkout Agent calls `validate_cart_for_checkout()`
3. Checkout Agent immediately calls `create_order()`
   - Gets shipping address (randomly selected from `SAMPLE_ADDRESSES`)
   - Creates order in database
   - Clears cart
   - Marks order as "completed"
   - Stores order in `state["current_order"]`
4. Order confirmation displayed (after order is already created)

### Current Tools
- `validate_cart_for_checkout()` - Validates cart has items
- `create_order()` - Immediately creates order and clears cart
- `get_order_status()` - Retrieves existing order
- `cancel_order()` - Cancels existing order

### Current Data Flow
- Cart items stored in database (`CartItem` table)
- Order created immediately in database (`Order` table)
- Order data stored in `state["current_order"]`
- Shipping address randomly selected from `SAMPLE_ADDRESSES`

## Proposed Solution

### Phase 1: Add Order Summary Preparation Tool

**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/tools.py`

**New Tool**: `prepare_order_summary(tool_context: ToolContext) -> Dict[str, Any]`

**Purpose**: Calculate order details and retrieve shipping address WITHOUT creating the order

**Functionality**:
1. Get cart items from database (same as `create_order`)
2. Calculate total amount (same logic as `create_order`)
3. Get shipping address (randomly select from `SAMPLE_ADDRESSES`)
4. Format order items with product details
5. Store summary in `state["pending_order_summary"]` (NOT `current_order`)
6. Return order summary data (items, total, shipping_address)

**Returns**:
```python
{
    "items": [
        {
            "product_id": "...",
            "name": "...",
            "quantity": 1,
            "price": 49.99,
            "picture": "...",
            "subtotal": 49.99
        }
    ],
    "total_amount": 49.99,
    "shipping_address": "123 Main Street, Apt 4B, New York, NY 10001",
    "item_count": 1,
    "message": "Order summary prepared. Please review and confirm."
}
```

**Key Differences from `create_order()`**:
- Does NOT create order in database
- Does NOT clear cart
- Does NOT store in `state["current_order"]`
- Stores in `state["pending_order_summary"]` instead
- Does NOT generate `order_id` (no order exists yet)

### Phase 2: Modify Checkout Agent Workflow

**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/agent.py`

**Updated Workflow Pattern**:

```
1. User: "I want to checkout" or "Place order"
2. Call validate_cart_for_checkout()
   - If invalid: Inform user and stop
   - If valid: Continue
3. Call prepare_order_summary()
   - Gets shipping address
   - Calculates totals
   - Stores summary in state["pending_order_summary"]
4. Display order summary to user:
   - List all items with images, names, quantities, prices
   - Show total amount prominently
   - Display shipping address
   - Ask: "Please review your order above. Would you like to confirm and place this order?"
5. Wait for user confirmation:
   - User says: "Yes", "Confirm", "Place order", "Proceed", etc.
   - User says: "No", "Cancel", "Go back", etc.
6. If confirmed:
   - Call create_order()
   - Order is created and cart is cleared
   - Display order confirmation
7. If cancelled:
   - Inform user order was cancelled
   - Keep cart intact
   - Clear state["pending_order_summary"]
```

**Updated Agent Instructions**:

Add to the instruction text:
- New tool `prepare_order_summary()` description
- Updated workflow that includes confirmation step
- How to handle user confirmation/cancellation
- When to use `prepare_order_summary()` vs `create_order()`

### Phase 3: Update `create_order()` Tool

**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/tools.py`

**Modifications**:
1. Check for `state["pending_order_summary"]` before creating order
2. If `pending_order_summary` exists:
   - Use shipping address from summary (don't randomly select new one)
   - Verify cart hasn't changed (optional validation)
   - Use same order details as summary
3. After order creation:
   - Clear `state["pending_order_summary"]`
   - Store in `state["current_order"]` as before

**Rationale**: Ensures the order created matches what the user confirmed

### Phase 4: Add Order Summary Artifact Support

**File**: `backend/app/agent_executor.py`

**Changes**:
1. Detect when `state["pending_order_summary"]` is set
2. Send order summary as artifact (similar to how cart/products are sent)
3. Use artifact name `"order_summary"` (distinct from `"order"`)

**Artifact Format**:
```python
{
    "type": "order_summary",
    "items": [...],
    "total_amount": 49.99,
    "shipping_address": "...",
    "item_count": 1
}
```

### Phase 5: Frontend Support for Order Summary

**File**: `frontend/src/lib/a2a-parser.ts`

**Changes**:
1. Add `order_summary` type to `StreamingEvent` interface
2. Parse `order_summary` artifacts in `parseStreamingEvent()`
3. Format order summary data similar to order data

**File**: `frontend/src/types/index.ts`

**Changes**:
1. Add `OrderSummary` interface (similar to `Order` but without `order_id`, `status`, `created_at`)
2. Add `orderSummary` field to `ChatMessage` interface

**File**: `frontend/src/components/OrderDisplay.tsx` OR new component

**Options**:
- **Option A**: Modify `OrderDisplay` to handle both orders and summaries
  - Add optional `orderSummary` prop
  - Show "Pending Confirmation" status instead of "Completed"
  - Hide order_id, status badge, created_at for summaries
- **Option B**: Create new `OrderSummaryDisplay` component
  - Similar to `OrderDisplay` but for pre-order summaries
  - Shows "Review Your Order" header
  - Includes confirmation prompt

**File**: `frontend/src/components/Chatbox.tsx`

**Changes**:
1. Handle `order_summary` events in streaming parser
2. Display order summary in chat (using `OrderSummaryDisplay` or modified `OrderDisplay`)
3. User can type confirmation message in chat input

### Phase 6: Handle User Confirmation

**Backend**: Checkout Agent
- Detect confirmation keywords: "yes", "confirm", "place order", "proceed", "ok", "go ahead"
- Detect cancellation keywords: "no", "cancel", "go back", "never mind"
- If confirmation detected: Call `create_order()`
- If cancellation detected: Clear `state["pending_order_summary"]` and inform user

**Frontend**: No changes needed (user types confirmation in chat)

## Implementation Steps

### Step 1: Backend - Add `prepare_order_summary()` Tool (30 min)
1. Create `prepare_order_summary()` function in `tools.py`
2. Reuse cart retrieval logic from `create_order()`
3. Calculate totals without creating order
4. Store summary in `state["pending_order_summary"]`
5. Return summary data

### Step 2: Backend - Update Checkout Agent Instructions (15 min)
1. Add `prepare_order_summary()` tool description
2. Update workflow pattern to include confirmation step
3. Add instructions for handling user confirmation/cancellation
4. Update tool list to include new tool

### Step 3: Backend - Modify `create_order()` Tool (15 min)
1. Check for `pending_order_summary` in state
2. Use shipping address from summary if available
3. Clear `pending_order_summary` after order creation
4. Add validation that cart matches summary (optional)

### Step 4: Backend - Add Order Summary Artifact Support (20 min)
1. Detect `state["pending_order_summary"]` in `agent_executor.py`
2. Send order summary artifact with name `"order_summary"`
3. Format artifact data according to schema

### Step 5: Frontend - Update Parser and Types (15 min)
1. Add `order_summary` to `StreamingEvent` type
2. Parse `order_summary` artifacts in `parseStreamingEvent()`
3. Add `OrderSummary` interface to types
4. Add `orderSummary` to `ChatMessage` interface

### Step 6: Frontend - Create/Update Order Summary Display (30 min)
1. Option A: Modify `OrderDisplay` to handle summaries
   - Add conditional rendering for summary vs order
   - Show different header/status
2. Option B: Create `OrderSummaryDisplay` component
   - Similar structure to `OrderDisplay`
   - Shows "Review Your Order" header
   - Includes confirmation prompt text

### Step 7: Frontend - Update Chatbox (15 min)
1. Handle `order_summary` events
2. Display order summary component
3. User types confirmation in chat input (no UI changes needed)

### Step 8: Testing (30 min)
1. Test full checkout flow:
   - Add items to cart
   - Request checkout
   - Verify order summary displayed
   - Confirm order
   - Verify order created
   - Verify cart cleared
2. Test cancellation flow:
   - Request checkout
   - See summary
   - Cancel
   - Verify cart still intact
   - Verify no order created
3. Test edge cases:
   - Cart changes after summary (optional validation)
   - Multiple checkout attempts
   - Empty cart validation

## Data Flow

### Order Summary Phase
```
User: "Checkout"
  ↓
validate_cart_for_checkout()
  ↓
prepare_order_summary()
  ↓
state["pending_order_summary"] = {...}
  ↓
Artifact sent: "order_summary"
  ↓
Frontend displays summary
  ↓
User: "Yes, confirm"
```

### Order Creation Phase
```
User: "Yes, confirm"
  ↓
create_order()
  ↓
Checks state["pending_order_summary"]
  ↓
Uses shipping address from summary
  ↓
Creates order in database
  ↓
Clears cart
  ↓
Clears state["pending_order_summary"]
  ↓
state["current_order"] = {...}
  ↓
Artifact sent: "order"
  ↓
Frontend displays order confirmation
```

## Edge Cases & Considerations

### 1. Cart Changes After Summary
**Scenario**: User requests checkout, sees summary, then adds/removes items before confirming
**Solution Options**:
- **Option A**: Re-validate cart matches summary before creating order
- **Option B**: Allow cart changes, recalculate on confirmation
- **Option C**: Lock cart during confirmation (complex, not recommended)

**Recommendation**: Option A - Validate cart matches summary, if not, show new summary

### 2. Multiple Checkout Attempts
**Scenario**: User requests checkout multiple times
**Solution**: Clear `pending_order_summary` when new summary is prepared

### 3. Shipping Address Consistency
**Scenario**: User sees summary with address A, but `create_order()` selects address B
**Solution**: Always use address from `pending_order_summary` if it exists

### 4. Session Expiration
**Scenario**: User sees summary but session expires before confirmation
**Solution**: `pending_order_summary` is lost, user must restart checkout (acceptable)

### 5. User Confirmation Detection
**Scenario**: User says something ambiguous like "sure" or "I guess"
**Solution**: Use LLM to detect intent, or be conservative and ask for explicit confirmation

## Benefits

1. **User Control**: Users can review order before committing
2. **Transparency**: Shipping address shown before order creation
3. **Error Prevention**: Users can catch mistakes before order is placed
4. **Better UX**: Matches standard e-commerce checkout flow
5. **Cancellation Support**: Users can back out without order being created

## Risks & Mitigations

1. **Risk**: User confusion if summary looks like completed order
   - **Mitigation**: Clear visual distinction (different header, "Pending Confirmation" status)

2. **Risk**: Cart changes between summary and confirmation
   - **Mitigation**: Validate cart matches summary before creating order

3. **Risk**: Shipping address changes between summary and order
   - **Mitigation**: Always use address from `pending_order_summary`

4. **Risk**: User doesn't understand they need to confirm
   - **Mitigation**: Clear prompt: "Please review your order above. Would you like to confirm and place this order?"

5. **Risk**: Additional step adds friction
   - **Mitigation**: This is standard e-commerce practice, users expect it

## Files to Modify

### Backend
1. `backend/app/shopping_agent/sub_agents/checkout_agent/tools.py`
   - Add `prepare_order_summary()` function
   - Modify `create_order()` to use summary data

2. `backend/app/shopping_agent/sub_agents/checkout_agent/agent.py`
   - Update agent instructions
   - Add `prepare_order_summary` to tools list

3. `backend/app/agent_executor.py`
   - Detect `pending_order_summary` in state
   - Send order summary artifact

### Frontend
1. `frontend/src/lib/a2a-parser.ts`
   - Add `order_summary` parsing

2. `frontend/src/types/index.ts`
   - Add `OrderSummary` interface

3. `frontend/src/components/OrderDisplay.tsx` OR new component
   - Handle order summaries

4. `frontend/src/components/Chatbox.tsx`
   - Handle `order_summary` events

## Estimated Time

- **Backend Implementation**: 1.5 hours
- **Frontend Implementation**: 1 hour
- **Testing**: 30 minutes
- **Total**: 3 hours

## Success Criteria

1. ✅ Order summary displayed before order creation
2. ✅ Shipping address shown in summary
3. ✅ User can confirm or cancel
4. ✅ Order only created after confirmation
5. ✅ Cart cleared only after order creation
6. ✅ Cancellation keeps cart intact
7. ✅ Order summary visually distinct from order confirmation
8. ✅ Shipping address consistent between summary and order

