# Agentic E-commerce Architecture Plan

## Overview

Modern agentic architecture leveraging A2A (Agent-to-Agent) and AP2 (Agent Payments Protocol) standards for secure, interoperable AI-driven e-commerce.

---

## Directory Structure

```
app/
├── common/                      # Shared utilities
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   └── utils.py
│
├── product_discovery_agent/     # Existing - move here
│   ├── __init__.py              # Exports: root_agent
│   ├── agent.py                 # Agent definition
│   └── tools.py                 # text_vector_search, image_vector_search
│
├── cart_agent/                  # NEW
│   ├── __init__.py              # Exports: root_agent
│   ├── agent.py                 # Cart agent definition
│   └── tools.py                 # Cart management tools
│
├── checkout_agent/              # NEW
│   ├── __init__.py              # Exports: root_agent
│   ├── agent.py                 # Checkout agent definition
│   └── tools.py                 # Order creation tools
│
├── payment_agent/              # NEW (AP2-compliant)
│   ├── __init__.py              # Exports: root_agent
│   ├── agent.py                 # Payment agent definition
│   └── tools.py                 # Payment processing tools
│
├── customer_service_agent/      # NEW
│   ├── __init__.py              # Exports: root_agent
│   ├── agent.py                 # Customer service agent definition
│   └── tools.py                 # Support tools
│
└── main.py                      # FastAPI app (orchestrator)
```

---

## Agent Tool Definitions

### 1. Product Discovery Agent

**Tools:**
- `text_vector_search(query: str)` - Semantic search over products
- `image_vector_search(image_bytes: bytes)` - Visual similarity search
- `get_product_details(product_id: str)` - Get full product information

**Agent Description:**
"Handles product discovery through text and image search"

**Output Schema:**
```python
class ProductResult(BaseModel):
    id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    description: Optional[str] = Field(description="Product description", default="")
    picture: Optional[str] = Field(description="Product image URL", default="")
    distance: Optional[float] = Field(description="Search relevance score", default=0.0)

class ProductSearchOutput(BaseModel):
    products: List[ProductResult] = Field(description="List of found products")
    summary: Optional[str] = Field(description="Brief summary of search results", default="")
```

---

### 2. Cart Agent

**Tools:**
- `add_to_cart(product_id: str, quantity: int)` - Add product to cart with AP2 intent mandate
- `get_cart(session_id: str)` - Retrieve cart contents
- `update_cart_item(cart_item_id: str, quantity: int)` - Update item quantity
- `remove_from_cart(cart_item_id: str)` - Remove item from cart
- `clear_cart(session_id: str)` - Empty entire cart
- `get_cart_total(session_id: str)` - Calculate cart total

**Agent Description:**
"Manages shopping cart operations including adding, updating, and removing items"

**Output Schema:**
```python
class CartItem(BaseModel):
    cart_item_id: str = Field(description="Cart item ID")
    product_id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    picture: Optional[str] = Field(description="Product image URL", default="")
    quantity: int = Field(description="Quantity")
    price: float = Field(description="Unit price")
    subtotal: float = Field(description="Item subtotal")

class CartOutput(BaseModel):
    items: List[CartItem] = Field(description="Cart items")
    total_items: int = Field(description="Total number of items")
    subtotal: float = Field(description="Cart subtotal")
    message: Optional[str] = Field(description="Status message", default="")
```

---

### 3. Checkout Agent

**Tools:**
- `create_order(session_id: str, shipping_address: str)` - Convert cart to order with AP2 cart mandate
- `get_order_status(order_id: str)` - Get order details and status
- `cancel_order(order_id: str)` - Cancel pending order
- `validate_cart_for_checkout(session_id: str)` - Check if cart is ready for checkout

**Agent Description:**
"Handles order creation from cart and order management"

**Output Schema:**
```python
class OrderItem(BaseModel):
    product_id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    quantity: int = Field(description="Quantity")
    price: float = Field(description="Unit price")

class OrderOutput(BaseModel):
    order_id: str = Field(description="Order ID")
    status: str = Field(description="Order status")
    items: List[OrderItem] = Field(description="Order items")
    total_amount: float = Field(description="Total amount")
    shipping_address: Optional[str] = Field(description="Shipping address", default="")
    created_at: Optional[str] = Field(description="Order creation time", default="")
    message: Optional[str] = Field(description="Status message", default="")
```

