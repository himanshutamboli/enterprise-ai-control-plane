"""Request/response schemas for the gateway API."""

from pydantic import BaseModel, Field, model_validator


class CompleteIn(BaseModel):
    model: str = Field(min_length=1)
    # Provide either a raw `prompt`, or reference a registered prompt by name (+ optional version).
    prompt: str | None = None
    prompt_name: str | None = None
    prompt_version: int | None = None
    variables: dict = Field(default_factory=dict)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    system: str | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "CompleteIn":
        if bool(self.prompt) == bool(self.prompt_name):
            raise ValueError("provide exactly one of 'prompt' or 'prompt_name'")
        return self


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
