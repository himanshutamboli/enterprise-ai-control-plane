import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.gateway.providers import MockProvider, estimate_cost
from control_plane.gateway.router import UnknownModelError, default_router


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client, name="Acme"):
    return client.post(
        "/orgs", json={"name": name, "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


# --- unit ---


def test_estimate_cost_matches_price_table():
    # claude-opus-4-8 = (5, 25) $/1M → 1000 in, 500 out
    assert estimate_cost("claude-opus-4-8", 1000, 500) == pytest.approx(
        1000 / 1e6 * 5 + 500 / 1e6 * 25
    )
    assert estimate_cost("unknown-model", 1000, 500) == 0.0


def test_mock_provider_is_deterministic_with_cost():
    p = MockProvider()
    a = p.complete(_req())
    b = p.complete(_req())
    assert a.text == b.text and a.provider == "mock"
    assert a.prompt_tokens > 0 and a.completion_tokens > 0 and a.cost_usd > 0


def test_router_resolves_and_rejects():
    r = default_router()
    assert "claude-opus-4-8" in r.models()
    assert r.resolve("mock-1").name == "mock"
    with pytest.raises(UnknownModelError):
        r.resolve("gpt-5")


def _req():
    from control_plane.gateway.providers import CompletionRequest

    return CompletionRequest(model="mock-1", prompt="hello world foo", max_tokens=64)


# --- API ---


def test_complete_meters_and_records_usage(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    r = client.post(
        "/v1/complete",
        json={"model": "claude-opus-4-8", "prompt": "summarize this please"},
        headers={"X-API-Key": key},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "mock" and body["cost_usd"] > 0

    usage = client.get(f"/orgs/{org}/usage", headers={"X-API-Key": key}).json()
    assert usage["total_calls"] == 1
    assert usage["by_model"][0]["model"] == "claude-opus-4-8"
    assert usage["total_cost_usd"] == pytest.approx(body["cost_usd"])


def test_unknown_model_is_400(client):
    d = _signup(client)
    key = d["owner"]["api_key"]
    r = client.post(
        "/v1/complete", json={"model": "gpt-5", "prompt": "hi"}, headers={"X-API-Key": key}
    )
    assert r.status_code == 400


def test_viewer_cannot_invoke_gateway(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "V", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    r = client.post(
        "/v1/complete",
        json={"model": "mock-1", "prompt": "hi"},
        headers={"X-API-Key": viewer["api_key"]},
    )
    assert r.status_code == 403


def test_complete_requires_api_key(client):
    assert client.post("/v1/complete", json={"model": "mock-1", "prompt": "hi"}).status_code == 401
