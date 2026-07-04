"""Prompt registry operations: save (auto-version), retrieve, list, and render."""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from control_plane.prompts.models import Prompt

_PLACEHOLDER = re.compile(r"{(\w+)}")


class MissingVariablesError(ValueError):
    """Rendering was attempted without all placeholders supplied."""

    def __init__(self, missing: set[str]) -> None:
        self.missing = sorted(missing)
        super().__init__(f"missing variables: {self.missing}")


def placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER.findall(template))


def render_template(template: str, variables: dict) -> str:
    missing = placeholders(template) - set(variables or {})
    if missing:
        raise MissingVariablesError(missing)
    return template.format_map(variables or {})


def _next_version(db: Session, org_id: str, name: str) -> int:
    current = db.scalar(
        select(func.max(Prompt.version)).where(Prompt.org_id == org_id, Prompt.name == name)
    )
    return (current or 0) + 1


def save_prompt(db: Session, org_id: str, name: str, template: str) -> Prompt:
    """Create the next immutable version of a named prompt."""
    prompt = Prompt(
        org_id=org_id, name=name, version=_next_version(db, org_id, name), template=template
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def get_prompt(db: Session, org_id: str, name: str, version: int | None = None) -> Prompt | None:
    stmt = select(Prompt).where(Prompt.org_id == org_id, Prompt.name == name)
    if version is None:
        stmt = stmt.order_by(Prompt.version.desc()).limit(1)
    else:
        stmt = stmt.where(Prompt.version == version)
    return db.scalar(stmt)


def list_prompts(db: Session, org_id: str) -> list[Prompt]:
    return list(
        db.scalars(
            select(Prompt).where(Prompt.org_id == org_id).order_by(Prompt.name, Prompt.version)
        )
    )
