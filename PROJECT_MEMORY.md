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
- **M2 — AI Gateway: done.** `control_plane.gateway`: `Provider` protocol + `MockProvider` (CI
  default) + `AnthropicProvider` drop-in; `ModelRouter` (default routes all models → mock); token
  price table + `estimate_cost`; `GatewayCall` model; `record_call`/`usage_summary`; `POST
  /v1/complete` (gated by `gateway:invoke`) + `GET /orgs/{id}/usage`. Refactored to shared
  `core.deps` + per-module `APIRouter`s composed in `core.api.create_app`; `app.state.model_router`
  is swappable. 21 tests, live-smoke verified. ADR-0003.
- **M3 — Prompt Registry: done.** `control_plane.prompts`: `Prompt` model (immutable versions,
  unique org+name+version); service (`save_prompt` auto-versions, `get_prompt`, `list_prompts`,
  `render_template` with variable validation); routes to save/list/fetch/render. New
  `prompt:read`/`prompt:write` perms. Gateway `/v1/complete` accepts `prompt_name`(+version,
  variables), renders the registered prompt, and records `prompt_name`/`prompt_version` on the
  `GatewayCall`. 28 tests, live-smoke verified. ADR-0004.
- **M4 — Evaluation Engine: done.** `control_plane.evals`: `Evaluator` protocol + defaults
  (exact_match/contains/non_empty); `EvalRun` + `EvalItemResult` models; `run_eval` runs a dataset
  through the gateway (metered via `record_call`), scores, persists, aggregates mean-score/pass-rate;
  run/list/detail routes; `eval:run`/`eval:read` perms. 34 tests. ADR-0005.
- **Next: M5 — Observability.** Trace gateway (and eval) calls with a `Tracer` matching the
  `llm-observatory` shape; expose traces per tenant. Then M6 operator dashboard.

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
