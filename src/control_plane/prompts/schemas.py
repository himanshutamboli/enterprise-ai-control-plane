"""Request/response schemas for the prompt registry."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128, pattern=r"^[\w.\-]+$")
    template: str = Field(min_length=1)


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    version: int
    template: str
    created_at: datetime


class RenderIn(BaseModel):
    variables: dict = Field(default_factory=dict)
    version: int | None = None


class RenderOut(BaseModel):
    name: str
    version: int
    text: str
