"""Evaluators: score one output, optionally against an expected reference.

Deterministic and offline — the CI-safe defaults. An LLM-as-judge evaluator would drop in behind
the same `Evaluator` protocol (lazy provider call), exactly like the gateway providers.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Score:
    passed: bool
    score: float  # 0.0–1.0


class Evaluator(Protocol):
    name: str

    def evaluate(self, output: str, expected: str | None) -> Score: ...


class ExactMatch:
    name = "exact_match"

    def evaluate(self, output: str, expected: str | None) -> Score:
        ok = output.strip() == (expected or "").strip()
        return Score(passed=ok, score=1.0 if ok else 0.0)


class Contains:
    name = "contains"

    def evaluate(self, output: str, expected: str | None) -> Score:
        ok = bool(expected) and expected.lower() in output.lower()
        return Score(passed=ok, score=1.0 if ok else 0.0)


class NonEmpty:
    name = "non_empty"

    def evaluate(self, output: str, expected: str | None) -> Score:
        ok = bool(output.strip())
        return Score(passed=ok, score=1.0 if ok else 0.0)


_EVALUATORS: dict[str, Evaluator] = {e.name: e for e in (ExactMatch(), Contains(), NonEmpty())}


def evaluator_names() -> list[str]:
    return sorted(_EVALUATORS)


def get_evaluator(name: str) -> Evaluator:
    if name not in _EVALUATORS:
        raise KeyError(name)
    return _EVALUATORS[name]
