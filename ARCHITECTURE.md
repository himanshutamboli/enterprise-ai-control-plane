# Architecture

## Shape: a modular monolith

One deployable FastAPI application composed of independent modules with clean boundaries. A
monolith (not microservices) because a solo builder gets 90% of the "platform" signal with 10%
of the operational cost — and modules can be split into services later *if they earn it*. Each
module owns its domain, exposes a small interface, and is independently testable.

```
                         ┌──────────────────────── FastAPI app ────────────────────────┐
   client ──▶ API ──▶    │  core (orgs · users · RBAC · config · health)                │
                         │        │                                                     │
                         │   gateway ──▶ model router ──▶ Provider (protocol)           │
                         │        │            │            ├─ MockProvider (CI default)│
                         │   cost metering ◀───┘            └─ Anthropic/OpenAI (opt)   │
                         │   prompts (versioned registry)                               │
                         │   evals (score gateway calls)                                │
                         │   observability (traces/metrics) ── reuses llm-observatory   │
                         └──────────────────────────────────────────────────────────────┘
        stores:  PostgreSQL (relational)   ·   Redis (cache / rate limits, when needed)
```

## Module boundaries

| Module | Owns | Key interface |
|---|---|---|
| `core` | Organizations, users, roles/permissions (RBAC), settings, app factory, health | `create_app()`, `require_permission()` |
| `gateway` | The single entry point for model calls: routing, retries, cost metering | `Provider` protocol, `Gateway.complete()` |
| `prompts` | Versioned prompt templates, retrieval by name/version | `PromptRegistry.get(name, version)` |
| `evals` | Scoring gateway outputs (offline datasets + online sampling) | `Evaluator` protocol, `run_eval()` |
| `observability` | Traces/spans/metrics for every call | `Tracer` (llm-observatory-compatible shape) |
| `dashboard` | Operator view over the above | (frontend) |

## Cross-cutting design pattern

Every place an external dependency exists (LLM provider, DB, tracer) uses the same shape:
**a `Protocol` + a deterministic CI-safe default + an optional real drop-in.** So the whole
platform runs and is fully tested offline; production swaps implementations, not call sites.
LLM drop-ins target Anthropic `claude-opus-4-8` (lazy-imported).

## How the existing repos integrate

Phase 1 repos are not thrown away — they are the reference implementations the modules adopt:

- **[llm-observatory](https://github.com/himanshutamboli/llm-observatory)** → the `observability`
  module (its `Tracer`/writer/data-model pattern).
- **[agentic-workflow](https://github.com/himanshutamboli/agentic-workflow)** → future `agents`
  module (planner/executor + guardrails).
- **[ai-product-analytics](https://github.com/himanshutamboli/ai-product-analytics)** → the cost
  & product-analytics views over gateway/eval data.
- **[rag-knowledge-assistant](https://github.com/himanshutamboli/rag-knowledge-assistant)** →
  future `knowledge` module.

## Control Plane vs. Control Tower

The **Plane** (this repo) is the backend. The **Control Tower** (existing Next.js UI) is the
executive frontend, currently on mock data. A later milestone exposes the Plane's read API and
points the Tower at it — turning the mock dashboards live. Until then, the Tower is untouched.

## Tech stack

Python 3.13 · FastAPI · Pydantic (settings) · SQLAlchemy 2.0 + Alembic (Postgres) · Redis
(optional) · Docker · GitHub Actions. Tooling: `uv`, `ruff` (line-length 100), `pytest`,
`pre-commit`, `src/` layout. Dependencies are added per module as it lands — the foundation
carries none.

## Decisions

Recorded as ADRs in [docs/adr/](docs/adr/). Start with
[ADR-0001](docs/adr/0001-foundation-modular-monolith-and-integration.md).
