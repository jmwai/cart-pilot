# Agent Hierarchy Refactoring Plan

## Overview
Refactor agent structure to use ADK's hierarchical multi-agent system. Move cart, checkout, customer service, and product discovery agents as sub-agents of the orchestrator. Payment agent remains separate at top level.

## Target Structure

```
backend/app/
├── orchestrator_agent/
│   ├── __init__.py
│   ├── agent.py (updated to use sub_agents)
│   └── sub_agents/          ← NEW DIRECTORY
│       ├── __init__.py
│       ├── cart_agent/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── tools.py
│       ├── checkout_agent/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── tools.py
│       ├── customer_service_agent/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── tools.py
│       └── product_discovery_agent/
│           ├── __init__.py
│           ├── agent.py
│           └── tools.py
├── payment_agent/          ← STAYS AT TOP LEVEL
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
└── ...
```

## Phase 1: Create Directory Structure and Move Agents

### 1.1 Create sub_agents directory
- Create `backend/app/orchestrator_agent/sub_agents/` directory
- Create `backend/app/orchestrator_agent/sub_agents/__init__.py`

### 1.2 Move agent directories
Move these directories from `backend/app/` to `backend/app/orchestrator_agent/sub_agents/`:
- `cart_agent/`
- `checkout_agent/`
- `customer_service_agent/`
- `product_discovery_agent/`

### 1.3 Update sub_agents/__init__.py
Create convenience exports for all sub-agents:
```python
"""Sub-agents for the shopping orchestrator."""
from .cart_agent import root_agent as cart_agent
from .checkout_agent import root_agent as checkout_agent
from .customer_service_agent import root_agent as customer_service_agent
from .product_discovery_agent import root_agent as product_discovery_agent

__all__ = [
    'cart_agent',
    'checkout_agent',
    'customer_service_agent',
    'product_discovery_agent',
]
```

## Phase 2: Update Orchestrator Agent

### 2.1 Update imports
**File**: `backend/app/orchestrator_agent/agent.py`

**Changes**:
- Remove: `from google.adk.tools import AgentTool`
- Update imports to use new paths:
  ```python
  from .sub_agents.cart_agent import root_agent as cart_agent
  from .sub_agents.checkout_agent import root_agent as checkout_agent
  from .sub_agents.customer_service_agent import root_agent as customer_service_agent
  from .sub_agents.product_discovery_agent import root_agent as product_discovery_agent
  ```
- Remove payment agent import (stays separate)

### 2.2 Update agent definition
**File**: `backend/app/orchestrator_agent/agent.py`

**Changes**:
- Remove `tools=[AgentTool(...), ...]` parameter
- Add `sub_agents=[cart_agent, checkout_agent, customer_service_agent, product_discovery_agent]` parameter
- **ADD (not replace)** instructions about LLM-driven delegation to sub-agents

**Important**: Keep all existing instructions. Add new text about hierarchical delegation at the beginning or end.

**New structure**:
```python
root_agent = LlmAgent(
    name="shopping_orchestrator",
    instruction="""You are the main shopping orchestrator for an e-commerce platform. Your role is to coordinate 
    between specialized agents to help users complete their shopping journey.
    
    ## Agent Hierarchy:
    You have access to specialized sub-agents through LLM-driven delegation:
    - Product Discovery Agent: Search for products using text queries
    - Cart Agent: Manage shopping cart (add, update, remove items)
    - Checkout Agent: Create orders from cart
    - Customer Service Agent: Handle inquiries, returns, and support
    
    You can delegate to these sub-agents naturally through conversation context, or use transfer_to_agent
    for explicit delegation when needed. All sub-agents share the same session state, so information
    flows seamlessly between them.
    
    Available agents:
    - Product Discovery Agent: Search for products using text queries
    - Cart Agent: Manage shopping cart (add, update, remove items)
    - Checkout Agent: Create orders from cart
    - Payment Agent: Process payments with AP2 compliance (separate agent, not a sub-agent)
    - Customer Service Agent: Handle inquiries, returns, and support
    
    ## Product Search Flow:
    When users search for products ("Find shoes", "Show me running shoes"):
    1. Use Product Discovery Agent to search
    2. The agent will show results and store them in state["current_results"]
    3. Present results clearly to the user
    
    ## Product Selection Flow:
    When users indicate they want to add an item ("add the blue shoes", "I want the white ones", "add the first one"):
    1. Access state["current_results"] to see available products
    2. Use reasoning to match the user's description to the correct product
       - "blue shoes" → find product with "blue" in name/description
       - "white ones" → find product with "white" in name/description  
       - "the first one" → use the first product in the list
       - "number 3" → use the third product (index 2)
    3. Extract the product_id from the matched product
    4. Call Cart Agent's add_to_cart tool with that product_id
    5. After adding to cart, automatically:
       a. Call Cart Agent's get_cart tool to show current cart contents
       b. Display the cart items clearly
       c. Prompt the user: "Your cart contains X items. Would you like to proceed to checkout?"
    
    ## Checkout Flow:
    When user confirms checkout (responds "yes", "checkout", "place order", "proceed", etc.):
    1. Use Checkout Agent's validate_cart_for_checkout tool first
    2. If cart is valid, call Checkout Agent's create_order tool
    3. The checkout agent will handle order creation and display order confirmation
    4. Congratulate the user on their successful order
    
    ## Other Operations:
    - "View cart", "Show my cart" → Use Cart Agent's get_cart tool
    - "Remove item", "Update quantity" → Use Cart Agent
    - "Checkout", "Place order" → Use Checkout Agent (validate first, then create order)
    - "Pay", "Process payment" → Use Payment Agent (not needed as orders are auto-completed)
    - "Return", "Refund", "Support" → Use Customer Service Agent
    
    Always maintain conversational flow and provide clear, helpful responses.
    """,
    description="Orchestrates shopping workflow by coordinating sub-agents",
    model=GEMINI_MODEL,
    sub_agents=[
        cart_agent,
        checkout_agent,
        customer_service_agent,
        product_discovery_agent,
    ],
)
```

