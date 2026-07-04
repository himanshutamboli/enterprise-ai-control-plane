import pytest

from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.dashboard import data
from control_plane.gateway.router import default_router
from control_plane.observability.tracer import Tracer


@pytest.fixture
def factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/t.db")
    init_db(engine)
    return make_session_factory(engine)


def test_seed_is_idempotent(factory):
    tracer = Tracer(factory)
    assert data.seed_demo(factory, default_router(), tracer) is True
    assert data.seed_demo(factory, default_router(), tracer) is False  # already populated


def test_operator_views_after_seed(factory):
    data.seed_demo(factory, default_router(), Tracer(factory))
    with factory() as db:
        ov = data.overview(db)
        # 1 demo org, 2 users (owner + dev), gateway calls from demo completions + eval items
        assert ov["orgs"] == 1 and ov["users"] == 2
        assert ov["gateway_calls"] >= 4 and ov["eval_runs"] == 1
        assert ov["traces"] >= 4 and ov["total_cost_usd"] > 0

        models = {r["model"] for r in data.spend_by_model(db)}
        assert "claude-opus-4-8" in models

        assert data.spend_by_org(db)[0]["org"] == "Demo Corp"
        assert len(data.daily_cost(db)) >= 1
        assert data.recent_eval_runs(db)[0]["pass_rate"] == 1.0
        assert data.recent_traces(db)[0]["spans"] >= 1


def test_empty_overview_is_zeroed(factory):
    with factory() as db:
        ov = data.overview(db)
        assert ov == {
            "orgs": 0,
            "users": 0,
            "gateway_calls": 0,
            "total_cost_usd": 0.0,
            "eval_runs": 0,
            "traces": 0,
        }
