"""
Artifact formatter for converting session state data into A2A artifacts.

This module provides formatting functions for different artifact types
(products, cart, order, order_summary) used in the agent executor.
"""

from typing import Dict, List, Optional, Any


class ArtifactFormatter:
    """Formats session state data into A2A artifacts."""

    @staticmethod
    def format_products(products_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format products list for artifact.
        
        Args:
            products_list: List of product dictionaries from session state
            
        Returns:
            List of formatted product dictionaries
        """
        formatted = []
        for product in products_list:
            price_usd_units = product.get("price_usd_units")
            price = 0.0
            if price_usd_units:
                # price_usd_units is stored as dollars (not cents), use directly
                # This matches how cart_agent/tools.py handles prices
                price = float(price_usd_units)
            image_url = product.get(
                "product_image_url") or product.get("picture") or ""
            formatted.append({
                "id": product.get("id", ""),
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "image_url": image_url,
                "price": price,
                "price_usd_units": price_usd_units,
                "distance": product.get("distance", 0.0)
            })
        return formatted

    @staticmethod
    def format_cart(cart_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format cart data for artifact.
        
        Args:
            cart_state: Session state dictionary containing cart data
            
        Returns:
            Formatted cart dictionary or None if cart is empty/invalid
        """
        cart_data = cart_state.get(
            "cart") or cart_state.get("cart_items")
        if not cart_data:
            return None
        if isinstance(cart_data, list):
            return {
                "type": "cart",
                "items": cart_data,
                "total_items": len(cart_data),
                "subtotal": sum(item.get("subtotal", 0.0) for item in cart_data)
            }
        return None

    @staticmethod
    def format_order_summary(summary_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format order summary data for artifact.
        
        Args:
            summary_state: Session state dictionary containing order summary data
            
        Returns:
            Formatted order summary dictionary or None if summary is invalid
        """
        summary_data = summary_state.get("pending_order_summary")
        if not summary_data or summary_data is None or not isinstance(summary_data, dict):
            return None
        return {
            "type": "order_summary",
            "items": summary_data.get("items", []),
            "total_amount": summary_data.get("total_amount", 0.0),
            "shipping_address": summary_data.get("shipping_address", ""),
            "item_count": summary_data.get("item_count", 0),
        }

    @staticmethod
    def format_order(order_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format order data for artifact.
        
        Args:
            order_state: Session state dictionary containing order data
            
        Returns:
            Formatted order dictionary or None if order is invalid
        """
        order_data = order_state.get("current_order")
        if not order_data:
            return None
        return {
            "type": "order",
            "order_id": order_data.get("order_id", ""),
            "status": order_data.get("status", ""),
            "items": order_data.get("items", []),
            "total_amount": order_data.get("total_amount", 0.0),
            "shipping_address": order_data.get("shipping_address", ""),
            "created_at": order_data.get("created_at", ""),
        }

