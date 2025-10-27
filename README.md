# Shopping Orchestrator - AI-Powered E-commerce Agent Platform

> **Note**: Update the badge URL in this README with your GitHub username and repository name.

Multi-agent AI system for e-commerce shopping assistance built with Google ADK and deployed on Cloud Run.

## Features

- 🤖 **AI Orchestrator** - Routes requests to specialized agents
- 🔍 **Product Discovery** - Semantic search with pgvector embeddings
- 🛒 **Cart Management** - Full cart CRUD operations
- 📦 **Checkout** - Order creation and management
- 💳 **Payment Processing** - AP2-compliant payment handling
- 🎧 **Customer Service** - Support inquiries and returns

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

## Documentation

- [API Documentation](backend/apidoc.md)
- [Architecture Plan](backend/agents.md)
- [Test Documentation](backend/tests/README.md)

## License

MIT

