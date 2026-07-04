# ADR-0004: Prompt Registry — immutable versions + gateway integration

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** Prompts are production assets that change and need attribution ("which prompt
  produced this, and what did it cost?"). Scattering them as strings in code makes that
  impossible. M3 makes prompts governed, versioned objects.

## Decisions

1. **Immutable, auto-incrementing versions.** Saving a prompt name never edits — it creates the
   next version (unique per org+name+version). Old versions stay retrievable, so a completion can
   always be traced to the exact template it ran.
2. **Tenant-scoped.** Prompts belong to an org; access requires `prompt:read`/`prompt:write` and
   passes tenant isolation, same as every other resource.
3. **Rendering validates variables.** `render_template` extracts `{placeholders}` and refuses to
   render (422) if any are missing — no silently half-filled prompts. Extra variables are ignored.
4. **Gateway integration closes the loop.** `/v1/complete` accepts either a raw `prompt` or a
   `prompt_name` (+ optional version + variables). When referenced, the gateway resolves and
   renders the registered prompt and records `prompt_name`/`prompt_version` on the `GatewayCall`
   — so usage and cost are attributable to a specific prompt version. Exactly-one-of is enforced.

## Consequences

- Prompt changes are auditable and reversible; nothing is lost on "editing" a prompt.
- Per-prompt (and per-version) cost/quality analysis is now possible — the `GatewayCall` rows
  carry the link; surfacing it in `/usage` and the eval module is a later, additive step.
- Rendering uses Python `str.format` semantics; if richer templating (loops/conditionals) is ever
  needed, swap the renderer behind `render_template` without touching callers.
