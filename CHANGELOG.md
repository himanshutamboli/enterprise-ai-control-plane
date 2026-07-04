# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [Unreleased]

### Added
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