---

### 4. Payment Agent (AP2-Compliant)

**Tools:**
- `create_payment_mandate(order_id: str, payment_method: str)` - Create AP2 payment mandate
- `process_payment(order_id: str, payment_method: str)` - Process payment with AP2 compliance
- `get_payment_status(payment_id: str)` - Check payment status
- `refund_payment(payment_id: str, reason: str)` - Initiate refund
- `get_payment_history(session_id: str)` - Retrieve payment history

**Agent Description:**
"Processes payments using AP2 protocol with cryptographic mandates"

**Output Schema:**
```python
class PaymentOutput(BaseModel):
    payment_id: str = Field(description="Payment ID")
    order_id: str = Field(description="Order ID")
    amount: float = Field(description="Payment amount")
    payment_method: str = Field(description="Payment method")
    status: str = Field(description="Payment status")
    transaction_id: Optional[str] = Field(description="Transaction ID", default="")
    payment_mandate_id: Optional[str] = Field(description="AP2 mandate ID", default="")
    message: Optional[str] = Field(description="Status message", default="")
```

---

### 5. Customer Service Agent

**Tools:**
- `create_inquiry(inquiry_type: str, message: str, order_id: Optional[str])` - Create customer inquiry
- `get_inquiry_status(inquiry_id: str)` - Check inquiry status
- `search_faq(query: str)` - Search FAQ knowledge base
- `initiate_return(order_id: str, reason: str)` - Initiate return process
- `get_order_inquiries(order_id: str)` - Get all inquiries for an order

**Agent Description:**
"Handles customer support including returns, refunds, and inquiries"

**Output Schema:**
```python
class InquiryOutput(BaseModel):
    inquiry_id: str = Field(description="Inquiry ID")
    inquiry_type: str = Field(description="Type of inquiry")
    message: str = Field(description="Inquiry message")
    status: str = Field(description="Inquiry status")
    order_id: Optional[str] = Field(description="Related order ID", default="")
    created_at: Optional[str] = Field(description="Creation time", default="")
    response: Optional[str] = Field(description="Response message", default="")
```

---

### 6. Shared AP2 Mandate Tools (in `common/`)

**Tools:**
- `create_mandate(mandate_type: str, user_id: str, session_id: str, data: Dict)` - Create AP2 mandate
- `verify_mandate(mandate_id: str)` - Verify mandate signature
- `get_mandate_chain(order_id: str)` - Get complete mandate chain for audit

---

## Database Schema (AP2-Aware)

### Mandates Table (AP2 Core)
```sql
mandates (
    mandate_id VARCHAR(255) PRIMARY KEY,
    mandate_type VARCHAR(50), -- 'intent', 'cart', 'payment'
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    mandate_data JSONB,
    signature VARCHAR(512),
    status VARCHAR(50), -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT NOW()
)
```

### Cart Management
```sql
cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    product_id VARCHAR(255),
    quantity INT,
    intent_mandate_id VARCHAR(255), -- AP2: Links to user intent
    added_at TIMESTAMP DEFAULT NOW()
)
```

### Orders
```sql
orders (
    order_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    total_amount DECIMAL(10,2),
    cart_mandate_id VARCHAR(255), -- AP2: Cryptographic proof of cart approval
    status VARCHAR(50), -- 'pending', 'completed', 'cancelled'
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)

order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id VARCHAR(255),
    product_id VARCHAR(255),
    quantity INT,
    price DECIMAL(10,2)
)
```

### Payments (AP2-Compliant)
```sql
payments (
    payment_id VARCHAR(255) PRIMARY KEY,
    order_id VARCHAR(255),
    amount DECIMAL(10,2),
    payment_method VARCHAR(50), -- 'credit_card', 'paypal', etc.
    payment_mandate_id VARCHAR(255), -- AP2: Cryptographic proof of payment authorization
    transaction_id VARCHAR(255),
    status VARCHAR(50), -- 'pending', 'completed', 'failed', 'refunded'
    created_at TIMESTAMP DEFAULT NOW()
)
```

### Customer Service
```sql
customer_inquiries (
    inquiry_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    inquiry_type VARCHAR(50), -- 'return', 'refund', 'question', 'complaint'
    message TEXT,
    related_order_id VARCHAR(255),
    status VARCHAR(50), -- 'open', 'resolved', 'escalated'
    created_at TIMESTAMP DEFAULT NOW()
)
```

