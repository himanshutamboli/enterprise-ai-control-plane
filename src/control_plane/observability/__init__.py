"""Observability: trace platform operations as traces + spans.

The `Tracer` mirrors the ergonomics of the `llm-observatory` flagship's SDK (`trace`/`span`/
`set_output`), so the pattern is shared rather than reinvented. Every gateway completion and eval
run emits a trace; traces are tenant-scoped and inspectable via the API.
"""
