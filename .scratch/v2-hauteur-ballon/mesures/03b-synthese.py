"""Synthèse du ticket v2-hauteur-ballon/03b : séries d'avant et d'après (`03b-serie.py`), mêmes matchs. Issues des tirs
par match (écart apparié, IC 95 % en approximation normale), contres et arrêts au-dessus de l'atteinte du joueur.
Utilisation : `python 03b-synthese.py avant.json apres.json`."""

from __future__ import annotations

import json
import math
import statistics
import sys

SAVES = ("capté", "repoussé", "claqué")


def per_match(rows: list[dict], test) -> list[float]:
    return [sum(1 for s in r["tirs"] if test(s)) for r in rows]


def paired(before: list[float], after: list[float]) -> str:
    d = [a - b for a, b in zip(after, before)]
    m, sd = statistics.fmean(d), statistics.stdev(d)
    half = 1.96 * sd / math.sqrt(len(d))
    flag = "  <- significatif" if abs(m) > half else ""
    return (f"{statistics.fmean(before):.2f} -> {statistics.fmean(after):.2f} par match, écart {m:+.2f} "
            f"[{m - half:+.2f} ; {m + half:+.2f}]{flag}")


def above(rows: list[dict]) -> str:
    blocks = [s for r in rows for s in r["tirs"] if s.get("contre_atteinte") is not None and s["contre_z"] is not None]
    saves = [s for r in rows for s in r["tirs"] if s.get("gardien_atteinte") is not None and s["gardien_z"] is not None]
    b = sum(s["contre_z"] > s["contre_atteinte"] + 1e-9 for s in blocks)
    k = sum(s["gardien_z"] > s["gardien_atteinte"] + 1e-9 for s in saves)
    aligned = all(r["contres_journal"] == sum(s["issue"] == "contré" for s in r["tirs"]) for r in rows)
    return (f"contres au-dessus de l'atteinte : {b}/{len(blocks)} ; arrêts au-dessus des mains : {k}/{len(saves)} "
            f"(journal aligné sur les contres : {aligned})")


before = sorted(json.load(open(sys.argv[1], encoding="utf-8")), key=lambda r: r["match"])
after = sorted(json.load(open(sys.argv[2], encoding="utf-8")), key=lambda r: r["match"])
print("avant :", above(before))
print("après :", above(after))
for label, test in (("buts", lambda s: s["issue"] == "but"), ("tirs", lambda s: True),
                    ("contrés", lambda s: s["issue"] == "contré"), ("arrêts", lambda s: s["issue"] in SAVES),
                    ("au-dessus", lambda s: s["issue"] == "au-dessus"), ("à côté", lambda s: s["issue"] == "à côté")):
    print(f"{label} : {paired(per_match(before, test), per_match(after, test))}")
print("buts (score) :", paired([sum(r["score"]) for r in before], [sum(r["score"]) for r in after]))
za = [s["contre_z"] for r in after for s in r["tirs"] if s["contre_z"] is not None]
zb = [s["contre_z"] for r in before for s in r["tirs"] if s["contre_z"] is not None]
print(f"hauteur au contre : max {max(zb):.2f} m avant, {max(za):.2f} m après")
ka = [s["gardien_z"] for r in after for s in r["tirs"] if s["gardien_z"] is not None]
kb = [s["gardien_z"] for r in before for s in r["tirs"] if s["gardien_z"] is not None]
print(f"hauteur au passage du gardien : max {max(kb):.2f} m avant, {max(ka):.2f} m après")
print(f"z min après : {min(r['z_min'] for r in after):.4f} ; modes incohérents : {sum(r['mode_incohérent'] for r in after)}")
