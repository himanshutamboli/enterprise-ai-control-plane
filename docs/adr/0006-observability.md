# ADR-0006: Observability — a tracer reusing the llm-observatory shape

- **Status:** Accepted
- **Date:** 2026-07-04
- **Context:** The platform should record what it does, not just do it. M5 adds tracing, and
  deliberately reuses the pattern from the `llm-observatory` flagship rather than inventing one.

## Decisions

1. **`llm-observatory`-shaped `Tracer`.** Same ergonomics — `with tracer.trace(...) as t: with
   t.span(...) as s: s.set_output(...)`. Reusing a proven shape (instead of a new API) is the
   whole point of having built the flagship first.
2. **Trace writes are out-of-band.** The tracer persists on context exit via its **own** session
   from the factory — independent of the caller's business transaction. Observability never rolls
   back with (or blocks) business writes, and a failed operation still yields an `error` trace.
3. **Auto-instrumentation at the route layer.** The gateway `complete` and eval `run` routes open
   a trace/span around the work; services stay unaware of tracing. Adding tracing to a new route
   is one `with` block.
4. **Tenant-scoped, read-gated.** Traces carry `org_id`; listing/detail require `obs:read` and pass
   tenant isolation like every other resource.

## Consequences

- Every governed model call and eval run is now inspectable (inputs, outputs, latency, status).
- The tracer's separate session means two connections touch the DB per request; fine for SQLite
  in dev/CI and for Postgres in production. If write volume grows, batch/async the writer behind
  the same `Tracer` interface.
- This trace store is intentionally close to `llm-observatory`'s model; a future step could export
  traces to a standalone observatory instance instead of the local tables.
