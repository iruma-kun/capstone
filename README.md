# Lexflow

Lexflow is a focused legal practice workspace built with FastAPI, Jinja2, HTMX, SQLAlchemy, and Pydantic. It turns the supplied legal-practice brief into a small working product: authentication, matter tracking, clients, tasks, documents, deadlines, and a validated REST API.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` and sign in with:

- Email: `admin@lexflow.test`
- Password: `demo1234`

Restricted legal-agent demo:

- Email: `agent@lexflow.test`
- Password: `demo1234`
- Access: assigned tasks and their attached files only

The checked-in example documents every setting. The local `.env` is ignored by Git and configures Docker Compose to use PostgreSQL and a host-installed Ollama server.

## Run with Docker and Ollama

Start Ollama on Windows and download the configured model once:

```powershell
ollama serve
ollama pull llama3.2
```

In another terminal, start PostgreSQL and the web application:

```powershell
docker compose up --build
```

The web container reads `.env`, connects to PostgreSQL through the Docker service name `db`, applies Alembic migrations, and reaches Ollama on the Windows host through `host.docker.internal:11434`.

To demonstrate the local LLM workflow, upload a PDF, DOCX, TXT, RTF, or CSV from **Documents**, open the uploaded filename, and select **Analyze with Ollama**. Lexflow extracts text locally, requests a structured analysis from the configured Ollama model, validates the response, and stores it with the document.

To run FastAPI directly on Windows instead of Docker, change the hosts in your local `.env` from `db` to `localhost` and from `host.docker.internal` to `localhost`.

## What is included

- Server-rendered dashboard and legal workflows
- HTMX search, filtering, task updates, and status updates
- JWT authentication in an HTTP-only cookie
- Passlib Argon2 password hashing
- Pydantic request and response validation
- SQLAlchemy models that support SQLite and PostgreSQL
- REST endpoints at `/api/v1/matters`
- Docker Compose configuration with PostgreSQL
- Authenticated document uploads and downloads with file type and size validation
- Persistent upload storage through the Docker `uploads_data` volume
- Task creation from the task workspace or directly inside a matter
- Ollama-powered case-file analysis for PDF, DOCX, TXT, RTF, and CSV uploads
- Structured summaries, parties, key points, deadlines, risks, and task suggestions
- Role-enforced legal-agent workspace limited to assigned tasks and attached files

AI orchestration, semantic search, Drive sync, Redis, and Celery are intentionally left as extension points. They add operational cost and should be introduced only when a real workflow needs them.
