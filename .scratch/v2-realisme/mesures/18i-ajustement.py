"""Ticket 18i : ajuste les tables de la chance évaluée sur les passes relevées par `18i-tables.py`, sur les matchs de rang pair
et les contrôle sur les matchs de rang impair (moitiés indépendantes, comme les lots des tickets 18g et 18h).
Usage : python .scratch/v2-realisme/mesures/18i-ajustement.py RELEVÉ.json
- coupe par case (adversaire selon sa distance à la trajectoire, près du passeur ou sur le trajet) : coupes par un
  adversaire de la case / adversaires présents dans la case ;
- garde d'une passe = produit des (1 - coupe) de ses adversaires ;
- coupe imprévue d'une passe précise = 1 - non perdues / somme des gardes ;
- passe imprécise non perdue hors coupe, sous 10 m et au-delà = non perdues / somme des gardes."""
from __future__ import annotations

import json
import sys
from collections import Counter

BINS = ["passeur<0.5", "passeur<1", "passeur<6", "trajet<1", "trajet<2", "trajet<3", "trajet<4", "trajet<5", "trajet<6"]


def fit(rows: list) -> dict:
    present, cuts = Counter(), Counter()
    for _, _, _, bins, cut in rows:
        present.update(bins)
        if cut is not None and cut != "hors":
            cuts[cut] += 1
    table = {b: cuts[b] / present[b] if present[b] else 0.0 for b in BINS}
    sums = Counter()
    for precise, length, not_lost, bins, _ in rows:
        keep = 1.0
        for b in bins:
            keep *= 1.0 - table[b]
        group = "précise" if precise else ("imprécise<10" if length < 10.0 else "imprécise>=10")
        sums[group + "|n"] += 1
        sums[group + "|garde"] += keep
        sums[group + "|non perdues"] += not_lost
    share = {g: sums[g + "|non perdues"] / sums[g + "|garde"] for g in ("précise", "imprécise<10", "imprécise>=10")
             if sums[g + "|garde"]}
    return {"table": table, "présents": dict(present), "coupe imprévue": 1.0 - share.get("précise", 1.0),
            "imprécise non perdue <10": share.get("imprécise<10"), "imprécise non perdue >=10": share.get("imprécise>=10"),
            "passes": dict((k, v) for k, v in sums.items() if k.endswith("|n"))}


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    lots = {"ajustement (matchs pairs)": [r for m in data if m["k"] % 2 == 0 for r in m["records"]],
            "contrôle (matchs impairs)": [r for m in data if m["k"] % 2 == 1 for r in m["records"]],
            "tout": [r for m in data for r in m["records"]]}
    for name, rows in lots.items():
        f = fit(rows)
        print(f"== {name} : {len(rows)} passes")
        print("  coupe par case : " + ", ".join(f"{b} {f['table'][b]:.3f} (n {f['présents'].get(b, 0)})" for b in BINS))
        print(f"  coupe imprévue {f['coupe imprévue']:.3f} ; imprécise non perdue <10 m {f['imprécise non perdue <10']:.3f},"
              f" >=10 m {f['imprécise non perdue >=10']:.3f} ; {f['passes']}")
