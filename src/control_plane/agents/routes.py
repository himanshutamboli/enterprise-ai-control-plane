"""Agent Builder API: define agents, list them, run them, list runs, list tools."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from control_plane.agents import service
from control_plane.agents.schemas import AgentCreate, AgentOut, AgentRunIn, AgentRunOut
from control_plane.agents.tools import tool_names, tool_specs
from control_plane.core.deps import ensure_tenant, get_db, require
from control_plane.core.models import User
from control_plane.core.rbac import Permission
from control_plane.gateway.router import UnknownModelError

router = APIRouter()


@router.get("/orgs/{org_id}/agent-tools")
def available_tools(
    org_id: str,
    user: User = Depends(require(Permission.AGENT_READ)),
) -> list[dict]:
    ensure_tenant(user, org_id)
    return tool_specs()


@router.post("/orgs/{org_id}/agents", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
def create_agent(
    org_id: str,
    body: AgentCreate,
    user: User = Depends(require(Permission.AGENT_WRITE)),
    db: Session = Depends(get_db),
) -> AgentOut:
    ensure_tenant(user, org_id)
    unknown = [t for t in body.tools if t not in tool_names()]
    if unknown:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"unknown tools {unknown}; available: {tool_names()}"
        )
    agent = service.save_agent(
        db, org_id, body.name, body.model, body.system_prompt, body.tools, body.max_steps
    )
    return AgentOut.model_validate(agent)


@router.get("/orgs/{org_id}/agents", response_model=list[AgentOut])
def list_agents(
    org_id: str,
    user: User = Depends(require(Permission.AGENT_READ)),
    db: Session = Depends(get_db),
) -> list[AgentOut]:
    ensure_tenant(user, org_id)
    return [AgentOut.model_validate(a) for a in service.list_agents(db, org_id)]


@router.get("/orgs/{org_id}/agents/{name}", response_model=AgentOut)
def get_agent(
    org_id: str,
    name: str,
    version: int | None = None,
    user: User = Depends(require(Permission.AGENT_READ)),
    db: Session = Depends(get_db),
) -> AgentOut:
    ensure_tenant(user, org_id)
    agent = service.get_agent(db, org_id, name, version)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"agent {name!r} not found")
    return AgentOut.model_validate(agent)


@router.post(
    "/orgs/{org_id}/agents/{name}/run",
    response_model=AgentRunOut,
    status_code=status.HTTP_201_CREATED,
)
def run_agent(
    org_id: str,
    name: str,
    body: AgentRunIn,
    request: Request,
    user: User = Depends(require(Permission.AGENT_RUN)),
    db: Session = Depends(get_db),
) -> AgentRunOut:
    ensure_tenant(user, org_id)
    agent = service.get_agent(db, org_id, name, body.version)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"agent {name!r} not found")
    try:
        run = service.run_agent(
            db,
            org_id,
            user.id,
            agent,
            body.input,
            request.app.state.model_router,
            request.app.state.tracer,
        )
    except UnknownModelError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"agent's model {agent.model!r} is not available"
        ) from None
    return AgentRunOut.model_validate(run)


@router.get("/orgs/{org_id}/agents/{name}/runs", response_model=list[AgentRunOut])
def list_runs(
    org_id: str,
    name: str,
    user: User = Depends(require(Permission.AGENT_READ)),
    db: Session = Depends(get_db),
) -> list[AgentRunOut]:
    ensure_tenant(user, org_id)
    return [AgentRunOut.model_validate(r) for r in service.list_runs(db, org_id, name)]
