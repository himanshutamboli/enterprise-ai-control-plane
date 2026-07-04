from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.delivery.service import delivery_risk


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client):
    return client.post(
        "/orgs", json={"name": "Acme", "owner_email": "o@acme.com", "owner_name": "O"}
    ).json()


TODAY = date(2026, 7, 1)


# --- unit: the risk heuristic ---


def test_healthy_project_is_green():
    health = {
        "pct_complete": 0.9,
        "points_total": 10,
        "points_done": 9,
        "blocked": 0,
        "open_high_severity": 0,
    }
    r = delivery_risk(health, TODAY + timedelta(days=30), TODAY)
    assert r["level"] == "green" and r["score"] < 33


def test_blocked_and_high_severity_raise_risk_with_reasons():
    health = {
        "pct_complete": 0.3,
        "points_total": 10,
        "points_done": 3,
        "blocked": 2,
        "open_high_severity": 2,
    }
    r = delivery_risk(health, TODAY + timedelta(days=2), TODAY)
    assert r["level"] == "red" and r["score"] >= 66
    joined = " ".join(r["reasons"])
    assert "blocked" in joined and "high-severity" in joined


def test_past_target_with_work_left_is_flagged():
    health = {
        "pct_complete": 0.5,
        "points_total": 10,
        "points_done": 5,
        "blocked": 0,
        "open_high_severity": 0,
    }
    r = delivery_risk(health, TODAY - timedelta(days=1), TODAY)
    assert "past target date" in " ".join(r["reasons"])


# --- API ---


def test_health_and_risk_endpoint(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    proj = client.post(
        f"/orgs/{org}/projects", json={"name": "Migration", "target_date": "2026-07-05"}, headers=h
    ).json()
    pid = proj["id"]
    for st, pts in [("done", 3), ("in_progress", 2), ("blocked", 5)]:
        client.post(
            f"/orgs/{org}/projects/{pid}/work-items",
            json={"title": f"task-{st}", "status": st, "points": pts},
            headers=h,
        )
    client.post(
        f"/orgs/{org}/projects/{pid}/raid",
        json={"kind": "risk", "description": "vendor slip", "severity": "high"},
        headers=h,
    )
    out = client.get(f"/orgs/{org}/projects/{pid}/health", headers=h).json()
    assert out["health"]["blocked"] == 1 and out["health"]["open_high_severity"] == 1
    assert out["health"]["pct_complete"] == pytest.approx(3 / 10)
    assert out["risk"]["level"] in {"amber", "red"}  # blocked + high-sev + low completion
    assert out["risk"]["reasons"]


def test_status_report_uses_gateway_and_is_traced(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    h = {"X-API-Key": key}
    pid = client.post(f"/orgs/{org}/projects", json={"name": "P"}, headers=h).json()["id"]
    client.post(
        f"/orgs/{org}/projects/{pid}/work-items",
        json={"title": "t", "status": "done", "points": 1},
        headers=h,
    )
    r = client.post(f"/orgs/{org}/projects/{pid}/status-report", json={}, headers=h)
    assert r.status_code == 200 and r.json()["report"]
    assert r.json()["risk"]["level"] == "green"
    # metered + traced
    assert client.get(f"/orgs/{org}/usage", headers=h).json()["total_calls"] == 1
    names = [t["name"] for t in client.get(f"/orgs/{org}/traces", headers=h).json()]
    assert "delivery.status_report" in names


def test_viewer_can_read_but_not_write(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "V", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    vh = {"X-API-Key": viewer["api_key"]}
    assert client.get(f"/orgs/{org}/projects", headers=vh).status_code == 200
    denied = client.post(f"/orgs/{org}/projects", json={"name": "X"}, headers=vh)
    assert denied.status_code == 403


def test_cross_tenant_project_denied(client):
    a = _signup(client)
    b = _signup(client)
    ah = {"X-API-Key": a["owner"]["api_key"]}
    pid = client.post(f"/orgs/{a['org']['id']}/projects", json={"name": "P"}, headers=ah).json()[
        "id"
    ]
    bh = {"X-API-Key": b["owner"]["api_key"]}
    # B tries to read A's project health under B's own org path → 404 (not in B's tenant)
    assert (
        client.get(f"/orgs/{b['org']['id']}/projects/{pid}/health", headers=bh).status_code == 404
    )
