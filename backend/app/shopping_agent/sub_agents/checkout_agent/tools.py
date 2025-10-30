from __future__ import annotations
from typing import Any, Dict, List
import uuid
import random
from datetime import datetime
from sqlalchemy import func
from google.adk.tools import ToolContext

from app.common.db import get_db_session
from app.common.models import CartItem, Order, OrderItem, CatalogItem

# Sample shipping addresses for demo purposes
SAMPLE_ADDRESSES = [
    "123 Main Street, Apt 4B, New York, NY 10001",
    "456 Oak Avenue, Suite 200, Los Angeles, CA 90001",
    "789 Pine Road, Seattle, WA 98101",
    "321 Elm Street, Chicago, IL 60601",
]


def create_order(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Convert cart to order with AP2 cart mandate.
    Shipping address is retrieved from user profile (hardcoded for demo).

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Order details with status
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    # Select random shipping address (demo: pretending it's from user profile)
    shipping_address = random.choice(SAMPLE_ADDRESSES)

    with get_db_session() as db:
        # Get cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).all()

        if not cart_items:
            raise ValueError("Cart is empty")

        # Create order
        order_id = str(uuid.uuid4())
        total_amount = 0.0

        # Calculate total amount and create order items
        items = []
        for cart_item in cart_items:
            product = cart_item.product
            # Get price from product (price_usd_units is in cents)
            price_usd_units = product.price_usd_units or 0
            price = float(price_usd_units) / 100.0
            subtotal = price * cart_item.quantity
            total_amount += subtotal

            order_item = OrderItem(
                order_id=order_id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=price
            )
            db.add(order_item)

            items.append({
                "product_id": cart_item.product_id,
                "name": product.name,
                "quantity": cart_item.quantity,
                "price": price,
                "picture": product.product_image_url or product.picture,
                "subtotal": subtotal,
            })

        order = Order(
            order_id=order_id,
            session_id=session_id,
            total_amount=total_amount,
            status="completed",  # Mark as completed since payment is skipped
            shipping_address=shipping_address
        )
        db.add(order)

        # Clear cart
        db.query(CartItem).filter(CartItem.session_id == session_id).delete()
        # commit() happens automatically in context manager

        # Store order in session state
        order_data = {
            "order_id": order_id,
            "status": "completed",
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "created_at": order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
        }
        tool_context.state["current_order"] = order_data
        tool_context.state["shipping_address"] = shipping_address

        return {
            "order_id": order_id,
            "status": "completed",
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "created_at": order_data["created_at"],
            "message": "Order created successfully",
        }


def get_order_status(tool_context: ToolContext, order_id: str) -> Dict[str, Any]:
    """
    Get order details and status.

    Args:
        tool_context: ADK tool context providing access to session
        order_id: Order identifier

    Returns:
        Order details with status
    """
    with get_db_session() as db:
        # Get order with items relationship
        order = db.query(Order).filter(Order.order_id == order_id).first()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Get order items via relationship
        items = []
        for order_item in order.items:
            product = order_item.product
            items.append({
                "product_id": order_item.product_id,
                "name": product.name,
                "quantity": order_item.quantity,
                "price": order_item.price,
                "picture": product.product_image_url or product.picture,
                "subtotal": order_item.price * order_item.quantity,
            })

        order_data = {
            "order_id": order.order_id,
            "status": order.status,
            "items": items,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at.isoformat() if order.created_at else "",
            "message": f"Order status: {order.status}",
        }

        # Store in session state
        tool_context.state["current_order"] = order_data

        return order_data


def cancel_order(tool_context: ToolContext, order_id: str) -> Dict[str, Any]:
    """
    Cancel pending order.

    Args:
        tool_context: ADK tool context providing access to session
        order_id: Order identifier

    Returns:
        Status with refund amount
    """
    with get_db_session() as db:
        order = db.query(Order).filter(Order.order_id == order_id).first()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status not in ["pending", "processing"]:
            raise ValueError(
                f"Cannot cancel order with status: {order.status}")

        # Update order status
        order.status = "cancelled"
        # commit() happens automatically in context manager

        return {
            "order_id": order_id,
            "status": "cancelled",
            "refund_amount": order.total_amount,
            "message": "Order cancelled successfully",
        }


def validate_cart_for_checkout(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Check if cart is ready for checkout.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Validation result with errors and warnings
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        # Check if cart has items
        item_count = db.query(func.count(CartItem.cart_item_id)).filter(
            CartItem.session_id == session_id
        ).scalar() or 0

        errors = []
        warnings = []

        if item_count == 0:
            errors.append("Cart is empty")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "item_count": item_count,
        }
