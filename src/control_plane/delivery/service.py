"""Delivery operations: CRUD, project health, the risk heuristic, and an AI status report."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from control_plane.delivery.models import Project, RaidItem, WorkItem
from control_plane.gateway import service as gateway_service
from control_plane.gateway.providers import CompletionRequest
from control_plane.gateway.router import ModelRouter

# --- CRUD ---------------------------------------------------------------------------------


def create_project(db: Session, org_id: str, name: str, target_date: date | None) -> Project:
    project = Project(org_id=org_id, name=name, target_date=target_date)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, org_id: str, project_id: str) -> Project | None:
    project = db.get(Project, project_id)
    return project if project is not None and project.org_id == org_id else None


def list_projects(db: Session, org_id: str) -> list[Project]:
    return list(
        db.scalars(select(Project).where(Project.org_id == org_id).order_by(Project.created_at))
    )


def add_work_item(db: Session, project_id: str, title: str, status: str, points: int) -> WorkItem:
    item = WorkItem(project_id=project_id, title=title, status=status, points=points)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_raid_item(
    db: Session, project_id: str, kind: str, description: str, severity: str
) -> RaidItem:
    item = RaidItem(project_id=project_id, kind=kind, description=description, severity=severity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# --- Health + risk ------------------------------------------------------------------------


def project_health(db: Session, project_id: str) -> dict:
    items = list(db.scalars(select(WorkItem).where(WorkItem.project_id == project_id)))
    by_status = {s: 0 for s in ("todo", "in_progress", "blocked", "done")}
    for it in items:
        by_status[it.status] = by_status.get(it.status, 0) + 1
    points_total = sum(it.points for it in items)
    points_done = sum(it.points for it in items if it.status == "done")

    raids = list(db.scalars(select(RaidItem).where(RaidItem.project_id == project_id)))
    open_raids = [r for r in raids if r.status == "open"]
    return {
        "work_items": len(items),
        "todo": by_status["todo"],
        "in_progress": by_status["in_progress"],
        "blocked": by_status["blocked"],
        "done": by_status["done"],
        "points_total": points_total,
        "points_done": points_done,
        "pct_complete": round(points_done / points_total, 4) if points_total else 0.0,
        "open_raid": len(open_raids),
        "open_high_severity": sum(1 for r in open_raids if r.severity == "high"),
    }


def delivery_risk(health: dict, target_date: date | None, today: date) -> dict:
    """A transparent, deterministic delivery-risk score (0–100) with stated reasons."""
    score = 0.0
    reasons: list[str] = []

    incomplete = 1 - health["pct_complete"]
    score += incomplete * 40
    if incomplete > 0.5 and health["points_total"]:
        reasons.append(f"only {health['pct_complete']:.0%} of scope complete")

    if health["blocked"]:
        score += min(20, health["blocked"] * 7)
        reasons.append(f"{health['blocked']} blocked work item(s)")

    if health["open_high_severity"]:
        score += min(20, health["open_high_severity"] * 10)
        reasons.append(f"{health['open_high_severity']} open high-severity RAID item(s)")

    remaining = health["points_total"] - health["points_done"]
    if target_date and remaining > 0:
        days_left = (target_date - today).days
        if days_left <= 0:
            score += 20
            reasons.append("past target date with work remaining")
        else:
            needed_per_day = remaining / days_left
            score += min(20, needed_per_day * 4)
            if needed_per_day > 3:
                reasons.append(f"needs {needed_per_day:.1f} pts/day to hit the target date")

    final = min(100, round(score))
    level = "red" if final >= 66 else "amber" if final >= 33 else "green"
    if not reasons:
        reasons.append("on track")
    return {"score": final, "level": level, "reasons": reasons}


# --- AI status report ---------------------------------------------------------------------


def _compose_report_prompt(project: Project, health: dict, risk: dict) -> str:
    reasons = "; ".join(risk["reasons"])
    return (
        "Write a concise executive delivery status update.\n"
        f"Project: {project.name} (target {project.target_date})\n"
        f"Progress: {health['pct_complete']:.0%} complete, {health['done']}/{health['work_items']} "
        f"items done, {health['blocked']} blocked.\n"
        f"RAID: {health['open_raid']} open ({health['open_high_severity']} high severity).\n"
        f"Delivery risk: {risk['level'].upper()} ({risk['score']}/100) — {reasons}.\n"
        "Answer:"
    )


def status_report(
    db: Session,
    org_id: str,
    user_id: str,
    project: Project,
    model: str,
    router: ModelRouter,
    tracer,
) -> str:
    health = project_health(db, project.id)
    risk = delivery_risk(health, project.target_date, date.today())
    provider = router.resolve(model)
    prompt = _compose_report_prompt(project, health, risk)
    with tracer.trace("delivery.status_report", org_id, user_id) as trace:
        with trace.span(f"complete:{model}", kind="llm", input=prompt[:1000]) as span:
            resp = provider.complete(CompletionRequest(model=model, prompt=prompt))
            span.set_output(resp.text[:1000])
    gateway_service.record_call(db, org_id, user_id, resp, 0)
    return resp.text
