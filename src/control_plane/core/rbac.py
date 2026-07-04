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
    GATEWAY_INVOKE = "gateway:invoke"  # used by the AI Gateway module (M2)


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),  # everything
    Role.ADMIN: {
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.USER_MANAGE,
        Permission.GATEWAY_INVOKE,
    },
    Role.MEMBER: {Permission.ORG_READ, Permission.USER_READ, Permission.GATEWAY_INVOKE},
    Role.VIEWER: {Permission.ORG_READ, Permission.USER_READ},
}


def has_permission(role: str, permission: Permission) -> bool:
    try:
        resolved = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(resolved, set())
