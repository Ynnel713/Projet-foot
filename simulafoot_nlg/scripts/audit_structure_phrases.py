"""Audit structurel (sujet, verbe principal, type de complement) pour les
pilotes V2 -- complement du n-gramme (qui ne detecte que des suites de MOTS
identiques, pas un squelette syntaxique partage avec un vocabulaire
different). Module reutilisable pour chaque nouveau scenario V2, PAS un
module moteur.

METHODE, LIMITES ASSUMEES (pas de spaCy/NLTK installes dans ce depot) :
    - sujet : "JOUEUR" si {joueur} est utilise, sinon le 1er mot (nickname
      SURNOM, ex. "Le roc").
    - verbe principal : heuristique -- le mot immediatement apres le sujet
      (apres avoir saute "ne"/"n'" pour les negations). Ne gere PAS les
      verbes composes, les inversions, ni la vraie analyse syntaxique --
      c'est un PROXY, pas un parseur. Chaque signal releve doit etre relu a
      la main avant conclusion (un triplet partage peut etre un faux positif,
      voir l'exemple "se" capte comme pseudo-verbe sur deux reflexifs
      differents dans le pilote FAUTE_SIMPLE du 01/10/2026).
    - type de complement : sac de mots-cles presents dans le reste de la
      phrase (adversaire, ballon/cuir, faute, arbitre, tete/aerien, tacle,
      corner, duel) -- une phrase peut porter plusieurs tags.

Usage (depuis un script de pilote ponctuel, pas depuis ce module) :
    from audit_structure_phrases import audit
    audit("MON_SCENARIO", [t for t, _ in MES_PHRASES])
"""

from __future__ import annotations

import re

_MOTS_CLES_COMPLEMENT = {
    "adversaire": r"\{adversaire\}",
    "ballon": r"\bballon\b|\bcuir\b",
    "faute": r"\bfaute\b|\bcoup franc\b",
    "arbitre": r"\barbitre\b",
    "aerien": r"a[ée]rien|t[êe]te\b",
    "tacle": r"\btacle\b",
    "corner": r"\bcorner\b",
    "duel": r"\bduel\b",
}


_SUJETS_CONNUS = ("joueur", "passeur", "receveur", "adversaire")


def _sujet_et_verbe(texte: str) -> tuple[str, str]:
    # Prend le slot sujet connu dont la POSITION dans le texte est la plus
    # petite (gere les ouvertures adverbiales/participiales frontales, ex.
    # "D'un corner excentre, {passeur} trouve..." -- {passeur} n'est pas en
    # position 0 mais reste le vrai sujet). Un {adversaire} mentionne plus
    # loin dans la phrase (objet, pas sujet) n'est donc pas pris a tort si
    # {passeur}/{receveur} apparaissent avant lui dans le texte.
    positions = [
        (texte.index("{" + nom_slot + "}"), nom_slot)
        for nom_slot in _SUJETS_CONNUS
        if "{" + nom_slot + "}" in texte
    ]
    if positions:
        pos, nom_slot = min(positions)
        marqueur = "{" + nom_slot + "}"
        return (nom_slot.upper(), _premier_verbe(texte[pos + len(marqueur):]))
    m = re.match(r"^(L[e'’]\s?\S+)\s+(.*)$", texte)
    if not m:
        return ("INCONNU", "?")
    return ("SURNOM", _premier_verbe(m.group(2)))


def _premier_verbe(reste: str) -> str:
    mots = reste.strip().split()
    i = 0
    while i < len(mots) and mots[i].lower() in {"ne", "n'", "n’"}:
        i += 1
    return mots[i].lower().strip(",.!:;") if i < len(mots) else "?"


def _tags_complement(texte: str) -> frozenset[str]:
    tags = set()
    for tag, pattern in _MOTS_CLES_COMPLEMENT.items():
        if re.search(pattern, texte, re.IGNORECASE):
            tags.add(tag)
    return frozenset(tags)


def audit(nom_pilote: str, phrases: list[str]) -> list[tuple[tuple[str, str, frozenset[str]], list[int]]]:
    """Imprime un rapport et retourne les triplets (sujet, verbe, tags)
    partages par >= 2 phrases -- a relire a la main, pas une preuve
    automatique de doublon."""
    triplets: dict[tuple[str, str, frozenset[str]], list[int]] = {}
    for i, texte in enumerate(phrases, 1):
        sujet, verbe = _sujet_et_verbe(texte)
        tags = _tags_complement(texte)
        triplet = (sujet, verbe, tags)
        triplets.setdefault(triplet, []).append(i)

    print(f"=== {nom_pilote} : {len(phrases)} phrases, {len(triplets)} triplets distincts ===")
    doublons = [(t, idxs) for t, idxs in triplets.items() if len(idxs) >= 2]
    for (sujet, verbe, tags), idxs in sorted(doublons, key=lambda x: -len(x[1])):
        print(f"  [{sujet}, verbe={verbe!r}, tags={sorted(tags)}] -> phrases {idxs}")
        for idx in idxs:
            print(f"      #{idx}: {' '.join(phrases[idx - 1].split())[:100]}")
    if not doublons:
        print("  (aucun triplet partage par >= 2 phrases)")
    return doublons
