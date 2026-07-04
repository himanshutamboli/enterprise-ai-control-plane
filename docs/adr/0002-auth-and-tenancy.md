# ADR-0002: API-key auth, open tenant signup, and static RBAC

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** M1 needs authentication, multi-tenancy, and access control for the platform core,
  without over-building for a career-signal-first project.

## Decisions

1. **`X-API-Key` header auth.** Each user has an opaque `cp_…` key; a request resolves to a user
   by key. Simple, stateless, and enough to demonstrate authn/authz cleanly. JWT/OAuth/SSO are a
   later concern behind the same `current_user` seam.
2. **Open tenant signup via `POST /orgs`.** Creating an org also creates its first **owner** and
   returns that owner's key once — resolving the bootstrap chicken-and-egg (you need a principal
   to create users, but the first org has none). Mirrors real SaaS signup.
3. **Static role→permission RBAC.** Four roles (owner/admin/member/viewer) map to a small
   permission set in code (`rbac.py`) — no permission tables. A pure `has_permission` check gates
   every protected route.
4. **Tenant isolation is explicit.** Beyond permissions, each route verifies the caller's
   `org_id` matches the path's org — a member of one tenant cannot touch another, even with a
   valid key and role.

## Consequences

- Clean, fully-offline-testable auth (no external IdP) with a clear upgrade path.
- API keys are shown only at creation and never returned in listings.
- Static RBAC is easy to reason about; if per-resource or custom roles are ever needed, migrate
  to a permission model then — not before.
- `create_all` builds the schema for now; Alembic migrations land before the schema churns.
