"""The FastAPI application factory.

Sets shared state (DB session factory, settings, model router) and composes each module's router.
Modules read their dependencies off ``app.state`` (see ``core.deps``), so adding a module is just
including its router here.

Serve with:  uv run uvicorn control_plane.core.api:app
"""

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from control_plane import __version__
from control_plane.core.config import Settings, get_settings
from control_plane.core.db import init_db, make_engine, make_session_factory


def create_app(
    session_factory: sessionmaker[Session] | None = None, settings: Settings | None = None
) -> FastAPI:
    settings = settings or get_settings()
    if session_factory is None:
        engine = make_engine(settings.database_url)
        init_db(engine)
        session_factory = make_session_factory(engine)

    app = FastAPI(title=settings.app_name, version=__version__)
    app.state.session_factory = session_factory
    app.state.settings = settings

    # Model router lives in app state so it can be swapped (e.g. real providers) per deployment.
    from control_plane.gateway.router import default_router

    app.state.model_router = default_router()

    from control_plane.core.routes import router as core_router
    from control_plane.evals.routes import router as evals_router
    from control_plane.gateway.routes import router as gateway_router
    from control_plane.prompts.routes import router as prompts_router

    app.include_router(core_router)
    app.include_router(gateway_router)
    app.include_router(prompts_router)
    app.include_router(evals_router)
    return app


app = create_app()  # module-level instance for `uvicorn control_plane.core.api:app`
