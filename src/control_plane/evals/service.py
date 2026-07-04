"""Run a dataset through the gateway and score each output."""

from collections.abc import Sequence
from time import perf_counter
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from control_plane.evals.evaluators import get_evaluator
from control_plane.evals.models import EvalItemResult, EvalRun
from control_plane.gateway import service as gateway_service
from control_plane.gateway.providers import CompletionRequest
from control_plane.gateway.router import ModelRouter


class _Item(Protocol):
    prompt: str
    expected: str | None


def run_eval(
    db: Session,
    org_id: str,
    user_id: str,
    model: str,
    evaluator_name: str,
    items: Sequence[_Item],
    router: ModelRouter,
) -> EvalRun:
    evaluator = get_evaluator(evaluator_name)  # KeyError → unknown evaluator
    provider = router.resolve(model)  # UnknownModelError → unknown model

    run = EvalRun(
        org_id=org_id,
        user_id=user_id,
        model=model,
        evaluator=evaluator_name,
        dataset_size=len(items),
    )
    db.add(run)
    db.flush()

    total_score, total_passed = 0.0, 0
    for idx, item in enumerate(items):
        started = perf_counter()
        resp = provider.complete(CompletionRequest(model=model, prompt=item.prompt))
        latency_ms = int((perf_counter() - started) * 1000)
        gateway_service.record_call(db, org_id, user_id, resp, latency_ms)  # meter eval traffic too
        score = evaluator.evaluate(resp.text, item.expected)
        db.add(
            EvalItemResult(
                run_id=run.id,
                idx=idx,
                input=item.prompt,
                expected=item.expected,
                output=resp.text,
                score=score.score,
                passed=score.passed,
            )
        )
        total_score += score.score
        total_passed += int(score.passed)

    n = len(items)
    run.mean_score = round(total_score / n, 4)
    run.pass_rate = round(total_passed / n, 4)
    db.commit()
    db.refresh(run)
    return run


def list_runs(db: Session, org_id: str) -> list[EvalRun]:
    return list(
        db.scalars(
            select(EvalRun).where(EvalRun.org_id == org_id).order_by(EvalRun.created_at.desc())
        )
    )


def get_run(db: Session, org_id: str, run_id: str) -> EvalRun | None:
    run = db.get(EvalRun, run_id)
    return run if run is not None and run.org_id == org_id else None