---

## Implementation Phases

### Phase 1: Refactor Existing Agent ✓
**Goal:** Reorganize current concierge_agent into product_discovery_agent

**Tasks:**
1. Rename `concierge_agent/` → `product_discovery_agent/`
2. Update imports in main.py
3. Update AGENT_DIR path
4. Test agent discovery

**Tools:**
- `text_vector_search()` (existing)
- `image_vector_search()` (existing)
- `get_product_details()` (new)

---

### Phase 2: Cart Agent
**Goal:** Implement shopping cart functionality

**Tasks:**
1. Create `cart_agent/` directory
2. Create `cart_items` table
3. Implement cart tools
4. Create cart agent definition
5. Update orchestrator to include cart agent

**Database:** `cart_items` table

**Tools:**
- `add_to_cart()`
- `get_cart()`
- `update_cart_item()`
- `remove_from_cart()`
- `clear_cart()`
- `get_cart_total()`

---

### Phase 3: Checkout Agent
**Goal:** Convert cart to orders

**Tasks:**
1. Create `checkout_agent/` directory
2. Create `orders` and `order_items` tables
3. Implement AP2 cart mandates
4. Implement checkout tools
5. Create checkout agent definition
6. Update orchestrator

**Database:** `orders`, `order_items` tables

**Tools:**
- `create_order()`
- `get_order_status()`
- `cancel_order()`
- `validate_cart_for_checkout()`

---

### Phase 4: Payment Agent (AP2-Compliant)
**Goal:** Process payments with AP2 mandates

**Tasks:**
1. Create `payment_agent/` directory
2. Create `payments` table
3. Create `mandates` table
4. Implement AP2 mandate tools
5. Implement payment tools
6. Create payment agent definition
7. Update orchestrator

**Database:** `payments`, `mandates` tables

**Tools:**
- `create_payment_mandate()`
- `process_payment()`
- `get_payment_status()`
- `refund_payment()`
- `get_payment_history()`

**AP2 Mandate Tools:**
- `create_mandate()`
- `verify_mandate()`
- `get_mandate_chain()`

---

### Phase 5: Customer Service Agent
**Goal:** Handle customer support

**Tasks:**
1. Create `customer_service_agent/` directory
2. Create `customer_inquiries` table
3. Implement support tools
4. Create customer service agent definition
5. Update orchestrator

**Database:** `customer_inquiries` table

**Tools:**
- `create_inquiry()`
- `get_inquiry_status()`
- `search_faq()`
- `initiate_return()`
- `get_order_inquiries()`

---

### Phase 6: Orchestrator
**Goal:** Coordinate all agents

**Tasks:**
1. Create orchestrator logic
2. Update main.py to use orchestrator
3. Wire all AgentTools
4. Test end-to-end workflows

**Orchestrator Agent:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from ..product_discovery_agent import root_agent as product_discovery_agent
from ..cart_agent import root_agent as cart_agent
from ..checkout_agent import root_agent as checkout_agent
from ..payment_agent import root_agent as payment_agent
from ..customer_service_agent import root_agent as customer_service_agent

