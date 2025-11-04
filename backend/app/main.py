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
import re

# Third-party imports
import vertexai

# A2A Protocol imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from app.a2a_agent_card import create_shopping_agent_card
from app.a2a_executor import ShoppingAgentExecutor

# Starlette imports
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.routing import Route

# Local imports
from app.common.config import get_settings
from app.handlers.routes import root, healthz, agent_card_endpoint
from app.handlers.products import get_products, get_product_by_id
from app.middleware.logging import LoggingMiddleware


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


# Add custom routes directly to the Starlette app
a2a_app.routes.append(Route("/", root, methods=["POST"]))
a2a_app.routes.append(Route("/healthz", healthz, methods=["GET"]))
a2a_app.routes.append(Route("/.well-known/agent-card.json",
                      agent_card_endpoint, methods=["GET"]))
# Product API routes
a2a_app.routes.append(Route("/api/products", get_products, methods=["GET"]))
# Use path parameter syntax for product ID
a2a_app.routes.append(
    Route("/api/products/{id}", get_product_by_id, methods=["GET"]))

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

# Add logging middleware
app = LoggingMiddleware(app)
