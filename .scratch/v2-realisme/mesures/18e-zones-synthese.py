"""Synthèse du diagnostic 18e-zones.py : par zone (surface / hors surface) et tranche de distance, nombre de tirs par
équipe et par match, issues et conversion. Usage : uv run python .scratch/v2-realisme/mesures/18e-zones-synthese.py DOSSIER"""
import glob
import json
import sys

sys.path.insert(0, ".")
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, in_penalty_area

R = [r for f in sorted(glob.glob(f"{sys.argv[1]}/lot*.json")) for r in json.load(open(f))]
matches = len({r["m"] for r in R}) or 1


def dist(r):  # au but attaqué : home vers x = longueur (même convention que `in_penalty_area`)
    gx = PITCH_LENGTH_M if r["team"] == "home" else 0.0
    return Vec2(r["x"], r["y"]).distance_to(Vec2(gx, PITCH_WIDTH_M / 2.0))


def line(name, S):
    if not S:
        return
    goals = sum(r["outcome"] == "but" for r in S)
    print(f"{name:<24} tirs/équipe {len(S) / matches / 2:5.2f}  but {100 * goals / len(S):5.1f} %  "
          + "  ".join(f"{o} {100 * sum(r['outcome'] == o for r in S) / len(S):4.1f}" for o in
                      ("contré", "à côté", "au-dessus", "dévissé", "capté", "repoussé", "claqué"))
          + f"  xG moyen {sum(r['xg'] or 0 for r in S) / len(S):.3f}")


pens = [r for r in R if r["origin"] == "penalty"]
open_play = [r for r in R if r["origin"] != "penalty"]
print(f"{matches} matchs, {len(R)} tirs (dont {len(pens)} penaltys)")
box = [r for r in open_play if in_penalty_area(r["team"], Vec2(r["x"], r["y"]))]
out = [r for r in open_play if r not in box]
line("toutes (hors penaltys)", open_play)
line("surface", box)
line("hors surface", out)
for lo, hi in ((0, 11), (11, 16.5), (16.5, 20), (20, 25), (25, 30), (30, 99)):
    line(f"distance [{lo} ; {hi}[", [r for r in open_play if lo <= dist(r) < hi])
print(f"part des tirs dans la surface : {100 * len(box) / max(1, len(open_play)):.1f} % (réel 68,3 %)")