root_agent = LlmAgent(
    name="shopping_agent",
    description="Orchestrates shopping workflow by routing to specialized agents",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(product_discovery_agent),
        AgentTool(cart_agent),
        AgentTool(checkout_agent),
        AgentTool(payment_agent),
        AgentTool(customer_service_agent),
    ],
)
```

---

## Key Principles

### 1. Modularity
- Each agent is self-contained in its own directory
- Agents can be developed and tested independently
- Clear separation of concerns

### 2. ADK Compatibility
- Directory-based agent discovery
- Each agent exports `root_agent` in `__init__.py`
- ADK automatically finds and registers agents

### 3. A2A Compliance
- Agents communicate via AgentTool delegation
- Each agent has a clear, single responsibility
- Tool-based interaction pattern

### 4. AP2 Compliance
- Cryptographic mandates for all financial transactions
- Mandate chain tracking (intent → cart → payment)
- Audit trail for compliance
- User consent verification

### 5. Scalability
- Easy to add new agents without breaking existing ones
- Agents can be reused across different orchestrators
- Horizontal scaling by adding agents

### 6. Simplicity
- Tools have clear, single purposes
- Simple agent descriptions
- Minimal parameters per tool
- Clear return structures

---

## Tool Summary

| Agent | Tool Count | Key Tools |
|-------|-----------|-----------|
| **Product Discovery** | 3 | text_vector_search, image_vector_search, get_product_details |
| **Cart** | 6 | add_to_cart, get_cart, update_cart_item, remove_from_cart, clear_cart, get_cart_total |
| **Checkout** | 4 | create_order, get_order_status, cancel_order, validate_cart_for_checkout |
| **Payment** | 5 | create_payment_mandate, process_payment, get_payment_status, refund_payment, get_payment_history |
| **Customer Service** | 5 | create_inquiry, get_inquiry_status, search_faq, initiate_return, get_order_inquiries |
| **Shared (AP2)** | 3 | create_mandate, verify_mandate, get_mandate_chain |
| **TOTAL** | **26** | |

---

## AP2 Mandate Flow

### 1. Intent Mandate
- Created when user expresses intent to purchase
- Links to cart_items via `intent_mandate_id`
- Proof of user's initial intent

### 2. Cart Mandate
- Created when user approves cart for checkout
- Links to orders via `cart_mandate_id`
- Cryptographic proof of cart approval

### 3. Payment Mandate
- Created when user authorizes payment
- Links to payments via `payment_mandate_id`
- Cryptographic proof of payment authorization

### Mandate Chain
```
User Intent → Intent Mandate → Cart → Cart Mandate → Order → Payment Mandate → Payment
```

---

## Security & Compliance

### AP2 Benefits
- **Cryptographic Proof:** All financial actions are cryptographically signed
- **Audit Trail:** Complete mandate chain for compliance
- **User Control:** Users must explicitly approve each transaction type
- **Interoperability:** Standard protocol for agent-agent payments
- **Fraud Prevention:** Mandates cannot be forged or altered

### Design Considerations
- All mandates are stored in `mandates` table
- Mandates include cryptographic signatures
- Mandate chain provides full audit trail
- User must approve each step (intent → cart → payment)
- Failed transactions can be traced through mandate chain

---

## Testing Strategy

### Unit Tests
- Test each agent independently
- Test each tool function
- Mock database calls

### Integration Tests
- Test agent-to-agent communication
- Test mandate flow
- Test database operations

### End-to-End Tests
- Test complete workflows:
  - Search → Add to Cart → Checkout → Payment
  - Return → Customer Service
  - Order cancellation

---

## Next Steps - Implementation Roadmap

### Immediate Actions (Today)

#### 1. Database Setup
- [ ] Connect to existing database
- [ ] Verify `catalog_items` table exists
- [ ] Plan migration strategy for new tables
- [ ] Document current schema

#### 2. Phase 1: Refactor Product Discovery Agent
- [ ] Rename `concierge_agent/` → `product_discovery_agent/`
- [ ] Update imports in `main.py`
- [ ] Update `AGENT_DIR` path
- [ ] Test agent discovery
- [ ] Verify `/list-apps` endpoint
- [ ] Run existing tests

**Estimated Time:** 30 minutes

---

### Short Term (Next 1-2 Days)

#### 3. Phase 2: Cart Agent
- [ ] Create `cart_agent/` directory structure
- [ ] Create `cart_items` table in database
- [ ] Implement cart tools (`add_to_cart`, `get_cart`, etc.)
- [ ] Create cart agent with output schema
- [ ] Add AP2 intent mandate support
- [ ] Write unit tests for cart tools
- [ ] Integration test with product discovery

**Estimated Time:** 4-6 hours

#### 4. Phase 3: Checkout Agent
- [ ] Create `checkout_agent/` directory structure
- [ ] Create `orders` and `order_items` tables
- [ ] Implement checkout tools
- [ ] Add AP2 cart mandate support
- [ ] Create checkout agent with output schema
- [ ] Write tests
- [ ] Integration test with cart agent

**Estimated Time:** 4-6 hours

---

### Medium Term (Next 3-5 Days)

#### 5. Phase 4: Payment Agent (AP2-Compliant)
- [ ] Create `payment_agent/` directory structure
- [ ] Create `payments` and `mandates` tables
- [ ] Implement AP2 mandate creation/verification
- [ ] Implement payment tools
- [ ] Create payment agent with output schema
- [ ] Add cryptographic signing for mandates
- [ ] Write comprehensive tests
- [ ] Integration test full payment flow

**Estimated Time:** 6-8 hours

#### 6. Phase 5: Customer Service Agent
- [ ] Create `customer_service_agent/` directory structure
- [ ] Create `customer_inquiries` table
- [ ] Implement support tools
- [ ] Create customer service agent with output schema
- [ ] Write tests
- [ ] Integration test with other agents

**Estimated Time:** 3-4 hours

---

### Long Term (Next Week)

#### 7. Phase 6: Orchestrator
- [ ] Create orchestrator agent
- [ ] Wire all AgentTools together
- [ ] Update `main.py` to use orchestrator
- [ ] End-to-end workflow testing
- [ ] Performance testing
- [ ] Load testing

**Estimated Time:** 4-6 hours

#### 8. Documentation & Polish
- [ ] Write agent documentation
- [ ] Create API documentation
- [ ] Write developer guides
- [ ] Create Postman collection
- [ ] Update README
- [ ] Write deployment guide

**Estimated Time:** 6-8 hours

---

### Testing Strategy

#### Unit Tests
- [ ] Product discovery tools
- [ ] Cart tools
- [ ] Checkout tools
- [ ] Payment tools
- [ ] Customer service tools
- [ ] AP2 mandate tools

#### Integration Tests
- [ ] Agent-to-agent communication
- [ ] Database operations
- [ ] Mandate flow
- [ ] Cart → Checkout → Payment flow

#### End-to-End Tests
- [ ] Complete shopping flow
- [ ] Return process
- [ ] Error handling
- [ ] Authentication flows

---

### Deployment Checklist

#### Pre-Deployment
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Security review completed

#### Deployment
- [ ] Build Docker image
- [ ] Push to container registry
- [ ] Deploy to Cloud Run
- [ ] Configure environment
- [ ] Set up monitoring
- [ ] Configure alerts

#### Post-Deployment
- [ ] Smoke tests
- [ ] Monitor logs
- [ ] Performance monitoring
- [ ] User acceptance testing

---

### Success Criteria

#### Phase 1 ✓
- [ ] Agent discovered by ADK
- [ ] Product search working
- [ ] Health check passing

#### Phase 2 ✓
- [ ] Cart operations working
- [ ] Intent mandates created
- [ ] Cart persists across sessions

#### Phase 3 ✓
- [ ] Orders created successfully
- [ ] Cart mandates working
- [ ] Order cancellation working

#### Phase 4 ✓
- [ ] Payments processed
- [ ] Payment mandates created
- [ ] Refunds working
- [ ] Mandate chain complete

#### Phase 5 ✓
- [ ] Inquiries created
- [ ] FAQ search working
- [ ] Returns initiated

#### Phase 6 ✓
- [ ] Full workflow working
- [ ] All agents communicating
- [ ] Performance acceptable
- [ ] Production ready

---

### Risk Mitigation

#### Technical Risks
- **Database migration issues:** Test migrations in staging first
- **Agent communication failures:** Implement retry logic
- **Mandate signature errors:** Add comprehensive validation
- **Performance bottlenecks:** Load test early

#### Timeline Risks
- **Scope creep:** Stick to defined phases
- **Testing delays:** Start tests early
- **Integration issues:** Integration tests first

---

### Dependencies

#### External
- Database connectivity
- Vertex AI API access
- ADK framework updates
- AP2 protocol documentation

#### Internal
- Team availability
- Code review process
- Testing environment
- Deployment pipeline

---

### Communication Plan

#### Daily Standups
- Progress updates
- Blockers
- Next day priorities

#### Weekly Reviews
- Phase completion
- Demo functionality
- Plan adjustments

#### Documentation Updates
- Keep `agents.md` current
- Update changelog
- Document decisions

---

## Output Schema Standards

All agents enforce structured responses using Pydantic models. This ensures:
- **Type Safety:** Enforced at runtime
- **Consistency:** Predictable response formats
- **Validation:** Automatic data validation
- **Documentation:** Self-documenting schemas

### Schema Summary

| Agent | Primary Schema | Secondary Schema |
|-------|---------------|------------------|
| **Product Discovery** | `ProductSearchOutput` | `ProductResult` |
| **Cart** | `CartOutput` | `CartItem` |
| **Checkout** | `OrderOutput` | `OrderItem` |
| **Payment** | `PaymentOutput` | - |
| **Customer Service** | `InquiryOutput` | - |

### Implementation Pattern

Each agent implements the schema in `agent.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class AgentOutput(BaseModel):
    # Define fields with Field descriptions
    primary_field: str = Field(description="...")
    optional_field: Optional[str] = Field(description="...", default="")

