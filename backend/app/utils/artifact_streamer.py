"""
Artifact streamer for sending A2A artifacts based on state changes.

This module handles streaming artifacts to the A2A event queue, tracking
which artifacts have been sent, and eliminating duplication between
incremental and final artifact sending.
"""

import logging
from typing import Dict, Any, Optional

from a2a.types import Part, DataPart
from a2a.server.tasks import TaskUpdater

from app.utils.artifact_formatter import ArtifactFormatter
from app.utils.state_tracker import StateTracker

logger = logging.getLogger(__name__)


class ArtifactStreamer:
    """Streams artifacts to A2A event queue based on state changes."""

    def __init__(
        self,
        updater: TaskUpdater,
        formatter: ArtifactFormatter,
        tracker: StateTracker
    ):
        """Initialize artifact streamer.

        Args:
            updater: A2A TaskUpdater for sending artifacts
            formatter: ArtifactFormatter for formatting state data
            tracker: StateTracker for detecting state changes
        """
        self.updater = updater
        self.formatter = formatter
        self.tracker = tracker
        self.sent_flags = {
            "products": False,
            "cart": False,
            "order": False,
            "order_summary": False,
            "payment_methods": False,
            "payment_method_selection": False
        }

    async def stream_if_changed(
        self,
        artifact_type: str,
        session_state: Dict[str, Any]
    ) -> bool:
        """Stream artifact if state changed and not already sent.

        Args:
            artifact_type: Type of artifact ('products', 'cart', 'order', 'order_summary')
            session_state: Current session state dictionary

        Returns:
            True if artifact was sent, False otherwise
        """
        if self.sent_flags.get(artifact_type, False):
            return False

        try:
            if artifact_type == "products":
                if "current_results" in session_state and self.tracker.has_products_changed(session_state):
                    formatted_products = self.formatter.format_products(
                        session_state.get("current_results", []))
                    if formatted_products:
                        product_data = {
                            "type": "product_list",
                            "products": formatted_products
                        }
                        await self.updater.add_artifact(
                            [Part(root=DataPart(
                                data=product_data,
                                mimeType="application/json"
                            ))],
                            name="products"
                        )
                        self.sent_flags["products"] = True
                        return True

            elif artifact_type == "cart":
                if (("cart" in session_state or "cart_items" in session_state) and
                        self.tracker.has_cart_changed(session_state)):
                    cart_artifact_data = self.formatter.format_cart(
                        session_state)
                    if cart_artifact_data:
                        logger.info(
                            f"Streaming cart artifact with {len(cart_artifact_data.get('items', []))} items")
                        await self.updater.add_artifact(
                            [Part(root=DataPart(
                                data=cart_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="cart"
                        )
                        self.sent_flags["cart"] = True
                        return True
                    else:
                        logger.debug(
                            "Cart artifact data was None after formatting")
                else:
                    cart_present = "cart" in session_state or "cart_items" in session_state
                    changed = self.tracker.has_cart_changed(
                        session_state) if cart_present else False
                    logger.debug(
                        f"Cart not streamed - present: {cart_present}, changed: {changed}, already_sent: {self.sent_flags.get('cart', False)}")

            elif artifact_type == "order_summary":
                if ("pending_order_summary" in session_state and
                        self.tracker.has_order_summary_changed(session_state)):
                    order_summary_artifact_data = self.formatter.format_order_summary(
                        session_state)
                    if order_summary_artifact_data:
                        await self.updater.add_artifact(
                            [Part(root=DataPart(
                                data=order_summary_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="order_summary"
                        )
                        self.sent_flags["order_summary"] = True
                        return True

            elif artifact_type == "order":
                if ("current_order" in session_state and
                        self.tracker.has_order_changed(session_state)):
                    current_order = session_state.get("current_order")
                    # Additional check: ensure order_id is different (new order)
                    initial_order = self.tracker.initial_order
                    if not initial_order or current_order.get("order_id") != initial_order.get("order_id"):
                        order_artifact_data = self.formatter.format_order(
                            session_state)
                        if order_artifact_data:
                            await self.updater.add_artifact(
                                [Part(root=DataPart(
                                    data=order_artifact_data,
                                    mimeType="application/json"
                                ))],
                                name="order"
                            )
                            self.sent_flags["order"] = True
                            return True

            elif artifact_type == "payment_methods":
                if ("available_payment_methods" in session_state and
                        self.tracker.has_payment_methods_changed(session_state)):
                    payment_methods_artifact_data = self.formatter.format_payment_methods(
                        session_state)
                    if payment_methods_artifact_data:
                        await self.updater.add_artifact(
                            [Part(root=DataPart(
                                data=payment_methods_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="payment_methods"
                        )
                        self.sent_flags["payment_methods"] = True
                        return True

            elif artifact_type == "payment_method_selection":
                if ("selected_payment_method" in session_state and
                        self.tracker.has_payment_method_selection_changed(session_state)):
                    selection_artifact_data = self.formatter.format_payment_method_selection(
                        session_state)
                    if selection_artifact_data:
                        await self.updater.add_artifact(
                            [Part(root=DataPart(
                                data=selection_artifact_data,
                                mimeType="application/json"
                            ))],
                            name="payment_method_selection"
                        )
                        self.sent_flags["payment_method_selection"] = True
                        return True

        except Exception as e:
            logger.error(f"Error streaming {artifact_type} artifact: {e}")
            return False

        return False

    async def ensure_all_sent(self, session_state: Dict[str, Any]) -> None:
        """Ensure all artifacts are sent after execution.

        Args:
            session_state: Final session state dictionary
        """
        # Try to send each artifact type if not already sent
        await self.stream_if_changed("products", session_state)
        await self.stream_if_changed("cart", session_state)
        await self.stream_if_changed("order_summary", session_state)
        await self.stream_if_changed("order", session_state)
        await self.stream_if_changed("payment_methods", session_state)
        await self.stream_if_changed("payment_method_selection", session_state)
