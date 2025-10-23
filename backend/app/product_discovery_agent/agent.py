from __future__ import annotations
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import AgentTool
from pydantic import BaseModel, Field
from typing import List, Optional

from .tools import text_vector_search

GEMINI_MODEL = "gemini-2.5-flash"


class ProductResult(BaseModel):
    id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    description: Optional[str] = Field(
        description="Product description", default="")
    picture: Optional[str] = Field(description="Product image URL", default="")
    distance: Optional[float] = Field(
        description="Search relevance score", default=0.0)


class ProductSearchOutput(BaseModel):
    products: List[ProductResult] = Field(description="List of found products")
    summary: Optional[str] = Field(
        description="Brief summary of search results", default="")


root_agent = LlmAgent(
    name="product_discovery_agent",
    instruction="""You are a product discovery assistant. Your role is to help users find products using semantic search.
    When users ask about products, use the text_vector_search tool to search for products based on text queries.
    Present search results clearly and help users understand what products are available.
    """,
    description="Handles product discovery through text and image search",
    model=GEMINI_MODEL,
    tools=[text_vector_search],
    output_schema=ProductSearchOutput,
    output_key="search_results",
)
