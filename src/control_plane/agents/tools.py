"""Built-in agent tools: deterministic, offline capabilities an agent can call.

Kept pure and side-effect-free (the CI-safe default set). Real tools (search, DB, HTTP) would
register behind the same `Tool` protocol, exactly like the gateway's providers.
"""

import ast
import operator
import re
from typing import Protocol

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


class Tool(Protocol):
    name: str
    description: str

    def run(self, text: str) -> str: ...


class Calculator:
    name = "calculator"
    description = "Evaluate a basic arithmetic expression found in the text."

    def run(self, text: str) -> str:
        match = re.search(r"[\d.]+(?:\s*[-+*/%^]\s*[\d.]+)+", text)
        expr = (match.group(0) if match else text).replace("^", "**")
        try:
            return str(_safe_eval(ast.parse(expr, mode="eval").body))
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
            return "calculator: no valid expression"


class WordCount:
    name = "word_count"
    description = "Count the words in the text."

    def run(self, text: str) -> str:
        return f"{len(text.split())} words"


class Reverse:
    name = "reverse"
    description = "Reverse the characters of the text."

    def run(self, text: str) -> str:
        return text[::-1]


_TOOLS: dict[str, Tool] = {t.name: t for t in (Calculator(), WordCount(), Reverse())}


def tool_names() -> list[str]:
    return sorted(_TOOLS)


def tool_specs() -> list[dict]:
    return [{"name": t.name, "description": t.description} for t in _TOOLS.values()]


def get_tool(name: str) -> Tool:
    if name not in _TOOLS:
        raise KeyError(name)
    return _TOOLS[name]
