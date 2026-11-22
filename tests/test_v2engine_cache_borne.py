"""Caches bornés du moteur V2 (ticket v2-realisme/27e).

`_lerp` reçoit des notes réelles continues (fatigue) : un cache illimité grossissait sans fin (872 Mo de pic après trois
matchs dans un même processus). Le cache est borné ; un test de garde refuse tout nouveau cache illimité dans
`v2engine/`.
"""

from __future__ import annotations

import ast
import pathlib

from v2engine import movement

V2ENGINE = pathlib.Path(__file__).resolve().parent.parent / "v2engine"


def test_lerp_cache_is_bounded():
    assert movement._lerp.cache_info().maxsize == 4096


def test_lerp_cache_stays_bounded_with_continuous_notes():
    movement._lerp.cache_clear()
    for i in range(10_000):
        movement._lerp(10.0 + i / 1000.0, ((10.0, 25.0), (99.0, 36.5)))
    assert movement._lerp.cache_info().currsize <= 4096


def _unbounded(decorator: ast.expr) -> bool:
    """`cache`, `functools.cache`, `lru_cache(None)` ou `lru_cache(maxsize=None)` (nom simple ou préfixé)."""
    def name(node: ast.expr) -> str:
        return node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", "")

    if name(decorator) == "cache":
        return True
    if isinstance(decorator, ast.Call) and name(decorator.func) == "lru_cache":
        size = decorator.args[0] if decorator.args else next(
            (k.value for k in decorator.keywords if k.arg == "maxsize"), None)
        return isinstance(size, ast.Constant) and size.value is None
    return False


def test_no_unbounded_cache_in_v2engine():
    found = [
        f"{path.name}:{node.lineno}"
        for path in sorted(V2ENGINE.rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in node.decorator_list
        if _unbounded(decorator)
    ]
    assert found == []
