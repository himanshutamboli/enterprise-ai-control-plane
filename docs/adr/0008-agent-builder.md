# ADR-0008: Agent Builder — reuse the agentic-workflow pattern as a module

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** The first first-party module on top of the core. It should make the "Phase-1
  flagships become modules" claim concrete by reusing the `agentic-workflow` pattern
  (planner/executor loop over tools, bounded by guardrails) inside the platform.

## Decisions

1. **Agents are versioned, tenant-scoped definitions.** An `AgentDef` = model + system prompt +
   allowed tools + `max_steps`; saving auto-increments the version (immutable, like prompts).
2. **A tool registry behind a `Tool` protocol.** Built-in tools (calculator, word_count, reverse)
   are deterministic and offline — the CI-safe default set. Real tools register behind the same
   protocol, mirroring the gateway's providers.
3. **Deterministic default planner.** `SequentialPlanner` calls each configured tool once then
   finishes — enough to demonstrate a bounded planner/executor loop offline. An LLM planner drops
   in behind the same `next_action` shape.
4. **The executor reuses the platform.** A run loops (≤ `max_steps` — the guardrail), executes
   tools recording spans, then composes a prompt and calls the **gateway** for the final answer —
   so agent runs are metered like any other model call and traced as an `agent.run`. RBAC:
   `agent:write` to define, `agent:run` to execute, `agent:read` to view.

## Consequences

- The agent pattern is now a governed, observable, metered platform capability rather than a
  standalone repo — the strongest possible demonstration that the flagships compose into the plane.
- Tool config is validated at save time against the registry, so runs can't reference unknown tools.
- The default planner is intentionally simple; richer planning (LLM-chosen tools, retries,
  human-in-the-loop approval like `agentic-workflow`) is additive behind the same interfaces.
