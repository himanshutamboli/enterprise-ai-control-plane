import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.observability import service as obs_service
from control_plane.observability.tracer import Tracer


@pytest.fixture
def factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return make_session_factory(engine)


@pytest.fixture
def client(factory):
    return TestClient(create_app(session_factory=factory))


def _signup(client):
    return client.post(
        "/orgs", json={"name": "Acme", "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


# --- unit: tracer ---


def test_tracer_persists_trace_and_spans(factory):
    tracer = Tracer(factory)
    with tracer.trace("op", "org1", "user1") as t:
        with t.span("step-a", kind="llm", input="in") as s:
            s.set_output("out")
    with factory() as db:
        traces = obs_service.list_traces(db, "org1")
        assert len(traces) == 1
        trace = obs_service.get_trace(db, "org1", traces[0].id)
        assert trace.name == "op" and trace.status == "ok"
        assert len(trace.spans) == 1
        assert trace.spans[0].output == "out" and trace.spans[0].kind == "llm"


def test_tracer_records_error_status(factory):
    tracer = Tracer(factory)
    with pytest.raises(ValueError):
        with tracer.trace("boom", "org1", "u1") as t:
            with t.span("x"):
                raise ValueError("kaboom")
    with factory() as db:
        assert obs_service.list_traces(db, "org1")[0].status == "error"


# --- API: instrumentation is automatic ---


def test_gateway_call_emits_a_trace(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    client.post("/v1/complete", json={"model": "mock-1", "prompt": "hi there"}, headers=h)

    traces = client.get(f"/orgs/{org}/traces", headers=h).json()
    assert len(traces) == 1 and traces[0]["name"] == "gateway.complete"

    detail = client.get(f"/orgs/{org}/traces/{traces[0]['id']}", headers=h).json()
    assert detail["spans"][0]["kind"] == "llm"
    assert detail["spans"][0]["output"]  # captured the model output


def test_eval_run_emits_a_trace(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    client.post(
        f"/orgs/{org}/evals/run",
        json={"model": "mock-1", "evaluator": "non_empty", "items": [{"prompt": "x"}]},
        headers=h,
    )
    names = [t["name"] for t in client.get(f"/orgs/{org}/traces", headers=h).json()]
    assert "eval.run" in names


def test_traces_are_tenant_isolated(client):
    a = _signup(client)
    b = _signup(client)
    ah, aorg = {"X-API-Key": a["owner"]["api_key"]}, a["org"]["id"]
    bh = {"X-API-Key": b["owner"]["api_key"]}
    client.post("/v1/complete", json={"model": "mock-1", "prompt": "hi"}, headers=ah)
    # B sees none of A's traces
    assert client.get(f"/orgs/{aorg}/traces", headers=bh).status_code == 403
    assert client.get(f"/orgs/{b['org']['id']}/traces", headers=bh).json() == []
