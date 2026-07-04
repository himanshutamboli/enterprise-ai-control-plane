# Project Memory

The long-term memory of this project — updated as work lands, and the anchor for handoffs
between sessions. Keep it short and current; detail lives in the linked docs.

## What this is

`enterprise-ai-control-plane` — a modular-monolith backend platform for running enterprise AI
(core/gateway/prompts/evals/observability/dashboard). Phase 2 of a longer arc; Phase 1 was a
7-repo AI portfolio. Primary goal: **career/portfolio signal** (Staff/Principal + AI-product).

## Current state

- **M0 — Foundation: done.** Scaffold + CI + module registry + long-term-memory docs (ADR-0001).
- **M1 — Platform Core: done.** `control_plane.core`: config (Pydantic settings), db (SQLAlchemy
  2.0, sqlite default / Postgres via `database_url`), models (Organization/User), rbac
  (owner/admin/member/viewer → permissions), schemas, service, and `api.create_app()`. Auth via
  `X-API-Key`; open tenant signup `POST /orgs` (creates org+owner, returns key once); routes for
  org read + user create/list; multi-tenant isolation; `/health`. 14 tests, live-smoke verified.
  ADR-0002. Serve: `uv run uvicorn control_plane.core.api:app`.
- **Next: M2 — AI Gateway.** `Provider` protocol + `MockProvider` (CI default) + model router +
  cost metering; `POST /v1/complete` gated by `gateway:invoke`. Anthropic drop-in behind the
  protocol (`claude-opus-4-8`, lazy import).

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
