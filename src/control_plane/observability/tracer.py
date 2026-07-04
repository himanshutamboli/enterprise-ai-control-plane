"""A small tracer with `llm-observatory`-style ergonomics.

    with tracer.trace("gateway.complete", org_id, user_id) as t:
        with t.span("provider.complete", kind="llm", input=prompt) as s:
            ...
            s.set_output(text)

On exit the trace (and its spans) are persisted via a fresh session from the factory — so tracing
is independent of the caller's business transaction, and a failed operation is still recorded
(status="error").
"""

from time import perf_counter

from sqlalchemy.orm import Session, sessionmaker

from control_plane.observability.models import Span, Trace


class _SpanCtx:
    def __init__(self, name: str, kind: str, input: str | None) -> None:
        self.record = Span(name=name, kind=kind, input=input)
        self._t0 = 0.0

    def __enter__(self) -> "_SpanCtx":
        self._t0 = perf_counter()
        return self

    def set_output(self, text: str) -> None:
        self.record.output = text

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.record.latency_ms = int((perf_counter() - self._t0) * 1000)
        self.record.status = "error" if exc_type else "ok"
        return False  # never suppress


class _TraceCtx:
    def __init__(self, name: str, org_id: str, user_id: str) -> None:
        self.record = Trace(name=name, org_id=org_id, user_id=user_id)
        self.spans: list[_SpanCtx] = []

    def span(self, name: str, kind: str = "step", input: str | None = None) -> _SpanCtx:
        span = _SpanCtx(name, kind, input)
        self.spans.append(span)
        return span


class Tracer:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def trace(self, name: str, org_id: str, user_id: str) -> "_TracerContext":
        return _TracerContext(self, name, org_id, user_id)

    def _persist(self, ctx: _TraceCtx, status: str, latency_ms: int) -> None:
        ctx.record.status = status
        ctx.record.latency_ms = latency_ms
        for span in ctx.spans:
            ctx.record.spans.append(span.record)
        with self._session_factory() as db:
            db.add(ctx.record)
            db.commit()


class _TracerContext:
    def __init__(self, tracer: Tracer, name: str, org_id: str, user_id: str) -> None:
        self._tracer = tracer
        self._ctx = _TraceCtx(name, org_id, user_id)
        self._t0 = 0.0

    def __enter__(self) -> _TraceCtx:
        self._t0 = perf_counter()
        return self._ctx

    def __exit__(self, exc_type, exc, tb) -> bool:
        latency_ms = int((perf_counter() - self._t0) * 1000)
        self._tracer._persist(self._ctx, "error" if exc_type else "ok", latency_ms)
        return False  # persist, then let any exception propagate
