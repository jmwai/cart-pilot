from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime

from app.common.db import get_conn, put_conn


def create_order(session_id: str, shipping_address: str) -> Dict[str, Any]:
    """
    Convert cart to order with AP2 cart mandate.

    Args:
        session_id: Session identifier
        shipping_address: Shipping address for the order

    Returns:
        Order details with status
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get cart items
        cur.execute(
            """SELECT ci.product_id, ci.quantity, c.name, c.picture
               FROM cart_items ci
               JOIN catalog_items c ON ci.product_id = c.id
               WHERE ci.session_id = %s""",
            (session_id,)
        )

        cart_items = cur.fetchall()

        if not cart_items:
            raise ValueError("Cart is empty")

        # Create order
        order_id = str(uuid.uuid4())
        total_amount = 0.0  # TODO: Calculate from product prices

        cur.execute(
            """INSERT INTO orders (order_id, session_id, total_amount, status, shipping_address, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (order_id, session_id, total_amount,
             "pending", shipping_address, datetime.now())
        )

        # Create order items
        items = []
        for row in cart_items:
            product_id, quantity, name, picture = row
            price = 0.0  # TODO: Get from product

            cur.execute(
                """INSERT INTO order_items (order_id, product_id, quantity, price)
                   VALUES (%s, %s, %s, %s)""",
                (order_id, product_id, quantity, price)
            )

            items.append({
                "product_id": product_id,
                "name": name,
                "quantity": quantity,
                "price": price,
            })

        # Clear cart
        cur.execute("DELETE FROM cart_items WHERE session_id = %s",
                    (session_id,))

        conn.commit()

        return {
            "order_id": order_id,
            "status": "pending",
            "items": items,
            "total_amount": total_amount,
            "shipping_address": shipping_address,
            "created_at": datetime.now().isoformat(),
            "message": "Order created successfully",
        }
    finally:
        put_conn(conn)


def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Get order details and status.

    Args:
        order_id: Order identifier

    Returns:
        Order details with status
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get order
        cur.execute(
            """SELECT order_id, status, total_amount, shipping_address, created_at
               FROM orders WHERE order_id = %s""",
            (order_id,)
        )

        order = cur.fetchone()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Get order items
        cur.execute(
            """SELECT oi.product_id, oi.quantity, oi.price, c.name
               FROM order_items oi
               JOIN catalog_items c ON oi.product_id = c.id
               WHERE oi.order_id = %s""",
            (order_id,)
        )

        items = []
        for row in cur.fetchall():
            items.append({
                "product_id": row[0],
                "name": row[3],
                "quantity": row[1],
                "price": row[2],
            })

        return {
            "order_id": order[0],
            "status": order[1],
            "items": items,
            "total_amount": float(order[2]),
            "shipping_address": order[3],
            "created_at": order[4].isoformat() if order[4] else "",
            "message": f"Order status: {order[1]}",
        }
    finally:
        put_conn(conn)


def cancel_order(order_id: str) -> Dict[str, Any]:
    """
    Cancel pending order.

    Args:
        order_id: Order identifier

    Returns:
        Status with refund amount
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get order
        cur.execute(
            "SELECT status, total_amount FROM orders WHERE order_id = %s", (order_id,))
        order = cur.fetchone()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order[0] not in ["pending", "processing"]:
            raise ValueError(f"Cannot cancel order with status: {order[0]}")

        # Update order status
        cur.execute(
            "UPDATE orders SET status = 'cancelled' WHERE order_id = %s",
            (order_id,)
        )
        conn.commit()

        return {
            "order_id": order_id,
            "status": "cancelled",
            "refund_amount": float(order[1]),
            "message": "Order cancelled successfully",
        }
    finally:
        put_conn(conn)


def validate_cart_for_checkout(session_id: str) -> Dict[str, Any]:
    """
    Check if cart is ready for checkout.

    Args:
        session_id: Session identifier

    Returns:
        Validation result with errors and warnings
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Check if cart has items
        cur.execute(
            "SELECT COUNT(*) FROM cart_items WHERE session_id = %s",
            (session_id,)
        )

        item_count = cur.fetchone()[0]

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
    finally:
        put_conn(conn)
