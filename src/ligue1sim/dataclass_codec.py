"""Codec JSON générique pour les dataclasses du moteur (sans perte).

`encode` transforme un objet (dataclass imbriquée, list/tuple/frozenset/dict,
scalaires, types numpy) en structure JSON pure ; `decode` fait le chemin
inverse en s'appuyant sur les annotations de type de la dataclass cible
(`typing.get_type_hints`) -- aucun schéma à maintenir à la main : ajouter un
champ à une dataclass suffit, tant que son type reste dans ceux gérés ici.

Règles de compatibilité arrière (utilisées par `match_persistence`) : à la
lecture, une clé ABSENTE du JSON retombe sur la valeur par défaut du champ
(donc un document écrit avant l'ajout d'un champ optionnel se relit sans
erreur) ; une clé INCONNUE est ignorée (un document plus récent reste lisible
par un code plus ancien). Un champ obligatoire absent lève `KeyError`.
"""

from __future__ import annotations

import dataclasses
import types
from typing import Any, Union, get_args, get_origin, get_type_hints

import numpy as np


def encode(value: Any) -> Any:
    """Valeur Python -> structure JSON (dict/list/str/int/float/bool/None)."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: encode(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, np.generic):
        return value.item()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(encode(v) for v in value)  # trié : sortie déterministe
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError(f"clés de dict non-str non gérées : {sorted(map(repr, value))[:3]}")
        return {k: encode(v) for k, v in value.items()}
    raise TypeError(f"type non sérialisable : {type(value).__name__}")


def decode(tp: Any, data: Any) -> Any:
    """Structure JSON -> valeur Python du type `tp` (annotation de type)."""
    origin = get_origin(tp)
    if origin in (Union, types.UnionType):
        args = [a for a in get_args(tp) if a is not type(None)]
        if data is None:
            return None
        if args and all(a in (int, str) for a in args):
            # ex. PlayerId = int | str : JSON distingue déjà 3 de "3", rien à convertir.
            if isinstance(data, bool) or not isinstance(data, tuple(args)):
                raise TypeError(f"{data!r} incompatible avec {tp!r}")
            return data
        if len(args) != 1:
            raise TypeError(f"union non gérée : {tp!r}")
        return decode(args[0], data)
    if origin is list:
        (item,) = get_args(tp)
        return [decode(item, x) for x in data]
    if origin is tuple:
        args = get_args(tp)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode(args[0], x) for x in data)
        return tuple(decode(a, x) for a, x in zip(args, data, strict=True))
    if origin is frozenset:
        (item,) = get_args(tp)
        return frozenset(decode(item, x) for x in data)
    if origin is set:
        (item,) = get_args(tp)
        return {decode(item, x) for x in data}
    if origin is dict:
        key_tp, val_tp = get_args(tp)
        return {decode(key_tp, k): decode(val_tp, v) for k, v in data.items()}
    if dataclasses.is_dataclass(tp):
        hints = get_type_hints(tp)
        kwargs = {}
        for f in dataclasses.fields(tp):
            if f.name in data:
                kwargs[f.name] = decode(hints[f.name], data[f.name])
            elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                raise KeyError(f"{tp.__name__}.{f.name} : champ obligatoire absent du document")
        return tp(**kwargs)
    if tp is float:
        return float(data)
    if tp in (int, str, bool):
        return data
    raise TypeError(f"annotation non gérée : {tp!r}")
