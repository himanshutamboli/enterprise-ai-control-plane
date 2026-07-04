"""Domain operations for organizations and users (persistence-facing, framework-agnostic)."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from control_plane.core.models import Organization, User
from control_plane.core.rbac import Role


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "org"


def _unique_slug(db: Session, base: str) -> str:
    slug, n = base, 1
    while db.scalar(select(Organization).where(Organization.slug == slug)) is not None:
        n += 1
        slug = f"{base}-{n}"
    return slug


def create_org_with_owner(
    db: Session, name: str, owner_email: str, owner_name: str
) -> tuple[Organization, User]:
    """Tenant signup: create the org and its first user (an owner)."""
    org = Organization(name=name, slug=_unique_slug(db, _slugify(name)))
    db.add(org)
    db.flush()
    owner = User(org_id=org.id, email=owner_email, name=owner_name, role=Role.OWNER.value)
    db.add(owner)
    db.commit()
    db.refresh(org)
    db.refresh(owner)
    return org, owner


def create_user(db: Session, org_id: str, email: str, name: str, role: str) -> User:
    user = User(org_id=org_id, email=email, name=name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_org(db: Session, org_id: str) -> Organization | None:
    return db.get(Organization, org_id)


def list_users(db: Session, org_id: str) -> list[User]:
    return list(db.scalars(select(User).where(User.org_id == org_id)))


def get_user_by_api_key(db: Session, api_key: str) -> User | None:
    return db.scalar(select(User).where(User.api_key == api_key))


def user_exists(db: Session, org_id: str, email: str) -> bool:
    return db.scalar(select(User).where(User.org_id == org_id, User.email == email)) is not None
