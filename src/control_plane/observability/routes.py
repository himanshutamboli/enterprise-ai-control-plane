"""Observability API: list traces and inspect a trace's spans (tenant-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.observability import service
from control_plane.observability.schemas import TraceDetailOut, TraceOut

router = APIRouter()


@router.get("/orgs/{org_id}/traces", response_model=list[TraceOut])
def list_traces(
    org_id: str,
    user: User = Depends(require(Permission.OBS_READ)),
    db: Session = Depends(get_db),
) -> list[TraceOut]:
    ensure_tenant(user, org_id)
    return [TraceOut.model_validate(t) for t in service.list_traces(db, org_id)]


@router.get("/orgs/{org_id}/traces/{trace_id}", response_model=TraceDetailOut)
def get_trace(
    org_id: str,
    trace_id: str,
    user: User = Depends(require(Permission.OBS_READ)),
    db: Session = Depends(get_db),
) -> TraceDetailOut:
    ensure_tenant(user, org_id)
    trace = service.get_trace(db, org_id, trace_id)
    if trace is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "trace not found")
    return TraceDetailOut.model_validate(trace)
