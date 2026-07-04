"""Cross-organization read queries + a demo seed for the operator dashboard.

Pure data access (SQLAlchemy only) so it's testable without a UI. These are the *operator*
(platform-admin) views — they intentionally span all tenants, unlike the tenant-scoped API.
"""

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from control_plane.core import service as core_service
from control_plane.core.models import Organization, User
from control_plane.evals import service as eval_service
from control_plane.evals.models import EvalRun
from control_plane.gateway import service as gateway_service
from control_plane.gateway.models import GatewayCall
from control_plane.gateway.providers import CompletionRequest
from control_plane.gateway.router import ModelRouter
from control_plane.observability.models import Trace
from control_plane.prompts import service as prompt_service


def overview(db: Session) -> dict:
    def _count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    total_cost = float(db.scalar(select(func.coalesce(func.sum(GatewayCall.cost_usd), 0.0))) or 0.0)
    return {
        "orgs": _count(Organization),
        "users": _count(User),
        "gateway_calls": _count(GatewayCall),
        "total_cost_usd": round(total_cost, 6),
        "eval_runs": _count(EvalRun),
        "traces": _count(Trace),
    }


def spend_by_model(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            GatewayCall.model,
            func.count().label("calls"),
            func.coalesce(func.sum(GatewayCall.cost_usd), 0.0),
        )
        .group_by(GatewayCall.model)
        .order_by(func.sum(GatewayCall.cost_usd).desc())
    ).all()
    return [{"model": m, "calls": int(c), "cost_usd": round(float(cost), 6)} for m, c, cost in rows]


def spend_by_org(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Organization.name,
            func.count(GatewayCall.id).label("calls"),
            func.coalesce(func.sum(GatewayCall.cost_usd), 0.0),
        )
        .join(GatewayCall, GatewayCall.org_id == Organization.id)
        .group_by(Organization.name)
        .order_by(func.sum(GatewayCall.cost_usd).desc())
    ).all()
    return [{"org": n, "calls": int(c), "cost_usd": round(float(cost), 6)} for n, c, cost in rows]


def daily_cost(db: Session) -> list[dict]:
    day = func.date(GatewayCall.created_at)
    rows = db.execute(
        select(day, func.coalesce(func.sum(GatewayCall.cost_usd), 0.0)).group_by(day).order_by(day)
    ).all()
    return [{"date": str(d), "cost_usd": round(float(cost), 6)} for d, cost in rows]


def recent_traces(db: Session, limit: int = 20) -> list[dict]:
    traces = db.scalars(select(Trace).order_by(Trace.created_at.desc()).limit(limit))
    return [
        {"name": t.name, "status": t.status, "latency_ms": t.latency_ms, "spans": len(t.spans)}
        for t in traces
    ]


def recent_eval_runs(db: Session, limit: int = 20) -> list[dict]:
    runs = db.scalars(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit))
    return [
        {
            "model": r.model,
            "evaluator": r.evaluator,
            "dataset_size": r.dataset_size,
            "mean_score": r.mean_score,
            "pass_rate": r.pass_rate,
        }
        for r in runs
    ]


@dataclass
class _EvalItem:
    prompt: str
    expected: str | None = None


# (model, prompt) run each day of the demo window, so cost/adoption trends over time.
_DEMO_CALLS = [
    ("claude-opus-4-8", "Summarize the Q3 board deck"),
    ("claude-opus-4-8", "Draft a migration plan"),
    ("claude-haiku-4-5", "Classify this support ticket"),
    ("mock-1", "health ping"),
]
_DEMO_DAYS = 7


def seed_demo(session_factory: sessionmaker[Session], router: ModelRouter, tracer) -> bool:
    """Populate a demo org with a week of gateway calls, an eval run, and traces.

    Returns True if it seeded, False if data already existed.
    """
    with session_factory() as db:
        if db.scalar(select(func.count()).select_from(Organization)):
            return False
        org, owner = core_service.create_org_with_owner(db, "Demo Corp", "ops@demo.co", "Ops")
        core_service.create_user(db, org.id, "dev@demo.co", "Dev", "member")
        prompt_service.save_prompt(db, org.id, "summarize", "Summarize for {aud}: {doc}")
        org_id, owner_id = org.id, owner.id

    now = dt.datetime.now(dt.UTC)
    with session_factory() as db:
        for day in range(_DEMO_DAYS):
            ts = now - dt.timedelta(days=_DEMO_DAYS - 1 - day)
            for model, prompt in _DEMO_CALLS:
                provider = router.resolve(model)
                with tracer.trace("gateway.complete", org_id, owner_id) as trace:
                    with trace.span(f"complete:{model}", kind="llm", input=prompt) as span:
                        resp = provider.complete(CompletionRequest(model=model, prompt=prompt))
                        span.set_output(resp.text[:1000])
                gateway_service.record_call(db, org_id, owner_id, resp, 5, created_at=ts)
        eval_service.run_eval(
            db,
            org_id,
            owner_id,
            "claude-opus-4-8",
            "non_empty",
            [_EvalItem("q1"), _EvalItem("q2"), _EvalItem("q3")],
            router,
        )
    return True
