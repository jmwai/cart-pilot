# Cart Pilot - AI-Powered Shopping Assistant

> **Note**: Update the badge URL in this README with your GitHub username and repository name.

Multi-agent AI system for e-commerce shopping assistance built with Google ADK and deployed on Cloud Run. Cart Pilot uses AI agents to create a futuristic shopping experience where intelligent assistants orchestrate your entire shopping journey.

## 🎯 Agent-Driven Architecture

This platform follows an **agent-driven architecture** where users interact naturally through conversation. The AI chat assistant orchestrates all shopping operations including product discovery, cart management, checkout, payments, and customer support.

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chatbox UI  │  │ Product Grid │  │ Product Pages │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                   │
│         │ A2A Protocol (JSON-RPC 2.0 over HTTP)             │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + ADK)                   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         A2A Executor (ShoppingAgentExecutor)          │  │
│  │  - Receives A2A requests                              │  │
│  │  - Manages session state                              │  │
│  │  - Streams responses                                  │  │
│  │  - Creates artifacts (products, cart, orders)        │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Shopping Agent (Orchestrator)                │  │
│  │  - Routes requests to sub-agents                     │  │
│  │  - Maintains conversation context                     │  │
│  │  - Uses LLM-driven delegation                        │  │
│  └──┬──────────┬──────────┬──────────┬───────────────┘  │
│     │          │          │          │                   │
│     ▼          ▼          ▼          ▼                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────┐        │
│  │ Cart │  │Check │  │Product│  │  Customer    │        │
│  │Agent │  │out   │  │Discover│  │  Service    │        │
│  │      │  │Agent │  │  Agent │  │  Agent      │        │
│  └──────┘  └──────┘  └──────┘  └──────────────┘        │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Payment Agent (Separate)                    │  │
│  │  - AP2-compliant payment processing                 │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Database (PostgreSQL + pgvector)           │  │
│  │  - Products, Cart, Orders, Payments                 │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## 🤖 Agents & Sub-Agents Architecture

### Main Agent: Shopping Agent (Orchestrator)

**Location**: `backend/app/shopping_agent/agent.py`

The Shopping Agent is the main orchestrator that routes user requests to specialized sub-agents using LLM-driven delegation. It does NOT call tools directly; instead, it delegates to sub-agents based on user intent.

**Key Responsibilities**:
- Understand user intent from natural language
- Route requests to appropriate sub-agents
- Maintain conversation flow
- Coordinate multi-step workflows

**Delegation Mechanism**:
- Uses `sub_agents` parameter (not `AgentTool`) for hierarchical delegation
- Each sub-agent is an expert in its domain
- State is shared across all sub-agents via session state

### Sub-Agents

All sub-agents are located in `backend/app/shopping_agent/sub_agents/`:

#### 1. Product Discovery Agent
**Location**: `backend/app/shopping_agent/sub_agents/product_discovery_agent/`

**Purpose**: Search and discover products using semantic search

**Tools**:
- `text_vector_search(query: str, tool_context: ToolContext)` - Semantic search using pgvector embeddings
- `image_vector_search(image_bytes: bytes, tool_context: ToolContext)` - Visual similarity search

**Key Features**:
- Stores search results in `state["current_results"]` for later reference
- Returns structured product data with images, prices, and descriptions
- Uses Vertex AI Multimodal Embedding Model for embeddings

#### 2. Cart Agent
**Location**: `backend/app/shopping_agent/sub_agents/cart_agent/`

**Purpose**: Manage shopping cart operations

**Tools**:
- `add_to_cart(product_description: str, quantity: int, tool_context: ToolContext)` - Add product to cart by matching description against search results
- `get_cart(tool_context: ToolContext)` - Retrieve cart contents with prices and totals
- `update_cart_item(cart_item_id: str, quantity: int)` - Update item quantity
- `remove_from_cart(cart_item_id: str)` - Remove item from cart
- `clear_cart(session_id: str)` - Empty entire cart
- `get_cart_total(session_id: str)` - Calculate cart total

