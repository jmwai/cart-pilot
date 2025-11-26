"""Route handlers for custom endpoints."""

import logging
from starlette.responses import JSONResponse, RedirectResponse

from app.agent_card import create_shopping_agent_card
from app.common.db import health_check


async def root(request):
    """Redirect root endpoint to the message sending endpoint."""
    return RedirectResponse(url="/v1/message:send")


async def healthz(request):
    """Health check endpoint."""
    if not health_check():
        return JSONResponse(
            {"status": "error", "message": "Database is not healthy"},
            status_code=500
        )
    return JSONResponse({"status": "ok", "message": "Agents Gateway is healthy"})


async def agent_card_endpoint(request):
    """Returns the agent card describing the shopping assistant capabilities."""
    def get_base_url(request):
        """Extract base URL from request, handling Cloud Run proxy headers."""
        # Check for Cloud Run proxy headers first
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        forwarded_host = request.headers.get("x-forwarded-host", "")

        if forwarded_proto and forwarded_host:
            # Cloud Run provides these headers
            return f"{forwarded_proto}://{forwarded_host}"

        # Fallback to request URL
        scheme = request.url.scheme
        host = request.headers.get("host") or (
            request.url.hostname or "localhost:8080")
        # Include port if it's not standard (80 for http, 443 for https)
        if ":" not in host and request.url.port:
            port = request.url.port
            if (scheme == "http" and port != 80) or (scheme == "https" and port != 443):
                host = f"{host}:{port}"
        return f"{scheme}://{host}"

    try:
        # Extract base URL from request
        base_url = get_base_url(request)

        # Use A2A SDK agent card with dynamic URL
        card = create_shopping_agent_card(base_url=base_url)
        # Convert to dict format
        return JSONResponse(card.model_dump())
    except Exception as e:
        # Fallback to manual JSON if A2A SDK fails
        logging.warning(f"Failed to load A2A agent card: {e}")
        # Extract base URL from request for fallback too
        try:
            base_url = get_base_url(request)
        except:
            base_url = "http://localhost:8080"

        return JSONResponse({
            "name": "Shopping Assistant",
            "description": "AI-powered shopping assistant that helps you discover products, manage your cart, and complete purchases",
            "url": base_url,
            "version": "1.0.0",
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": False
            },
            "defaultInputModes": ["text", "text/plain"],
            "defaultOutputModes": ["text", "text/plain"],
            "preferredTransport": "HTTP_JSON",
            "skills": [
                {
                    "id": "discover_products",
                    "name": "Product Discovery",
                    "description": "Search and discover products using natural language queries",
                    "examples": ["Find me some running shoes", "Show me blue t-shirts"]
                },
                {
                    "id": "manage_cart",
                    "name": "Cart Management",
                    "description": "Add items to cart, view cart contents, update quantities, and remove items",
                    "examples": ["Add running shoes to my cart", "Show me my cart"]
                },
                {
                    "id": "checkout",
                    "name": "Checkout",
                    "description": "Create orders from cart and manage order status",
                    "examples": ["I want to checkout", "Place my order"]
                },
                {
                    "id": "pay",
                    "name": "Payment Processing",
                    "description": "Process payments for orders with AP2 compliance",
                    "examples": ["I want to pay for my order", "Process my payment"]
                },
                {
                    "id": "customer_service",
                    "name": "Customer Service",
                    "description": "Handle returns, refunds, and customer inquiries",
                    "examples": ["I want to return an item", "Get a refund for my order"]
                }
            ]
        })
