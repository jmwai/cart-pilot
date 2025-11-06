"""
State tracker for detecting changes in session state.

This module provides functionality to track initial state and detect
changes for determining which artifacts need to be sent.
"""

from typing import Dict, Any, Optional


class StateTracker:
    """Tracks initial state and detects changes."""

    def __init__(self, initial_state: Dict[str, Any]):
        """Initialize state tracker with initial state snapshot.

        Args:
            initial_state: Dictionary containing initial session state
        """
        self.initial_state = initial_state
        self.initial_products = initial_state.get("current_results", [])
        self.initial_cart = initial_state.get(
            "cart") or initial_state.get("cart_items", [])
        self.initial_order = initial_state.get("current_order")
        self.initial_order_summary = initial_state.get("pending_order_summary")
        self.initial_payment_methods = initial_state.get(
            "available_payment_methods", [])
        self.initial_selected_payment_method = initial_state.get(
            "selected_payment_method")

    def has_products_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if products changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if products changed, False otherwise
        """
        current_results = current_state.get("current_results", [])
        return current_results and current_results != self.initial_products

    def has_cart_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if cart changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if cart changed, False otherwise
        """
        current_cart = current_state.get(
            "cart") or current_state.get("cart_items", [])
        return current_cart != self.initial_cart

    def has_order_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if order changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if order changed, False otherwise
        """
        current_order = current_state.get("current_order")
        if not current_order or current_order == self.initial_order:
            return False
        # Additional check: ensure order_id is different (new order)
        if not self.initial_order:
            return True
        return current_order.get("order_id") != self.initial_order.get("order_id")

    def has_order_summary_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if order summary changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if order summary changed, False otherwise
        """
        current_order_summary = current_state.get("pending_order_summary")
        # Only send if summary is new (different from initial) and not None
        return (current_order_summary is not None and
                current_order_summary != self.initial_order_summary)

    def has_payment_methods_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if payment methods changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if payment methods changed, False otherwise
        """
        current_payment_methods = current_state.get(
            "available_payment_methods", [])
        return current_payment_methods and current_payment_methods != self.initial_payment_methods

    def has_payment_method_selection_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if payment method selection changed.

        Args:
            current_state: Current session state dictionary

        Returns:
            True if payment method selection changed, False otherwise
        """
        current_selected = current_state.get("selected_payment_method")
        return current_selected and current_selected != self.initial_selected_payment_method
