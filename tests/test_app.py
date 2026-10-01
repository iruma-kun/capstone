import atexit
import os
import re
import shutil
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_lexflow.db"
TEST_UPLOAD_DIR = Path(tempfile.mkdtemp(prefix="lexflow_upload_test_"))
os.environ["UPLOAD_DIR"] = str(TEST_UPLOAD_DIR)
atexit.register(shutil.rmtree, TEST_UPLOAD_DIR, ignore_errors=True)

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main_module
from app.main import app
from app.database import SessionLocal
from app.models import User
from app.schemas import DocumentAnalysis, ExtractedDeadline


def authenticated_client(client: TestClient, email: str = "admin@lexflow.test") -> None:
    response = client.post("/login", data={"email": email, "password": "demo1234"}, follow_redirects=False)
    assert response.status_code == 303
    client.cookies.update(response.cookies)


def test_login_and_core_pages():
    with TestClient(app) as client:
        authenticated_client(client)
        for path in ("/app", "/app/matters", "/app/tasks", "/app/clients", "/app/documents"):
            page = client.get(path)
            assert page.status_code == 200
        api = client.get("/api/v1/matters")
        assert api.status_code == 200
        assert len(api.json()) >= 4


def test_bad_login_is_rejected():
    with TestClient(app) as client:
        response = client.post("/login", data={"email": "wrong@example.com", "password": "wrong"})
        assert response.status_code == 400
        assert "incorrect" in response.text


def test_create_task_and_upload_document(monkeypatch):
    with TestClient(app) as client:
        authenticated_client(client)
        matter_id = client.get("/api/v1/matters").json()[0]["id"]
        with SessionLocal() as db:
            admin_id = db.scalar(select(User.id).where(User.email == "admin@lexflow.test"))

        task = client.post(
            "/app/tasks",
            data={"title": "Review uploaded brief", "matter_id": matter_id, "assignee_id": admin_id, "due_date": "2026-10-10", "return_to": "/app/tasks"},
            follow_redirects=False,
        )
        assert task.status_code == 303
        assert "Review uploaded brief" in client.get("/app/tasks").text

        upload = client.post(
            "/app/documents/upload",
            data={"matter_id": matter_id, "category": "Evidence", "return_to": "/app/documents"},
            files={"document": ("case-brief.txt", b"Settlement response is due October 10, 2026. Northstar Labs must review the proposed terms.", "text/plain")},
            follow_redirects=False,
        )
        assert upload.status_code == 303
        documents_page = client.get("/app/documents")
        assert "case-brief.txt" in documents_page.text
        match = re.search(r'href="(/app/documents/\d+/download)"[^>]*title="Download case-brief.txt"', documents_page.text)
        assert match
        download = client.get(match.group(1))
        assert download.status_code == 200
        assert b"Settlement response" in download.content

        monkeypatch.setattr(
            main_module,
            "analyze_document",
            lambda text, filename, matter_reference: DocumentAnalysis(
                summary="A settlement response is required from Northstar Labs.",
                document_type="Settlement correspondence",
                parties=["Northstar Labs"],
                key_points=["The proposed terms require review."],
                deadlines=[ExtractedDeadline(date="2026-10-10", description="Submit the settlement response.")],
                risks=["Missing the response deadline."],
                suggested_tasks=["Review the proposed settlement terms."],
            ),
        )
        document_id = int(match.group(1).split("/")[3])
        analyzed = client.post(f"/app/documents/{document_id}/analyze", follow_redirects=False)
        assert analyzed.status_code == 303
        detail = client.get(f"/app/documents/{document_id}")
        assert detail.status_code == 200
        assert "A settlement response is required" in detail.text
        assert "Submit the settlement response" in detail.text


def test_rejects_unsupported_document_type():
    with TestClient(app) as client:
        authenticated_client(client)
        matter_id = client.get("/api/v1/matters").json()[0]["id"]
        response = client.post(
            "/app/documents/upload",
            data={"matter_id": matter_id, "category": "Evidence"},
            files={"document": ("unsafe.exe", b"not an allowed document", "application/octet-stream")},
        )
        assert response.status_code == 422
        assert "Unsupported file type" in response.text


def test_legal_agent_sees_only_assigned_tasks_and_files():
    with TestClient(app) as client:
        authenticated_client(client)
        matter_id = client.get("/api/v1/matters").json()[0]["id"]
        private_upload = client.post(
            "/app/documents/upload",
            data={"matter_id": matter_id, "category": "Internal"},
            files={"document": ("manager-only.txt", b"This document is not attached to the agent task.", "text/plain")},
            follow_redirects=False,
        )
        assert private_upload.status_code == 303
        documents_page = client.get("/app/documents").text
        private_match = re.search(r'href="(/app/documents/\d+/download)"[^>]*title="Download manager-only.txt"', documents_page)
        assert private_match

        client.post("/logout")
        authenticated_client(client, "agent@lexflow.test")
        home = client.get("/app", follow_redirects=False)
        assert home.status_code == 303
        assert home.headers["location"] == "/app/tasks"

        tasks_page = client.get("/app/tasks")
        assert tasks_page.status_code == 200
        assert "Review opposing counsel response" in tasks_page.text
        assert "Demo vendor dispute case.txt" in tasks_page.text
        assert "Prepare signature packet" not in tasks_page.text
        assert "New task" not in tasks_page.text
        assigned_match = re.search(r'href="(/app/documents/\d+/download)"[^>]*>[^<]*<span>↓</span>Demo vendor dispute case.txt', tasks_page.text)
        assert assigned_match
        assert client.get(assigned_match.group(1)).status_code == 200

        assert client.get("/app/matters").status_code == 403
        assert client.get("/app/clients").status_code == 403
        assert client.get("/app/documents").status_code == 403
        assert client.get("/api/v1/matters").status_code == 403
        assert client.get(private_match.group(1)).status_code == 403
