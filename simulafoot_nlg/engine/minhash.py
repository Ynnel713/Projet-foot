"""Signature MinHash d'un texte, via hashlib (aucune dependance externe).

Sert a la penalite de similarite (anti_repeat.similarity_penalty) : deux textes rendus
DIFFERENTS peuvent etre quasi identiques une fois les slots remplis, ce que l'identifiant de
phrase ne voit pas. Chaque texte est decoupe en shingles de mots (3 mots consecutifs, en
minuscules, sans ponctuation ni accents composes/decomposes) ; la signature est le minimum, par
permutation, du hash des shingles. La part de composantes egales entre deux signatures estime la
similarite de Jaccard des deux ensembles de shingles.

DETERMINISME : sha256, jamais hash() -- le resultat ne depend pas de PYTHONHASHSEED (verrouille par
tests/test_minhash.py, en sous-processus).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Sequence

NB_PERMUTATIONS = 64
TAILLE_SHINGLE = 3  # mots consecutifs
_MOT_RE = re.compile(r"\w+")
_VALEUR_MAX = 2**64 - 1


def shingles(text: str, taille: int = TAILLE_SHINGLE) -> frozenset[str]:
    """Ensemble des suites de `taille` mots consecutifs (mots en minuscules, NFC). Un texte de
    moins de `taille` mots donne un seul shingle (tout le texte) ; un texte sans mot, aucun."""
    mots = [mot.lower() for mot in _MOT_RE.findall(unicodedata.normalize("NFC", text))]
    if not mots:
        return frozenset()
    if len(mots) < taille:
        return frozenset({" ".join(mots)})
    return frozenset(" ".join(mots[i : i + taille]) for i in range(len(mots) - taille + 1))


def _hash(permutation: int, shingle: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{permutation}|{shingle}".encode()).digest()[:8], "big")


def signature(text: str, *, permutations: int = NB_PERMUTATIONS) -> tuple[int, ...]:
    """Signature MinHash de `text` : `permutations` entiers. Un texte sans mot a une signature
    constante (toutes composantes au maximum) : deux textes vides sont identiques."""
    ensemble = shingles(text)
    return tuple(
        min((_hash(i, shingle) for shingle in ensemble), default=_VALEUR_MAX) for i in range(permutations)
    )


def similarite(a: Sequence[int], b: Sequence[int]) -> float:
    """Estimation de la similarite de Jaccard [0, 1] : part des composantes egales. Leve
    ValueError si les signatures n'ont pas la meme longueur (nombre de permutations different : les
    comparer fausserait le resultat) ou sont vides."""
    if len(a) != len(b) or not a:
        raise ValueError(f"Signatures incomparables (longueurs {len(a)} et {len(b)}).")
    return sum(x == y for x, y in zip(a, b, strict=True)) / len(a)


def serialiser(sig: Sequence[int]) -> str:
    """Forme stockee dans similarity_signatures.signature (JSON, liste d'entiers)."""
    return json.dumps(list(sig))


def deserialiser(texte: str) -> tuple[int, ...]:
    return tuple(int(x) for x in json.loads(texte))
