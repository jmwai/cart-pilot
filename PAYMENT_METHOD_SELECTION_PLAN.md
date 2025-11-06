# Payment Method Selection Implementation Plan

## Overview
This plan outlines the implementation of payment method selection using the Agent Payments Protocol (AP2) specification. The implementation will integrate payment method selection into the checkout flow, create AP2 mandates (Cart Mandate and Payment Mandate), and process payments before order creation.

## References
- [AP2 Specification](https://ap2-protocol.org/specification/)
- [A2A Extension for AP2](https://ap2-protocol.org/a2a-extension/)
- [AP2 Sample Implementation](https://github.com/google-agentic-commerce/AP2/tree/main/samples/python/src/roles)

## Current State Analysis

### Current Checkout Flow
1. User requests checkout
2. `validate_cart_for_checkout()` validates cart
3. `prepare_order_summary()` prepares summary (no order created)
4. User confirms order
5. `create_order()` creates order immediately with status="completed" (payment skipped)

### Current Payment Agent
- Exists but not integrated into checkout flow
- Has tools: `create_payment_mandate()`, `process_payment()`, `get_payment_status()`, etc.
- Currently requires `order_id` to create payment mandate (order must exist first)

### Current Models
- `Mandate` model exists with fields: `mandate_id`, `mandate_type`, `session_id`, `mandate_data`, `signature`, `status`
- `Payment` model exists with fields: `payment_id`, `order_id`, `amount`, `payment_method`, `payment_mandate_id`, `transaction_id`, `status`
- `Order` model has `status` field (currently set to "completed" immediately)

## AP2 Protocol Requirements

### Key Concepts from AP2 Specification

1. **Cart Mandate (Section 4.1.1)**
   - Verifiable Digital Credential (VDC) that captures user's intent to purchase specific cart contents
   - Created BEFORE payment method selection
   - Contains: cart items, quantities, prices, total amount
   - Provides cryptographic proof of user's shopping intent

2. **Payment Mandate (Section 4.1.3)**
   - VDC that authorizes payment for a specific transaction
   - Created AFTER payment method selection
   - Contains: payment method, amount, order reference, cart mandate reference
   - Links payment authorization to specific cart contents

3. **Payment Method Selection (Section 5.4)**
   - User selects from available payment methods
   - Payment methods retrieved from Credentials Provider (simulated for demo)
   - Selection stored in session state

4. **Human Present Transaction Flow (Section 5.1)**
   - User reviews order summary
   - User confirms order
   - User selects payment method
   - Cart Mandate created
   - Payment Mandate created
   - Payment processed
   - Order created

## Implementation Plan

### Phase 1: Backend - Payment Method Management

#### 1.1 Create Payment Method Tools
**File**: `backend/app/payment_agent/tools.py`

**New Functions**:
- `get_available_payment_methods(tool_context: ToolContext) -> Dict[str, Any]`
  - Returns list of available payment methods (hardcoded for demo)
  - Each payment method includes: `id`, `type` (e.g., "credit_card", "debit_card"), `display_name`, `last_four` (for cards), `expiry_month`, `expiry_year`, `cardholder_name`
  - Stores available methods in `tool_context.state["available_payment_methods"]`
  - Returns: `{"payment_methods": [...], "message": "Available payment methods retrieved"}`

- `select_payment_method(tool_context: ToolContext, payment_method_id: str) -> Dict[str, Any]`
  - Validates payment method exists
  - Stores selected payment method in `tool_context.state["selected_payment_method"]`
  - Returns: `{"payment_method_id": "...", "display_name": "...", "message": "Payment method selected"}`

**Dummy Payment Methods** (for demo):
```python
DUMMY_PAYMENT_METHODS = [
    {
        "id": "pm_visa_1234",
        "type": "credit_card",
        "display_name": "Visa •••• 1234",
        "last_four": "1234",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cardholder_name": "John Doe",
        "brand": "Visa"
    },
    {
        "id": "pm_mastercard_5678",
        "type": "credit_card",
        "display_name": "Mastercard •••• 5678",
        "last_four": "5678",
        "expiry_month": 6,
        "expiry_year": 2026,
        "cardholder_name": "John Doe",
        "brand": "Mastercard"
    },
    {
        "id": "pm_amex_9012",
        "type": "credit_card",
        "display_name": "American Express •••• 9012",
        "last_four": "9012",
        "expiry_month": 3,
        "expiry_year": 2027,
        "cardholder_name": "John Doe",
        "brand": "American Express"
    }
]
```

#### 1.2 Create Cart Mandate Tool
**File**: `backend/app/payment_agent/tools.py`

**New Function**:
- `create_cart_mandate(tool_context: ToolContext) -> Dict[str, Any]`
  - Retrieves cart items from session state or database
  - Creates Cart Mandate VDC with:
    - Cart items (product_id, name, quantity, price)
    - Total amount
    - Timestamp
    - Session ID
  - Stores mandate in database (`Mandate` table with `mandate_type="cart"`)
  - Stores mandate_id in `tool_context.state["cart_mandate_id"]`
  - Returns: `{"mandate_id": "...", "cart_items": [...], "total_amount": ..., "message": "Cart mandate created"}`

**Cart Mandate Structure** (per AP2 spec):
```json
{
  "mandate_id": "cart_mandate_<uuid>",
  "mandate_type": "cart",
  "session_id": "...",
  "mandate_data": {
    "cart_items": [
      {
        "product_id": "...",
        "name": "...",
        "quantity": 1,
        "price": 19.99
      }
    ],
    "total_amount": 19.99,
    "timestamp": "2025-01-XX..."
  },
  "status": "pending"
}
```

#### 1.3 Update Payment Mandate Tool
**File**: `backend/app/payment_agent/tools.py`

**Modify Function**:
- `create_payment_mandate(tool_context: ToolContext, cart_mandate_id: Optional[str] = None) -> Dict[str, Any]`
  - If `cart_mandate_id` not provided, retrieve from `tool_context.state["cart_mandate_id"]`
  - Retrieve selected payment method from `tool_context.state["selected_payment_method"]`
  - Retrieve order summary from `tool_context.state["pending_order_summary"]` (amount, items)
  - Create Payment Mandate VDC with:
    - Payment method details
    - Amount
    - Cart mandate reference
    - Order summary reference
    - Timestamp
  - Store mandate in database (`Mandate` table with `mandate_type="payment"`)
  - Store mandate_id in `tool_context.state["payment_mandate_id"]`
  - Returns: `{"mandate_id": "...", "payment_method": "...", "amount": ..., "cart_mandate_id": "...", "message": "Payment mandate created"}`

**Payment Mandate Structure** (per AP2 spec):
```json
{
  "mandate_id": "payment_mandate_<uuid>",
  "mandate_type": "payment",
  "session_id": "...",
  "mandate_data": {
    "payment_method_id": "pm_visa_1234",
    "payment_method_type": "credit_card",
    "amount": 19.99,
    "cart_mandate_id": "cart_mandate_<uuid>",
    "order_summary_reference": {...},
    "timestamp": "2025-01-XX..."
  },
  "status": "pending"
}
```

#### 1.4 Update Process Payment Tool
**File**: `backend/app/payment_agent/tools.py`

**Modify Function**:
- `process_payment(tool_context: ToolContext, order_id: Optional[str] = None) -> Dict[str, Any]`
  - If `order_id` not provided, retrieve from `tool_context.state["current_order"]` or create order first
  - Retrieve payment mandate from `tool_context.state["payment_mandate_id"]`
  - Retrieve selected payment method from `tool_context.state["selected_payment_method"]`
  - Process payment (simulate for demo - no actual payment gateway)
  - Create `Payment` record
  - Update mandate status to "approved"
  - Update order status to "completed"
  - Returns: `{"payment_id": "...", "order_id": "...", "amount": ..., "status": "completed", "transaction_id": "...", "message": "Payment processed successfully"}`

**Note**: For demo, payment processing is simulated. In production, this would integrate with actual payment gateway.

#### 1.5 Update Payment Agent Instructions
**File**: `backend/app/payment_agent/agent.py`

**Update Instructions**:
- Add workflow for payment method selection
- Emphasize AP2 mandate creation order: Cart Mandate → Payment Method Selection → Payment Mandate → Payment Processing
- Add guidance on when to call each tool

**New Output Schema Fields**:
- `payment_methods?: List[PaymentMethod]` - Available payment methods
- `selected_payment_method?: PaymentMethod` - Selected payment method
- `cart_mandate_id?: str` - Cart mandate ID
- `payment_mandate_id?: str` - Payment mandate ID

### Phase 2: Backend - Checkout Agent Integration

#### 2.1 Update Checkout Flow
**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/agent.py`

**Modify Instructions**:
- After user confirms order summary, transfer to Payment Agent (instead of creating order immediately)
- Payment Agent handles: payment method selection → Cart Mandate → Payment Mandate → Payment Processing
- After payment processed, return to Checkout Agent to create order
- Order creation now happens AFTER payment is processed

**Updated Workflow**:
1. `validate_cart_for_checkout()`
2. `prepare_order_summary()`
3. User confirms order
4. **Transfer to Payment Agent** (new step)
5. Payment Agent: `get_available_payment_methods()` → User selects → `select_payment_method()` → `create_cart_mandate()` → `create_payment_mandate()` → `process_payment()`
6. **Return to Checkout Agent** (after payment processed)
7. `create_order()` (order status set to "completed" since payment already processed)

#### 2.2 Update Create Order Tool
**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/tools.py`

**Modify Function**:
- `create_order(tool_context: ToolContext) -> Dict[str, Any]`
  - Check if payment has been processed (`tool_context.state.get("payment_processed")` or check for `Payment` record)
  - If payment not processed, raise error: "Payment must be processed before creating order"
  - Retrieve payment details from state or database
  - Create order with status="completed" (payment already processed)
  - Link order to payment via `order_id` in `Payment` table
  - Store order in `tool_context.state["current_order"]`

**Note**: Order creation now happens AFTER payment, ensuring payment is always processed before order is created.

### Phase 3: Frontend - Payment Method Selection UI

#### 3.1 Create Payment Method Selection Component
**File**: `frontend/src/components/PaymentMethodSelection.tsx`

**New Component**:
- Displays list of available payment methods
- Allows user to select a payment method
- Shows payment method details (card type, last four digits, expiry)
- Has "Select" button for each payment method
- Sends message to agent when payment method is selected

**Props**:
```typescript
interface PaymentMethodSelectionProps {
  paymentMethods: PaymentMethod[];
  onSelect: (paymentMethodId: string) => void;
  selectedPaymentMethodId?: string;
}
```

**Payment Method Interface**:
```typescript
interface PaymentMethod {
  id: string;
  type: string;
  display_name: string;
  last_four?: string;
  expiry_month?: number;
  expiry_year?: number;
  cardholder_name?: string;
  brand?: string;
}
```

#### 3.2 Update Types
**File**: `frontend/src/types/index.ts`

**Add Types**:
```typescript
export interface PaymentMethod {
  id: string;
  type: string;
  display_name: string;
  last_four?: string;
  expiry_month?: number;
  expiry_year?: number;
  cardholder_name?: string;
  brand?: string;
}

export interface PaymentMethodData {
  type: "payment_methods";
  payment_methods: PaymentMethod[];
}

export interface PaymentMethodSelectionData {
  type: "payment_method_selection";
  payment_methods: PaymentMethod[];
  selected_payment_method_id?: string;
}
```

**Update ChatMessage**:
```typescript
export interface ChatMessage {
  // ... existing fields
  paymentMethods?: PaymentMethod[]; // Available payment methods
  selectedPaymentMethod?: PaymentMethod; // Selected payment method
}
```

#### 3.3 Update A2A Parser
**File**: `frontend/src/lib/a2a-parser.ts`

**Add Parsing**:
- Parse `payment_methods` artifact type
- Parse `payment_method_selection` artifact type
- Return `StreamingEvent` with `type: 'payment_methods'` or `type: 'payment_method_selection'`

#### 3.4 Update Chatbox Component
**File**: `frontend/src/components/Chatbox.tsx`

**Add Rendering**:
- Render `PaymentMethodSelection` component when `msg.paymentMethods` is present
- Handle payment method selection by sending message to agent: "Select payment method {id}"
- Update streaming state to track `paymentMethods` and `selectedPaymentMethod`

#### 3.5 Update Order Summary Display
**File**: `frontend/src/components/OrderSummaryDisplay.tsx`

**Modify Component**:
- After user confirms order, show message: "Please select a payment method to continue"
- Update confirmation prompt to indicate payment method selection is next step

### Phase 4: Backend - Artifact Streaming

#### 4.1 Update Artifact Formatter
**File**: `backend/app/utils/artifact_formatter.py`

**Add Methods**:
- `format_payment_methods(payment_methods_state: Dict) -> Optional[Dict]`
  - Formats payment methods list for artifact
  - Returns: `{"type": "payment_methods", "payment_methods": [...]}`

- `format_payment_method_selection(selection_state: Dict) -> Optional[Dict]`
  - Formats selected payment method for artifact
  - Returns: `{"type": "payment_method_selection", "selected_payment_method_id": "...", "payment_methods": [...]}`

#### 4.2 Update Artifact Streamer
**File**: `backend/app/utils/artifact_streamer.py`

**Add Streaming**:
- Stream `payment_methods` artifact when `tool_context.state["available_payment_methods"]` is set
- Stream `payment_method_selection` artifact when `tool_context.state["selected_payment_method"]` is set
- Update `sent_flags` to include `"payment_methods"` and `"payment_method_selection"`

#### 4.3 Update Agent Executor
**File**: `backend/app/agent_executor.py`

**Add Artifact Detection**:
- Detect `available_payment_methods` in session state
- Detect `selected_payment_method` in session state
- Stream artifacts via `ArtifactStreamer`

### Phase 5: Agent Coordination

#### 5.1 Update Shopping Agent
**File**: `backend/app/shopping_agent/agent.py`

**Update Instructions**:
- After Checkout Agent prepares order summary and user confirms, transfer to Payment Agent
- Payment Agent handles payment method selection and payment processing
- After payment processed, return control to Checkout Agent to create order

**Updated Flow**:
1. User: "I want to checkout"
2. Shopping Agent → Checkout Agent
3. Checkout Agent: `validate_cart_for_checkout()` → `prepare_order_summary()`
4. User confirms order
5. Shopping Agent → Payment Agent (transfer)
6. Payment Agent: `get_available_payment_methods()` → User selects → `select_payment_method()` → `create_cart_mandate()` → `create_payment_mandate()` → `process_payment()`
7. Shopping Agent → Checkout Agent (return)
8. Checkout Agent: `create_order()` (payment already processed)

#### 5.2 Update Checkout Agent Instructions
**File**: `backend/app/shopping_agent/sub_agents/checkout_agent/agent.py`

**Add Transfer Logic**:
- After user confirms order summary, transfer to Payment Agent
- Wait for payment to be processed (check `tool_context.state["payment_processed"]` or `Payment` record)
- After payment processed, create order

### Phase 6: Testing & Validation

#### 6.1 Unit Tests
- Test `get_available_payment_methods()` returns dummy payment methods
- Test `select_payment_method()` stores selection in state
- Test `create_cart_mandate()` creates mandate with correct data
- Test `create_payment_mandate()` links to cart mandate
- Test `process_payment()` processes payment and updates order

#### 6.2 Integration Tests
- Test full checkout flow: cart → order summary → payment method selection → payment → order creation
- Test mandate creation order: Cart Mandate → Payment Mandate
- Test payment method selection UI displays correctly
- Test order creation only happens after payment

#### 6.3 AP2 Compliance Validation
- Verify Cart Mandate contains required fields per AP2 spec
- Verify Payment Mandate contains required fields per AP2 spec
- Verify mandate linking (Payment Mandate references Cart Mandate)
- Verify mandate status transitions (pending → approved)

## Implementation Order

1. **Phase 1**: Backend - Payment Method Management (Tools & Agent)
2. **Phase 2**: Backend - Checkout Agent Integration
3. **Phase 3**: Frontend - Payment Method Selection UI
4. **Phase 4**: Backend - Artifact Streaming
5. **Phase 5**: Agent Coordination
6. **Phase 6**: Testing & Validation

## Risk Mitigation

1. **State Management**: Ensure payment method selection and mandate IDs are properly stored in session state
2. **Error Handling**: Handle cases where payment method selection is cancelled or payment fails
3. **Order Creation Timing**: Ensure order is only created after payment is successfully processed
4. **Mandate Linking**: Ensure Payment Mandate correctly references Cart Mandate
5. **Frontend-Backend Sync**: Ensure frontend correctly displays payment methods and handles selection

## Success Criteria

1. ✅ User can view available payment methods after confirming order summary
2. ✅ User can select a payment method
3. ✅ Cart Mandate is created before payment method selection
4. ✅ Payment Mandate is created after payment method selection
5. ✅ Payment is processed before order creation
6. ✅ Order is created with status="completed" only after payment is processed
7. ✅ All mandates are stored in database with correct linking
8. ✅ Frontend displays payment method selection UI correctly
9. ✅ Full checkout flow works end-to-end

## Notes

- **Demo Payment Methods**: For demo purposes, payment methods are hardcoded. In production, these would be retrieved from a Credentials Provider.
- **Payment Processing**: Payment processing is simulated for demo. In production, this would integrate with actual payment gateway.
- **Mandate Signatures**: For demo, mandate signatures are not implemented. In production, mandates would be cryptographically signed per AP2 spec.
- **Error Recovery**: If payment fails, user should be able to retry with same or different payment method.

