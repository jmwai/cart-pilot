from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime
from sqlalchemy import func

from app.common.db import get_db_session
from app.common.models import CartItem, Order, OrderItem, CatalogItem


def create_order(session_id: str, shipping_address: str) -> Dict[str, Any]:
    """
    Convert cart to order with AP2 cart mandate.

    Args:
        session_id: Session identifier
        shipping_address: Shipping address for the order

    Returns:
        Order details with status
    """
    with get_db_session() as db:
        # Get cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).all()

        if not cart_items:
            raise ValueError("Cart is empty")

        # Create order
        order_id = str(uuid.uuid4())
        total_amount = 0.0  # TODO: Calculate from product prices

        order = Order(
            order_id=order_id,
            session_id=session_id,
            total_amount=total_amount,
            status="pending",
            shipping_address=shipping_address
        )
        db.add(order)

        # Create order items
        items = []
        for cart_item in cart_items:
            product = cart_item.product
            price = 0.0  # TODO: Get from product

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
            })

        # Clear cart
        db.query(CartItem).filter(CartItem.session_id == session_id).delete()
        # commit() happens automatically in context manager

        return {
            "order_id": order_id,
            "status": "pending",
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "created_at": order.created_at.isoformat(),
            "message": "Order created successfully",
        }


def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Get order details and status.

    Args:
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
            })

        return {
            "order_id": order.order_id,
            "status": order.status,
            "items": items,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at.isoformat() if order.created_at else "",
            "message": f"Order status: {order.status}",
        }


def cancel_order(order_id: str) -> Dict[str, Any]:
    """
    Cancel pending order.

    Args:
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


def validate_cart_for_checkout(session_id: str) -> Dict[str, Any]:
    """
    Check if cart is ready for checkout.

    Args:
        session_id: Session identifier

    Returns:
        Validation result with errors and warnings
    """
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
