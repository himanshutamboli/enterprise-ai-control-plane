"""Agent definitions + the planner/executor run loop (governed, traced, metered)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from control_plane.agents.models import AgentDef, AgentRun
from control_plane.agents.planner import SequentialPlanner
from control_plane.agents.tools import get_tool
from control_plane.gateway import service as gateway_service
from control_plane.gateway.providers import CompletionRequest
from control_plane.gateway.router import ModelRouter


def _next_version(db: Session, org_id: str, name: str) -> int:
    current = db.scalar(
        select(func.max(AgentDef.version)).where(AgentDef.org_id == org_id, AgentDef.name == name)
    )
    return (current or 0) + 1


def save_agent(
    db: Session,
    org_id: str,
    name: str,
    model: str,
    system_prompt: str,
    tools: list[str],
    max_steps: int,
) -> AgentDef:
    agent = AgentDef(
        org_id=org_id,
        name=name,
        version=_next_version(db, org_id, name),
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        max_steps=max_steps,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def get_agent(db: Session, org_id: str, name: str, version: int | None = None) -> AgentDef | None:
    stmt = select(AgentDef).where(AgentDef.org_id == org_id, AgentDef.name == name)
    stmt = (
        stmt.where(AgentDef.version == version)
        if version
        else stmt.order_by(AgentDef.version.desc()).limit(1)
    )
    return db.scalar(stmt)


def list_agents(db: Session, org_id: str) -> list[AgentDef]:
    return list(
        db.scalars(
            select(AgentDef)
            .where(AgentDef.org_id == org_id)
            .order_by(AgentDef.name, AgentDef.version)
        )
    )


def list_runs(db: Session, org_id: str, name: str) -> list[AgentRun]:
    return list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.org_id == org_id, AgentRun.agent_name == name)
            .order_by(AgentRun.created_at.desc())
        )
    )


def _compose(system_prompt: str, text: str, steps: list[dict]) -> str:
    lines = [system_prompt, f"\nUser: {text}"]
    if steps:
        lines.append("\nTool results:")
        lines += [f"- {s['tool']}: {s['observation']}" for s in steps]
    lines.append("\nAnswer:")
    return "\n".join(lines)


def run_agent(
    db: Session,
    org_id: str,
    user_id: str,
    agent: AgentDef,
    text: str,
    router: ModelRouter,
    tracer,
) -> AgentRun:
    """Bounded planner/executor loop: run tools (≤ max_steps), then compose a final answer."""
    provider = router.resolve(agent.model)  # UnknownModelError → unknown model
    planner = SequentialPlanner()
    used: set[str] = set()
    steps: list[dict] = []

    with tracer.trace("agent.run", org_id, user_id) as trace:
        for _ in range(agent.max_steps):  # the guardrail: never exceed the step budget
            action = planner.next_action(agent.tools, used)
            if action.kind == "finish":
                break
            tool = get_tool(action.tool)
            with trace.span(f"tool:{tool.name}", kind="tool", input=text[:500]) as span:
                observation = tool.run(text)
                span.set_output(observation)
            used.add(action.tool)
            steps.append({"tool": action.tool, "observation": observation})

        prompt = _compose(agent.system_prompt, text, steps)
        with trace.span(f"complete:{agent.model}", kind="llm", input=prompt[:1000]) as span:
            resp = provider.complete(CompletionRequest(model=agent.model, prompt=prompt))
            span.set_output(resp.text[:1000])

    gateway_service.record_call(db, org_id, user_id, resp, 0)
    run = AgentRun(
        org_id=org_id,
        user_id=user_id,
        agent_name=agent.name,
        agent_version=agent.version,
        input=text,
        output=resp.text,
        status="ok",
        steps=steps,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