## Phase 3: Update All Import Paths

### 3.1 Update test imports
**Files to update**:
- `backend/tests/unit/test_cart_tools.py`
- `backend/tests/unit/test_checkout_tools.py`
- `backend/tests/unit/test_customer_service_tools.py`
- `backend/tests/unit/test_product_discovery_tools.py`

**Changes**:
```python
# Old:
from app.cart_agent.tools import add_to_cart

# New:
from app.orchestrator_agent.sub_agents.cart_agent.tools import add_to_cart
```

### 3.2 Verify a2a_executor.py
**File**: `backend/app/a2a_executor.py`

**Status**: Should not need changes (imports orchestrator which hasn't changed location)

### 3.3 Check for other imports
Search for any other files importing from old paths:
- `from app.cart_agent`
- `from app.checkout_agent`
- `from app.customer_service_agent`
- `from app.product_discovery_agent`

## Phase 4: Verify Agent Hierarchy

### 4.1 Verify parent-child relationships
After refactoring, verify:
- Each sub-agent has `parent_agent == orchestrator`
- Orchestrator can find sub-agents via `find_agent(name)`
- Sub-agents can access parent via `parent_agent` attribute

### 4.2 Update documentation
- Update any documentation referencing old paths
- Document the new hierarchical structure

## Phase 5: Testing Checklist

- [ ] All imports resolve correctly
- [ ] Orchestrator can delegate to sub-agents
- [ ] Sub-agents can access shared session state
- [ ] Tests pass with new import paths
- [ ] Payment agent remains accessible separately
- [ ] A2A executor works with new structure

## Implementation Steps

1. **Create directory structure**
   - Create `orchestrator_agent/sub_agents/` directory
   - Create `sub_agents/__init__.py`

2. **Move agent directories**
   - Move 4 agent directories to `sub_agents/`

3. **Update orchestrator**
   - Update imports
   - Change from AgentTool to sub_agents
   - Update instructions

4. **Update test imports**
   - Update all test files to use new paths

5. **Verify and test**
   - Run tests
   - Verify imports work
   - Test agent delegation

## Files to Modify

### Create:
- `backend/app/orchestrator_agent/sub_agents/__init__.py`

### Modify:
- `backend/app/orchestrator_agent/agent.py`
- `backend/tests/unit/test_cart_tools.py`
- `backend/tests/unit/test_checkout_tools.py`
- `backend/tests/unit/test_customer_service_tools.py`
- `backend/tests/unit/test_product_discovery_tools.py`

### Move:
- `backend/app/cart_agent/` → `backend/app/orchestrator_agent/sub_agents/cart_agent/`
- `backend/app/checkout_agent/` → `backend/app/orchestrator_agent/sub_agents/checkout_agent/`
- `backend/app/customer_service_agent/` → `backend/app/orchestrator_agent/sub_agents/customer_service_agent/`
- `backend/app/product_discovery_agent/` → `backend/app/orchestrator_agent/sub_agents/product_discovery_agent/`

## Notes

- Payment agent stays at top level (`backend/app/payment_agent/`)
- Each sub-agent's `__init__.py` continues to export `root_agent`
- Session state is shared across the hierarchy automatically
- LLM-driven delegation allows orchestrator to route to sub-agents naturally
- `transfer_to_agent` can be used for explicit delegation if needed

