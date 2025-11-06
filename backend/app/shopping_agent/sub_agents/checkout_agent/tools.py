from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
import random
from datetime import datetime
from sqlalchemy import func
from google.adk.tools import ToolContext

from app.common.db import get_db_session
from app.common.models import CartItem, Order, OrderItem, CatalogItem, Payment

# Sample shipping addresses for demo purposes
SAMPLE_ADDRESSES = [
    "123 Main Street, Apt 4B, New York, NY 10001",
    "456 Oak Avenue, Suite 200, Los Angeles, CA 90001",
    "789 Pine Road, Seattle, WA 98101",
    "321 Elm Street, Chicago, IL 60601",
]


def prepare_order_summary(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Prepare order summary with shipping address WITHOUT creating the order.
    This allows users to review order details before confirming.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Order summary with items, total, and shipping address
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    # Select shipping address (demo: randomly selected, pretending it's from user profile)
    # If pending_order_summary exists, reuse its shipping address for consistency
    pending_summary = tool_context.state.get("pending_order_summary")
    if pending_summary and isinstance(pending_summary, dict) and pending_summary is not None:
        shipping_address = pending_summary.get("shipping_address")
    else:
        shipping_address = random.choice(SAMPLE_ADDRESSES)

    with get_db_session() as db:
        # Get cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).all()

        if not cart_items:
            raise ValueError("Cart is empty")

        # Calculate total amount and format items (without creating order)
        total_amount = 0.0
        items = []
        for cart_item in cart_items:
            product = cart_item.product
            # Get price from product (price_usd_units is stored as dollars, not cents)
            price_usd_units = product.price_usd_units or 0
            price = float(price_usd_units)  # Already in dollars, use directly
            subtotal = price * cart_item.quantity
            total_amount += subtotal

            items.append({
                "product_id": cart_item.product_id,
                "name": product.name,
                "quantity": cart_item.quantity,
                "price": price,
                "picture": product.product_image_url or product.picture,
                "subtotal": subtotal,
            })

        # Store summary in state (NOT current_order - order doesn't exist yet)
        order_summary = {
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "item_count": len(items),
        }
        tool_context.state["pending_order_summary"] = order_summary

        return {
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "item_count": len(items),
            "message": "Order summary prepared. Please review and confirm.",
        }


def create_order(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Convert cart to order. Payment must be processed before order creation.
    Shipping address is retrieved from user profile (hardcoded for demo).

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Order details with status
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    # Check if payment has been processed
    payment_processed = tool_context.state.get("payment_processed", False)
    payment_data = tool_context.state.get("payment_data")

    if not payment_processed or not payment_data:
        raise ValueError(
            "Payment must be processed before creating order. Please complete payment first."
        )

    # Check for pending_order_summary - use its shipping address if available
    # This ensures the order matches what the user confirmed
    pending_summary = tool_context.state.get("pending_order_summary")
    if pending_summary and isinstance(pending_summary, dict) and pending_summary is not None:
        shipping_address = pending_summary.get("shipping_address")
        # Use shipping address from summary for consistency
    else:
        # Fallback: Select random shipping address (demo: pretending it's from user profile)
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
            # Get price from product (price_usd_units is stored as dollars, not cents)
            price_usd_units = product.price_usd_units or 0
            price = float(price_usd_units)  # Already in dollars, use directly
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
            status="completed",  # Payment already processed
            shipping_address=shipping_address
        )
        db.add(order)

        # Create Payment record now that we have order_id
        # Payment details were stored in state by process_payment()
        payment = Payment(
            payment_id=payment_data["payment_id"],
            order_id=order_id,
            amount=payment_data["amount"],
            payment_method=payment_data["payment_method"],
            payment_mandate_id=payment_data["payment_mandate_id"],
            transaction_id=payment_data["transaction_id"],
            status="completed"
        )
        db.add(payment)

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
            "payment_id": payment_data["payment_id"],
            "transaction_id": payment_data["transaction_id"],
        }
        tool_context.state["current_order"] = order_data
        tool_context.state["shipping_address"] = shipping_address

        # Clear pending_order_summary and payment data since order is now created
        # Use assignment to None instead of del (state may not support deletion)
        tool_context.state["pending_order_summary"] = None
        tool_context.state["payment_data"] = None
        tool_context.state["payment_processed"] = False

        return {
            "order_id": order_id,
            "status": "completed",
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "created_at": order_data["created_at"],
            "payment_id": payment_data["payment_id"],
            "transaction_id": payment_data["transaction_id"],
            "message": "Order created successfully",
        }


def get_order_status(tool_context: ToolContext, order_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get order details and status.

    If order_id is not provided, retrieves the order from session state["current_order"].
    If no order is found in state, raises an error.

    Args:
        tool_context: ADK tool context providing access to session
        order_id: Optional order identifier. If not provided, uses order from session state.

    Returns:
        Order details with status
    """
    # If order_id not provided, try to get from session state
    if not order_id:
        session_state = tool_context.state
        current_order = session_state.get("current_order")

        if current_order and isinstance(current_order, dict):
            order_id = current_order.get("order_id")

        if not order_id:
            raise ValueError(
                "No order ID provided and no order found in session. Please provide an order ID or place an order first.")

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