root_agent = LlmAgent(
    name="agent_name",
    description="Agent description",
    model="gemini-2.5-flash",
    tools=[...],
    output_schema=AgentOutput,
    output_key="output",
)
```

---

## Documentation Plan

### 1. API Documentation (FastAPI Auto-Generated)

**Implementation:**
- FastAPI automatically generates OpenAPI/Swagger documentation
- Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- Includes all endpoints, request/response schemas, and examples

**Key Endpoints to Document:**
```
GET  /healthz                           # Health check
GET  /list-apps                          # List available agents
POST /apps/{app_name}/users/{user_id}/sessions/{session_id}  # Create/update session
POST /run_sse                           # Execute agent (streaming)
GET  /sessions/{session_id}             # Get session details
```

**Request/Response Examples:**
```json
// Create Session
POST /apps/concierge_agent/users/user_123/sessions/session_abc
{
  "state": {"preferred_language": "English"}
}

// Run Agent
POST /run_sse
{
  "app_name": "concierge_agent",
  "user_id": "user_123",
  "session_id": "session_abc",
  "new_message": {
    "role": "user",
    "parts": [{"text": "Find running shoes"}]
  },
  "streaming": false
}
```

**Sections:**
- Authentication methods
- Error responses
- Rate limiting
- WebSocket support for streaming

---

### 2. Agent Documentation

**Per-Agent Documentation Files:**

```
docs/
├── agents/
│   ├── product_discovery.md
│   ├── cart.md
│   ├── checkout.md
│   ├── payment.md
│   └── customer_service.md
├── api/
│   ├── endpoints.md
│   ├── authentication.md
│   └── examples.md
├── integration/
│   ├── a2a-protocol.md
│   ├── ap2-mandates.md
│   └── webhooks.md
└── guides/
    ├── getting-started.md
    ├── deployment.md
    └── troubleshooting.md
