"""Recording and summarizing gateway usage."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from control_plane.gateway.models import GatewayCall
from control_plane.gateway.providers import CompletionResponse


def record_call(
    db: Session, org_id: str, user_id: str, resp: CompletionResponse, latency_ms: int
) -> GatewayCall:
    call = GatewayCall(
        org_id=org_id,
        user_id=user_id,
        model=resp.model,
        provider=resp.provider,
        prompt_tokens=resp.prompt_tokens,
        completion_tokens=resp.completion_tokens,
        cost_usd=resp.cost_usd,
        latency_ms=latency_ms,
    )
    db.add(call)
    db.commit()
    return call


def usage_summary(db: Session, org_id: str) -> dict:
    rows = db.execute(
        select(
            GatewayCall.model,
            func.count().label("calls"),
            func.coalesce(func.sum(GatewayCall.cost_usd), 0.0),
            func.coalesce(func.sum(GatewayCall.prompt_tokens + GatewayCall.completion_tokens), 0),
        )
        .where(GatewayCall.org_id == org_id)
        .group_by(GatewayCall.model)
    ).all()
    by_model = [
        {"model": m, "calls": int(c), "cost_usd": round(float(cost), 6), "tokens": int(tok)}
        for m, c, cost, tok in rows
    ]
    return {
        "total_calls": sum(x["calls"] for x in by_model),
        "total_cost_usd": round(sum(x["cost_usd"] for x in by_model), 6),
        "total_tokens": sum(x["tokens"] for x in by_model),
        "by_model": sorted(by_model, key=lambda x: x["cost_usd"], reverse=True),
    }
