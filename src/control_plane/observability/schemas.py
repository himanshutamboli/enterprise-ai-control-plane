"""Request/response schemas for observability."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    status: str
    latency_ms: int
    created_at: datetime


class SpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    kind: str
    input: str | None
    output: str | None
    status: str
    latency_ms: int


class TraceDetailOut(TraceOut):
    spans: list[SpanOut]
