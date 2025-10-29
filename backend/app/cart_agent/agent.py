from __future__ import annotations
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional

from .tools import (
    add_to_cart,
    get_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    get_cart_total,
)

GEMINI_MODEL = "gemini-2.5-flash"


class CartItem(BaseModel):
    cart_item_id: str = Field(description="Cart item ID")
    product_id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    picture: Optional[str] = Field(description="Product image URL", default="")
    quantity: int = Field(description="Quantity")
    price: float = Field(description="Unit price")
    subtotal: float = Field(description="Item subtotal")


class CartOutput(BaseModel):
    items: List[CartItem] = Field(description="Cart items")
    total_items: int = Field(description="Total number of items")
    subtotal: float = Field(description="Cart subtotal")
    message: Optional[str] = Field(description="Status message", default="")


root_agent = LlmAgent(
    name="cart_agent",
    instruction="""You are a shopping cart management assistant. Your role is to help users manage their shopping cart.
    You can add items to the cart, view cart contents, update quantities, remove items, and clear the cart.
    Always confirm actions clearly and show cart totals when appropriate.
    
    IMPORTANT: When showing cart contents, always include:
    - Product images (from picture field)
    - Product names
    - Quantities
    - Prices and subtotals
    - Use clear formatting to make cart easy to scan
    
    The get_cart tool returns all cart items with images, prices, and quantities automatically.
    """,
    description="Manages shopping cart operations including adding, updating, and removing items",
    model=GEMINI_MODEL,
    tools=[
        add_to_cart,
        get_cart,
        update_cart_item,
        remove_from_cart,
        clear_cart,
        get_cart_total,
    ],
    output_schema=CartOutput,
    output_key="cart",
)
