"""Prompt registry API: save (new version), list, fetch, render — all tenant-scoped."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.prompts import service
from control_plane.prompts.schemas import PromptCreate, PromptOut, RenderIn, RenderOut

router = APIRouter()


def _fetch(db: Session, org_id: str, name: str, version: int | None):
    prompt = service.get_prompt(db, org_id, name, version)
    if prompt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"prompt {name!r} not found")
    return prompt


@router.post(
    "/orgs/{org_id}/prompts", response_model=PromptOut, status_code=status.HTTP_201_CREATED
)
def create_prompt(
    org_id: str,
    body: PromptCreate,
    user: User = Depends(require(Permission.PROMPT_WRITE)),
    db: Session = Depends(get_db),
) -> PromptOut:
    ensure_tenant(user, org_id)
    prompt = service.save_prompt(db, org_id, body.name, body.template)
    return PromptOut.model_validate(prompt)


@router.get("/orgs/{org_id}/prompts", response_model=list[PromptOut])
def list_prompts(
    org_id: str,
    user: User = Depends(require(Permission.PROMPT_READ)),
    db: Session = Depends(get_db),
) -> list[PromptOut]:
    ensure_tenant(user, org_id)
    return [PromptOut.model_validate(p) for p in service.list_prompts(db, org_id)]


@router.get("/orgs/{org_id}/prompts/{name}", response_model=PromptOut)
def get_prompt(
    org_id: str,
    name: str,
    version: int | None = None,
    user: User = Depends(require(Permission.PROMPT_READ)),
    db: Session = Depends(get_db),
) -> PromptOut:
    ensure_tenant(user, org_id)
    return PromptOut.model_validate(_fetch(db, org_id, name, version))


@router.post("/orgs/{org_id}/prompts/{name}/render", response_model=RenderOut)
def render_prompt(
    org_id: str,
    name: str,
    body: RenderIn,
    user: User = Depends(require(Permission.PROMPT_READ)),
    db: Session = Depends(get_db),
) -> RenderOut:
    ensure_tenant(user, org_id)
    prompt = _fetch(db, org_id, name, body.version)
    try:
        text = service.render_template(prompt.template, body.variables)
    except service.MissingVariablesError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None
    return RenderOut(name=prompt.name, version=prompt.version, text=text)
