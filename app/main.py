from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .auth import create_token, current_user, verify_password
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Client, Document, Matter, MatterStatus, Task, User
from .schemas import MatterCreate, MatterRead, TaskCreate
from .seed import seed_demo
from .services.document_text import DocumentTextError, SUPPORTED_ANALYSIS_TYPES, extract_document_text
from .services.ollama import OllamaError, analyze_document

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=ROOT / "templates")
UPLOAD_DIR = Path(settings.upload_dir).resolve()
ALLOWED_DOCUMENT_TYPES = {".pdf", ".doc", ".docx", ".txt", ".rtf", ".png", ".jpg", ".jpeg", ".xls", ".xlsx", ".csv"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo(db, UPLOAD_DIR)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def page_context(request: Request, db: Session, active: str, manager_only: bool = False, **extra):
    user = current_user(request, db)
    if not user:
        return None
    if manager_only and user.role == "Legal agent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This area is restricted to practice managers")
    return {"request": request, "user": user, "active": active, "today": date.today(), **extra}


def require_user(request: Request, db: Session) -> User:
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_manager(request: Request, db: Session) -> User:
    user = require_user(request, db)
    if user.role == "Legal agent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This action is restricted to practice managers")
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if current_user(request, db):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {"error": "The email or password is incorrect."}, status_code=400)
    response = RedirectResponse("/app", status_code=303)
    response.set_cookie("access_token", create_token(user), httponly=True, samesite="lax", max_age=settings.access_token_expire_minutes * 60)
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.get("/app", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    ctx = page_context(request, db, "dashboard")
    if not ctx:
        return RedirectResponse("/", status_code=303)
    if ctx["user"].role == "Legal agent":
        return RedirectResponse("/app/tasks", status_code=303)
    active_count = db.scalar(select(func.count(Matter.id)).where(Matter.status.in_([MatterStatus.active, MatterStatus.review]))) or 0
    open_tasks = db.scalar(select(func.count(Task.id)).where(Task.completed.is_(False))) or 0
    client_count = db.scalar(select(func.count(Client.id))) or 0
    due_soon = db.scalar(select(func.count(Matter.id)).where(Matter.next_deadline.between(date.today(), date.today() + timedelta(days=7)))) or 0
    matters = db.scalars(select(Matter).options(selectinload(Matter.client)).order_by(Matter.updated_at.desc()).limit(5)).all()
    tasks = db.scalars(select(Task).options(selectinload(Task.matter)).where(Task.completed.is_(False)).order_by(Task.due_date.asc()).limit(4)).all()
    ctx.update(stats={"active": active_count, "tasks": open_tasks, "clients": client_count, "due": due_soon}, matters=matters, tasks=tasks)
    return templates.TemplateResponse(request, "dashboard.html", ctx)


def matter_query(q: str, matter_status: str):
    stmt = select(Matter).options(selectinload(Matter.client)).order_by(Matter.updated_at.desc())
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.join(Client).where(or_(Matter.title.ilike(term), Matter.reference.ilike(term), Client.name.ilike(term)))
    if matter_status and matter_status != "All":
        try:
            stmt = stmt.where(Matter.status == MatterStatus(matter_status))
        except ValueError:
            pass
    return stmt


@app.get("/app/matters", response_class=HTMLResponse)
def matters_page(request: Request, q: str = "", matter_status: str = "All", db: Session = Depends(get_db)):
    ctx = page_context(request, db, "matters", manager_only=True)
    if not ctx:
        return RedirectResponse("/", status_code=303)
    matters = db.scalars(matter_query(q, matter_status)).all()
    ctx.update(matters=matters, clients=db.scalars(select(Client).order_by(Client.name)).all(), q=q, matter_status=matter_status, statuses=[s.value for s in MatterStatus])
    template = "partials/matter_rows.html" if request.headers.get("HX-Request") else "matters.html"
    return templates.TemplateResponse(request, template, ctx)


@app.post("/app/matters")
def create_matter(request: Request, title: str = Form(...), practice_area: str = Form(...), client_id: int = Form(...), assigned_to: str = Form("Unassigned"), priority: str = Form("Normal"), next_deadline: str = Form(""), summary: str = Form(""), db: Session = Depends(get_db)):
    require_manager(request, db)
    payload = MatterCreate(title=title, practice_area=practice_area, client_id=client_id, assigned_to=assigned_to, priority=priority, next_deadline=next_deadline or None, summary=summary)
    count = (db.scalar(select(func.count(Matter.id))) or 0) + 1
    matter = Matter(reference=f"MAT-{date.today().year}-{count:04d}", **payload.model_dump())
    db.add(matter)
    db.commit()
    response = RedirectResponse(f"/app/matters/{matter.id}", status_code=303)
    if request.headers.get("HX-Request"):
        response.headers["HX-Redirect"] = f"/app/matters/{matter.id}"
    return response


@app.get("/app/matters/{matter_id}", response_class=HTMLResponse)
def matter_detail(matter_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = page_context(request, db, "matters", manager_only=True)
    if not ctx:
        return RedirectResponse("/", status_code=303)
    matter = db.scalar(select(Matter).options(selectinload(Matter.client), selectinload(Matter.tasks).selectinload(Task.document), selectinload(Matter.documents)).where(Matter.id == matter_id))
    if not matter:
        raise HTTPException(404, "Matter not found")
    ctx.update(matter=matter, statuses=[s.value for s in MatterStatus], users=db.scalars(select(User).order_by(User.name)).all())
    return templates.TemplateResponse(request, "matter_detail.html", ctx)


@app.post("/app/matters/{matter_id}/status")
def update_matter_status(matter_id: int, request: Request, matter_status: str = Form(...), db: Session = Depends(get_db)):
    require_manager(request, db)
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(404, "Matter not found")
    matter.status = MatterStatus(matter_status)
    db.commit()
    return templates.TemplateResponse(request, "partials/status_badge.html", {"matter": matter})


@app.get("/app/clients", response_class=HTMLResponse)
def clients_page(request: Request, db: Session = Depends(get_db)):
    ctx = page_context(request, db, "clients", manager_only=True)
    if not ctx:
        return RedirectResponse("/", status_code=303)
    clients = db.scalars(select(Client).options(selectinload(Client.matters)).order_by(Client.name)).all()
    ctx.update(clients=clients)
    return templates.TemplateResponse(request, "clients.html", ctx)


@app.get("/app/documents", response_class=HTMLResponse)
def documents_page(request: Request, db: Session = Depends(get_db)):
    ctx = page_context(request, db, "documents", manager_only=True)
    if not ctx:
        return RedirectResponse("/", status_code=303)
    documents = db.scalars(select(Document).options(selectinload(Document.matter)).order_by(Document.uploaded_at.desc())).all()
    ctx.update(documents=documents, matters=db.scalars(select(Matter).order_by(Matter.title)).all())
    return templates.TemplateResponse(request, "documents.html", ctx)


def display_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


@app.post("/app/documents/upload")
async def upload_document(
    request: Request,
    matter_id: int = Form(...),
    category: str = Form("General"),
    document: UploadFile = File(...),
    return_to: str = Form("/app/documents"),
    db: Session = Depends(get_db),
):
    require_manager(request, db)
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(422, "Matter does not exist")
    original_name = Path(document.filename or "").name.strip()
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(422, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}")
    if not category.strip() or len(category.strip()) > 60:
        raise HTTPException(422, "Category must be between 1 and 60 characters")

    contents = await document.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if not contents:
        raise HTTPException(422, "The selected file is empty")
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Files must be {settings.max_upload_mb} MB or smaller")

    storage_key = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / storage_key
    destination.write_bytes(contents)
    record = Document(
        name=original_name[:180],
        category=category.strip(),
        size=display_file_size(len(contents)),
        storage_key=storage_key,
        content_type=(document.content_type or "application/octet-stream")[:120],
        matter=matter,
    )
    try:
        db.add(record)
        db.commit()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    safe_return = return_to if return_to.startswith("/app/") else "/app/documents"
    return RedirectResponse(safe_return, status_code=303)


@app.get("/app/documents/{document_id}/download")
def download_document(document_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    document = db.get(Document, document_id)
    if not document or not document.storage_key:
        raise HTTPException(404, "Uploaded file not found")
    if user.role == "Legal agent":
        authorized_task = db.scalar(select(Task.id).where(Task.assignee_id == user.id, Task.document_id == document.id))
        if not authorized_task:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This file is not attached to one of your tasks")
    file_path = (UPLOAD_DIR / document.storage_key).resolve()
    if file_path.parent != UPLOAD_DIR or not file_path.is_file():
        raise HTTPException(404, "Uploaded file not found")
    return FileResponse(file_path, filename=document.name, media_type=document.content_type or "application/octet-stream")


@app.get("/app/documents/{document_id}", response_class=HTMLResponse)
def document_detail(document_id: int, request: Request, error: str = "", db: Session = Depends(get_db)):
    ctx = page_context(request, db, "documents", manager_only=True)
    if not ctx:
        return RedirectResponse("/", status_code=303)
    document = db.scalar(select(Document).options(selectinload(Document.matter)).where(Document.id == document_id))
    if not document:
        raise HTTPException(404, "Document not found")
    analysis = None
    if document.ai_analysis:
        try:
            analysis = json.loads(document.ai_analysis)
        except json.JSONDecodeError:
            error = "The saved AI analysis could not be read. Run the analysis again."
    ctx.update(
        document=document,
        analysis=analysis,
        analysis_error=error,
        analysis_supported=Path(document.name).suffix.lower() in SUPPORTED_ANALYSIS_TYPES,
        ollama_model=settings.ollama_model,
    )
    return templates.TemplateResponse(request, "document_detail.html", ctx)


@app.post("/app/documents/{document_id}/analyze")
def analyze_case_document(document_id: int, request: Request, db: Session = Depends(get_db)):
    require_manager(request, db)
    document = db.scalar(select(Document).options(selectinload(Document.matter)).where(Document.id == document_id))
    if not document or not document.storage_key:
        raise HTTPException(404, "Uploaded file not found")
    file_path = (UPLOAD_DIR / document.storage_key).resolve()
    if file_path.parent != UPLOAD_DIR or not file_path.is_file():
        raise HTTPException(404, "Uploaded file not found")
    try:
        text = extract_document_text(file_path)
        analysis = analyze_document(text, document.name, document.matter.reference)
    except (DocumentTextError, OllamaError) as exc:
        query = urlencode({"error": str(exc)})
        return RedirectResponse(f"/app/documents/{document.id}?{query}", status_code=303)
    document.ai_analysis = analysis.model_dump_json()
    document.ai_model = settings.ollama_model
    document.ai_analyzed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/app/documents/{document.id}", status_code=303)


@app.get("/app/tasks", response_class=HTMLResponse)
def tasks_page(request: Request, db: Session = Depends(get_db)):
    ctx = page_context(request, db, "tasks")
    if not ctx:
        return RedirectResponse("/", status_code=303)
    user = ctx["user"]
    task_query = select(Task).options(selectinload(Task.matter), selectinload(Task.document)).order_by(Task.completed, Task.due_date)
    if user.role == "Legal agent":
        task_query = task_query.where(Task.assignee_id == user.id)
    tasks = db.scalars(task_query).all()
    ctx.update(
        tasks=tasks,
        open_tasks=sum(not task.completed for task in tasks),
        matters=db.scalars(select(Matter).order_by(Matter.title)).all() if user.role != "Legal agent" else [],
        users=db.scalars(select(User).order_by(User.name)).all() if user.role != "Legal agent" else [],
        documents=db.scalars(select(Document).options(selectinload(Document.matter)).where(Document.storage_key.is_not(None)).order_by(Document.name)).all() if user.role != "Legal agent" else [],
    )
    return templates.TemplateResponse(request, "tasks.html", ctx)


@app.post("/app/tasks")
def create_task(
    request: Request,
    title: str = Form(...),
    matter_id: int = Form(...),
    assignee_id: int = Form(...),
    document_id: str = Form(""),
    due_date: str = Form(""),
    return_to: str = Form("/app/tasks"),
    db: Session = Depends(get_db),
):
    require_manager(request, db)
    payload = TaskCreate(title=title, matter_id=matter_id, assignee_id=assignee_id, document_id=int(document_id) if document_id else None, due_date=due_date or None)
    matter = db.get(Matter, payload.matter_id)
    if not matter:
        raise HTTPException(422, "Matter does not exist")
    assignee_user = db.get(User, payload.assignee_id)
    if not assignee_user:
        raise HTTPException(422, "Assigned user does not exist")
    document = db.get(Document, payload.document_id) if payload.document_id else None
    if document and document.matter_id != matter.id:
        raise HTTPException(422, "The attached document must belong to the selected matter")
    task = Task(title=payload.title, due_date=payload.due_date, matter=matter, assignee=assignee_user.name, assignee_user=assignee_user, document=document)
    db.add(task)
    db.commit()
    safe_return = return_to if return_to.startswith("/app/") else "/app/tasks"
    return RedirectResponse(safe_return, status_code=303)


@app.post("/app/tasks/{task_id}/toggle", response_class=HTMLResponse)
def toggle_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    task = db.scalar(select(Task).options(selectinload(Task.matter), selectinload(Task.document)).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Task not found")
    if user.role == "Legal agent" and task.assignee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This task is not assigned to you")
    task.completed = not task.completed
    db.commit()
    return templates.TemplateResponse(request, "partials/task_row.html", {"request": request, "task": task, "today": date.today(), "user": user})


@app.get("/api/v1/matters", response_model=list[MatterRead])
def api_matters(request: Request, db: Session = Depends(get_db)):
    require_manager(request, db)
    return db.scalars(select(Matter).options(selectinload(Matter.client)).order_by(Matter.updated_at.desc())).all()


@app.post("/api/v1/matters", response_model=MatterRead, status_code=201)
def api_create_matter(payload: MatterCreate, request: Request, db: Session = Depends(get_db)):
    require_manager(request, db)
    if not db.get(Client, payload.client_id):
        raise HTTPException(422, "Client does not exist")
    count = (db.scalar(select(func.count(Matter.id))) or 0) + 1
    matter = Matter(reference=f"MAT-{date.today().year}-{count:04d}", **payload.model_dump())
    db.add(matter)
    db.commit()
    return db.scalar(select(Matter).options(selectinload(Matter.client)).where(Matter.id == matter.id))
