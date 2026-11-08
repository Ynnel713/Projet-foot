"""Ticket v2-realisme/03j : issue à 3 s par état du ballon, parts groupées sur les 50 matchs avec intervalle de confiance à 95 %.

Les parts par match sont faussées pour les états rares (un match sans ballon dans l'état pèse comme un zéro, ou n'existe pas) ;
on regroupe donc les ballons de tous les matchs et on rééchantillonne les MATCHS (bootstrap par grappes, 4000 tirages, graine
fixée) : l'intervalle tient compte de ce que les ballons d'un même match ne sont pas indépendants.

    uv run python .scratch/v2-realisme/mesures/03j-intervalles.py .scratch/v2-realisme/mesures/03j.json
"""
import json
import random
import sys

STATES = ["tir : à côté", "tir : contré", "tir : claqué", "tir : but", "tir : repoussé", "tir : capté", "passe ou centre", "autre"]
ISSUES = [("au gardien", "Gardien"), ("à un coéquipier", "Coéquipier"), ("à l'adversaire", "Adversaire"),
          ("encore libre", "Libre"), ("sortie de but", "Sortie de but"), ("corner", "Corner"), ("engagement", "But")]
DRAWS = 4000


def pooled(rows: list[tuple[float, float]]) -> float:
    n = sum(d for _, d in rows)
    return sum(s for s, _ in rows) / n if n else float("nan")


def interval(rows: list[tuple[float, float]], rng: random.Random) -> tuple[float, float]:
    values = sorted(pooled([rng.choice(rows) for _ in rows]) for _ in range(DRAWS))
    values = [v for v in values if v == v]
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def main(path: str) -> None:
    per = json.load(open(path, encoding="utf-8"))["par match"]
    n_matches = len(next(iter(per.values())))
    rng = random.Random(20260923)
    print("| État (ballons sur 50 matchs) | " + " | ".join(label for _, label in ISSUES) + " |")
    print("|---|" + "---|" * len(ISSUES))
    for state in STATES:
        base = f"gardien : ballons avec sortie, état : {state}"
        if base + ", ballon à 3 s, au gardien (part)" not in per:  # état jamais observé (aucun ballon) : absent du JSON
            continue
        counts = [per[base + " (par match)"][i] or 0.0 for i in range(n_matches)]
        total = sum(counts)
        cells = []
        for issue, _ in ISSUES:
            shares = per[f"{base}, ballon à 3 s, {issue} (part)"]
            rows = [((shares[i] or 0.0) * counts[i], counts[i]) for i in range(n_matches)]
            lo, hi = interval(rows, rng)
            cells.append(f"{pooled(rows) * 100:.1f} % [{lo * 100:.1f} ; {hi * 100:.1f}]")
        print(f"| {state} ({total:.0f}) | " + " | ".join(cells) + " |")


main(sys.argv[1])
