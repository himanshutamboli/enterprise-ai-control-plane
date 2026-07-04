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
- **M2 — AI Gateway** — `Provider` protocol + `MockProvider` (CI default) + a model router;
  cost metering per call; `/v1/complete`. Anthropic drop-in behind the protocol.
- **M3 — Prompt Registry** — versioned prompts, retrieval by name/version, used by the gateway.
- **M4 — Evaluation Engine** — score gateway calls (offline datasets + online sampling), reusing
  the eval concepts from `llm-observatory`.
- **M5 — Observability** — trace every gateway call (the `llm-observatory` `Tracer` shape).
- **M6 — Operator Dashboard** — a thin UI over cost/evals/traces.
- **M7 — Tower integration (optional)** — expose a read API; point the existing Control Tower at
  live data.

## Definition of done (per module)

Tests green in CI · lint/format clean · a short section in ARCHITECTURE or its own doc · an ADR
if a real decision was made · CHANGELOG updated · the module registry status flipped to
`available`.
