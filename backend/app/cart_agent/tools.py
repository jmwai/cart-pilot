from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime

from app.common.db import get_conn, put_conn


def add_to_cart(product_id: str, quantity: int, session_id: str) -> Dict[str, Any]:
    """
    Add product to cart with AP2 intent mandate support.

    Args:
        product_id: Unique identifier for the product
        quantity: Number of items to add (must be > 0)
        session_id: Session identifier

    Returns:
        Dict containing cart item details
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    # Get product details first
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, picture, product_image_url FROM catalog_items WHERE id = %s",
            (product_id,)
        )
        product = cur.fetchone()

        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Insert cart item
        cart_item_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO cart_items (cart_item_id, session_id, product_id, quantity, added_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (cart_item_id, session_id, product_id, quantity, datetime.now())
        )
        conn.commit()

        return {
            "cart_item_id": cart_item_id,
            "product_id": product_id,
            "name": product[1],
            "picture": product[3] or product[2],
            "quantity": quantity,
            "added_at": datetime.now().isoformat(),
        }
    finally:
        put_conn(conn)


def get_cart(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve cart contents.

    Args:
        session_id: Session identifier

    Returns:
        List of cart items with details
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT ci.cart_item_id, ci.product_id, ci.quantity, 
                      c.name, c.picture, c.product_image_url
               FROM cart_items ci
               JOIN catalog_items c ON ci.product_id = c.id
               WHERE ci.session_id = %s
               ORDER BY ci.added_at DESC""",
            (session_id,)
        )

        items = []
        for row in cur.fetchall():
            items.append({
                "cart_item_id": row[0],
                "product_id": row[1],
                "quantity": row[2],
                "name": row[3],
                "picture": row[5] or row[4],
            })

        return items
    finally:
        put_conn(conn)


def update_cart_item(cart_item_id: str, quantity: int) -> Dict[str, Any]:
    """
    Update item quantity in cart.

    Args:
        cart_item_id: Cart item identifier
        quantity: New quantity (must be > 0)

    Returns:
        Updated cart item details
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
            (quantity, cart_item_id)
        )
        conn.commit()

        if cur.rowcount == 0:
            raise ValueError(f"Cart item {cart_item_id} not found")

        return {
            "cart_item_id": cart_item_id,
            "quantity": quantity,
            "updated_at": datetime.now().isoformat(),
        }
    finally:
        put_conn(conn)


def remove_from_cart(cart_item_id: str) -> Dict[str, Any]:
    """
    Remove item from cart.

    Args:
        cart_item_id: Cart item identifier

    Returns:
        Status message
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM cart_items WHERE cart_item_id = %s", (cart_item_id,))
        conn.commit()

        if cur.rowcount == 0:
            raise ValueError(f"Cart item {cart_item_id} not found")

        return {
            "status": "removed",
            "cart_item_id": cart_item_id,
        }
    finally:
        put_conn(conn)


def clear_cart(session_id: str) -> Dict[str, Any]:
    """
    Empty entire cart.

    Args:
        session_id: Session identifier

    Returns:
        Status with items removed count
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_items WHERE session_id = %s",
                    (session_id,))
        conn.commit()

        return {
            "status": "cleared",
            "items_removed": cur.rowcount,
        }
    finally:
        put_conn(conn)


def get_cart_total(session_id: str) -> Dict[str, Any]:
    """
    Calculate cart total.

    Args:
        session_id: Session identifier

    Returns:
        Cart totals and item count
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT COUNT(*), SUM(ci.quantity)
               FROM cart_items ci
               WHERE ci.session_id = %s""",
            (session_id,)
        )

        result = cur.fetchone()
        item_count = result[0] or 0
        total_items = result[1] or 0

        return {
            "item_count": item_count,
            "total_items": total_items,
            "subtotal": 0.0,  # TODO: Calculate from product prices
        }
    finally:
        put_conn(conn)
