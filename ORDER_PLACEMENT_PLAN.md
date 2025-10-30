# Order Placement Implementation Plan

## Overview
Implement order placement functionality with cart display, checkout confirmation, and order completion flow. The order will be marked as paid automatically (no payment integration).

## Current State Analysis

### ✅ Already Implemented:
- Cart functionality (`cart_agent`) with add/update/remove operations
- Cart stored in session state (`state["cart"]`)
- Cart displayed in chatbox UI (`CartDisplay` component)
- Checkout agent exists with `create_order` tool
- Order models exist in database
- Frontend `Order` and `OrderItem` types defined

### ❌ Needs Implementation:
- Fix `create_order` tool to calculate prices correctly
- Add hardcoded shipping address logic
- Update checkout agent tools to accept `ToolContext`
- Update orchestrator to handle checkout flow
- Add order confirmation prompt logic
- Create order display component for frontend
- Add order artifact support in A2A executor
- Update frontend parser to handle order artifacts
- Update chatbox to display order confirmations

---

## Phase 1: Backend - Fix Checkout Tools

### 1.1 Update `create_order` Tool
**File**: `backend/app/checkout_agent/tools.py`

**Changes**:
1. Add `tool_context: ToolContext` as first parameter
2. Extract `session_id` from `tool_context._invocation_context.session.id`
3. Fix price calculation:
   - Get `price_usd_units` from product
   - Calculate `price` as `price_usd_units / 100.0`
   - Calculate `total_amount` by summing all item subtotals
4. Add hardcoded shipping address:
   - Create a list of sample addresses
   - Select one randomly (or use first one for consistency)
   - Store in `tool_context.state["shipping_address"]`
5. After order creation, store order info in `tool_context.state["current_order"]`
6. Mark order status as "completed" (since payment is skipped)

**Shipping Addresses** (hardcoded):
```python
SAMPLE_ADDRESSES = [
    "123 Main Street, Apt 4B, New York, NY 10001",
    "456 Oak Avenue, Suite 200, Los Angeles, CA 90001",
    "789 Pine Road, Seattle, WA 98101",
    "321 Elm Street, Chicago, IL 60601",
]
```

### 1.2 Update Other Checkout Tools
**File**: `backend/app/checkout_agent/tools.py`

**Tools to update**:
- `get_order_status`: Add `tool_context: ToolContext`, extract `session_id` from context
- `cancel_order`: Add `tool_context: ToolContext`
- `validate_cart_for_checkout`: Add `tool_context: ToolContext`, extract `session_id` from context

### 1.3 Update Checkout Agent Instructions
**File**: `backend/app/checkout_agent/agent.py`

**Changes**:
- Add instructions to prompt user for order confirmation
- Mention that shipping address comes from user profile
- After order creation, display order details clearly
- Emphasize showing order ID, items, total, and shipping address

---

## Phase 2: Backend - Update Orchestrator Flow

### 2.1 Update Orchestrator Instructions
**File**: `backend/app/orchestrator_agent/agent.py`

**Changes**:
- Add "Checkout Flow" section:
  1. After items added to cart, automatically show cart contents
  2. Prompt user: "Your cart contains X items. Would you like to proceed to checkout?"
  3. When user confirms checkout ("yes", "checkout", "place order"):
     - Call `validate_cart_for_checkout` first
     - If valid, call `create_order` with shipping address from profile
     - Show order confirmation with details
  4. Tell user: "We've retrieved your shipping address from your profile: [address]"
  5. Display order information: Order ID, items, total, shipping address, status

---

## Phase 3: Backend - A2A Executor Updates

### 3.1 Add Order Artifact Support
**File**: `backend/app/a2a_executor.py`

**Changes**:
1. Add order formatting helper function:
```python
def format_order(order_state):
    order_data = order_state.get("current_order")
    if not order_data:
        return None
    return {
        "type": "order",
        "order_id": order_data.get("order_id"),
        "status": order_data.get("status"),
        "items": order_data.get("items", []),
        "total_amount": order_data.get("total_amount"),
        "shipping_address": order_data.get("shipping_address"),
        "created_at": order_data.get("created_at"),
    }
```

2. Check for `current_order` in session state after order creation
3. Send order as `DataPart` artifact with name "order" (similar to products/cart)

---

## Phase 4: Frontend - Types and Parser Updates

### 4.1 Update Types
**File**: `frontend/src/types/index.ts`

**Changes**:
1. Add `OrderData` interface:
```typescript
export interface OrderData {
  type: "order";
  order_id: string;
  status: string;
  items: OrderItem[];
  total_amount: number;
  shipping_address?: string;
  created_at?: string;
}
```

2. Update `OrderItem` interface to match backend (already exists, verify)

### 4.2 Update A2A Parser
**File**: `frontend/src/lib/a2a-parser.ts`

**Changes**:
1. Add `order` to `ParsedA2AResponse` interface:
```typescript
export interface ParsedA2AResponse {
  text: string;
  products: Product[];
  cart?: CartItem[];
  order?: Order;  // Add this
}
```

2. Add order parsing in `parseA2AResponse`:
   - Extract order from `DataPart` artifact with name "order"
   - Format using `formatOrder` helper

