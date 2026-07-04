"""AI Delivery Manager API: projects, work items, RAID, health/risk, and status reports."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.delivery import service
from control_plane.delivery.schemas import (
    HealthOut,
    ProjectCreate,
    ProjectOut,
    RaidCreate,
    RaidOut,
    RiskOut,
    StatusReportIn,
    StatusReportOut,
    WorkItemCreate,
    WorkItemOut,
)
from control_plane.gateway.router import UnknownModelError

router = APIRouter()


def _project_or_404(db: Session, user: User, org_id: str, project_id: str):
    ensure_tenant(user, org_id)
    project = service.get_project(db, org_id, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return project


@router.post(
    "/orgs/{org_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED
)
def create_project(
    org_id: str,
    body: ProjectCreate,
    user: User = Depends(require(Permission.DELIVERY_WRITE)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    ensure_tenant(user, org_id)
    return ProjectOut.model_validate(
        service.create_project(db, org_id, body.name, body.target_date)
    )


@router.get("/orgs/{org_id}/projects", response_model=list[ProjectOut])
def list_projects(
    org_id: str,
    user: User = Depends(require(Permission.DELIVERY_READ)),
    db: Session = Depends(get_db),
) -> list[ProjectOut]:
    ensure_tenant(user, org_id)
    return [ProjectOut.model_validate(p) for p in service.list_projects(db, org_id)]


@router.post(
    "/orgs/{org_id}/projects/{project_id}/work-items",
    response_model=WorkItemOut,
    status_code=status.HTTP_201_CREATED,
)
def add_work_item(
    org_id: str,
    project_id: str,
    body: WorkItemCreate,
    user: User = Depends(require(Permission.DELIVERY_WRITE)),
    db: Session = Depends(get_db),
) -> WorkItemOut:
    _project_or_404(db, user, org_id, project_id)
    return WorkItemOut.model_validate(
        service.add_work_item(db, project_id, body.title, body.status, body.points)
    )


@router.post(
    "/orgs/{org_id}/projects/{project_id}/raid",
    response_model=RaidOut,
    status_code=status.HTTP_201_CREATED,
)
def add_raid_item(
    org_id: str,
    project_id: str,
    body: RaidCreate,
    user: User = Depends(require(Permission.DELIVERY_WRITE)),
    db: Session = Depends(get_db),
) -> RaidOut:
    _project_or_404(db, user, org_id, project_id)
    return RaidOut.model_validate(
        service.add_raid_item(db, project_id, body.kind, body.description, body.severity)
    )


@router.get("/orgs/{org_id}/projects/{project_id}/health", response_model=HealthOut)
def project_health(
    org_id: str,
    project_id: str,
    user: User = Depends(require(Permission.DELIVERY_READ)),
    db: Session = Depends(get_db),
) -> HealthOut:
    project = _project_or_404(db, user, org_id, project_id)
    health = service.project_health(db, project_id)
    risk = service.delivery_risk(health, project.target_date, date.today())
    return HealthOut(
        project=ProjectOut.model_validate(project), health=health, risk=RiskOut(**risk)
    )


@router.post("/orgs/{org_id}/projects/{project_id}/status-report", response_model=StatusReportOut)
def status_report(
    org_id: str,
    project_id: str,
    body: StatusReportIn,
    request: Request,
    user: User = Depends(require(Permission.DELIVERY_WRITE)),
    db: Session = Depends(get_db),
) -> StatusReportOut:
    project = _project_or_404(db, user, org_id, project_id)
    try:
        report = service.status_report(
            db,
            org_id,
            user.id,
            project,
            body.model,
            request.app.state.model_router,
            request.app.state.tracer,
        )
    except UnknownModelError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown model {body.model!r}") from None
    health = service.project_health(db, project_id)
    risk = service.delivery_risk(health, project.target_date, date.today())
    return StatusReportOut(
        project=project.name, model=body.model, risk=RiskOut(**risk), report=report
    )
