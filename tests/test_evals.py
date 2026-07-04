import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.evals.evaluators import Contains, ExactMatch, NonEmpty, get_evaluator


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client):
    return client.post(
        "/orgs", json={"name": "Acme", "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


# --- unit: evaluators ---


def test_evaluators_score_as_expected():
    assert ExactMatch().evaluate("paris", "paris ").passed
    assert not ExactMatch().evaluate("paris", "london").passed
    assert Contains().evaluate("The answer is Paris.", "paris").passed
    assert NonEmpty().evaluate("x", None).passed
    assert not NonEmpty().evaluate("   ", None).passed


def test_get_unknown_evaluator_raises():
    with pytest.raises(KeyError):
        get_evaluator("bleu")


# --- API ---


def test_run_eval_scores_and_persists(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    # non_empty passes for every mock output → pass_rate 1.0
    r = client.post(
        f"/orgs/{org}/evals/run",
        json={
            "model": "mock-1",
            "evaluator": "non_empty",
            "items": [{"prompt": "hello"}, {"prompt": "world"}],
        },
        headers=h,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["dataset_size"] == 2 and body["pass_rate"] == 1.0
    assert len(body["results"]) == 2 and body["results"][0]["idx"] == 0

    # the run is listable and fetchable
    runs = client.get(f"/orgs/{org}/evals/runs", headers=h).json()
    assert len(runs) == 1 and runs[0]["id"] == body["id"]
    detail = client.get(f"/orgs/{org}/evals/runs/{body['id']}", headers=h).json()
    assert detail["mean_score"] == 1.0

    # eval traffic is metered through the gateway too
    assert client.get(f"/orgs/{org}/usage", headers=h).json()["total_calls"] == 2


def test_exact_match_against_mock_fails(client):
    d = _signup(client)
    h = {"X-API-Key": d["owner"]["api_key"]}
    org = d["org"]["id"]
    r = client.post(
        f"/orgs/{org}/evals/run",
        json={
            "model": "mock-1",
            "evaluator": "exact_match",
            "items": [{"prompt": "hi", "expected": "definitely not the mock output"}],
        },
        headers=h,
    )
    assert r.status_code == 201 and r.json()["pass_rate"] == 0.0


def test_unknown_evaluator_and_model_are_400(client):
    d = _signup(client)
    h = {"X-API-Key": d["owner"]["api_key"]}
    org = d["org"]["id"]
    bad_eval = client.post(
        f"/orgs/{org}/evals/run",
        json={"model": "mock-1", "evaluator": "bleu", "items": [{"prompt": "x"}]},
        headers=h,
    )
    bad_model = client.post(
        f"/orgs/{org}/evals/run",
        json={"model": "gpt-5", "evaluator": "non_empty", "items": [{"prompt": "x"}]},
        headers=h,
    )
    assert bad_eval.status_code == 400 and bad_model.status_code == 400


def test_viewer_cannot_run_but_can_read(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "V", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    vh = {"X-API-Key": viewer["api_key"]}
    denied = client.post(
        f"/orgs/{org}/evals/run",
        json={"model": "mock-1", "evaluator": "non_empty", "items": [{"prompt": "x"}]},
        headers=vh,
    )
    assert denied.status_code == 403
    assert client.get(f"/orgs/{org}/evals/runs", headers=vh).status_code == 200
