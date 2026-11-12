"""Fusion des 8 lots de la série du ticket 28c (50 matchs, graine d'audit) : moyennes par match pondérées par la taille
du lot ; parts des grosses occasions pondérées par leur nombre."""
import json
from pathlib import Path

M = Path(__file__).parent
SIZES = (7, 7, 7, 7, 6, 6, 5, 5)
lots = [json.loads((M / f"28c-lot{i}.json").read_text(encoding="utf-8")) for i in range(8)]
n = sum(SIZES)
per_match = lambda key: sum(l[key] * s for l, s in zip(lots, SIZES)) / n
chances = [l["grosses occasions par match"] * s for l, s in zip(lots, SIZES)]
total = sum(chances)
print(f"matchs : {n} ; grosses occasions : {total:.0f}")
for key in ("buts par match", "tirs tracés par équipe", "grosses occasions par match"):
    if key in lots[0]:
        print(f"{key} : {per_match(key):.2f}")
print("par lot :", [round(l["grosses occasions par match"], 2) for l in lots])
for key in ("grosses occasions sans tir (part)", "grosses occasions : danger moyen au pic"):
    print(f"{key} : {sum(l[key] * c for l, c in zip(lots, chances)) / total:.3f}")
keys = sorted({k for l in lots for k in l if k.startswith("grosses occasions, ")})
for key in keys:
    print(f"{key} : {sum(l.get(key, 0.0) * c for l, c in zip(lots, chances)) / total:.3f}")
