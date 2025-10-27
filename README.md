# Shopping Orchestrator - AI-Powered E-commerce Agent Platform

> **Note**: Update the badge URL in this README with your GitHub username and repository name.

Multi-agent AI system for e-commerce shopping assistance built with Google ADK and deployed on Cloud Run.

## 🎯 Agent-Driven Architecture

This platform follows an **agent-driven architecture** where users interact naturally through conversation. The AI chat assistant orchestrates all shopping operations including product discovery, cart management, checkout, payments, and customer support.

## Features

### Backend (Agent Orchestration)
- 🤖 **AI Orchestrator** - Routes requests to specialized agents
- 🔍 **Product Discovery Agent** - Semantic search with pgvector embeddings
- 🛒 **Cart Agent** - Full cart CRUD operations with AP2 intent mandates
- 📦 **Checkout Agent** - Order creation and management with AP2 cart mandates
- 💳 **Payment Agent** - AP2-compliant payment handling with cryptographic mandates
- 🎧 **Customer Service Agent** - Support inquiries, returns, and refunds

### Frontend (Visual Catalog + Chat Interface)
- 🏠 **Product Listing** - Browse featured products in a clean grid layout
- 📦 **Product Details** - Detailed product views with images and specs
- 💬 **AI Chat Assistant** - Floating chatbox for agent-driven shopping
- 🎨 **Modern UI** - Clean, minimalist design
- 📱 **Responsive Design** - Works on all devices

## Tech Stack

- **Backend**: FastAPI, Google ADK, SQLAlchemy 2.0
- **AI**: Gemini 2.5 Flash, Vertex AI
- **Database**: PostgreSQL with pgvector
- **Testing**: pytest, 92+ unit tests
- **Deployment**: Cloud Run ready

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
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
│   ├── common/          # Shared utilities and models
│   ├── cart_agent/      # Cart management
│   ├── checkout_agent/  # Order processing
│   ├── payment_agent/   # Payment processing
│   ├── customer_service_agent/  # Support
│   └── product_discovery_agent/  # Product search
├── tests/               # Test suite (92 tests)
└── migrations/          # Alembic migrations
```

## How It Works

### Complete Shopping Journey via Agent

1. **Product Discovery**: "Find me running shoes" → Agent searches and returns products
2. **Add to Cart**: "Add Air Jordan 1 to my cart" → Agent creates cart item
3. **View Cart**: "Show me my cart" → Agent displays cart contents
4. **Checkout**: "Checkout with 123 Main St" → Agent creates order
5. **Payment**: "Pay with credit card" → Agent processes payment
6. **Support**: "Return order ORD-123" → Agent initiates return

All operations happen through natural conversation with the AI agent!

## Documentation

- [Frontend README](frontend/README.md) - Frontend implementation guide
- [Agent-Driven Architecture](AGENT_DRIVEN_ARCHITECTURE.md) - How agent-driven shopping works
- [API Documentation](backend/apidoc.md) - Backend API reference
- [Architecture Plan](backend/agents.md) - Agent system design
- [Test Documentation](backend/tests/README.md) - Testing guide
- [Frontend Implementation Summary](FRONTEND_IMPLEMENTATION_SUMMARY.md) - Frontend implementation details

## License

MIT

