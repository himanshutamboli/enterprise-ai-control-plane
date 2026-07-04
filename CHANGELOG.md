# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **M6 — Operator Dashboard.** A Streamlit platform-admin view (cross-org KPIs, spend by
  model/org, daily-cost trend, recent eval runs + traces) over pure, testable read queries
  (`control_plane.dashboard.data`); a demo seed populates a week of activity. UI dependencies
  (streamlit, plotly) live in an optional `dashboard` dependency group. ADR-0007. **Completes the
  Phase 2 core vertical slice — all six modules built.**
- **M5 — Observability.** A `Tracer` with `llm-observatory`-style ergonomics (`trace`/`span`/
  `set_output`) that persists `Trace` + `Span` via its own session (independent of the business
  transaction; records errors too). Gateway completions and eval runs are auto-instrumented;
  tenant-scoped `GET /orgs/{id}/traces` + `/traces/{id}`; new `obs:read` permission. ADR-0006.
- **M4 — Evaluation Engine.** `Evaluator` protocol with deterministic defaults (exact-match,
  contains, non-empty); `run_eval` runs a dataset through the gateway, scores each output, and
  persists an `EvalRun` + per-item `EvalItemResult` with mean-score/pass-rate. Endpoints to run,
  list, and fetch runs; new `eval:run`/`eval:read` permissions; eval calls metered via the
  gateway. ADR-0005.
- **M3 — Prompt Registry.** Versioned, tenant-scoped prompts (immutable auto-incrementing
  versions), variable rendering, and routes to save/list/fetch/render. The gateway's
  `/v1/complete` accepts a `prompt_name` (+ optional `version`, `variables`) and records the
  prompt name/version on the `GatewayCall`. New `prompt:read`/`prompt:write` permissions. ADR-0004.
- **M2 — AI Gateway.** `Provider` protocol with a deterministic `MockProvider` (CI default) +
  `AnthropicProvider` drop-in; `ModelRouter`; token→cost pricing; per-call metering persisted as
  `GatewayCall`; `POST /v1/complete` (gated by `gateway:invoke`) and `GET /orgs/{id}/usage`.
  Refactored the app into shared dependencies (`core.deps`) + per-module routers. ADR-0003.
- **M1 — Platform Core.** FastAPI app factory + Pydantic settings; `Organization`/`User`
  (SQLAlchemy 2.0, SQLite default / Postgres via `database_url`); static RBAC (owner/admin/
  member/viewer → permissions); `X-API-Key` auth with open tenant signup (`POST /orgs`);
  multi-tenant isolation; `/health`. Routes for org read + user create/list. ADR-0002.
- **M0 — Foundation.** Repo scaffold (uv, ruff, pytest, pre-commit, GitHub Actions CI,
  Python 3.13, `src/` layout, MIT).
- Module registry (`control_plane/app.py`) + `control-plane` CLI that prints the module map.
- Long-term-memory docs: `VISION`, `ARCHITECTURE`, `ROADMAP`, `docs/MODULE_CATALOG`,
  `PROJECT_MEMORY`, and `docs/adr/0001`.

[Unreleased]: https://github.com/himanshutamboli/enterprise-ai-control-plane/commits/main
