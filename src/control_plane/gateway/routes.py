"""Gateway API: governed model completion + per-tenant usage."""

from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.gateway import service
from control_plane.gateway.providers import CompletionRequest
from control_plane.gateway.router import UnknownModelError
from control_plane.gateway.schemas import CompleteIn, CompleteOut, UsageOut
from control_plane.prompts import service as prompt_service

router = APIRouter()


def _resolve_prompt(db: Session, org_id: str, body: CompleteIn) -> tuple[str, int | None]:
    """Return (prompt_text, prompt_version). Renders a registered prompt if referenced."""
    if body.prompt:
        return body.prompt, None
    prompt = prompt_service.get_prompt(db, org_id, body.prompt_name, body.prompt_version)
    if prompt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"prompt {body.prompt_name!r} not found")
    try:
        text = prompt_service.render_template(prompt.template, body.variables)
    except prompt_service.MissingVariablesError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None
    return text, prompt.version


@router.post("/v1/complete", response_model=CompleteOut)
def complete(
    body: CompleteIn,
    request: Request,
    user: User = Depends(require(Permission.GATEWAY_INVOKE)),
    db: Session = Depends(get_db),
) -> CompleteOut:
    model_router = request.app.state.model_router
    try:
        provider = model_router.resolve(body.model)
    except UnknownModelError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"unknown model {body.model!r}; available: {model_router.models()}",
        ) from None

    prompt_text, prompt_version = _resolve_prompt(db, user.org_id, body)
    tracer = request.app.state.tracer
    started = perf_counter()
    with tracer.trace("gateway.complete", user.org_id, user.id) as trace:
        with trace.span(f"complete:{body.model}", kind="llm", input=prompt_text[:1000]) as span:
            resp = provider.complete(
                CompletionRequest(body.model, prompt_text, body.max_tokens, body.system)
            )
            span.set_output(resp.text[:1000])
    latency_ms = int((perf_counter() - started) * 1000)
    service.record_call(
        db, user.org_id, user.id, resp, latency_ms, body.prompt_name, prompt_version
    )
    return CompleteOut.model_validate(resp, from_attributes=True)


@router.get("/orgs/{org_id}/usage", response_model=UsageOut)
def usage(
    org_id: str,
    user: User = Depends(require(Permission.ORG_READ)),
    db: Session = Depends(get_db),
) -> UsageOut:
    ensure_tenant(user, org_id)
    return UsageOut.model_validate(service.usage_summary(db, org_id))
