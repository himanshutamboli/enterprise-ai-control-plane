"""Evaluation API: run an eval over a dataset, list runs, fetch a run's detail."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.evals import service
from control_plane.evals.evaluators import evaluator_names
from control_plane.evals.schemas import EvalRunDetailOut, EvalRunIn, EvalRunOut
from control_plane.gateway.router import UnknownModelError

router = APIRouter()


@router.post(
    "/orgs/{org_id}/evals/run", response_model=EvalRunDetailOut, status_code=status.HTTP_201_CREATED
)
def run_eval(
    org_id: str,
    body: EvalRunIn,
    request: Request,
    user: User = Depends(require(Permission.EVAL_RUN)),
    db: Session = Depends(get_db),
) -> EvalRunDetailOut:
    ensure_tenant(user, org_id)
    try:
        run = service.run_eval(
            db,
            org_id,
            user.id,
            body.model,
            body.evaluator,
            body.items,
            request.app.state.model_router,
        )
    except KeyError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"unknown evaluator; available: {evaluator_names()}"
        ) from None
    except UnknownModelError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown model {body.model!r}") from None
    return EvalRunDetailOut.model_validate(run)


@router.get("/orgs/{org_id}/evals/runs", response_model=list[EvalRunOut])
def list_runs(
    org_id: str,
    user: User = Depends(require(Permission.EVAL_READ)),
    db: Session = Depends(get_db),
) -> list[EvalRunOut]:
    ensure_tenant(user, org_id)
    return [EvalRunOut.model_validate(r) for r in service.list_runs(db, org_id)]


@router.get("/orgs/{org_id}/evals/runs/{run_id}", response_model=EvalRunDetailOut)
def get_run(
    org_id: str,
    run_id: str,
    user: User = Depends(require(Permission.EVAL_READ)),
    db: Session = Depends(get_db),
) -> EvalRunDetailOut:
    ensure_tenant(user, org_id)
    run = service.get_run(db, org_id, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "eval run not found")
    return EvalRunDetailOut.model_validate(run)
