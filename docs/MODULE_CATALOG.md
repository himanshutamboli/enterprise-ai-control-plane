# Module Catalog

Every candidate idea, triaged so ambition is *recorded* without becoming a build list. Most of
these are future or optional; the near-term work is only the **Core** rows (see
[ROADMAP.md](ROADMAP.md)). Complexity: S (days) · M (1–2 wk) · L (weeks) · XL (months / a product).

**Tiers:** `Core` = the platform spine we build now · `Module` = optional first-party add-on ·
`OSS` = open-source extension/toolkit · `Commercial` = paid/SaaS, only if validated ·
`Frontend` = belongs to the Control Tower UI · `Separate` = good idea, off this thesis.

| # | Idea | Tier | Cx | Maps to / notes |
|---|---|---|---|---|
| 1 | Enterprise AI Control Plane | **Core** | XL | This repo — the platform itself. |
| 2 | AI Product Analytics | Core✓ | — | **Built** ([ai-product-analytics](https://github.com/himanshutamboli/ai-product-analytics)); becomes the analytics view over gateway/eval data. |
| 3 | AI Cost Optimization (FinOps) | **Core** | M | Gateway cost metering + analytics; partly built (ai-product-analytics economics). |
| 4 | AI Governance (policy/audit/PII) | **Core**→Module | L | Guardrails + audit log start in core; deep governance is a later module. |
| 5 | Observability | Core✓ | — | **Built** ([llm-observatory](https://github.com/himanshutamboli/llm-observatory)); the `observability` module. |
| 6 | Agent Builder | Module | L | Reuses [agentic-workflow](https://github.com/himanshutamboli/agentic-workflow) (planner/executor + guardrails). |
| 7 | Enterprise Knowledge Graph / RAG | Module | L | Reuses [rag-knowledge-assistant](https://github.com/himanshutamboli/rag-knowledge-assistant). |
| 8 | Enterprise MCP Platform | Module / OSS | L | MCP server registry + governance; emerging, good OSS angle. |
| 9 | AI SDLC Platform | Module | XL | Prompts + evals + datasets + releases; overlaps core prompts/evals. |
| 10 | Autonomous QA Platform | Module | L | Agent that reads PRDs → generates/executes tests; builds on Agent Builder. |
| 11 | AI Delivery Manager | Module | L | TPM-aligned: sprint health, RAID, delivery-risk; strong personal fit. |
| 12 | AI Solution Architect Copilot | Commercial | L | RFP/BRD → architecture/PRD/estimate; consulting lead-gen. |
| 13 | Product Discovery AI | Commercial | L | Interviews/tickets → opportunities; product-management fit. |
| 14 | AI Architecture Studio | Module | XL | Visual drag-and-drop AI system designer; heavy frontend. |
| 15 | Executive AI Dashboard / AI CTO Dashboard | **Frontend** | M | This is the **Control Tower** — already exists; wire to the Plane's API later. |
| 16 | AI Consulting Toolkit | OSS | S–M | Templates/checklists/prompt libs; portfolio + lead-gen. |
| 17 | AI Startup Accelerator Kit | OSS / Commercial | L | Auth+billing+RAG+agents starter; could reuse the core. |
| 18 | AI Product Operating System | Commercial | XL | Umbrella framing of several modules; a vision, not a repo. |
| 19 | AI Workflow Marketplace | Commercial | XL | App-store for workflows; only meaningful with users/community. |
| 20 | AI Procurement Intelligence | Separate | L | Model/vendor comparison; niche, off the core thesis. |
| 21 | AI Resume Intelligence | Separate | M | Useful, but unrelated to the control plane — keep as its own thing. |

## How to read this

- **Build now:** rows tagged `Core` (plus the two already built that slot in as modules).
- **Build next, if the core lands well:** the `Module` rows most aligned to the profile —
  Agent Builder, AI Delivery Manager, Governance.
- **Package later, only if validated:** `OSS` then `Commercial`.
- **Politely decline for this platform:** `Separate` rows — good ideas, wrong home.
