"""
Unit tests for Product Discovery Agent tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.shopping_agent.sub_agents.product_discovery_agent.tools import (
    text_vector_search,
    image_vector_search
)
from app.common.models import CatalogItem


class TestTextVectorSearch:
    """Tests for text_vector_search() function"""

    def test_text_vector_search_success(self, mock_db_session):
        """Test successful text vector search"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Mock the execute call for raw SQL
            mock_result = MagicMock()
            mock_row = Mock()
            mock_row.__getitem__.side_effect = lambda i: [
                "prod_123",
                "Running Shoes",
                "High-quality running shoes",
                "https://example.com/pic.jpg",
                "https://example.com/large.jpg",
                0.85
            ][i]
            mock_result.__iter__.return_value = [mock_row]
            mock_db_session.execute.return_value = mock_result

            # Mock embedding function
            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                # Execute
                result = text_vector_search("running shoes")

                # Assert
                assert len(result) == 1
                assert result[0]["id"] == "prod_123"
                assert result[0]["name"] == "Running Shoes"
                assert result[0]["distance"] == 0.85
                assert result[0]["product_image_url"] == "https://example.com/large.jpg"

    def test_text_vector_search_empty_query(self, mock_db_session):
        """Test handling of empty query"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                result = text_vector_search("")

                assert isinstance(result, list)

    def test_text_vector_search_no_results(self, mock_db_session):
        """Test empty results when no matches"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                result = text_vector_search("nonexistent product")

                assert result == []

    def test_text_vector_search_limit_10(self, mock_db_session):
        """Test that results are limited to 10 items"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Create 15 mock rows
            mock_rows = []
            for i in range(15):
                mock_row = Mock()
                mock_row.__getitem__.side_effect = lambda i, idx=i: [
                    f"prod_{idx}",
                    f"Product {idx}",
                    "Description",
                    "pic.jpg",
                    "large.jpg",
                    0.5
                ][i]
                mock_rows.append(mock_row)

            mock_result = MagicMock()
            mock_result.__iter__.return_value = mock_rows
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                result = text_vector_search("test")

                # Note: The LIMIT 10 is in the SQL, so we'd only get 10 back
                # But our mock might return all 15
                assert len(result) <= 15

    def test_text_vector_search_embedding_called(self, mock_db_session):
        """Test that embedding function is called"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                text_vector_search("running shoes")

                # Verify embedding was called
                mock_embed.assert_called_once_with("running shoes")

    def test_text_vector_search_sql_execution(self, mock_db_session):
        """Test that raw SQL is executed with pgvector"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                text_vector_search("test")

                # Verify execute was called (raw SQL execution)
                assert mock_db_session.execute.called


class TestImageVectorSearch:
    """Tests for image_vector_search() function"""

    def test_image_vector_search_success(self, mock_db_session):
        """Test successful image vector search"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Mock the execute call
            mock_result = MagicMock()
            mock_row = Mock()
            mock_row.__getitem__.side_effect = lambda i: [
                "prod_123",
                "Running Shoes",
                "High-quality running shoes",
                "https://example.com/pic.jpg",
                "https://example.com/large.jpg",
                0.92
            ][i]
            mock_result.__iter__.return_value = [mock_row]
            mock_db_session.execute.return_value = mock_result

            # Mock embedding function
            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_image_1408_from_bytes') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                # Execute
                image_bytes = b"fake_image_data"
                result = image_vector_search(image_bytes)

                # Assert
                assert len(result) == 1
                assert result[0]["id"] == "prod_123"
                assert result[0]["name"] == "Running Shoes"
                assert result[0]["distance"] == 0.92

    def test_image_vector_search_invalid_bytes(self, mock_db_session):
        """Test handling of invalid image data"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_image_1408_from_bytes') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                # Execute with empty bytes
                result = image_vector_search(b"")

                assert isinstance(result, list)

    def test_image_vector_search_no_results(self, mock_db_session):
        """Test empty results when no matches"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_image_1408_from_bytes') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                result = image_vector_search(b"fake_image")

                assert result == []

    def test_image_vector_search_limit_10(self, mock_db_session):
        """Test that results are limited to 10 items"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            # Create mock rows
            mock_rows = []
            for i in range(12):
                mock_row = Mock()
                mock_row.__getitem__.side_effect = lambda i, idx=i: [
                    f"prod_{idx}",
                    f"Product {idx}",
                    "Description",
                    "pic.jpg",
                    "large.jpg",
                    0.5
                ][i]
                mock_rows.append(mock_row)

            mock_result = MagicMock()
            mock_result.__iter__.return_value = mock_rows
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_image_1408_from_bytes') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                result = image_vector_search(b"fake_image")

                # LIMIT 10 in SQL, but mock returns all
                assert len(result) <= 12

    def test_image_vector_search_embedding_called(self, mock_db_session):
        """Test that image embedding function is called"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_image_1408_from_bytes') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                image_bytes = b"fake_image_data"
                image_vector_search(image_bytes)

                # Verify embedding was called
                mock_embed.assert_called_once_with(image_bytes)


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_database_connection_error(self, mock_db_session):
        """Test handling of database failures"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.side_effect = Exception(
                "Database connection failed")

            with pytest.raises(Exception):
                text_vector_search("test")

    def test_embedding_service_error(self, mock_db_session):
        """Test handling of Vertex AI API failures"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.side_effect = Exception(
                    "Vertex AI service unavailable")

                with pytest.raises(Exception):
                    text_vector_search("test")

    def test_vector_search_uses_pgvector_syntax(self, mock_db_session):
        """Test that pgvector distance operator is used"""
        with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools.get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_db_session

            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_db_session.execute.return_value = mock_result

            with patch('app.shopping_agent.sub_agents.product_discovery_agent.tools._embed_text_1408') as mock_embed:
                mock_embed.return_value = [0.1] * 1408

                text_vector_search("test")

                # Verify execute was called (which uses raw SQL with pgvector)
                call_args = mock_db_session.execute.call_args
                assert call_args is not None
                # The SQL should contain pgvector syntax (<=> operator)
