from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime
from sqlalchemy import func

from app.common.db import get_db_session
from app.common.models import CartItem, CatalogItem


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

    with get_db_session() as db:
        # Get product details
        product = db.query(CatalogItem).filter(
            CatalogItem.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Create cart item
        cart_item = CartItem(
            cart_item_id=str(uuid.uuid4()),
            session_id=session_id,
            product_id=product_id,
            quantity=quantity
        )
        db.add(cart_item)
        # commit() happens automatically in context manager

        return {
            "cart_item_id": cart_item.cart_item_id,
            "product_id": product_id,
            "name": product.name,
            "picture": product.product_image_url or product.picture,
            "quantity": quantity,
            "added_at": cart_item.created_at.isoformat(),
        }


def get_cart(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve cart contents.

    Args:
        session_id: Session identifier

    Returns:
        List of cart items with details
    """
    with get_db_session() as db:
        # Query cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).order_by(CartItem.added_at.desc()).all()

        items = []
        for item in cart_items:
            # Load product data via relationship
            product = item.product
            items.append({
                "cart_item_id": item.cart_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "name": product.name,
                "picture": product.product_image_url or product.picture,
            })

        return items


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

    with get_db_session() as db:
        cart_item = db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id).first()
        if not cart_item:
            raise ValueError(f"Cart item {cart_item_id} not found")

        cart_item.quantity = quantity
        # commit() happens automatically in context manager

        return {
            "cart_item_id": cart_item_id,
            "quantity": quantity,
            "updated_at": datetime.now().isoformat(),
        }


def remove_from_cart(cart_item_id: str) -> Dict[str, Any]:
    """
    Remove item from cart.

    Args:
        cart_item_id: Cart item identifier

    Returns:
        Status message
    """
    with get_db_session() as db:
        cart_item = db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id).first()
        if not cart_item:
            raise ValueError(f"Cart item {cart_item_id} not found")

        db.delete(cart_item)
        # commit() happens automatically in context manager

        return {
            "status": "removed",
            "cart_item_id": cart_item_id,
        }


def clear_cart(session_id: str) -> Dict[str, Any]:
    """
    Empty entire cart.

    Args:
        session_id: Session identifier

    Returns:
        Status with items removed count
    """
    with get_db_session() as db:
        items_removed = db.query(CartItem).filter(
            CartItem.session_id == session_id).delete()
        # commit() happens automatically in context manager

        return {
            "status": "cleared",
            "items_removed": items_removed,
        }


def get_cart_total(session_id: str) -> Dict[str, Any]:
    """
    Calculate cart total.

    Args:
        session_id: Session identifier

    Returns:
        Cart totals and item count
    """
    with get_db_session() as db:
        # Get counts and sums using SQLAlchemy aggregation
        item_count = db.query(func.count(CartItem.cart_item_id)).filter(
            CartItem.session_id == session_id
        ).scalar() or 0

        total_items = db.query(func.sum(CartItem.quantity)).filter(
            CartItem.session_id == session_id
        ).scalar() or 0

        return {
            "item_count": item_count,
            "total_items": total_items,
            "subtotal": 0.0,  # TODO: Calculate from product prices
        }
