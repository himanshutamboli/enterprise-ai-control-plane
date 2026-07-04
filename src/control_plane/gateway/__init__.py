"""AI Gateway: the single, governed entry point for model calls.

Providers sit behind one `Provider` protocol; a `ModelRouter` maps model names to providers; every
call is metered (tokens + cost) and recorded per tenant. The default router is fully offline
(`MockProvider`) so the platform runs and tests in CI; real providers (Anthropic) drop in behind
the same protocol.
"""
