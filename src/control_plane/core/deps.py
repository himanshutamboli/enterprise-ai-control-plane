"""Shared FastAPI dependencies, usable by any module's router.

They read the session factory off ``request.app.state`` (set by the app factory), so modules
don't depend on how the app was constructed — which keeps module routers decoupled and testable.
"""

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane.core import service
from control_plane.core.models import User
from control_plane.core.rbac import Permission, has_permission


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as db:
        yield db


def get_current_user(
    x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)
) -> User:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing X-API-Key")
    user = service.get_user_by_api_key(db, x_api_key)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
    return user


def require(permission: Permission):
    """Dependency factory: require an RBAC permission of the authenticated user."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires permission {permission}")
        return user

    return dependency


def ensure_tenant(user: User, org_id: str) -> None:
    if user.org_id != org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cross-tenant access denied")
