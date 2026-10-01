import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class MatterStatus(str, enum.Enum):
    intake = "Intake"
    active = "Active"
    review = "In review"
    closed = "Closed"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Agency")
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee_user")


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(40), default="")
    company: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    matters: Mapped[list["Matter"]] = relationship(back_populates="client")


class Matter(Base):
    __tablename__ = "matters"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    practice_area: Mapped[str] = mapped_column(String(80))
    status: Mapped[MatterStatus] = mapped_column(Enum(MatterStatus), default=MatterStatus.intake)
    priority: Mapped[str] = mapped_column(String(20), default="Normal")
    summary: Mapped[str] = mapped_column(Text, default="")
    next_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    assigned_to: Mapped[str] = mapped_column(String(100), default="Unassigned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client: Mapped[Client] = relationship(back_populates="matters")
    tasks: Mapped[list["Task"]] = relationship(back_populates="matter", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="matter", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    assignee: Mapped[str] = mapped_column(String(100))
    matter_id: Mapped[int] = mapped_column(ForeignKey("matters.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    matter: Mapped[Matter] = relationship(back_populates="tasks")
    assignee_user: Mapped[User | None] = relationship(back_populates="assigned_tasks")
    document: Mapped["Document | None"] = relationship(back_populates="tasks")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60))
    size: Mapped[str] = mapped_column(String(20), default="—")
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    matter_id: Mapped[int] = mapped_column(ForeignKey("matters.id"))
    matter: Mapped[Matter] = relationship(back_populates="documents")
    tasks: Mapped[list[Task]] = relationship(back_populates="document")
