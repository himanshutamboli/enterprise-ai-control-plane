"""Agent Builder: define and run governed agents on the platform.

Reuses the `agentic-workflow` flagship's pattern — a planner/executor loop over a tool registry,
bounded by guardrails — but as a first-class module: agents are versioned, tenant-scoped
definitions; runs go through the gateway (metered) and are traced by observability.
"""
