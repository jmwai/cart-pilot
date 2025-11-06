"""
Unit tests for config.py.
"""
import pytest
import os
from unittest.mock import patch

from app.common.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class"""

    def test_settings_required_fields(self):
        """Test that required fields are enforced"""
        # Clear any existing environment variables
        import os
        env_backup = {}
        for key in ['PROJECT_ID', 'GOOGLE_API_KEY']:
            if key in os.environ:
                env_backup[key] = os.environ[key]
                del os.environ[key]

        try:
            # Clear cache to force reload
            get_settings.cache_clear()
            # Pydantic Settings will raise ValidationError if required fields are missing
            with pytest.raises(Exception):  # ValidationError or similar
                Settings()
        finally:
            # Restore environment
            for key, value in env_backup.items():
                os.environ[key] = value
            get_settings.cache_clear()

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key'
    }, clear=True)
    def test_settings_from_env(self):
        """Test loading settings from environment variables"""
        get_settings.cache_clear()
        settings = Settings()
        assert settings.PROJECT_ID == 'test-project'
        assert settings.GOOGLE_API_KEY == 'test-key'
        assert settings.REGION == 'europe-west1'  # default value

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key',
        'REGION': 'us-central1',
        'GEMINI_MODEL': 'gemini-pro'
    })
    def test_settings_custom_values(self):
        """Test settings with custom values"""
        settings = Settings()
        assert settings.REGION == 'us-central1'
        assert settings.GEMINI_MODEL == 'gemini-pro'

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key',
        'DB_PORT': '5433'
    })
    def test_settings_db_config(self):
        """Test database configuration"""
        settings = Settings()
        assert settings.DB_PORT == 5433
        assert settings.DB_USER == 'postgres'  # default value

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key',
        'API_TOP_K_MAX': '100',
        'MAX_UPLOAD_MB': '20'
    })
    def test_settings_api_config(self):
        """Test API configuration"""
        settings = Settings()
        assert settings.API_TOP_K_MAX == 100
        assert settings.MAX_UPLOAD_MB == 20


class TestGetSettings:
    """Tests for get_settings() function"""

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key'
    })
    def test_get_settings_cached(self):
        """Test that get_settings uses caching"""
        # Clear cache
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return same instance due to caching
        assert settings1 is settings2

    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'GOOGLE_API_KEY': 'test-key'
    })
    def test_get_settings_returns_settings(self):
        """Test that get_settings returns Settings instance"""
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)
