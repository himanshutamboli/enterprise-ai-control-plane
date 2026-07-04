# enterprise-ai-control-plane 🛰️

[![CI](https://github.com/himanshutamboli/enterprise-ai-control-plane/actions/workflows/ci.yml/badge.svg)](https://github.com/himanshutamboli/enterprise-ai-control-plane/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/lint-ruff-orange.svg)](https://github.com/astral-sh/ruff)
[![status](https://img.shields.io/badge/status-building-blue.svg)](ROADMAP.md)

> A modular **control plane for running enterprise AI in production** — organizations & access
> control, an AI gateway (model routing + cost metering), a prompt registry, an evaluation
> engine, and observability — built as a **modular monolith** with clean module boundaries.

This is **Phase 2** of a longer arc. Phase 1 shipped a 7-repo
[AI engineering portfolio](https://github.com/himanshutamboli/ai-portfolio); this repo unifies
that work into one platform: the observability, agent, and product-analytics repos become
first-class **modules** of the control plane rather than standalone demos.

## Control Plane vs. Control Tower

- **Control Plane** (this repo) — the *backend platform*: real services, APIs, data.
- **[Control Tower](https://github.com/himanshutamboli/enterprise-ai-delivery-control-tower)** —
  the existing *executive UI* (a Next.js single-pane-of-glass). A later milestone points it at
  this plane's live API so its dashboards run on real data instead of mocks.

## Modules (the vertical slice)

| Module | Status | What it does |
|---|---|---|
| **core** | ✅ available | Organizations, users, RBAC, tenant isolation, config, app factory, health |
| **gateway** | ✅ available | Provider protocol, model routing, per-call cost metering + usage |
| **prompts** | ✅ available | Versioned prompt registry; gateway can run a prompt by reference |
| **evals** | ✅ available | Score gateway outputs over a dataset (mean-score, pass-rate) |
| **observability** | ✅ available | Traces + spans per gateway/eval call (reuses the `llm-observatory` pattern) |
| **dashboard** | ✅ available | Streamlit operator view (cross-org spend, evals, traces) |

All six core modules are built. Run `uv run control-plane` to print the live module map, or
`uv sync --group dashboard && uv run streamlit run dashboard.py` for the operator dashboard.

## Engineering approach

Every module follows the same bar: a short PRD → architecture sketch → tests → docs/ADR →
CI-green commit. The pervasive pattern is **pluggable protocol + deterministic CI-safe default +
optional real/LLM drop-in**, so the whole platform runs and is tested offline (Anthropic model
`claude-opus-4-8` where an LLM is wired in). Stack: `uv`, `ruff`, `pytest`, `pre-commit`, GitHub
Actions, Python 3.13, `src/` layout; FastAPI + PostgreSQL + Redis as modules land.

## Quickstart

```bash
uv sync --dev
uv run control-plane                              # print the module map
uv run uvicorn control_plane.core.api:app         # serve the platform API (http://localhost:8000/docs)
uv run pytest
```

Tenant signup returns an owner API key; every other call is gated by that key + RBAC + tenant isolation:

```bash
curl -X POST localhost:8000/orgs -H 'content-type: application/json' \
  -d '{"name":"Acme","owner_email":"owner@acme.com","owner_name":"Owner"}'
# → { "org": {...}, "owner": { ..., "api_key": "cp_..." } }
curl localhost:8000/orgs/<org_id>/users -H "X-API-Key: cp_..."

# Governed model call through the gateway (metered), then per-tenant usage:
curl -X POST localhost:8000/v1/complete -H "X-API-Key: cp_..." -H 'content-type: application/json' \
  -d '{"model":"claude-opus-4-8","prompt":"summarize this"}'
curl localhost:8000/orgs/<org_id>/usage -H "X-API-Key: cp_..."
```

The default gateway routes every model to a deterministic offline mock, so it runs and tests
with no API keys; register a real `AnthropicProvider` behind the same interface per deployment.

```bash
# Register a versioned prompt, then run it through the gateway by reference (usage ties to the version):
curl -X POST localhost:8000/orgs/<org_id>/prompts -H "X-API-Key: cp_..." -H 'content-type: application/json' \
  -d '{"name":"summarize","template":"Summarize for a {audience}: {doc}"}'
curl -X POST localhost:8000/v1/complete -H "X-API-Key: cp_..." -H 'content-type: application/json' \
  -d '{"model":"claude-opus-4-8","prompt_name":"summarize","variables":{"audience":"exec","doc":"..."}}'

# Evaluate a model over a small dataset (mean-score + pass-rate; eval traffic is metered too):
curl -X POST localhost:8000/orgs/<org_id>/evals/run -H "X-API-Key: cp_..." -H 'content-type: application/json' \
  -d '{"model":"claude-opus-4-8","evaluator":"contains","items":[{"prompt":"capital of France?","expected":"Paris"}]}'
```

## Project docs (long-term memory)

- [VISION.md](VISION.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [ROADMAP.md](ROADMAP.md)
- [docs/MODULE_CATALOG.md](docs/MODULE_CATALOG.md) — the full catalog of candidate modules, triaged
- [PROJECT_MEMORY.md](PROJECT_MEMORY.md) · [CHANGELOG.md](CHANGELOG.md) · [docs/adr/](docs/adr/)

## License

MIT
