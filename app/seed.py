from datetime import date, timedelta
from pathlib import Path
import shutil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import hash_password
from .models import Client, Document, Matter, MatterStatus, Task, User


DEMO_AGENT_EMAIL = "agent@lexflow.test"
DEMO_PASSWORD = "demo1234"
DEMO_ADMIN_NAME = "Rudransh Choubey"
DEMO_AGENT_NAME = "Tanish Mishra"


def ensure_demo_document(db: Session, matter: Matter, upload_dir: Path | None) -> Document:
    document = db.scalar(select(Document).where(Document.name == "Demo vendor dispute case.txt"))
    if not document:
        document = Document(
            name="Demo vendor dispute case.txt",
            category="Evidence",
            size="5.1 KB",
            storage_key="demo-vendor-dispute-case.txt",
            content_type="text/plain",
            matter=matter,
        )
        db.add(document)
        db.flush()
    if upload_dir and document.storage_key:
        source = Path(__file__).resolve().parent.parent / "sample_data" / "demo_vendor_dispute_case.txt"
        destination = upload_dir / document.storage_key
        if source.is_file() and not destination.exists():
            upload_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return document


def seed_demo(db: Session, upload_dir: Path | None = None) -> None:
    admin = db.scalar(select(User).where(User.email == "admin@lexflow.test"))
    if not admin:
        admin = User(name=DEMO_ADMIN_NAME, email="admin@lexflow.test", password_hash=hash_password(DEMO_PASSWORD), role="Agency admin")
        db.add(admin)
    else:
        admin.name = DEMO_ADMIN_NAME

    agent = db.scalar(select(User).where(User.email == DEMO_AGENT_EMAIL))
    if not agent:
        agent = User(name=DEMO_AGENT_NAME, email=DEMO_AGENT_EMAIL, password_hash=hash_password(DEMO_PASSWORD), role="Legal agent")
        db.add(agent)
    else:
        agent.name = DEMO_AGENT_NAME
    db.flush()

    if db.scalar(select(func.count(Client.id))):
        for matter in db.scalars(select(Matter).where(Matter.assigned_to == "Maya Chen")):
            matter.assigned_to = DEMO_ADMIN_NAME
        for matter in db.scalars(select(Matter).where(Matter.assigned_to == "Jon Bell")):
            matter.assigned_to = DEMO_AGENT_NAME
        for task in db.scalars(select(Task).where(Task.assignee == "Maya Chen")):
            task.assignee = DEMO_ADMIN_NAME
        for task in db.scalars(select(Task).where(Task.assignee == "Jon Bell")):
            task.assignee = DEMO_AGENT_NAME
        matter = db.scalar(select(Matter).where(Matter.reference == "MAT-2026-0138"))
        if matter:
            document = ensure_demo_document(db, matter, upload_dir)
            task = db.scalar(select(Task).where(Task.title == "Review opposing counsel response"))
            if task:
                task.assignee = agent.name
                task.assignee_id = agent.id
                task.document_id = document.id
        for task in db.scalars(select(Task).where(Task.assignee == agent.name, Task.assignee_id.is_(None))):
            task.assignee_id = agent.id
        db.commit()
        return

    clients = [
        Client(name="Avery Morgan", email="avery@example.com", phone="+1 415 555 0142", company="Morgan Studio"),
        Client(name="Northstar Labs", email="legal@northstar.test", phone="+1 212 555 0188", company="Northstar Labs"),
        Client(name="Elena Ruiz", email="elena@example.com", phone="+1 305 555 0116", company="Ruiz & Co."),
        Client(name="Harbor Health", email="ops@harborhealth.test", phone="+1 617 555 0164", company="Harbor Health"),
    ]
    db.add_all(clients)
    db.flush()
    today = date.today()
    matters = [
        Matter(reference="MAT-2026-0142", title="Morgan estate planning", practice_area="Estate planning", status=MatterStatus.active, priority="High", client=clients[0], assigned_to=DEMO_ADMIN_NAME, next_deadline=today + timedelta(days=2), summary="Prepare updated estate plan and coordinate signatures with all beneficiaries."),
        Matter(reference="MAT-2026-0138", title="Northstar vendor dispute", practice_area="Commercial", status=MatterStatus.review, priority="High", client=clients[1], assigned_to=DEMO_AGENT_NAME, next_deadline=today + timedelta(days=5), summary="Review vendor correspondence and prepare a settlement position."),
        Matter(reference="MAT-2026-0131", title="Ruiz trademark filing", practice_area="Intellectual property", status=MatterStatus.intake, priority="Normal", client=clients[2], assigned_to="Priya Shah", next_deadline=today + timedelta(days=9), summary="Complete clearance search and confirm filing classes."),
        Matter(reference="MAT-2026-0124", title="Harbor employment review", practice_area="Employment", status=MatterStatus.active, priority="Normal", client=clients[3], assigned_to=DEMO_ADMIN_NAME, next_deadline=today + timedelta(days=12), summary="Audit employment agreements and policy updates."),
        Matter(reference="MAT-2026-0116", title="Northstar privacy policy", practice_area="Privacy", status=MatterStatus.closed, priority="Low", client=clients[1], assigned_to=DEMO_AGENT_NAME, next_deadline=None, summary="Privacy policy update completed and delivered."),
    ]
    db.add_all(matters)
    db.flush()
    documents = [
        Document(name="Estate planning questionnaire.pdf", category="Client intake", size="1.8 MB", matter=matters[0]),
        Document(name="Vendor correspondence.pdf", category="Evidence", size="4.2 MB", matter=matters[1]),
        Document(name="Trademark search results.pdf", category="Research", size="2.1 MB", matter=matters[2]),
        Document(name="Employment agreement.docx", category="Draft", size="860 KB", matter=matters[3]),
    ]
    db.add_all(documents)
    db.flush()
    demo_document = ensure_demo_document(db, matters[1], upload_dir)
    db.add_all([
        Task(title="Prepare signature packet", due_date=today + timedelta(days=2), assignee=admin.name, assignee_id=admin.id, matter=matters[0]),
        Task(title="Review opposing counsel response", due_date=today + timedelta(days=1), assignee=agent.name, assignee_id=agent.id, document=demo_document, matter=matters[1]),
        Task(title="Confirm trademark classes", due_date=today + timedelta(days=4), assignee="Priya Shah", matter=matters[2]),
        Task(title="Send policy summary to client", due_date=today + timedelta(days=7), assignee=admin.name, assignee_id=admin.id, matter=matters[3]),
        Task(title="Archive final correspondence", due_date=today - timedelta(days=1), assignee=agent.name, assignee_id=agent.id, matter=matters[4], completed=True),
    ])
    db.commit()
