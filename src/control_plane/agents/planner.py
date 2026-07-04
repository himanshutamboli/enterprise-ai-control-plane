"""The planner decides the next action in an agent run.

`SequentialPlanner` is the deterministic default: call each configured tool once, in order, then
finish — enough to demonstrate a bounded planner/executor loop offline. An LLM planner (letting
the model choose tools) drops in behind the same `next_action` shape.
"""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass
class Action:
    kind: Literal["tool", "finish"]
    tool: str | None = None


class Planner(Protocol):
    def next_action(self, tools: list[str], used: set[str]) -> Action: ...


class SequentialPlanner:
    def next_action(self, tools: list[str], used: set[str]) -> Action:
        for tool in tools:
            if tool not in used:
                return Action("tool", tool)
        return Action("finish")
