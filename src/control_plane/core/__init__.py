"""Platform core: organizations, users, RBAC, config, and the FastAPI app factory.

The backbone every other module plugs into. Multi-tenant by construction — every user belongs
to an organization, and access is gated by role-based permissions plus tenant isolation.
"""
