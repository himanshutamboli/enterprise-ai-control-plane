"""Query traces (tenant-scoped)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from control_plane.observability.models import Trace


def list_traces(db: Session, org_id: str, limit: int = 100) -> list[Trace]:
    return list(
        db.scalars(
            select(Trace)
            .where(Trace.org_id == org_id)
            .order_by(Trace.created_at.desc())
            .limit(limit)
        )
    )


def get_trace(db: Session, org_id: str, trace_id: str) -> Trace | None:
    trace = db.get(Trace, trace_id)
    return trace if trace is not None and trace.org_id == org_id else None