**Key Features**:
- Automatically matches product descriptions to search results stored in session state
- Stores cart items in `state["cart"]` for executor access
- Supports positional references ("first one", "blue shoes", etc.)

#### 3. Checkout Agent
**Location**: `backend/app/shopping_agent/sub_agents/checkout_agent/`

**Purpose**: Create orders from cart and manage order status

**Tools**:
- `create_order(tool_context: ToolContext)` - Convert cart to order, auto-complete payment
- `get_order_status(tool_context: ToolContext, order_id: str)` - Get order details
- `cancel_order(tool_context: ToolContext, order_id: str)` - Cancel pending order
- `validate_cart_for_checkout(tool_context: ToolContext)` - Validate cart before checkout

**Key Features**:
- Automatically retrieves shipping address (hardcoded for demo)
- Auto-completes orders (payment skipped for demo)
- Stores order in `state["current_order"]` for executor access
- Clears cart after order creation

#### 4. Customer Service Agent
**Location**: `backend/app/shopping_agent/sub_agents/customer_service_agent/`

**Purpose**: Handle customer support inquiries, returns, and refunds

**Tools**:
- `create_inquiry(inquiry_type: str, message: str, session_id: str, order_id: Optional[str])` - Create customer inquiry
- `get_inquiry_status(inquiry_id: str)` - Check inquiry status
- `search_faq(query: str)` - Search FAQ knowledge base
- `initiate_return(order_id: str, reason: str)` - Initiate return process
- `get_order_inquiries(order_id: str)` - Get all inquiries for an order

### Separate Agent: Payment Agent

**Location**: `backend/app/payment_agent/`

**Purpose**: Process payments with AP2 compliance (separate from orchestrator)

**Tools**:
- `create_payment_mandate(order_id: str, payment_method: str)` - Create AP2 payment mandate
- `process_payment(order_id: str, payment_method: str)` - Process payment with AP2 compliance
- `get_payment_status(payment_id: str)` - Check payment status
- `refund_payment(payment_id: str, reason: str)` - Initiate refund
- `get_payment_history(session_id: str)` - Retrieve payment history

## 🔧 Tools Architecture

### Tool Context Pattern

All tools that need access to session state accept `ToolContext` as the first parameter:

```python
def add_to_cart(
    tool_context: ToolContext,
    product_description: str,
    quantity: int = 1
) -> Dict[str, Any]:
    # Access session state
    session_id = tool_context._invocation_context.session.id
    current_results = tool_context.state.get("current_results", [])
    
    # Store results in state
    tool_context.state["cart"] = cart_items
```

### Session State Management

State is shared across all agents and persists across requests:

**State Keys**:
- `current_results` - Product search results (set by Product Discovery Agent)
- `cart` - Cart items array (set by Cart Agent)
- `current_order` - Current order details (set by Checkout Agent)
- `shipping_address` - Shipping address (set by Checkout Agent)

**State Persistence**:
- State is stored in ADK's `InMemorySessionService`
- Session ID is derived from A2A `contextId`
- State persists across multiple requests in the same conversation

## 📡 Frontend-Backend Communication

### A2A Protocol (Agent-to-Agent)

The frontend and backend communicate using the **A2A Protocol** (Agent-to-Agent Protocol), which provides:

- **Standardized agent communication** via JSON-RPC 2.0
- **Streaming support** for real-time updates
- **Structured data exchange** via artifacts
- **Session continuity** via `contextId`

### Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User sends message in Chatbox                            │
│    ↓                                                         │
│ 2. ShoppingAPI.sendMessageStream()                          │
│    - Wraps message in A2A format                            │
│    - Includes contextId for session continuity             │
│    ↓                                                         │
│ 3. A2A Client sends POST to backend                         │
│    Endpoint: Agent card URL (/.well-known/agent-card.json) │
│    ↓                                                         │
│ 4. A2A Executor receives request                           │
│    - Extracts user message                                  │
│    - Gets/creates session using contextId                   │
│    - Preserves existing state                               │
│    ↓                                                         │
│ 5. ADK Runner executes Shopping Agent                       │
│    - Shopping Agent routes to sub-agent                     │
│    - Sub-agent calls tools                                  │
│    - Tools update session state                             │
│    ↓                                                         │
│ 6. Executor streams events                                  │
│    - Text chunks (incremental)                              │
│    - Status updates                                         │
│    - Artifacts (products, cart, orders)                    │
│    ↓                                                         │
│ 7. Frontend receives streaming events                      │
│    - Parses events using a2a-parser.ts                     │
│    - Updates UI incrementally                              │
│    - Displays artifacts in chatbox                          │
└─────────────────────────────────────────────────────────────┘
```

### A2A Protocol Details

**Agent Card** (`backend/app/a2a_agent_card.py`):
- Defines agent capabilities and skills
- Exposed at `/.well-known/agent-card.json`
- Frontend uses this to initialize A2A client

**Request Format**:
```json
{
  "message": {
    "messageId": "uuid",
    "role": "user",
    "parts": [{"kind": "text", "text": "Find running shoes"}],
    "kind": "message",
    "contextId": "session-context-id"
  },
  "configuration": {
    "blocking": false,
    "acceptedOutputModes": ["text/plain"]
  }
}
```

**Response Format** (Streaming):
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "contextId": "session-context-id",
    "kind": "status-update",
    "status": {
      "state": "working",
      "message": {...}
    }
  }
}
```

**Artifacts** (Structured Data):
- Products: `DataPart` with `mimeType: "application/json"` and `type: "product_list"`
- Cart: `DataPart` with `type: "cart"`
- Orders: `DataPart` with `type: "order"`

### Session Management

**Session ID**:
- Derived from A2A `contextId`
- Maintained across requests via `localStorage` in frontend
- Used to preserve state between requests

**State Persistence**:
```python
# Backend: Get or create session
session = await self.runner.session_service.get_session(
    app_name=self.agent.name,
    user_id=user_id,
    session_id=task.context_id  # Uses contextId
)

# Tools: Access and update state
tool_context.state["current_results"] = products
tool_context.state["cart"] = cart_items
```

**Frontend State Tracking**:
```typescript
// Track contextId for session continuity
private contextId: string | null = null;

// Extract from responses
if (event.result?.contextId) {
  this.contextId = event.result.contextId;
  localStorage.setItem('shopping_context_id', this.contextId);
}
```

## 🔄 Data Flow Example

### Complete Shopping Flow

1. **User searches for products**:
   ```
   User: "Find me running shoes"
   ↓
   Shopping Agent → Product Discovery Agent
   ↓
   Product Discovery Agent calls text_vector_search()
   ↓
   Stores results in state["current_results"]
   ↓
   Returns products → Executor → Frontend
   ↓
   Frontend displays ProductList component
   ```

2. **User adds to cart**:
   ```
   User: "Add the blue shoes to my cart"
   ↓
   Shopping Agent → Cart Agent
   ↓
   Cart Agent calls add_to_cart(product_description="blue shoes")
   ↓
   add_to_cart() calls find_product_in_results()
   ↓
   Matches "blue shoes" from state["current_results"]
   ↓
   Creates cart item, stores in state["cart"]
   ↓
   Returns cart → Executor → Frontend
   ↓
   Frontend displays CartDisplay component
   ```

3. **User checks out**:
   ```
   User: "I want to checkout"
   ↓
   Shopping Agent → Checkout Agent
   ↓
   Checkout Agent calls create_order()
   ↓
   Retrieves cart from state["cart"]
   ↓
   Creates order, clears cart
   ↓
   Stores order in state["current_order"]
   ↓
   Returns order → Executor → Frontend
   ↓
   Frontend displays OrderDisplay component
   ```

## Features

