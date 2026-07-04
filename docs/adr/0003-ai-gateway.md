# ADR-0003: AI Gateway — provider protocol, router, and cost metering

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** The platform's reason to exist is governed, observable, cost-aware model access.
  M2 introduces that single entry point without coupling the platform to any one LLM vendor.

## Decisions

1. **One `Provider` protocol.** Every provider returns the same `CompletionResponse` (text +
   usage + cost). Callers never branch on vendor. `MockProvider` (deterministic, offline) is the
   CI default; `AnthropicProvider` (lazy `anthropic`, `claude-opus-4-8`) is the real drop-in.
2. **A `ModelRouter` maps model → provider.** Requests name a model; the router resolves the
   provider. The default router sends all models to the mock, so the platform runs and tests with
   no API keys; a deployment registers real providers behind the same interface.
3. **Meter every call.** Cost is derived from a token price table and each call is persisted as a
   `GatewayCall` (org, user, model, tokens, cost, latency). This is what makes cost analytics and
   governance possible downstream — the gateway is the chokepoint where usage is truthfully known.
4. **RBAC + tenancy apply.** `POST /v1/complete` requires `gateway:invoke`; usage is tenant-scoped.
5. **App refactor for modularity.** Shared FastAPI dependencies moved to `core.deps` (reading
   `app.state`), and each module now contributes an `APIRouter` the app factory includes. Adding a
   module is "include its router" — no edits to existing modules.

## Consequences

- Vendor-agnostic by construction; swapping/adding providers is local to `providers.py` + router
  registration.
- Every model call is attributable and costed — the foundation for the cost, eval, and
  observability modules.
- The mock default keeps CI hermetic; real spend only happens when a real provider is registered.
- The model router currently maps 1:1 model→provider; fallback/least-cost routing is a later,
  additive change behind the same `resolve()`.
