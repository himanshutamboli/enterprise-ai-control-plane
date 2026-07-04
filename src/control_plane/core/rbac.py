"""Role-based access control: roles, permissions, and the role→permission mapping.

Deliberately simple and static (no permission tables): four roles, a small permission set, and a
pure `has_permission` check. Enough to gate the API and grow with the platform.
"""

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(StrEnum):
    ORG_READ = "org:read"
    ORG_MANAGE = "org:manage"
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    GATEWAY_INVOKE = "gateway:invoke"  # AI Gateway module (M2)
    PROMPT_READ = "prompt:read"  # Prompt Registry module (M3)
    PROMPT_WRITE = "prompt:write"
    EVAL_RUN = "eval:run"  # Evaluation Engine module (M4)
    EVAL_READ = "eval:read"
    OBS_READ = "obs:read"  # Observability module (M5)
    AGENT_READ = "agent:read"  # Agent Builder module (M8)
    AGENT_WRITE = "agent:write"
    AGENT_RUN = "agent:run"
    DELIVERY_READ = "delivery:read"  # AI Delivery Manager module (M9)
    DELIVERY_WRITE = "delivery:write"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),  # everything
    Role.ADMIN: {
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.USER_MANAGE,
        Permission.GATEWAY_INVOKE,
        Permission.PROMPT_READ,
        Permission.PROMPT_WRITE,
        Permission.EVAL_RUN,
        Permission.EVAL_READ,
        Permission.OBS_READ,
        Permission.AGENT_READ,
        Permission.AGENT_WRITE,
        Permission.AGENT_RUN,
        Permission.DELIVERY_READ,
        Permission.DELIVERY_WRITE,
    },
    Role.MEMBER: {
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.GATEWAY_INVOKE,
        Permission.PROMPT_READ,
        Permission.EVAL_RUN,
        Permission.EVAL_READ,
        Permission.OBS_READ,
        Permission.AGENT_READ,
        Permission.AGENT_RUN,
        Permission.DELIVERY_READ,
        Permission.DELIVERY_WRITE,
    },
    Role.VIEWER: {
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.PROMPT_READ,
        Permission.EVAL_READ,
        Permission.OBS_READ,
        Permission.AGENT_READ,
        Permission.DELIVERY_READ,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    try:
        resolved = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(resolved, set())
