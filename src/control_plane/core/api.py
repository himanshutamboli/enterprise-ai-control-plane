"""The FastAPI application factory + core routes (orgs, users, health).

Auth is via an ``X-API-Key`` header that resolves to a user; ``POST /orgs`` is the open
tenant-signup endpoint (creates an org + owner and returns the owner's key once). Every other
route requires a key, an RBAC permission, and belonging to the tenant in the path.

Serve with:  uv run uvicorn control_plane.core.api:app
"""

from collections.abc import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from control_plane import __version__
from control_plane.core import service
from control_plane.core.config import Settings, get_settings
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.core.models import User
from control_plane.core.rbac import Permission, has_permission
from control_plane.core.schemas import (
    OrgCreate,
    OrgCreateOut,
    OrgOut,
    UserCreate,
    UserCreateOut,
    UserOut,
)


def create_app(
    session_factory: sessionmaker[Session] | None = None, settings: Settings | None = None
) -> FastAPI:
    settings = settings or get_settings()
    if session_factory is None:
        engine = make_engine(settings.database_url)
        init_db(engine)
        session_factory = make_session_factory(engine)

    app = FastAPI(title=settings.app_name, version=__version__)
    app.state.session_factory = session_factory
    app.state.settings = settings

    def get_db() -> Iterator[Session]:
        with session_factory() as db:
            yield db

    def current_user(
        x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)
    ) -> User:
        if not x_api_key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing X-API-Key")
        user = service.get_user_by_api_key(db, x_api_key)
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
        return user

    def require(permission: Permission):
        def dependency(user: User = Depends(current_user)) -> User:
            if not has_permission(user.role, permission):
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires permission {permission}")
            return user

        return dependency

    def ensure_tenant(user: User, org_id: str) -> None:
        if user.org_id != org_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "cross-tenant access denied")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__, "environment": settings.environment}

    @app.post("/orgs", response_model=OrgCreateOut, status_code=status.HTTP_201_CREATED)
    def signup(body: OrgCreate, db: Session = Depends(get_db)) -> OrgCreateOut:
        org, owner = service.create_org_with_owner(db, body.name, body.owner_email, body.owner_name)
        return OrgCreateOut(
            org=OrgOut.model_validate(org), owner=UserCreateOut.model_validate(owner)
        )

    @app.get("/orgs/{org_id}", response_model=OrgOut)
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

    @app.post(
        "/orgs/{org_id}/users",
        response_model=UserCreateOut,
        status_code=status.HTTP_201_CREATED,
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

    @app.get("/orgs/{org_id}/users", response_model=list[UserOut])
    def list_org_users(
        org_id: str,
        user: User = Depends(require(Permission.USER_READ)),
        db: Session = Depends(get_db),
    ) -> list[UserOut]:
        ensure_tenant(user, org_id)
        return [UserOut.model_validate(u) for u in service.list_users(db, org_id)]

    return app


app = create_app()  # module-level instance for `uvicorn control_plane.core.api:app`
