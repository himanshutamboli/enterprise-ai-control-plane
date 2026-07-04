"""Request/response schemas for the Agent Builder."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128, pattern=r"^[\w.\-]+$")
    model: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    tools: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=5, ge=1, le=20)


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    version: int
    model: str
    system_prompt: str
    tools: list[str]
    max_steps: int
    created_at: datetime


class AgentRunIn(BaseModel):
    input: str = Field(min_length=1)
    version: int | None = None


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    agent_name: str
    agent_version: int
    input: str
    output: str
    status: str
    steps: list
    created_at: datetime
