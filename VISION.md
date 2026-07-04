# Vision

## The one-liner

A single, modular **control plane for running enterprise AI in production** — the backend that
teams need once they move past "we called an LLM" into "we operate AI as a product": routing,
cost, prompts, evaluation, governance, and observability, behind organizations and access
control.

## Why this, why now

Most organizations bolt LLM calls into apps with no shared layer for cost, quality, prompts, or
policy. The control plane is that shared layer. It's also the coherent *product* framing for a
portfolio that already contains its major pieces as separate repos — unifying them tells a
Staff/Principal-level story that scattered demos cannot.

## What it is / isn't

- **Is:** a modular monolith (one deployable, clean module boundaries) that runs offline and in
  CI, with real providers/LLMs as optional drop-ins.
- **Isn't (yet):** a multi-tenant SaaS, a billing system, or a 20-product suite. Those are
  captured in [ROADMAP.md](ROADMAP.md) and [docs/MODULE_CATALOG.md](docs/MODULE_CATALOG.md) as
  future phases — not near-term work.

## Phases

- **Phase 1 — done.** 7-repo AI engineering portfolio (analytics → ML → RAG → observability →
  agents → product analytics), on a shared engineering baseline. Prior experience this builds on.
- **Phase 2 — now.** The control-plane core: platform core → gateway → prompts → evals →
  observability → operator dashboard. A credible vertical slice, each module production-grade.
- **Phase 3+ — later.** Optional first-party modules, an OSS toolkit, then (only if it earns it)
  commercial/SaaS packaging. See the roadmap.

## Primary goal

Career/portfolio signal: prove enterprise architecture + AI-product leadership through one
substantial, integrated artifact. Commercialization is a distant north star, not a driver of
near-term decisions.

## Non-goals (for now)

Multi-cloud, Kubernetes operators, a billing/subscription system, and building all 20 catalog
ideas. Depth on a few modules beats breadth across many.
