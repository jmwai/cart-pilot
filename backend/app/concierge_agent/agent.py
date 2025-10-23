from __future__ import annotations
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import AgentTool
from pydantic import BaseModel, Field
from typing import List, Optional

from .tools import text_vector_search

GEMINI_MODEL = "gemini-2.5-flash"

# product_discovery_agent = LlmAgent(
#     name="product_discovery_agent",
#     instructions="""You are a shopping assistant.
#     You are tasked with helping the user find products.
#     """,
#     description="Responds to natural language queries about products by using text-based vector search.",
#     model=GEMINI_MODEL,
#     tools=[text_vector_search],
# )

root_agent = LlmAgent(
    name="shopping_assistant",
    instruction="""You are a shopping assistant tasked with helping users find products.
    When users ask about products, use the text_vector_search tool to search for products based on text queries.
    """,
    description="Acts as the main router for the online boutique. It classifies the user's intent and delegates the request to the appropriate specialist agent.",
    model=GEMINI_MODEL,
    tools=[text_vector_search],
)
