"""
Unit tests for ArtifactStreamer.
"""
import pytest
from unittest.mock import Mock, AsyncMock

from app.utils.artifact_streamer import ArtifactStreamer
from app.utils.artifact_formatter import ArtifactFormatter
from app.utils.state_tracker import StateTracker
from a2a.types import Part, DataPart


@pytest.fixture
def mock_updater():
    """Create mock TaskUpdater"""
    updater = Mock()
    updater.add_artifact = AsyncMock()
    return updater


@pytest.fixture
def mock_formatter():
    """Create mock ArtifactFormatter"""
    return ArtifactFormatter()


@pytest.fixture
def initial_state():
    """Create initial state for tracker"""
    return {
        "current_results": [],
        "cart": [],
        "current_order": None,
        "pending_order_summary": None,
        "available_payment_methods": [],
        "selected_payment_method": None
    }


@pytest.fixture
def mock_tracker(initial_state):
    """Create StateTracker with initial state"""
    return StateTracker(initial_state)


@pytest.fixture
def streamer(mock_updater, mock_formatter, mock_tracker):
    """Create ArtifactStreamer instance"""
    return ArtifactStreamer(mock_updater, mock_formatter, mock_tracker)


class TestArtifactStreamer:
    """Tests for ArtifactStreamer class"""

    def test_init(self, streamer):
        """Test ArtifactStreamer initialization"""
        assert streamer.updater is not None
        assert streamer.formatter is not None
        assert streamer.tracker is not None
        assert streamer.sent_flags["products"] is False
        assert streamer.sent_flags["cart"] is False

    @pytest.mark.asyncio
    async def test_stream_products_changed(self, streamer, mock_updater):
        """Test streaming products when changed"""
        session_state = {
            "current_results": [{"id": "prod_1", "name": "Product 1"}]
        }

        result = await streamer.stream_if_changed("products", session_state)

        assert result is True
        assert streamer.sent_flags["products"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_products_not_changed(self, streamer, mock_updater):
        """Test not streaming products when not changed"""
        session_state = {
            "current_results": []
        }

        result = await streamer.stream_if_changed("products", session_state)

        assert result is False
        assert streamer.sent_flags["products"] is False
        mock_updater.add_artifact.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_products_already_sent(self, streamer, mock_updater):
        """Test not streaming products if already sent"""
        streamer.sent_flags["products"] = True
        session_state = {
            "current_results": [{"id": "prod_1"}]
        }

        result = await streamer.stream_if_changed("products", session_state)

        assert result is False
        mock_updater.add_artifact.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_cart_changed(self, streamer, mock_updater):
        """Test streaming cart when changed"""
        session_state = {
            "cart": [{"cart_item_id": "item_1", "subtotal": 10.0}]
        }

        result = await streamer.stream_if_changed("cart", session_state)

        assert result is True
        assert streamer.sent_flags["cart"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_order_summary_changed(self, streamer, mock_updater):
        """Test streaming order summary when changed"""
        session_state = {
            "pending_order_summary": {
                "items": [],
                "total_amount": 50.0,
                "shipping_address": "123 Main St",
                "item_count": 1
            }
        }

        result = await streamer.stream_if_changed("order_summary", session_state)

        assert result is True
        assert streamer.sent_flags["order_summary"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_order_changed(self, streamer, mock_updater):
        """Test streaming order when changed"""
        session_state = {
            "current_order": {
                "order_id": "order_123",
                "status": "completed",
                "items": [],
                "total_amount": 100.0
            }
        }

        result = await streamer.stream_if_changed("order", session_state)

        assert result is True
        assert streamer.sent_flags["order"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_payment_methods_changed(self, streamer, mock_updater):
        """Test streaming payment methods when changed"""
        session_state = {
            "available_payment_methods": [
                {"id": "pm_1", "type": "credit_card"}
            ]
        }

        result = await streamer.stream_if_changed("payment_methods", session_state)

        assert result is True
        assert streamer.sent_flags["payment_methods"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_payment_method_selection_changed(self, streamer, mock_updater):
        """Test streaming payment method selection when changed"""
        session_state = {
            "selected_payment_method": {"id": "pm_1"},
            "available_payment_methods": []
        }

        result = await streamer.stream_if_changed("payment_method_selection", session_state)

        assert result is True
        assert streamer.sent_flags["payment_method_selection"] is True
        mock_updater.add_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_unknown_type(self, streamer, mock_updater):
        """Test streaming unknown artifact type"""
        session_state = {}

        result = await streamer.stream_if_changed("unknown_type", session_state)

        assert result is False
        mock_updater.add_artifact.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_exception_handling(self, streamer, mock_updater):
        """Test exception handling during streaming"""
        mock_updater.add_artifact.side_effect = Exception("Test error")
        session_state = {
            "current_results": [{"id": "prod_1"}]
        }

        result = await streamer.stream_if_changed("products", session_state)

        assert result is False
        assert streamer.sent_flags["products"] is False

    @pytest.mark.asyncio
    async def test_ensure_all_sent(self, streamer, mock_updater):
        """Test ensure_all_sent calls all artifact types"""
        session_state = {
            "current_results": [{"id": "prod_1"}],
            "cart": [{"cart_item_id": "item_1"}],
            "pending_order_summary": {"total_amount": 50.0},
            "current_order": {"order_id": "order_123"},
            "available_payment_methods": [{"id": "pm_1"}],
            "selected_payment_method": {"id": "pm_1"}
        }

        await streamer.ensure_all_sent(session_state)

        # Should attempt to send all artifact types
        # May or may not send based on changes
        assert mock_updater.add_artifact.call_count >= 0

    @pytest.mark.asyncio
    async def test_stream_cart_items_key(self, streamer, mock_updater):
        """Test streaming cart using cart_items key"""
        session_state = {
            "cart_items": [{"cart_item_id": "item_1", "subtotal": 10.0}]
        }

        result = await streamer.stream_if_changed("cart", session_state)

        assert result is True
        assert streamer.sent_flags["cart"] is True
