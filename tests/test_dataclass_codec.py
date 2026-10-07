import json
from dataclasses import dataclass, field

import numpy as np
import pytest

from ligue1sim.dataclass_codec import decode, encode


@dataclass(frozen=True)
class _Inner:
    a: int
    b: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Outer:
    inner: _Inner
    items: list[_Inner]
    tags: frozenset[str]
    scores: dict[str, float]
    maybe: _Inner | None = None
    optional_new: int | None = None
    extra: list[int] = field(default_factory=list)


def test_roundtrip_nested_types_through_json():
    obj = _Outer(
        _Inner(1, ("x", "y")), [_Inner(2), _Inner(3, ("z",))], frozenset({"b", "a"}), {"k": 0.1 + 0.2}, _Inner(9), 5, [1, 2]
    )
    assert decode(_Outer, json.loads(json.dumps(encode(obj), allow_nan=False))) == obj


def test_numpy_scalars_are_encoded_as_python():
    assert encode({"a": np.int64(3), "b": np.float64(1.5)}) == {"a": 3, "b": 1.5}
    json.dumps(encode({"a": np.int64(3)}))


def test_missing_optional_uses_default_and_unknown_keys_are_ignored():
    data = {"inner": {"a": 1, "zzz": 0}, "items": [], "tags": [], "scores": {}}
    out = decode(_Outer, data)
    assert out.maybe is None and out.optional_new is None and out.extra == []


def test_missing_required_field_raises():
    with pytest.raises(KeyError):
        decode(_Outer, {"items": [], "tags": [], "scores": {}})
