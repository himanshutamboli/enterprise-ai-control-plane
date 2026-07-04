import pytest
from fastapi.testclient import TestClient

from control_plane.core.api import create_app
from control_plane.core.db import init_db, make_engine, make_session_factory


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine)))


def _signup(client, name="Acme"):
    r = client.post(
        "/orgs", json={"name": name, "owner_email": "owner@acme.com", "owner_name": "Owner"}
    )
    assert r.status_code == 201
    return r.json()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["version"]


def test_signup_creates_org_and_owner_key(client):
    d = _signup(client)
    assert d["org"]["slug"] == "acme"
    assert d["owner"]["role"] == "owner"
    assert d["owner"]["api_key"].startswith("cp_")


def test_owner_can_add_and_list_users(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    r = client.post(
        f"/orgs/{org}/users",
        json={"email": "m@acme.com", "name": "Mem", "role": "member"},
        headers={"X-API-Key": key},
    )
    assert r.status_code == 201 and r.json()["role"] == "member"
    users = client.get(f"/orgs/{org}/users", headers={"X-API-Key": key}).json()
    assert len(users) == 2  # owner + member
    assert all("api_key" not in u for u in users)  # keys never listed


def test_missing_key_is_unauthorized(client):
    org = _signup(client)["org"]["id"]
    assert client.get(f"/orgs/{org}").status_code == 401


def test_viewer_cannot_manage_users(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    viewer = client.post(
        f"/orgs/{org}/users",
        json={"email": "v@acme.com", "name": "View", "role": "viewer"},
        headers={"X-API-Key": key},
    ).json()
    vkey = viewer["api_key"]
    assert client.get(f"/orgs/{org}/users", headers={"X-API-Key": vkey}).status_code == 200
    denied = client.post(
        f"/orgs/{org}/users",
        json={"email": "x@acme.com", "name": "X"},
        headers={"X-API-Key": vkey},
    )
    assert denied.status_code == 403


def test_cross_tenant_access_denied(client):
    a = _signup(client, "Acme")
    b = _signup(client, "Beta")
    akey, borg = a["owner"]["api_key"], b["org"]["id"]
    assert client.get(f"/orgs/{borg}", headers={"X-API-Key": akey}).status_code == 403


def test_duplicate_email_conflicts(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    payload = {"email": "dupe@acme.com", "name": "Dupe"}
    assert (
        client.post(f"/orgs/{org}/users", json=payload, headers={"X-API-Key": key}).status_code
        == 201
    )
    assert (
        client.post(f"/orgs/{org}/users", json=payload, headers={"X-API-Key": key}).status_code
        == 409
    )


def test_validation_error_on_bad_body(client):
    d = _signup(client)
    key, org = d["owner"]["api_key"], d["org"]["id"]
    r = client.post(f"/orgs/{org}/users", json={"name": "NoEmail"}, headers={"X-API-Key": key})
    assert r.status_code == 422
