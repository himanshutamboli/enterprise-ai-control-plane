"""Providers behind one protocol + token→cost pricing.

`MockProvider` is deterministic and offline — the CI-safe default. `AnthropicProvider` is the
real drop-in (lazy `anthropic` import, model `claude-opus-4-8`). Both return the same
`CompletionResponse` with usage and cost, so callers never branch on provider.
"""

from dataclasses import dataclass
from typing import Protocol

# $ per 1M tokens (input, output).
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "mock-1": (0.5, 1.5),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    if model not in PRICES:
        return 0.0
    price_in, price_out = PRICES[model]
    return prompt_tokens / 1e6 * price_in + completion_tokens / 1e6 * price_out


@dataclass
class CompletionRequest:
    model: str
    prompt: str
    max_tokens: int = 512
    system: str | None = None


@dataclass
class CompletionResponse:
    model: str
    provider: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class Provider(Protocol):
    name: str

    def complete(self, request: CompletionRequest) -> CompletionResponse: ...


class MockProvider:
    """Deterministic, offline provider — the CI-safe default."""

    name = "mock"

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        text = f"[mock:{request.model}] " + " ".join(reversed(request.prompt.split()))
        prompt_tokens = max(1, len(request.prompt.split()))
        completion_tokens = max(1, len(text.split()))
        return CompletionResponse(
            model=request.model,
            provider=self.name,
            text=text[: request.max_tokens * 4],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=estimate_cost(request.model, prompt_tokens, completion_tokens),
        )


class AnthropicProvider:
    """Real drop-in — routes calls to the Anthropic API. Requires ANTHROPIC_API_KEY."""

    name = "anthropic"

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        import anthropic

        client = anthropic.Anthropic()
        kwargs: dict = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system:
            kwargs["system"] = request.system
        response = client.messages.create(**kwargs)
        text = "".join(b.text for b in response.content if b.type == "text")
        pt, ct = response.usage.input_tokens, response.usage.output_tokens
        return CompletionResponse(
            model=request.model,
            provider=self.name,
            text=text,
            prompt_tokens=pt,
            completion_tokens=ct,
            cost_usd=estimate_cost(request.model, pt, ct),
        )
