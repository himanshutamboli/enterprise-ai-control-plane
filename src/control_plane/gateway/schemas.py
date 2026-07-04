"""Request/response schemas for the gateway API."""

from pydantic import BaseModel, Field


class CompleteIn(BaseModel):
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    system: str | None = None


class CompleteOut(BaseModel):
    model: str
    provider: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class ModelUsage(BaseModel):
    model: str
    calls: int
    cost_usd: float
    tokens: int


class UsageOut(BaseModel):
    total_calls: int
    total_cost_usd: float
    total_tokens: int
    by_model: list[ModelUsage]
