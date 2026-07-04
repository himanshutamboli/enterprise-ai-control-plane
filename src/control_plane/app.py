"""Application entry point + the platform's module registry.

The Control Plane is a modular monolith. This registry is the single source of truth for what
modules exist and their build status; `main()` prints the map so `control-plane` always shows
where the platform stands. Real module code lands as each is built (see ROADMAP.md).
"""

from dataclasses import dataclass
from typing import Literal

from control_plane import __version__
from control_plane.logging_config import get_logger

logger = get_logger(__name__)

Status = Literal["planned", "building", "available"]


@dataclass(frozen=True)
class Module:
    key: str
    name: str
    status: Status
    summary: str


# The vertical slice we build first (core → gateway → prompts → evals → observability → UI).
MODULES: list[Module] = [
    Module("core", "Platform Core", "available", "Orgs, users, RBAC, config, app factory, health."),
    Module(
        "gateway", "AI Gateway", "available", "Provider protocol, model routing, cost metering."
    ),
    Module(
        "prompts",
        "Prompt Registry",
        "available",
        "Versioned prompts with retrieval by name/version.",
    ),
    Module("evals", "Evaluation Engine", "available", "Offline/online scoring over gateway calls."),
    Module(
        "observability",
        "Observability",
        "available",
        "Tracing/metrics (reuses the llm-observatory pattern).",
    ),
    Module("dashboard", "Dashboard", "available", "Operator view over the modules above."),
]


def module_map() -> list[Module]:
    return list(MODULES)


def main() -> None:
    logger.info("Enterprise AI Control Plane v%s — module map:", __version__)
    for m in MODULES:
        logger.info("  [%-9s] %-18s — %s", m.status, m.name, m.summary)


if __name__ == "__main__":
    main()
