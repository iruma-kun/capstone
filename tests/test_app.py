"""
LexFlow - Basic Application Tests
Tests for the legal practice management system
"""

import os

# Import the app
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app


class TestLexFlowApp:
    """Test the main FastAPI application"""

    def test_app_creation(self):
        """Test that the app is created successfully"""
        assert app is not None
        assert app.title == "Lexflow"

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_redirect(self):
        """Test root redirects to login"""
        client = TestClient(app, follow_redirects=False)
        response = client.get("/")
        # Should redirect to login
        assert response.status_code in [302, 303, 307]
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
        # Login expects email and password fields
        response = client.post(
            "/login", data={"email": "test@test.com", "password": "test"}
        )
        # Should return 400 for invalid credentials or redirect on success
        assert response.status_code in [200, 302, 303, 307, 400]


class TestModels:
    """Test data models"""

    def test_import_models(self):
        """Test that models can be imported"""
        from app.models import Client, Document, Matter, MatterStatus, Task, User

        assert User is not None
        assert Client is not None
        assert Matter is not None
        assert Document is not None
        assert Task is not None
        assert MatterStatus is not None

    def test_user_model_attributes(self):
        """Test User model has expected attributes"""
        from app.models import User

        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password",
            role="Agency",
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == "Agency"

    def test_client_model_attributes(self):
        """Test Client model has expected attributes"""
        from app.models import Client

        client = Client(
            name="Acme Corp",
            email="legal@acme.com",
            phone="+1-555-0100",
            company="Acme Inc",
        )
        assert client.name == "Acme Corp"
        assert client.email == "legal@acme.com"
        assert client.phone == "+1-555-0100"
        assert client.company == "Acme Inc"

    def test_matter_model_attributes(self):
        """Test Matter model has expected attributes"""
        from app.models import Matter, MatterStatus

        matter = Matter(
            title="Contract Review",
            practice_area="Corporate Law",
            client_id=1,
            status=MatterStatus.intake,
            priority="Normal",
            assigned_to="John Doe",
            next_deadline=None,
            summary="Review vendor contract",
        )
        assert matter.title == "Contract Review"
        assert matter.practice_area == "Corporate Law"
        assert matter.status == MatterStatus.intake
        assert matter.priority == "Normal"


class TestSchemas:
    """Test Pydantic schemas"""

    def test_matter_create_schema(self):
        """Test MatterCreate schema"""
        from datetime import date

        from app.schemas import MatterCreate

        matter_data = MatterCreate(
            title="New Matter",
            practice_area="Corporate",
            client_id=1,
            assigned_to="John Doe",
            priority="High",
            next_deadline=date(2026, 12, 31),
            summary="Test matter",
        )
        assert matter_data.title == "New Matter"
        assert matter_data.priority == "High"

    def test_client_summary_schema(self):
        """Test ClientSummary schema"""
        from app.schemas import ClientSummary

        client = ClientSummary(id=1, name="Test Client")
        assert client.id == 1
        assert client.name == "Test Client"

    def test_task_create_schema(self):
        """Test TaskCreate schema"""
        from datetime import date

        from app.schemas import TaskCreate

        task = TaskCreate(
            title="Review contract",
            matter_id=1,
            assignee_id=1,
            due_date=date(2026, 12, 31),
        )
        assert task.title == "Review contract"
        assert task.matter_id == 1


class TestServices:
    """Test service modules"""

    def test_ollama_service_import(self):
        """Test Ollama service can be imported"""
        from app.services.ollama import OllamaError, analyze_document

        assert analyze_document is not None
        assert OllamaError is not None

    def test_document_text_service_import(self):
        """Test document text extraction service"""
        from app.services.document_text import (
            SUPPORTED_ANALYSIS_TYPES,
            DocumentTextError,
            extract_document_text,
        )

        assert extract_document_text is not None
        assert DocumentTextError is not None
        assert SUPPORTED_ANALYSIS_TYPES is not None


class TestConfig:
    """Test configuration"""

    def test_config_loading(self):
        """Test settings can be loaded"""
        from app.config import settings

        assert settings is not None
        assert hasattr(settings, "DATABASE_URL")
        assert hasattr(settings, "SECRET_KEY")
        assert settings.app_name == "Lexflow"


class TestDatabase:
    """Test database configuration"""

    def test_database_module_import(self):
        """Test database module loads"""
        from app.database import Base, SessionLocal, engine, get_db

        assert Base is not None
        assert get_db is not None
        assert engine is not None
        assert SessionLocal is not None


class TestSeed:
    """Test seed functionality"""

    def test_seed_module_import(self):
        """Test seed module can be imported"""
        from app.seed import seed_demo

        assert seed_demo is not None


# Run with: pytest tests/ -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
