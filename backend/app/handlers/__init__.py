"""Route handlers for the application."""

from app.handlers.routes import root, healthz, agent_card_endpoint

__all__ = ["root", "healthz", "agent_card_endpoint"]
