"""
Unit tests for StateTracker.
"""
import pytest

from app.utils.state_tracker import StateTracker


class TestStateTracker:
    """Tests for StateTracker class"""

    def test_init(self):
        """Test StateTracker initialization"""
        initial_state = {
            "current_results": [{"id": "prod_1"}],
            "cart": [{"cart_item_id": "item_1"}],
            "current_order": {"order_id": "order_1"},
            "pending_order_summary": {"total_amount": 50.0},
            "available_payment_methods": [{"id": "pm_1"}],
            "selected_payment_method": {"id": "pm_1"}
        }
        tracker = StateTracker(initial_state)

        assert tracker.initial_products == [{"id": "prod_1"}]
        assert tracker.initial_cart == [{"cart_item_id": "item_1"}]
        assert tracker.initial_order == {"order_id": "order_1"}
        assert tracker.initial_order_summary == {"total_amount": 50.0}

    def test_has_products_changed_true(self):
        """Test detecting products change"""
        initial_state = {"current_results": [{"id": "prod_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"current_results": [{"id": "prod_2"}]}
        assert tracker.has_products_changed(current_state) is True

    def test_has_products_changed_false(self):
        """Test no products change detected"""
        initial_state = {"current_results": [{"id": "prod_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"current_results": [{"id": "prod_1"}]}
        assert tracker.has_products_changed(current_state) is False

    def test_has_products_changed_empty(self):
        """Test that empty products list doesn't trigger change"""
        initial_state = {"current_results": []}
        tracker = StateTracker(initial_state)

        current_state = {"current_results": []}
        assert tracker.has_products_changed(current_state) is False

    def test_has_cart_changed_true(self):
        """Test detecting cart change"""
        initial_state = {"cart": [{"cart_item_id": "item_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"cart": [{"cart_item_id": "item_2"}]}
        assert tracker.has_cart_changed(current_state) is True

    def test_has_cart_changed_false(self):
        """Test no cart change detected"""
        initial_state = {"cart": [{"cart_item_id": "item_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"cart": [{"cart_item_id": "item_1"}]}
        assert tracker.has_cart_changed(current_state) is False

    def test_has_cart_changed_cart_items_key(self):
        """Test cart change detection using cart_items key"""
        initial_state = {"cart_items": [{"cart_item_id": "item_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"cart_items": [{"cart_item_id": "item_2"}]}
        assert tracker.has_cart_changed(current_state) is True

    def test_has_order_changed_new_order(self):
        """Test detecting new order"""
        initial_state = {}
        tracker = StateTracker(initial_state)

        current_state = {"current_order": {"order_id": "order_1"}}
        assert tracker.has_order_changed(current_state) is True

    def test_has_order_changed_different_order_id(self):
        """Test detecting order change with different order_id"""
        initial_state = {"current_order": {"order_id": "order_1"}}
        tracker = StateTracker(initial_state)

        current_state = {"current_order": {"order_id": "order_2"}}
        assert tracker.has_order_changed(current_state) is True

    def test_has_order_changed_same_order(self):
        """Test no order change detected for same order"""
        initial_state = {"current_order": {"order_id": "order_1"}}
        tracker = StateTracker(initial_state)

        current_state = {"current_order": {"order_id": "order_1"}}
        assert tracker.has_order_changed(current_state) is False

    def test_has_order_changed_no_order(self):
        """Test no change when order is removed"""
        initial_state = {"current_order": {"order_id": "order_1"}}
        tracker = StateTracker(initial_state)

        current_state = {}
        assert tracker.has_order_changed(current_state) is False

    def test_has_order_summary_changed_new_summary(self):
        """Test detecting new order summary"""
        initial_state = {}
        tracker = StateTracker(initial_state)

        current_state = {"pending_order_summary": {"total_amount": 50.0}}
        assert tracker.has_order_summary_changed(current_state) is True

    def test_has_order_summary_changed_different_summary(self):
        """Test detecting order summary change"""
        initial_state = {"pending_order_summary": {"total_amount": 50.0}}
        tracker = StateTracker(initial_state)

        current_state = {"pending_order_summary": {"total_amount": 100.0}}
        assert tracker.has_order_summary_changed(current_state) is True

    def test_has_order_summary_changed_same_summary(self):
        """Test no order summary change detected"""
        summary = {"total_amount": 50.0}
        initial_state = {"pending_order_summary": summary}
        tracker = StateTracker(initial_state)

        current_state = {"pending_order_summary": summary}
        assert tracker.has_order_summary_changed(current_state) is False

    def test_has_order_summary_changed_none(self):
        """Test that None summary doesn't trigger change"""
        initial_state = {"pending_order_summary": None}
        tracker = StateTracker(initial_state)

        current_state = {"pending_order_summary": None}
        assert tracker.has_order_summary_changed(current_state) is False

    def test_has_payment_methods_changed_true(self):
        """Test detecting payment methods change"""
        initial_state = {"available_payment_methods": [{"id": "pm_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"available_payment_methods": [{"id": "pm_2"}]}
        assert tracker.has_payment_methods_changed(current_state) is True

    def test_has_payment_methods_changed_false(self):
        """Test no payment methods change detected"""
        initial_state = {"available_payment_methods": [{"id": "pm_1"}]}
        tracker = StateTracker(initial_state)

        current_state = {"available_payment_methods": [{"id": "pm_1"}]}
        assert tracker.has_payment_methods_changed(current_state) is False

    def test_has_payment_methods_changed_empty(self):
        """Test that empty payment methods list doesn't trigger change"""
        initial_state = {"available_payment_methods": []}
        tracker = StateTracker(initial_state)

        current_state = {"available_payment_methods": []}
        assert tracker.has_payment_methods_changed(current_state) is False

    def test_has_payment_method_selection_changed_true(self):
        """Test detecting payment method selection change"""
        initial_state = {"selected_payment_method": {"id": "pm_1"}}
        tracker = StateTracker(initial_state)

        current_state = {"selected_payment_method": {"id": "pm_2"}}
        assert tracker.has_payment_method_selection_changed(
            current_state) is True

    def test_has_payment_method_selection_changed_false(self):
        """Test no payment method selection change detected"""
        initial_state = {"selected_payment_method": {"id": "pm_1"}}
        tracker = StateTracker(initial_state)

        current_state = {"selected_payment_method": {"id": "pm_1"}}
        assert tracker.has_payment_method_selection_changed(
            current_state) is False

    def test_has_payment_method_selection_changed_none(self):
        """Test that None selection doesn't trigger change"""
        initial_state = {}
        tracker = StateTracker(initial_state)

        current_state = {}
        assert tracker.has_payment_method_selection_changed(
            current_state) is False
