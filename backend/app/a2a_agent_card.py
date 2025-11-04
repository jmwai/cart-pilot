"""
Agent Card for Shopping Assistant - A2A Protocol

This module defines the agent card that describes the shopping assistant's
capabilities, skills, and configuration for A2A protocol clients.
"""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    TransportProtocol,
)


def create_shopping_agent_card() -> AgentCard:
    """
    Create the agent card for the Shopping Assistant.

    Returns:
        AgentCard: The configured agent card for A2A protocol
    """
    return AgentCard(
        name="Shopping Assistant",
        description="AI-powered shopping assistant that helps you discover products, manage your cart, and complete purchases",
        url="http://localhost:8080",
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
            stateTransitionHistory=False
        ),
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        preferredTransport=TransportProtocol.http_json,
        skills=[
            AgentSkill(
                id="discover_products",
                name="Product Discovery",
                description="Search and discover products using natural language queries and return structured product data",
                tags=["Search products", "Find items"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "Find me some running shoes",
                    "Show me blue t-shirts",
                    "What kitchen appliances do you have?"
                ]
            ),
            AgentSkill(
                id="manage_cart",
                name="Cart Management",
                description="Add items to cart, view cart contents, update quantities, and remove items",
                tags=["Shopping cart", "Add to cart"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "Add running shoes to my cart",
                    "Show me my cart",
                    "Remove item from cart",
                    "Clear my cart"
                ]
            ),
            AgentSkill(
                id="checkout",
                name="Checkout",
                description="Create orders from cart and manage order status",
                tags=["Place order", "Checkout"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "I want to checkout",
                    "Place my order",
                    "What's the status of my order?"
                ]
            ),
            AgentSkill(
                id="pay",
                name="Payment Processing",
                description="Process payments for orders with AP2 compliance",
                tags=["Pay", "Payment"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "I want to pay for my order",
                    "Process my payment"
                ]
            ),
            AgentSkill(
                id="customer_service",
                name="Customer Service",
                description="Handle returns, refunds, and customer inquiries",
                tags=["Returns", "Refunds", "Support"],
                inputModes=["text"],
                outputModes=["text"],
                examples=[
                    "I want to return an item",
                    "Get a refund for my order",
                    "How do I track my package?"
                ]
            )
        ]
    )