### Backend (Agent Orchestration)
- 🤖 **Shopping Agent** - Main orchestrator that routes to sub-agents
- 🔍 **Product Discovery Agent** - Semantic search with pgvector embeddings
- 🛒 **Cart Agent** - Full cart CRUD operations with session state matching
- 📦 **Checkout Agent** - Order creation and management
- 💳 **Payment Agent** - AP2-compliant payment handling (separate agent)
- 🎧 **Customer Service Agent** - Support inquiries, returns, and refunds

### Frontend (Visual Catalog + Chat Interface)
- 🏠 **Product Listing** - Browse featured products in a clean grid layout
- 📦 **Product Details** - Detailed product views with images and specs
- 💬 **AI Chat Assistant** - Floating chatbox for agent-driven shopping
- 📋 **Product List** - Vertical list display with thumbnails matching cart
- 🛒 **Cart Display** - Visual cart representation with quantity controls
- ✅ **Order Confirmation** - Order details with shipping information
- 🎨 **Modern UI** - Clean, minimalist design
- 📱 **Responsive Design** - Works on all devices

## Tech Stack

- **Backend**: FastAPI, Google ADK, SQLAlchemy 2.0
- **AI**: Gemini 2.5 Flash, Vertex AI Multimodal Embeddings
- **Database**: PostgreSQL with pgvector
- **Protocol**: A2A (Agent-to-Agent) Protocol
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS
- **Testing**: pytest, 92+ unit tests
- **Deployment**: Cloud Run ready

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Run Tests

```bash
cd backend
pip install -r requirements-test.txt
pytest tests/unit/ -v
```

## Project Structure

```
backend/
├── app/
│   ├── common/                    # Shared utilities and models
│   ├── shopping_agent/            # Main orchestrator agent
│   │   ├── agent.py               # Shopping Agent definition
│   │   └── sub_agents/            # Sub-agents directory
│   │       ├── cart_agent/        # Cart management
│   │       ├── checkout_agent/    # Order processing
│   │       ├── customer_service_agent/  # Support
│   │       └── product_discovery_agent/  # Product search
│   ├── payment_agent/             # Payment processing (separate)
│   ├── a2a_executor.py            # A2A protocol bridge
│   ├── a2a_agent_card.py          # Agent card definition
│   └── main.py                    # FastAPI application
├── tests/                         # Test suite (92 tests)
└── migrations/                    # Alembic migrations

frontend/
├── src/
│   ├── app/                       # Next.js pages
│   ├── components/                # React components
│   │   ├── Chatbox.tsx            # AI chat interface
│   │   ├── ProductList.tsx        # Product list display
│   │   ├── CartDisplay.tsx        # Cart display
│   │   └── OrderDisplay.tsx       # Order confirmation
│   ├── lib/
│   │   ├── shopping-api.ts        # A2A client integration
│   │   └── a2a-parser.ts          # A2A event parser
│   └── types/                     # TypeScript definitions
└── package.json
```

## How It Works

### Complete Shopping Journey via Agent

1. **Product Discovery**: "Find me running shoes" → Product Discovery Agent searches and returns products
2. **Add to Cart**: "Add Air Jordan 1 to my cart" → Cart Agent matches product from state and creates cart item
3. **View Cart**: "Show me my cart" → Cart Agent displays cart contents
4. **Checkout**: "Checkout" → Checkout Agent creates order and clears cart
5. **Order Confirmation**: Order details displayed automatically
6. **Support**: "Return order ORD-123" → Customer Service Agent initiates return

All operations happen through natural conversation with the AI agent!

## Documentation

- [Frontend README](frontend/README.md) - Frontend implementation guide
- [Agent Architecture](backend/agents.md) - Detailed agent system design
- [API Documentation](backend/apidoc.md) - Backend API reference
- [Test Documentation](backend/tests/README.md) - Testing guide
- [Frontend Implementation Summary](FRONTEND_IMPLEMENTATION_SUMMARY.md) - Frontend implementation details
- [Workflow Documentation](WORKFLOW_DOCUMENTATION.md) - Complete workflow details

## License

MIT
