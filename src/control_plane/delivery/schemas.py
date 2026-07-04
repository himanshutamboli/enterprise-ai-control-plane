"""Request/response schemas for the AI Delivery Manager."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    target_date: date | None
    created_at: datetime


class WorkItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    status: Literal["todo", "in_progress", "blocked", "done"] = "todo"
    points: int = Field(default=1, ge=0, le=100)


class WorkItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    status: str
    points: int


class RaidCreate(BaseModel):
    kind: Literal["risk", "assumption", "issue", "dependency"]
    description: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"] = "medium"


class RaidOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: str
    description: str
    severity: str
    status: str


class RiskOut(BaseModel):
    score: int
    level: str
    reasons: list[str]


class HealthOut(BaseModel):
    project: ProjectOut
    health: dict
    risk: RiskOut


class StatusReportIn(BaseModel):
    model: str = "claude-opus-4-8"


class StatusReportOut(BaseModel):
    project: str
    model: str
    risk: RiskOut
    report: str
