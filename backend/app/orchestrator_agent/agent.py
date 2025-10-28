from __future__ import annotations
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

# Import all specialized agents
from app.product_discovery_agent import root_agent as product_discovery_agent
from app.cart_agent import root_agent as cart_agent
from app.checkout_agent import root_agent as checkout_agent
from app.payment_agent import root_agent as payment_agent
from app.customer_service_agent import root_agent as customer_service_agent

GEMINI_MODEL = "gemini-2.5-flash"


root_agent = LlmAgent(
    name="shopping_orchestrator",
    instruction="""You are the main shopping orchestrator for an e-commerce platform. Your role is to coordinate 
    between specialized agents to help users complete their shopping journey.
    
    Available agents:
    - Product Discovery Agent: Search for products using text queries
    - Cart Agent: Manage shopping cart (add, update, remove items)
    - Checkout Agent: Create orders from cart
    - Payment Agent: Process payments with AP2 compliance
    - Customer Service Agent: Handle inquiries, returns, and support
    
    Route user requests to the appropriate agent based on their intent:
    - "Find products", "Search for" → Product Discovery Agent
    - "Add to cart", "Remove from cart", "View cart" → Cart Agent
    - "Checkout", "Place order" → Checkout Agent
    - "Pay", "Process payment" → Payment Agent
    - "Return", "Refund", "Support", "Help" → Customer Service Agent
    
    Always provide clear responses and guide users through their shopping journey.
    You return structured data as received.
    """,
    description="Orchestrates shopping workflow by routing to specialized agents, You return structured data as received.",
    model=GEMINI_MODEL,
    tools=[
        AgentTool(product_discovery_agent),
        AgentTool(cart_agent),
        AgentTool(checkout_agent),
        AgentTool(payment_agent),
        AgentTool(customer_service_agent),
    ],
)
