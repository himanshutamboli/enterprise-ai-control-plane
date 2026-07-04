"""Request/response schemas for the evaluation engine."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvalItemIn(BaseModel):
    prompt: str = Field(min_length=1)
    expected: str | None = None


class EvalRunIn(BaseModel):
    model: str = Field(min_length=1)
    evaluator: str = Field(min_length=1)
    items: list[EvalItemIn] = Field(min_length=1)


class EvalRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    model: str
    evaluator: str
    dataset_size: int
    mean_score: float
    pass_rate: float
    created_at: datetime


class ItemResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    idx: int
    input: str
    expected: str | None
    output: str
    score: float
    passed: bool


class EvalRunDetailOut(EvalRunOut):
    results: list[ItemResultOut]
