"""Operator dashboard (Streamlit) — a platform-admin view over the control plane.

Reads the same database the API writes to (via the service layer), across all tenants. Seeds a
demo org on first run so there's something to see.

Run:  uv sync --group dashboard && uv run streamlit run dashboard.py
"""

import plotly.graph_objects as go
import streamlit as st

from control_plane.core.config import get_settings
from control_plane.core.db import init_db, make_engine, make_session_factory
from control_plane.dashboard import data
from control_plane.gateway.router import default_router
from control_plane.observability.tracer import Tracer

st.set_page_config(page_title="Control Plane — Operator", layout="wide", page_icon="🛰️")
ACCENT = "#6C5CE7"


@st.cache_resource
def _session_factory():
    engine = make_engine(get_settings().database_url)
    init_db(engine)
    sf = make_session_factory(engine)
    data.seed_demo(sf, default_router(), Tracer(sf))  # populate on first run
    return sf


sf = _session_factory()

st.title("🛰️ Enterprise AI Control Plane — Operator")
st.caption(
    "Platform-admin view across all organizations: adoption, spend, evaluations, and traces."
)

with sf() as db:
    ov = data.overview(db)
    by_model = data.spend_by_model(db)
    by_org = data.spend_by_org(db)
    daily = data.daily_cost(db)
    traces = data.recent_traces(db)
    runs = data.recent_eval_runs(db)

k = st.columns(6)
k[0].metric("Organizations", ov["orgs"])
k[1].metric("Users", ov["users"])
k[2].metric("Gateway calls", ov["gateway_calls"])
k[3].metric("Total cost", f"${ov['total_cost_usd']:,.4f}")
k[4].metric("Eval runs", ov["eval_runs"])
k[5].metric("Traces", ov["traces"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Spend by model")
    fig = go.Figure(
        go.Bar(
            x=[r["cost_usd"] for r in by_model],
            y=[r["model"] for r in by_model],
            orientation="h",
            marker_color=ACCENT,
        )
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
with col2:
    st.subheader("Spend by organization")
    st.dataframe(by_org, width="stretch")

st.subheader("Daily cost")
fig = go.Figure(
    go.Scatter(
        x=[r["date"] for r in daily], y=[r["cost_usd"] for r in daily], line=dict(color=ACCENT)
    )
)
fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, width="stretch")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Recent eval runs")
    st.dataframe(runs, width="stretch")
with col4:
    st.subheader("Recent traces")
    st.dataframe(traces, width="stretch")
