from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import MatterStatus


class MatterCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    practice_area: str = Field(min_length=2, max_length=80)
    client_id: int
    assigned_to: str = Field(default="Unassigned", max_length=100)
    priority: str = Field(default="Normal", pattern="^(Low|Normal|High)$")
    next_deadline: date | None = None
    summary: str = Field(default="", max_length=3000)


class ClientSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MatterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    title: str
    practice_area: str
    status: MatterStatus
    priority: str
    next_deadline: date | None
    assigned_to: str
    created_at: datetime
    client: ClientSummary


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    matter_id: int
    assignee_id: int
    document_id: int | None = None
    due_date: date | None = None


class ExtractedDeadline(BaseModel):
    date: str | None = None
    description: str = Field(min_length=1, max_length=500)


class DocumentAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=5000)
    document_type: str = Field(default="Unknown", max_length=120)
    parties: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    deadlines: list[ExtractedDeadline] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_tasks: list[str] = Field(default_factory=list)
