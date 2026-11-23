"""Synthèse du ticket v2-hauteur-ballon/02a2 : compare la série d'avant et celle d'après (`02a2-serie.py`), match par
match (score, tirs, empreinte 2D), puis lit la hauteur réelle des tirs d'après : à la ligne selon l'issue, au passage du
gardien, au contre. Utilisation : `python 02a2-synthese.py avant.json apres.json`."""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter

BAR = 2.44
AERIAL = 2.5


def q(values: list[float]) -> str:
    if not values:
        return "aucun"
    v = sorted(values)
    pick = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    return (f"n={len(v)}, min {v[0]:.2f}, q10 {pick(0.1):.2f}, médiane {statistics.median(v):.2f}, "
            f"q90 {pick(0.9):.2f}, max {v[-1]:.2f}")


before = {r["match"]: r for r in json.load(open(sys.argv[1], encoding="utf-8"))}
after = {r["match"]: r for r in json.load(open(sys.argv[2], encoding="utf-8"))}
same_score = sum(before[i]["score"] == after[i]["score"] for i in after)
key = lambda s: (s["minute"], s["joueur"], s["issue"], s["origine"])
same_shots = sum([key(s) for s in before[i]["tirs"]] == [key(s) for s in after[i]["tirs"]] for i in after)
same_2d = sum(before[i]["empreinte_2d"] == after[i]["empreinte_2d"] for i in after)
print(f"matchs : {len(after)} ; scores identiques {same_score} ; tirs identiques (minute, tireur, issue, origine) "
      f"{same_shots} ; piste 2D identique {same_2d}")
print(f"buts : {sum(sum(r['score']) for r in before.values())} avant, {sum(sum(r['score']) for r in after.values())} après")
shots = [s for r in after.values() for s in r["tirs"]]
print("issues :", dict(Counter(s["issue"] for s in shots)))
print(f"z min sur la piste : {min(r['z_min'] for r in after.values()):.4f} ; modes incohérents : "
      f"{sum(r['mode_incohérent'] for r in after.values())}")
by = lambda outcome: [s["ligne_z"] for s in shots if s["issue"] == outcome and s["ligne_z"] is not None]
goals, over, wide = by("but"), by("au-dessus"), by("à côté")
print(f"buts, hauteur à la ligne : {q(goals)} ; sous la barre : {sum(z < BAR for z in goals)}/{len(goals)}")
print(f"au-dessus, hauteur à la ligne : {q(over)} ; au-dessus de la barre : {sum(z >= BAR for z in over)}/{len(over)}")
print(f"à côté, hauteur à la ligne : {q(wide)} ; rasants : {sum(z == 0.0 for z in wide)}")
print(f"tirs rasants (hauteur 0 à la ligne) parmi les buts : {sum(z == 0.0 for z in goals)}")
missing = [s for s in shots if s["issue"] in ("but", "au-dessus", "à côté") and s["ligne_z"] is None]
print(f"tirs sur la ligne sans hauteur relevée : {len(missing)} ({dict(Counter(s['issue'] for s in missing))})")
keeper = [s["gardien_z"] for s in shots if s["gardien_z"] is not None]
saves = [s["gardien_z"] for s in shots if s["gardien_z"] is not None and s["issue"] in ("capté", "repoussé", "claqué")]
print(f"passage au gardien (tous tirs jugés) : {q(keeper)} ; au-dessus de 2,44 m : {sum(z >= BAR for z in keeper)}")
print(f"arrêts : {q(saves)} ; au-dessus de 2,44 m : {sum(z >= BAR for z in saves)}")
blocks = [s["contre_z"] for s in shots if s["contre_z"] is not None]
print(f"contres : {q(blocks)} ; au-dessus de 2,5 m : {sum(z > AERIAL for z in blocks)} ; au-dessus de 1,8 m : "
      f"{sum(z > 1.8 for z in blocks)}")
