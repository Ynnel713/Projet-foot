"""Décomposition de l'écart de chance des tirs entre deux séries appariées (ticket v2-realisme/03h).

A = série avec la ligne défensive du 03c, B = série sans (`LINE_RATIO = 0`, placement du 03b). Pour chaque match, trois
chances moyennes par tir : gardien à sa place réelle, à son point visé, sur la bissectrice sans ligne (03b). L'écart
P(A, réelle) - P(B, réelle) est la somme exacte de quatre termes :

  dynamique avec la ligne  = P(A, réelle) - P(A, visé)   le gardien n'est pas encore à son point visé
  cible                    = P(A, visé) - P(A, 03b)      effet de la ligne (et de la profondeur de face-à-face)
  mélange de tirs          = P(A, 03b) - P(B, 03b)       mêmes gardiens sur la bissectrice, tirs différents
  dynamique sans la ligne  = P(B, 03b) - P(B, réelle)    le même écart pour la série B

Usage : uv run python -m scripts.decomposition_tirs avec.json sans.json
Lecture seule : rien ici ne modifie le jeu."""

from __future__ import annotations

import json
import sys

from scripts.bench_series import summary

KEYS = ("chance du tir (shot_probability)", "chance du tir : gardien à son point visé",
        "chance du tir : gardien sur la bissectrice sans ligne (03b)")
TERMS = ("dynamique avec la ligne", "cible (ligne et face-à-face)", "mélange de tirs", "dynamique sans la ligne")


def decompose(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    """Les quatre termes et l'écart total pour un match (ou une moyenne) de la série A et de la série B."""
    a_real, a_aim, a_03b = (a[k] for k in KEYS)
    b_real, b_aim, b_03b = (b[k] for k in KEYS)
    return dict(zip(TERMS, (a_real - a_aim, a_aim - a_03b, a_03b - b_03b, b_03b - b_real))) | {"écart total": a_real - b_real}


def main(path_a: str, path_b: str) -> None:
    a, b = (json.load(open(p, encoding="utf-8")) for p in (path_a, path_b))
    if a["matchs"] != b["matchs"]:
        raise SystemExit("séries non appariées : les deux séries doivent porter sur les mêmes matchs")
    per_match = []
    for i in range(len(a["matchs"])):
        pair = [{k: s["par match"][k][i] for k in KEYS} for s in (a, b)]
        if all(v is not None for p in pair for v in p.values()):  # match sans tir adverse : écarté
            per_match.append(decompose(*pair))
    print(f"{len(per_match)} matchs appariés sur {len(a['matchs'])}")
    for name in (*TERMS, "écart total"):
        s = summary([m[name] for m in per_match])
        low, high = s["ic95"]
        flag = "" if low <= 0.0 <= high else "  <- significatif"
        print(f"{name} : {s['moyenne']:+.5f} [{low:+.5f} ; {high:+.5f}]{flag}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
