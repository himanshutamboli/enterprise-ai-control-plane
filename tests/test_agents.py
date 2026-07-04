import pytest
from fastapi.testclient import TestClient

from control_plane.agents.planner import SequentialPlanner
from control_plane.agents.tools import Calculator, Reverse, WordCount, get_tool
from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client):
    return client.post(
        "/orgs", json={"name": "Acme", "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


def _agent(client, org, key, tools=None, max_steps=5, name="assistant"):
    return client.post(
        f"/orgs/{org}/agents",
        json={
            "name": name,
            "model": "mock-1",
            "system_prompt": "You are helpful.",
            "tools": tools if tools is not None else ["calculator", "word_count"],
            "max_steps": max_steps,
        },
        headers={"X-API-Key": key},
    )


# --- unit ---


def test_tools_are_deterministic():
    assert Calculator().run("what is 2+3*4") == "14"
    assert Calculator().run("no math here").startswith("calculator:")
    assert WordCount().run("a b c") == "3 words"
    assert Reverse().run("abc") == "cba"
    with pytest.raises(KeyError):
        get_tool("browser")


def test_sequential_planner_walks_then_finishes():
    p = SequentialPlanner()
    assert p.next_action(["a", "b"], set()).tool == "a"
    assert p.next_action(["a", "b"], {"a"}).tool == "b"
    assert p.next_action(["a", "b"], {"a", "b"}).kind == "finish"


# --- API ---


def test_create_agent_versions_and_validates_tools(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    assert _agent(client, org, key).json()["version"] == 1
    assert _agent(client, org, key).json()["version"] == 2  # same name → next version
    bad = _agent(client, org, key, tools=["browser"])
    assert bad.status_code == 400


def test_run_agent_executes_tools_then_answers(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    _agent(client, org, key, tools=["calculator", "word_count"])
    r = client.post(
        f"/orgs/{org}/agents/assistant/run", json={"input": "add 2+2 for me"}, headers=h
    )
    assert r.status_code == 201
    body = r.json()
    assert [s["tool"] for s in body["steps"]] == ["calculator", "word_count"]
    assert body["steps"][0]["observation"] == "4"
    assert body["output"]  # composed answer from the (mock) model

    # the run was metered and traced
    assert client.get(f"/orgs/{org}/usage", headers=h).json()["total_calls"] == 1
    names = [t["name"] for t in client.get(f"/orgs/{org}/traces", headers=h).json()]
    assert "agent.run" in names


def test_max_steps_guardrail_bounds_tool_calls(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    _agent(client, org, key, tools=["calculator", "word_count", "reverse"], max_steps=2)
    body = client.post(
        f"/orgs/{org}/agents/assistant/run", json={"input": "3+3 words here"}, headers=h
    ).json()
    assert len(body["steps"]) == 2  # capped at max_steps, 'reverse' never runs


def test_viewer_can_read_but_not_write_or_run(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    _agent(client, org, key)
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "V", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    vh = {"X-API-Key": viewer["api_key"]}
    assert client.get(f"/orgs/{org}/agents", headers=vh).status_code == 200
    assert _agent(client, org, viewer["api_key"], name="x").status_code == 403
    denied = client.post(f"/orgs/{org}/agents/assistant/run", json={"input": "hi"}, headers=vh)
    assert denied.status_code == 403


def test_run_missing_agent_is_404(client):
    d = _signup(client)
    h = {"X-API-Key": d["owner"]["api_key"]}
    org = d["org"]["id"]
    assert (
        client.post(f"/orgs/{org}/agents/ghost/run", json={"input": "hi"}, headers=h).status_code
        == 404
    )
