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
    product_image_url: Optional[str] = Field(
        description="Primary product image URL", default="")
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
    
    IMPORTANT: When presenting search results, always include:
    - Product images (use product_image_url or picture field - these are stored in the search results)
    - Product names with distinguishing features (color, size, style) to help users differentiate
    - Product prices if available (from price_usd_units field)
    - Product IDs for reference
    
    The search tool automatically stores results in state, so you can reference them later for product selection.
    """,
    description="Handles product discovery through text and image search",
    model=GEMINI_MODEL,
    tools=[text_vector_search],
    output_schema=ProductSearchOutput,
    output_key="search_results",
)
