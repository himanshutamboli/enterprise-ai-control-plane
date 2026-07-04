# ADR-0001: Modular monolith, integration over rebuild, and minimal living docs

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** Starting Phase 2 — a unified Enterprise AI Control Plane — after shipping a
  7-repo Phase-1 portfolio. Primary goal is career/portfolio signal (Staff/Principal + AI
  product), built solo. A large set of candidate ideas (20+) and an ambitious multi-phase,
  commercialization-oriented brief were on the table.

## Decisions

1. **Modular monolith, not microservices.** One deployable FastAPI app with clean module
   boundaries. A solo builder gets the "platform" signal without the operational cost of
   distributed systems; modules can be extracted into services later *only if they earn it*.
2. **Integrate, don't rebuild.** The existing flagships (`llm-observatory`, `agentic-workflow`,
   `ai-product-analytics`, `rag-knowledge-assistant`) are the reference implementations that the
   platform's modules adopt — a stronger story than starting over.
3. **Control Plane ≠ Control Tower.** This repo is the backend platform; the existing Next.js
   Control Tower stays untouched. Wiring the Tower to the Plane's live API is a later, optional
   milestone — not a reason to modify the Tower now.
4. **Minimal living docs, not a 26-file process bible.** A large upfront "engineering handbook"
   is process theater for a solo dev and invites analysis paralysis. We keep ~6 concise,
   load-bearing docs (VISION, ARCHITECTURE, ROADMAP, MODULE_CATALOG, PROJECT_MEMORY, CHANGELOG)
   and add one ADR per real decision. Docs grow *with* the code.
5. **Triage the ambition.** The 20+ ideas are captured in `docs/MODULE_CATALOG.md` and tagged
   (Core / Module / OSS / Commercial / Frontend / Separate) so ambition is recorded without
   becoming a near-term build list. Build the Core vertical slice deep before any breadth.
6. **Career-signal first.** Commercialization/SaaS/fundraising remain a distant north star and
   must not drive near-term engineering decisions.

## Consequences

- Fast path to a demoable, defensible platform; low operational overhead.
- One repo to reason about; module boundaries enforced by discipline + tests, not by network.
- Some catalog ideas will never be built here — intentional. Depth over breadth.
- Revisit the monolith decision only if a module needs independent scaling or a separate team.
