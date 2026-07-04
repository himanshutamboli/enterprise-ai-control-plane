"""Model router: maps a requested model name to the provider that serves it.

The default router sends every model to `MockProvider` so the platform is fully offline in CI.
A deployment swaps in real providers behind the same interface, e.g.::

    router.register("claude-opus-4-8", AnthropicProvider())
"""

from control_plane.gateway.providers import MockProvider, Provider


class UnknownModelError(KeyError):
    """Raised when a request names a model the router doesn't serve."""


class ModelRouter:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, model: str, provider: Provider) -> None:
        self._providers[model] = provider

    def resolve(self, model: str) -> Provider:
        if model not in self._providers:
            raise UnknownModelError(model)
        return self._providers[model]

    def models(self) -> list[str]:
        return sorted(self._providers)


def default_router() -> ModelRouter:
    """CI-safe router: all known models route to the deterministic mock provider."""
    router = ModelRouter()
    mock = MockProvider()
    for model in ("mock-1", "claude-opus-4-8", "claude-haiku-4-5"):
        router.register(model, mock)
    return router
