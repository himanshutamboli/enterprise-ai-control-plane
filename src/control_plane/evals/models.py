"""Persistence for evaluation runs and their per-item results."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from control_plane.core.db import Base


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    model: Mapped[str] = mapped_column(String(64))
    evaluator: Mapped[str] = mapped_column(String(32))
    dataset_size: Mapped[int] = mapped_column(Integer)
    mean_score: Mapped[float] = mapped_column(Float, default=0.0)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    results: Mapped[list["EvalItemResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="EvalItemResult.idx"
    )


class EvalItemResult(Base):
    __tablename__ = "eval_item_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"), index=True)
    idx: Mapped[int] = mapped_column(Integer)
    input: Mapped[str] = mapped_column(Text)
    expected: Mapped[str | None] = mapped_column(Text)
    output: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)

    run: Mapped["EvalRun"] = relationship(back_populates="results")
