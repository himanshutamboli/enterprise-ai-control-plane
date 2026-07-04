# ADR-0007: Operator dashboard — direct reads, optional UI deps

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** M6 gives the platform an operator (platform-admin) view. It needs to be demoable and
  shouldn't burden the API/runtime with UI dependencies.

## Decisions

1. **Operator view reads directly, cross-tenant.** Unlike the tenant-scoped API, the dashboard is
   the platform-owner's view across all orgs. It queries the same database via a pure data module
   (`dashboard.data`) rather than calling the HTTP API — simpler, and no auth juggling for an
   internal console.
2. **UI logic split from query logic.** `dashboard/data.py` has zero UI imports (SQLAlchemy only),
   so the operator queries and the demo seed are unit-tested in CI. The Streamlit app
   (`dashboard.py`) is a thin rendering layer on top.
3. **UI deps are optional.** `streamlit`/`plotly` live in a `dashboard` dependency group, not the
   runtime deps — the API image and CI stay lean (`uv sync --dev`); the dashboard is
   `uv sync --group dashboard`.
4. **Self-seeding demo.** On first run the dashboard seeds a demo org with a week of gateway calls
   (backdated for a real cost trend), an eval run, and traces — so it renders something meaningful
   with zero setup, mirroring the other repos' demo ergonomics.

## Consequences

- The platform has an operator console without coupling the backend to a UI framework.
- Cross-tenant reads are intentional here and deliberately *not* exposed through the tenant API.
- Reading the DB directly (vs the API) means the dashboard trusts its process; if a hosted,
  multi-user operator console is ever needed, it would move behind the API with an admin scope.
- Backdated seed timestamps use wall-clock `now`; fine for a demo (tests assert shape, not dates).
