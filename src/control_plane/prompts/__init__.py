"""Prompt Registry: versioned, tenant-scoped prompt templates.

Prompts become governed assets — every save creates a new immutable version — that can be
retrieved by name (latest) or name+version, rendered with variables, and referenced by the
gateway so a completion is tied to an exact prompt version.
"""
