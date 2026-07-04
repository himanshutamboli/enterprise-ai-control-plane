"""Core API routes: health, tenant signup, org read, user create/list."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane import __version__
from control_plane.core import service
from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.core.schemas import (
    OrgCreate,
    OrgCreateOut,
    OrgOut,
    UserCreate,
    UserCreateOut,
    UserOut,
)

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "environment": request.app.state.settings.environment,
    }


@router.post("/orgs", response_model=OrgCreateOut, status_code=status.HTTP_201_CREATED)
def signup(body: OrgCreate, db: Session = Depends(get_db)) -> OrgCreateOut:
    org, owner = service.create_org_with_owner(db, body.name, body.owner_email, body.owner_name)
    return OrgCreateOut(org=OrgOut.model_validate(org), owner=UserCreateOut.model_validate(owner))


@router.get("/orgs/{org_id}", response_model=OrgOut)
def read_org(
    org_id: str,
    user: User = Depends(require(Permission.ORG_READ)),
    db: Session = Depends(get_db),
) -> OrgOut:
    ensure_tenant(user, org_id)
    org = service.get_org(db, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    return OrgOut.model_validate(org)


@router.post(
    "/orgs/{org_id}/users", response_model=UserCreateOut, status_code=status.HTTP_201_CREATED
)
def add_user(
    org_id: str,
    body: UserCreate,
    user: User = Depends(require(Permission.USER_MANAGE)),
    db: Session = Depends(get_db),
) -> UserCreateOut:
    ensure_tenant(user, org_id)
    if service.user_exists(db, org_id, body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "user with this email already exists")
    created = service.create_user(db, org_id, body.email, body.name, body.role.value)
    return UserCreateOut.model_validate(created)


@router.get("/orgs/{org_id}/users", response_model=list[UserOut])
def list_org_users(
    org_id: str,
    user: User = Depends(require(Permission.USER_READ)),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    ensure_tenant(user, org_id)
    return [UserOut.model_validate(u) for u in service.list_users(db, org_id)]
