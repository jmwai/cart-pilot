from __future__ import annotations
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional

from .tools import (
    create_order,
    get_order_status,
    cancel_order,
    validate_cart_for_checkout,
)

GEMINI_MODEL = "gemini-2.5-flash"


class OrderItem(BaseModel):
    product_id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    quantity: int = Field(description="Quantity")
    price: float = Field(description="Unit price")


class OrderOutput(BaseModel):
    order_id: str = Field(description="Order ID")
    status: str = Field(description="Order status")
    items: List[OrderItem] = Field(description="Order items")
    total_amount: float = Field(description="Total amount")
    shipping_address: Optional[str] = Field(
        description="Shipping address", default="")
    created_at: Optional[str] = Field(
        description="Order creation time", default="")
    message: Optional[str] = Field(description="Status message", default="")


root_agent = LlmAgent(
    name="checkout_agent",
    instruction="""You are a checkout assistant. Your role is to help users complete their purchases.
    You can create orders from carts, check order status, and cancel orders.
    
    ## Order Creation Flow:
    1. When user wants to checkout, first validate the cart using validate_cart_for_checkout
    2. If cart is valid, inform the user that you're retrieving their shipping address from their profile
    3. Call create_order (it will automatically get the shipping address from the user's profile)
    4. After order creation, clearly display:
       - Order ID (highlight this prominently)
       - Order status (completed)
       - All items with quantities and prices
       - Total amount
       - Shipping address (mention it's from their profile)
    5. Congratulate the user on their successful order
    
    ## Important Notes:
    - Shipping address is automatically retrieved from the user's profile (don't ask for it)
    - Orders are automatically marked as completed (payment is processed automatically)
    - Cart is automatically cleared after order creation
    - Always display order information clearly and congratulate the user
    
    Always confirm order details and provide clear, friendly status updates.
    """,
    description="Handles order creation from cart and order management",
    model=GEMINI_MODEL,
    tools=[
        create_order,
        get_order_status,
        cancel_order,
        validate_cart_for_checkout,
    ],
    output_schema=OrderOutput,
    output_key="order",
)
