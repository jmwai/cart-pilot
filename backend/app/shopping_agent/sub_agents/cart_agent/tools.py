from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
from sqlalchemy import func
from google.adk.tools import ToolContext

from app.common.db import get_db_session
from app.common.models import CartItem, CatalogItem


def find_product_in_results(tool_context: ToolContext, description: str) -> Dict[str, Any]:
    """
    Helper function to find a product from current search results by matching description.

    Args:
        tool_context: ADK tool context providing access to state
        description: Product description to match (e.g., "blue shoes", "the first one", "number 3")

    Returns:
        Dict with product details including product_id

    Raises:
        ValueError: If no search results found or product not matched
    """
    # Access state["current_results"]
    current_results = tool_context.state.get("current_results", [])

    # Debug: Log state keys and session info to help diagnose issues
    state_keys = list(tool_context.state.keys()) if hasattr(
        tool_context.state, 'keys') else []
    session_id = None
    try:
        session_id = tool_context._invocation_context.session.id if hasattr(
            tool_context._invocation_context, 'session') else 'unknown'
    except Exception:
        session_id = 'unknown'

    if not current_results:
        # Provide more helpful error message with debugging info
        available_keys = ', '.join(state_keys) if state_keys else 'none'
        raise ValueError(
            f"No search results found in state for session {session_id}. "
            f"Available state keys: {available_keys}. "
            f"Please search for products first.")

    # Match description to product
    description_lower = description.lower().strip()

    # Handle positional references
    if description_lower in ["first", "first one", "number 1", "1", "one", "the first", "the first one"]:
        if len(current_results) > 0:
            return current_results[0]
        else:
            raise ValueError("No products found in search results.")

    if description_lower in ["second", "second one", "number 2", "2", "two", "the second", "the second one"]:
        if len(current_results) > 1:
            return current_results[1]
        else:
            raise ValueError(
                "Not enough products in search results. Only 1 product found.")

    if description_lower in ["third", "third one", "number 3", "3", "three", "the third", "the third one"]:
        if len(current_results) > 2:
            return current_results[2]
        else:
            raise ValueError(
                "Not enough products in search results. Only found products.")

    # Match by keywords in name/description
    matched_products = []
    for result in current_results:
        name = (result.get("name", "") or "").lower()
        desc = (result.get("description", "") or "").lower()
        # Check if all keywords in description match
        keywords = [kw.strip()
                    for kw in description_lower.split() if kw.strip()]
        if all(keyword in name or keyword in desc for keyword in keywords):
            matched_products.append(result)

    if not matched_products:
        # Provide helpful error message
        available_names = [r.get("name", "Unknown")
                           for r in current_results[:5]]
        raise ValueError(
            f"Could not find product matching '{description}' in search results. "
            f"Available products: {', '.join(available_names)}"
        )

    # Return first match (most relevant)
    return matched_products[0]


