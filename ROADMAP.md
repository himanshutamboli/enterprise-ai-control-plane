# Roadmap

## Phases

| Phase | Focus | Status |
|---|---|---|
| 1 | AI engineering portfolio (7 repos) — prior experience this builds on | ✅ done |
| 2 | **Control-plane core** — the vertical slice below | 🟡 in progress |
| 3 | Optional first-party modules (agents, knowledge, governance, SDLC) | ⚪ later |
| 4 | OSS toolkit & extensions (consulting toolkit, starter kit, MCP) | ⚪ later |
| 5 | Commercial/SaaS packaging — **only if it earns it** | ⚪ maybe |

Phases 3–5 are deliberately vague: they exist so the ambition is recorded, not so we build them
soon. The full candidate list lives in [docs/MODULE_CATALOG.md](docs/MODULE_CATALOG.md).

## Phase 2 milestones (the vertical slice)

Each milestone is one focused step: PRD → design → implement → tests → docs/ADR → CI-green commit.

- **M0 — Foundation** ✅ — repo, tooling, CI, module registry, long-term-memory docs, module catalog.
- **M1 — Platform Core** ✅ — FastAPI app factory, Pydantic settings, `Organization`/`User`
  (SQLAlchemy 2.0), RBAC (roles → permissions), multi-tenant isolation, `X-API-Key` auth with
  open tenant signup, and `/health`. Postgres via `database_url`; SQLite by default + in tests.
- **M2 — AI Gateway** ✅ — `Provider` protocol + `MockProvider` (CI default) + `AnthropicProvider`
  drop-in; `ModelRouter`; per-call cost metering persisted as `GatewayCall`; `POST /v1/complete`
  (gated by `gateway:invoke`) and `GET /orgs/{id}/usage`.
- **M3 — Prompt Registry** ✅ — versioned, tenant-scoped prompts (auto-incrementing immutable
  versions), retrieval by name/version, variable rendering, and a `render` endpoint; the gateway
  can run a registered prompt by reference and records the prompt name/version on each call.
- **M4 — Evaluation Engine** ✅ — `Evaluator` protocol + CI-safe defaults (exact-match / contains
  / non-empty); run a dataset through the gateway, score each output, persist an `EvalRun` +
  per-item results with mean-score / pass-rate; run/list/detail endpoints. Eval traffic is metered
  through the gateway.
- **M5 — Observability** ✅ — a `Tracer` (context-manager `trace`/`span`/`set_output`, the
  `llm-observatory` shape) that persists traces + spans via its own session; the gateway and eval
  routes are auto-instrumented; tenant-scoped `traces` list + detail endpoints.
- **M6 — Operator Dashboard** — a thin UI over cost/evals/traces.
- **M7 — Tower integration (optional)** — expose a read API; point the existing Control Tower at
  live data.

## Definition of done (per module)

Tests green in CI · lint/format clean · a short section in ARCHITECTURE or its own doc · an ADR
if a real decision was made · CHANGELOG updated · the module registry status flipped to
`available`.
