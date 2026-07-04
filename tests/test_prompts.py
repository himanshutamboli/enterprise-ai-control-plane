import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.prompts.service import (
    MissingVariablesError,
    placeholders,
    render_template,
)


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client):
    return client.post(
        "/orgs", json={"name": "Acme", "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


# --- unit: rendering ---


def test_placeholders_and_render():
    assert placeholders("Hi {name}, {n} items") == {"name", "n"}
    assert render_template("Hi {name}", {"name": "Ada", "extra": 1}) == "Hi Ada"


def test_render_missing_variable_raises():
    with pytest.raises(MissingVariablesError) as e:
        render_template("Hi {name}", {})
    assert e.value.missing == ["name"]


# --- API ---


def test_save_auto_increments_versions(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    v1 = client.post(
        f"/orgs/{org}/prompts", json={"name": "greet", "template": "Hi {x}"}, headers=h
    )
    v2 = client.post(
        f"/orgs/{org}/prompts", json={"name": "greet", "template": "Hello {x}!"}, headers=h
    )
    assert v1.json()["version"] == 1 and v2.json()["version"] == 2
    # fetch latest, then a pinned version
    assert client.get(f"/orgs/{org}/prompts/greet", headers=h).json()["version"] == 2
    assert (
        client.get(f"/orgs/{org}/prompts/greet?version=1", headers=h).json()["template"] == "Hi {x}"
    )


def test_render_endpoint(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    client.post(f"/orgs/{org}/prompts", json={"name": "greet", "template": "Hi {name}"}, headers=h)
    r = client.post(
        f"/orgs/{org}/prompts/greet/render", json={"variables": {"name": "Ada"}}, headers=h
    )
    assert r.status_code == 200 and r.json()["text"] == "Hi Ada"
    bad = client.post(f"/orgs/{org}/prompts/greet/render", json={"variables": {}}, headers=h)
    assert bad.status_code == 422


def test_write_requires_permission(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "V", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    vh = {"X-API-Key": viewer["api_key"]}
    # viewer can read the list but not create
    assert client.get(f"/orgs/{org}/prompts", headers=vh).status_code == 200
    denied = client.post(f"/orgs/{org}/prompts", json={"name": "x", "template": "t"}, headers=vh)
    assert denied.status_code == 403


def test_gateway_can_run_a_registered_prompt(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    client.post(
        f"/orgs/{org}/prompts",
        json={"name": "summarize", "template": "Summarize: {doc}"},
        headers=h,
    )
    r = client.post(
        "/v1/complete",
        json={"model": "mock-1", "prompt_name": "summarize", "variables": {"doc": "hello world"}},
        headers=h,
    )
    assert r.status_code == 200
    # the mock echoes the rendered prompt reversed → confirms the template was rendered
    assert "Summarize:" in r.json()["text"]

    usage = client.get(f"/orgs/{org}/usage", headers=h).json()
    assert usage["total_calls"] == 1


def test_complete_rejects_both_or_neither_prompt(client):
    d = _signup(client)
    h = {"X-API-Key": d["owner"]["api_key"]}
    neither = client.post("/v1/complete", json={"model": "mock-1"}, headers=h)
    both = client.post(
        "/v1/complete",
        json={"model": "mock-1", "prompt": "hi", "prompt_name": "greet"},
        headers=h,
    )
    assert neither.status_code == 422 and both.status_code == 422