```

**Agent Documentation Template:**
```markdown
# [Agent Name] Agent

## Overview
Brief description of agent purpose and responsibilities.

## Capabilities
- List of capabilities
- Use cases

## Tools
### tool_name
- **Description:** What the tool does
- **Parameters:** Input parameters
- **Returns:** Output structure
- **Example:** Usage example

## Output Schema
```python
# Pydantic model
```

## Integration Points
- Other agents it communicates with
- Data dependencies

## Error Handling
- Common errors
- Error responses
```

---

### 3. Tool Documentation

**Inline Documentation (Docstrings):**
```python
def add_to_cart(product_id: str, quantity: int) -> Dict[str, Any]:
    """
    Add product to cart with AP2 intent mandate support.
    
    This tool adds a product to the user's shopping cart and creates
    an intent mandate for AP2 compliance tracking.
    
    Args:
        product_id: Unique identifier for the product
        quantity: Number of items to add (must be > 0)
    
    Returns:
        Dict containing:
            - cart_item_id: Unique identifier for cart item
            - product_id: Product identifier
            - quantity: Quantity added
            - added_at: Timestamp
    
    Raises:
        ValueError: If product_id is invalid or quantity <= 0
        DatabaseError: If database operation fails
    
    Example:
        >>> add_to_cart("prod_123", 2)
        {
            "cart_item_id": "cart_item_456",
            "product_id": "prod_123",
            "quantity": 2,
            "added_at": "2024-01-15T10:30:00Z"
        }
    """
```

**Tool Reference Guide:**
- Complete list of all tools across all agents
- Input/output specifications
- Parameter descriptions
- Return value structures
- Error codes

---

### 4. Developer Documentation

**README.md Structure:**
```markdown
# E-commerce Agent Platform

## Architecture
- Agent structure
- Database schema
- API design

## Setup
- Prerequisites
- Installation
- Configuration

## Development
- Running locally
- Building Docker image
- Running tests

## Deployment
- Docker deployment
- Cloud Run deployment
- Environment variables

