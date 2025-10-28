"""
FastAPI application for agents-gateway.

Conforms to ADK guidance: clear API surface, structured JSON, and minimal
agent/tool coupling at the HTTP layer. Endpoints are stubbed for Phase 1 and
will be wired to ADK Agents and FunctionTools incrementally.
"""
from __future__ import annotations

import logging
import os
import uuid

# Third-party imports
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
import vertexai
from vertexai import agent_engines
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService


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

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    # memory_service_uri=MEMORY_BANK_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
    trace_to_cloud=False,
)

print("ADK FastAPI app created successfully")


@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start_time = time.time()
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Response: {response.status_code} in {process_time:.2f}s")
    return response


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    # run a health check on the database
    if not health_check():
        raise HTTPException(status_code=500, detail="Database is not healthy")
    return {"status": "ok", "message": "Agents Gateway is healthy"}


@app.get("/.well-known/agent-card.json")
def agent_card() -> Dict[str, Any]:
    """
    Returns the agent card describing the shopping assistant capabilities.
    This is used by A2A clients to discover agent capabilities.
    """
    return {
        "name": "Shopping Assistant",
        "description": "AI-powered shopping assistant that helps you discover products, manage your cart, and complete purchases",
        "url": "http://localhost:8080/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False
        },
        "defaultInputModes": [
            "text",
            "text/plain"
        ],
        "defaultOutputModes": [
            "text",
            "text/plain"
        ],
        "skills": [
            {
                "id": "discover_products",
                "name": "Product Discovery",
                "description": "Search and discover products using natural language queries",
                "tags": [
                    "Search products",
                    "Find items"
                ],
                "examples": [
                    "Find me some running shoes",
                    "Show me blue t-shirts",
                    "What kitchen appliances do you have?"
                ]
            },
            {
                "id": "manage_cart",
                "name": "Cart Management",
                "description": "Add items to cart, view cart contents, update quantities, and remove items",
                "tags": [
                    "Shopping cart",
                    "Add to cart"
                ],
                "examples": [
                    "Add running shoes to my cart",
                    "Show me my cart",
                    "Remove item from cart",
                    "Clear my cart"
                ]
            },
            {
                "id": "checkout",
                "name": "Checkout",
                "description": "Create orders from cart and manage order status",
                "tags": [
                    "Place order",
                    "Checkout"
                ],
                "examples": [
                    "I want to checkout",
                    "Place my order",
                    "What's the status of my order?"
                ]
            },
            {
                "id": "pay",
                "name": "Payment Processing",
                "description": "Process payments for orders with AP2 compliance",
                "tags": [
                    "Pay",
                    "Payment"
                ],
                "examples": [
                    "I want to pay for my order",
                    "Process my payment"
                ]
            },
            {
                "id": "customer_service",
                "name": "Customer Service",
                "description": "Handle returns, refunds, and customer inquiries",
                "tags": [
                    "Returns",
                    "Refunds",
                    "Support"
                ],
                "examples": [
                    "I want to return an item",
                    "Get a refund for my order",
                    "How do I track my package?"
                ]
            }
        ]
    }
