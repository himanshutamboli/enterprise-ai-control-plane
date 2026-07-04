# ADR-0009: AI Delivery Manager — an explainable risk score + AI status report

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** A TPM-native module. The valuable, differentiated piece is *delivery-risk
  prediction*; the question is how to do it credibly.

## Decisions

1. **Model the delivery primitives.** `Project` → `WorkItem`s (status + story points) + a RAID log
   (`RaidItem`: risk / assumption / issue / dependency, with severity and open/closed). Enough to
   compute health without becoming a full Jira.
2. **Risk is a transparent heuristic, not a black box.** `delivery_risk` returns a 0–100 score, a
   RAG level, **and a reason for every contribution** (completion gap, blocked items, open
   high-severity RAID, schedule pressure like "needs 10.5 pts/day to hit the target"). Explainable
   beats a mystery ML score for a delivery signal a TPM has to defend — same philosophy as the
   churn business-cost threshold and the agent's heuristic planner.
3. **The AI part is the narrative, through the gateway.** `status-report` composes the computed
   numbers into a prompt and calls the **gateway** for an executive summary — so the report is
   metered and traced (`delivery.status_report`) like any other model use, and works offline via
   the mock provider.
4. **RBAC.** `delivery:read` for health/lists; `delivery:write` to create projects/items/RAID and
   to generate a report (it costs a model call).

## Consequences

- A believable delivery-risk signal that a program manager can explain line by line — the module's
  differentiator.
- The heuristic weights are tunable constants in one function; if real historical data ever exists,
  a learned model can replace `delivery_risk` behind the same signature.
- Only the *narrative* depends on an LLM; health and risk are fully deterministic and CI-tested.