def add_to_cart(
    tool_context: ToolContext,
    product_description: str,
    quantity: int = 1
) -> Dict[str, Any]:
    """
    Add product to cart with AP2 intent mandate support.

    Matches product_description against state["current_results"] to find the product.
    Product must be in session state from a previous search.

    Args:
        tool_context: ADK tool context providing access to session and state
        product_description: Product description to match from search results (e.g., "blue shoes", "first one")
        quantity: Number of items to add (must be > 0, default: 1)

    Returns:
        Dict containing cart item details with cart_item_id, product_id, name, picture, quantity
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    if not product_description or not product_description.strip():
        raise ValueError("product_description cannot be empty")

    product_description = product_description.strip()

    # Get product from session state (search results)
    product_match = find_product_in_results(tool_context, product_description)
    product_id = product_match["id"]

    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        # Get product details from database
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

        # Update session state with current cart to ensure executor can detect changes
        # Query all cart items for this session to update state
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).order_by(CartItem.added_at.desc()).all()

        items = []
        for item in cart_items:
            # Load product data via relationship
            product = item.product
            price = product.price_usd_units or 0.0
            cart_item_data = {
                "cart_item_id": item.cart_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "name": product.name,
                "picture": product.product_image_url or product.picture,
                "price": price,
                "subtotal": price * item.quantity,
            }
            items.append(cart_item_data)

        # Store cart items in state for executor access
        tool_context.state["cart"] = items

        return {
            "cart_item_id": cart_item.cart_item_id,
            "product_id": product_id,
            "name": product.name,
            "picture": product.product_image_url or product.picture,
            "quantity": quantity,
        }


def get_cart(tool_context: ToolContext) -> List[Dict[str, Any]]:
    """
    Retrieve cart contents.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        List of cart items with details
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        # Query cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).order_by(CartItem.added_at.desc()).all()

        items = []
        for item in cart_items:
            # Load product data via relationship
            product = item.product
            price = product.price_usd_units or 0.0
            cart_item_data = {
                "cart_item_id": item.cart_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "name": product.name,
                "picture": product.product_image_url or product.picture,
                "price": price,
                "subtotal": price * item.quantity,
            }
            items.append(cart_item_data)

        # Store cart items in state for executor access
        tool_context.state["cart"] = items

        return items


def update_cart_item(tool_context: ToolContext, cart_item_id: str, quantity: int) -> Dict[str, Any]:
    """
    Update item quantity in cart.

    Args:
        tool_context: ADK tool context providing access to session
        cart_item_id: Cart item identifier
        quantity: New quantity (must be > 0)

    Returns:
        Updated cart item details
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        cart_item = db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id).first()
        if not cart_item:
            raise ValueError(f"Cart item {cart_item_id} not found")

        cart_item.quantity = quantity
        # commit() happens automatically in context manager

        # Update session state with current cart to ensure executor can detect changes
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).order_by(CartItem.added_at.desc()).all()

        items = []
        for item in cart_items:
            # Load product data via relationship
            product = item.product
            price = product.price_usd_units or 0.0
            cart_item_data = {
                "cart_item_id": item.cart_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "name": product.name,
                "picture": product.product_image_url or product.picture,
                "price": price,
                "subtotal": price * item.quantity,
            }
            items.append(cart_item_data)

        # Store cart items in state for executor access
        tool_context.state["cart"] = items

        return {
            "cart_item_id": cart_item_id,
            "quantity": quantity,
            "updated_at": datetime.now().isoformat(),
        }


def remove_from_cart(tool_context: ToolContext, cart_item_id: str) -> Dict[str, Any]:
    """
    Remove item from cart.

    Args:
        tool_context: ADK tool context providing access to session
        cart_item_id: Cart item identifier

    Returns:
        Status message
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        cart_item = db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item_id).first()
        if not cart_item:
            raise ValueError(f"Cart item {cart_item_id} not found")

        db.delete(cart_item)
        # commit() happens automatically in context manager

        # Update session state with current cart to ensure executor can detect changes
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).order_by(CartItem.added_at.desc()).all()

        items = []
        for item in cart_items:
            # Load product data via relationship
            product = item.product
            price = product.price_usd_units or 0.0
            cart_item_data = {
                "cart_item_id": item.cart_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "name": product.name,
                "picture": product.product_image_url or product.picture,
                "price": price,
                "subtotal": price * item.quantity,
            }
            items.append(cart_item_data)

        # Store cart items in state for executor access
        tool_context.state["cart"] = items

        return {
            "status": "removed",
            "cart_item_id": cart_item_id,
        }


def clear_cart(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Empty entire cart.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Status with items removed count
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        items_removed = db.query(CartItem).filter(
            CartItem.session_id == session_id).delete()
        # commit() happens automatically in context manager

        # Update session state with empty cart to ensure executor can detect changes
        tool_context.state["cart"] = []

        return {
            "status": "cleared",
            "items_removed": items_removed,
        }


def get_cart_total(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Calculate cart total.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Cart totals and item count
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

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
