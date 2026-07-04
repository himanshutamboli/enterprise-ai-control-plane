# Project Memory

The long-term memory of this project — updated as work lands, and the anchor for handoffs
between sessions. Keep it short and current; detail lives in the linked docs.

## What this is

`enterprise-ai-control-plane` — a modular-monolith backend platform for running enterprise AI
(core/gateway/prompts/evals/observability/dashboard). Phase 2 of a longer arc; Phase 1 was a
7-repo AI portfolio. Primary goal: **career/portfolio signal** (Staff/Principal + AI-product).

## Current state

- **M0 — Foundation: done.** Repo scaffolded (uv/ruff/pytest/pre-commit/CI, Python 3.13, `src/`
  layout, MIT). Module registry in `control_plane/app.py` (`uv run control-plane` prints it).
  Long-term-memory docs written: VISION, ARCHITECTURE, ROADMAP, MODULE_CATALOG, this file,
  CHANGELOG, ADR-0001. 2 tests, CI green.
- **Next: M1 — Platform Core.** FastAPI app factory + Pydantic settings + `Organization`/`User`
  + RBAC + `/health`. SQLAlchemy/Postgres (SQLite in tests).

## Key decisions (see docs/adr/)

- Modular monolith, not microservices (solo builder; split later only if earned).
- Integrate the existing Phase-1 flagships as modules; don't rebuild them.
- Control **Plane** (this backend) is separate from the existing Control **Tower** (Next.js UI);
  wire them together only in a later, optional milestone.
- Minimal *living* docs, not a 26-file process bible; add an ADR per real decision.
- Every external dependency behind a Protocol + CI-safe default + optional real drop-in.

## Conventions

- Per-module loop: short PRD → design → implement → tests → docs/ADR → CI-green commit.
- LLM drop-ins target Anthropic `claude-opus-4-8`, lazy-imported.
- Author runs all git/terminal commands and pushes (no gh CLI); create the GitHub repo before
  first push.

## Open tasks / next actions

1. M1 Platform Core (see ROADMAP milestones).
2. Create the GitHub repo `enterprise-ai-control-plane` and push M0.

## Risks / watch-items

- Scope creep from the 20-idea catalog — resist; build the Core slice deep before breadth.
- Don't let commercialization/SaaS framing drive near-term engineering.