3. Add `formatOrder` helper function:
```typescript
function formatOrder(order: any): Order {
  return {
    order_id: order.order_id || '',
    status: order.status || '',
    items: (order.items || []).map(formatOrderItem),
    total_amount: order.total_amount || 0,
    shipping_address: order.shipping_address,
    created_at: order.created_at,
  };
}

function formatOrderItem(item: any): OrderItem {
  return {
    product_id: item.product_id || '',
    name: item.name || '',
    quantity: item.quantity || 0,
    price: item.price || 0,
  };
}
```

4. Add order handling in `parseStreamingEvent`:
   - Detect `artifact-update` with `artifact.name === "order"`
   - Return `{ type: 'order', data: { order: formatOrder(...) } }`

---

## Phase 5: Frontend - Order Display Component

### 5.1 Create OrderDisplay Component
**File**: `frontend/src/components/OrderDisplay.tsx` (NEW)

**Features**:
- Display order ID prominently
- Show order status badge (completed/pending)
- List order items with images, names, quantities, prices
- Display total amount
- Display shipping address
- Show order date/time
- Visual confirmation styling (green checkmark, success message)

**Design**:
- Similar to `CartDisplay` component
- Success/confirmation styling
- Card-based layout

---

## Phase 6: Frontend - Chatbox Integration

### 6.1 Update Chatbox Component
**File**: `frontend/src/components/Chatbox.tsx`

**Changes**:
1. Add `order` to `MessageWithArtifacts` interface:
```typescript
interface MessageWithArtifacts extends ChatMessage {
  products?: Product[];
  cart?: CartItem[];
  order?: Order;  // Add this
}
```

2. Update `handleSend` and `handlePromptClick` to handle order events:
   - Add `streamingOrder` state variable
   - Handle `'order'` event type from `parseStreamingEvent`
   - Store order in message artifacts

3. Render `OrderDisplay` component when message has order:
   - Add conditional rendering after cart display
   - Show order confirmation with success styling

4. Update loading messages:
   - Add "Creating your order..." when processing checkout
   - Add "Confirming order..." when order is being created

---

## Phase 7: Testing & Refinement

### 7.1 Test Scenarios
1. **Add to Cart → View Cart → Checkout**:
   - Add item to cart
   - Verify cart displays automatically
   - Verify checkout prompt appears
   - Confirm checkout
   - Verify order confirmation displays

2. **Multiple Items**:
   - Add multiple items
   - Verify all items shown in cart
   - Verify quantities correct
   - Complete checkout
   - Verify all items in order

3. **Empty Cart**:
   - Try to checkout with empty cart
   - Verify error handling

4. **Price Calculation**:
   - Verify prices calculated correctly
   - Verify total amount matches sum of items

5. **Shipping Address**:
   - Verify address appears in order confirmation
   - Verify message mentions "from your profile"

---

## Implementation Checklist

### Backend
- [ ] Phase 1.1: Update `create_order` tool with ToolContext
- [ ] Phase 1.1: Fix price calculation in `create_order`
- [ ] Phase 1.1: Add hardcoded shipping address logic
- [ ] Phase 1.1: Store order in session state
- [ ] Phase 1.1: Mark order as "completed"
- [ ] Phase 1.2: Update `get_order_status` tool
- [ ] Phase 1.2: Update `cancel_order` tool
- [ ] Phase 1.2: Update `validate_cart_for_checkout` tool
- [ ] Phase 1.3: Update checkout agent instructions
- [ ] Phase 2.1: Update orchestrator with checkout flow
- [ ] Phase 3.1: Add order artifact support in executor

### Frontend
- [ ] Phase 4.1: Add OrderData interface
- [ ] Phase 4.2: Update parser for order artifacts
- [ ] Phase 4.2: Add formatOrder helper
- [ ] Phase 5.1: Create OrderDisplay component
- [ ] Phase 6.1: Update Chatbox for order display
- [ ] Phase 6.1: Handle order streaming events

### Testing
- [ ] Test full checkout flow
- [ ] Test price calculations
- [ ] Test order display
- [ ] Test empty cart handling
- [ ] Verify shipping address message

---

## Assumptions Made

1. **Cart Display**: Cart will be shown automatically after adding items (can be changed)
2. **Checkout Prompt**: Agent will prompt user to checkout after showing cart (can be changed)
3. **Order Display**: Order will be displayed as structured artifact with visual component
4. **Shipping Address**: Single hardcoded address selected from list (can randomize)
5. **Order Status**: Orders will be marked as "completed" (since payment skipped)
6. **Cart Clearing**: Cart will be cleared after order creation (existing behavior)

---

## Questions for User

1. Should cart display automatically after adding items, or only on request?
2. Should checkout prompt appear automatically, or wait for user to initiate?
3. Should order confirmation be a visual component or just text?
4. Should shipping address be fixed or randomly selected?
5. Should order status be "completed" or "pending"?
6. Should cart be cleared immediately or kept until user confirms?

---

## Next Steps

Once questions are answered, proceed with implementation in order:
1. Backend fixes (Phase 1)
2. Orchestrator updates (Phase 2)
3. Executor updates (Phase 3)
4. Frontend parser (Phase 4)
5. Order display component (Phase 5)
6. Chatbox integration (Phase 6)
7. Testing (Phase 7)