## Contributing
- Code style
- Testing requirements
- Pull request process
```

**Developer Guides:**
- `DEVELOPMENT.md` - Development workflow
- `ARCHITECTURE.md` - System architecture details
- `TESTING.md` - Testing strategies and examples
- `DEPLOYMENT.md` - Deployment procedures

---

### 5. Protocol Documentation (AP2/A2A)

**AP2 Mandate Documentation:**
```markdown
# AP2 Mandate Flow

## Overview
Explanation of AP2 protocol implementation

## Mandate Types
1. Intent Mandate
2. Cart Mandate
3. Payment Mandate

## Implementation Details
- Cryptographic signatures
- Mandate creation process
- Verification procedures
- Audit trail

## Code Examples
```python
# Create mandate
mandate = create_mandate(
    mandate_type="intent",
    user_id="user_123",
    session_id="session_abc",
    data={"product_id": "prod_123", "quantity": 2}
)
```

## Mandate Chain
Diagram showing mandate relationships
```

**A2A Agent Communication:**
- Agent discovery mechanism
- Tool delegation patterns
- Inter-agent communication examples
- Error propagation between agents

---

### 6. Database Schema Documentation

**Schema Documentation Includes:**
- Table descriptions
- Column definitions
- Relationships (foreign keys)
- Indexes and constraints
- Sample data

**Example:**
```sql
-- cart_items table
-- Stores items in user shopping carts with AP2 intent mandate support

CREATE TABLE cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,           -- User identifier
    session_id VARCHAR(255) NOT NULL,         -- Session identifier
    product_id VARCHAR(255) NOT NULL,         -- References catalog_items.id
    quantity INT NOT NULL CHECK (quantity > 0), -- Quantity validation
    intent_mandate_id VARCHAR(255),           -- AP2 mandate ID
    added_at TIMESTAMP DEFAULT NOW(),         -- Auto-timestamp
    
    FOREIGN KEY (product_id) REFERENCES catalog_items(id),
    INDEX idx_user_session (user_id, session_id),
    INDEX idx_product (product_id)
);
```

---

### 7. API Reference (Postman/OpenAPI)

**Export Formats:**
- OpenAPI 3.0 specification (`openapi.json`)
- Postman collection (`postman_collection.json`)
- Insomnia workspace

**Contents:**
- All endpoints
- Request/response examples
- Authentication flows
- Error scenarios
- Environment variables

---

### 8. Integration Documentation

**Client Integration Guides:**
- JavaScript/TypeScript SDK
- Python SDK
- curl examples
- SDK installation
- Authentication setup
- Basic usage examples

**Webhook Documentation:**
- Webhook event types
- Webhook security
- Webhook payload structures
- Retry logic
- Testing webhooks

---

### 9. Troubleshooting Documentation

**Common Issues:**
- Agent not responding
- Authentication errors
- Database connection issues
- Payment failures
- Session management problems

**Debugging Guides:**
- Log analysis
- Error code reference
- Performance tuning
- Scaling considerations

---

### 10. Changelog & Versioning

**Keep Track Of:**
- Agent versions
- API versions
- Breaking changes
- New features
- Bug fixes
- Deprecations

**Format:**
```markdown
# Changelog

## [2.0.0] - 2024-01-15
### Added
- Payment agent with AP2 compliance
- Customer service agent
- Webhook support

### Changed
- Cart agent output schema
- Session management structure

### Breaking Changes
- Removed `order_summary` endpoint
- Changed `cart_items` response format

## [1.0.0] - 2024-01-01
### Added
- Initial release
- Product discovery agent
- Cart agent
- Checkout agent
```

---

### Documentation Standards

**Writing Guidelines:**
- Clear, concise language
- Code examples for all concepts
- Diagrams for complex flows
- Consistent formatting
- Regular updates with code changes

**Documentation Tools:**
- Markdown for all docs
- Mermaid for diagrams
- Sphinx or MkDocs for site generation
- Docusaurus for documentation site

**Quality Checklist:**
- [ ] All endpoints documented
- [ ] All tools have docstrings
- [ ] Code examples provided
- [ ] Diagrams for complex flows
- [ ] Troubleshooting section complete
- [ ] Changelog up to date
- [ ] API examples tested

---

## References

- **AP2 Protocol:** https://ap2-protocol.org/
- **A2A Protocol:** https://a2aprotocol.ai/
- **Google ADK:** https://cloud.google.com/adk
- **Model Context Protocol:** MCP for tool integration
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

