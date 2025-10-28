"""
FastAPI application for agents-gateway.

Conforms to ADK guidance: clear API surface, structured JSON, and minimal
agent/tool coupling at the HTTP layer. Endpoints are stubbed for Phase 1 and
will be wired to ADK Agents and FunctionTools incrementally.

Now includes A2A protocol support for agent-to-agent communication.
"""
from __future__ import annotations

import logging
import os
import uuid

# Third-party imports
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import vertexai
from vertexai import agent_engines
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService

# A2A Protocol imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import DatabaseTaskStore, InMemoryTaskStore
from a2a.types import TransportProtocol
from app.a2a_agent_card import create_shopping_agent_card
from app.a2a_executor import ShoppingAgentExecutor

# Starlette imports
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse, RedirectResponse


# Local imports
from app.common.config import get_settings
from app.common.db import health_check
from app.common.utils import get_or_create_agent_engine


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

try:
    settings = get_settings()
    print("Settings loaded successfully")
except Exception as e:
    print(f"ERROR: Failed to load settings: {e}")
    raise

# Vertex AI initialization
try:
    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.PROJECT_ID
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.REGION
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
    vertexai.init(project=settings.PROJECT_ID, location=settings.REGION)
    print("Vertex AI initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize Vertex AI: {e}")
    raise

# AGENT_ENGINE_DISPLAY_NAME = "concierge-agent"
# try:
#     agent_engine = get_or_create_agent_engine(AGENT_ENGINE_DISPLAY_NAME)
#     print(f"Agent engine ready: {agent_engine.resource_name}")
# except Exception as e:
#     print(f"ERROR: Failed to create/get agent engine: {e}")
#     raise

# agent_engine_id = agent_engine.resource_name


# SESSION_SERVICE_URI = f"agentengine://{agent_engine_id}"
# MEMORY_BANK_SERVICE_URI = f"agentengine://{agent_engine_id}"

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_SERVICE_URI = f"sqlite:///./session.db"
# MEMORY_BANK_SERVICE_URI = f"sqlite:///./memory_bank.db"
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
SERVE_WEB_INTERFACE = False

# Initialize A2A Protocol as primary application
# Create agent card
agent_card = create_shopping_agent_card()

# Create executor
executor = ShoppingAgentExecutor()

# Create task store
task_store = InMemoryTaskStore()

# Create request handler
request_handler = DefaultRequestHandler(executor, task_store)

# Create A2A Starlette application (supports JSON-RPC 2.0)
a2a_starlette_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler
)

# Build the Starlette app from A2A application
# A2AStarletteApplication has a .build() method that returns a Starlette app
a2a_app = a2a_starlette_app.build()

print("A2A Protocol application created successfully")


# Custom route handlers
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
    try:
        # Use A2A SDK agent card
        card = create_shopping_agent_card()
        # Convert to dict format
        return JSONResponse(card.model_dump())
    except Exception as e:
        # Fallback to manual JSON if A2A SDK fails
        logging.warning(f"Failed to load A2A agent card: {e}")
        return JSONResponse({
            "name": "Shopping Assistant",
            "description": "AI-powered shopping assistant that helps you discover products, manage your cart, and complete purchases",
            "url": "http://localhost:8080/",
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


# Add custom routes directly to the Starlette app
a2a_app.routes.append(Route("/", root, methods=["POST"]))
a2a_app.routes.append(Route("/healthz", healthz, methods=["GET"]))
a2a_app.routes.append(Route("/.well-known/agent-card.json",
                      agent_card_endpoint, methods=["GET"]))

# Use the built Starlette app
app = a2a_app

# Wrap with CORS middleware
app = StarletteCORSMiddleware(
    app,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom logging middleware for Starlette
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        import time
        start_time = time.time()

        if scope['type'] == 'http':
            print(f"Request: {scope.get('method')} {scope.get('path')}")

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                process_time = time.time() - start_time
                print(f"Response: {message['status']} in {process_time:.2f}s")
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Add logging middleware
app = LoggingMiddleware(app)
