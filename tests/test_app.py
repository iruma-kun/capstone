"""
LexFlow - Basic Application Tests
Tests for the legal practice management system
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Import the app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app


class TestLexFlowApp:
    """Test the main FastAPI application"""

    def test_app_creation(self):
        """Test that the app is created successfully"""
        assert app is not None
        assert app.title == "LexFlow Legal Practice Management System"

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_root_redirect(self):
        """Test root redirects to login"""
        client = TestClient(app, follow_redirects=False)
        response = client.get("/")
        # Should redirect to login
        assert response.status_code in [302, 307]
        assert "/login" in response.headers.get("location", "")

    def test_login_page(self):
        """Test login page loads"""
        client = TestClient(app)
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestAuth:
    """Test authentication functionality"""

    def test_login_endpoint_exists(self):
        """Test login POST endpoint exists"""
        client = TestClient(app)
        response = client.post("/login", data={"username": "test", "password": "test"})
        # Should return 401 for invalid credentials or redirect on success
        assert response.status_code in [200, 302, 307, 401]


class TestModels:
    """Test data models"""

    def test_import_models(self):
        """Test that models can be imported"""
        from app.models import User, Client, Matter, Document, Task
        assert User is not None
        assert Client is not None
        assert Matter is not None
        assert Document is not None
        assert Task is not None

    def test_user_model_attributes(self):
        """Test User model has expected attributes"""
        from app.models import User
        user = User(
            email="test@example.com",
            full_name="Test User",
            role="attorney"
        )
        assert user.email == "test@example.com"
        assert user.role == "attorney"

    def test_client_model_attributes(self):
        """Test Client model has expected attributes"""
        from app.models import Client
        client = Client(
            name="Acme Corp",
            email="legal@acme.com",
            phone="+1-555-0100"
        )
        assert client.name == "Acme Corp"
        assert client.email == "legal@acme.com"

    def test_matter_model_attributes(self):
        """Test Matter model has expected attributes"""
        from app.models import Matter
        matter = Matter(
            title="Contract Review",
            description="Review vendor contract",
            client_id=1,
            status="open"
        )
        assert matter.title == "Contract Review"
        assert matter.status == "open"


class TestSchemas:
    """Test Pydantic schemas"""

    def test_user_schema(self):
        """Test UserCreate schema"""
        from app.schemas import UserCreate
        user_data = UserCreate(
            email="new@example.com",
            full_name="New User",
            password="securepass123",
            role="paralegal"
        )
        assert user_data.email == "new@example.com"
        assert user_data.role == "paralegal"

    def test_matter_schema(self):
        """Test MatterCreate schema"""
        from app.schemas import MatterCreate
        matter_data = MatterCreate(
            title="New Matter",
            description="Description",
            client_id=1
        )
        assert matter_data.title == "New Matter"


class TestServices:
    """Test service modules"""

    def test_ollama_service_import(self):
        """Test Ollama service can be imported"""
        from app.services.ollama import OllamaService
        assert OllamaService is not None

    def test_document_text_service_import(self):
        """Test document text extraction service"""
        from app.services.document_text import extract_text
        assert extract_text is not None


class TestConfig:
    """Test configuration"""

    def test_config_loading(self):
        """Test settings can be loaded"""
        from app.config import settings
        assert settings is not None
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'SECRET_KEY')


class TestDatabase:
    """Test database configuration"""

    def test_database_module_import(self):
        """Test database module loads"""
        from app.database import Base, get_db
        assert Base is not None
        assert get_db is not None


# Run with: pytest tests/ -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
