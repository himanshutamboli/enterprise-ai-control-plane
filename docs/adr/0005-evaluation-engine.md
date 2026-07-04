# ADR-0005: Evaluation Engine — evaluators, runs, and gateway reuse

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** A control plane must answer "is the model output any good?", not just "did we call
  it?". M4 adds scoring over a dataset, reusing the concepts proven in `llm-observatory`.

## Decisions

1. **`Evaluator` protocol + deterministic defaults.** `exact_match`, `contains`, and `non_empty`
   are pure and offline — the CI-safe defaults. An LLM-as-judge evaluator drops in behind the same
   protocol (lazy provider call), mirroring the gateway's provider pattern.
2. **Runs produce outputs through the gateway.** `run_eval` resolves the model via the same
   `ModelRouter` and calls the provider, so evaluation exercises the real path — and every eval
   call is metered as a `GatewayCall`. Eval and cost share one source of truth.
3. **Persist a run + per-item results.** An `EvalRun` stores model, evaluator, dataset size, and
   aggregate mean-score / pass-rate; `EvalItemResult` stores each input/expected/output/score.
   Runs are tenant-scoped, listable, and fetchable in detail.
4. **RBAC split.** `eval:run` (owner/admin/member) to execute; `eval:read` (all roles) to view.

## Consequences

- The platform can now compare models/prompts on a labeled set and track quality over time.
- Because eval reuses the gateway, "what did this eval cost?" is answerable from the same usage
  data — a natural bridge to the cost and observability modules.
- Datasets are passed inline for now; a stored, versioned dataset registry is a later additive
  step (it mirrors the prompt registry).
