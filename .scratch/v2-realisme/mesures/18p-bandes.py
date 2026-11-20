"""Diagnostic du ticket v2-realisme/18p, quatrième passe : part non perdue hors coupe selon l'écart latéral RÉALISÉ au
receveur (L x tan|angle tiré|), comparée aux parts par bande du moteur (`possession._LATERAL_NOT_LOST`, 0,99 / 0,99 /
0,98 / 0,80, la dernière au-delà de 4 m sans borne) ; par Passing ; masse de la loi d'écart au-delà de 4 et de 8 m selon
Passing. Passes non coupées par un adversaire de la table seulement.
Usage : python .scratch/v2-realisme/mesures/18p-bandes.py D/rec-26*.json"""
import json
import math
import sys

sys.path.insert(0, ".")
import v2engine.possession as P

R = [r for p in sys.argv[1:] for r in json.load(open(p))]


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut_obs(r):
    return bool(r.get("first")) and r["first_team"] != r["team"] and any(o["n"] == r["first"] and o["cut"] > 0 for o in r["opp"])


def dev(r):
    return r["L"] * math.tan(math.radians(abs(r["ang_deg"])))


B = ((0, 1), (1, 2), (2, 4), (4, 6), (6, 8), (8, 12), (12, 99))
print("Part non perdue (hors coupe par un adversaire de la table) selon l'écart latéral réalisé au receveur")
for lo, hi in ((0, 50), (50, 70), (70, 100), (0, 100)):
    print(f" Passing {lo}-{hi}")
    for a, b in B:
        S = [r for r in R if lo <= r["passing"] < hi and a <= dev(r) < b and not cut_obs(r)]
        if len(S) < 20:
            continue
        o = sum(not lost(r) for r in S) / len(S)
        print(f"  écart {a:>2}-{b:<2} m  n {len(S):6d}  non perdue {o:.3f} ± {1.96 * math.sqrt(max(o * (1 - o), 1e-4) / len(S)):.3f}")
print("Masse prévue par la loi d'écart (moyenne des poids de bande enregistrés) et réalisée, au-delà de 4 m")
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    S = [r for r in R if lo <= r["passing"] < hi]
    print(f"  Passing {lo}-{hi}  prévue {sum(r['w'][3] for r in S) / len(S):.3f}  réalisée {sum(dev(r) >= 4 for r in S) / len(S):.3f}"
          f"  au-delà de 8 m réalisée {sum(dev(r) >= 8 for r in S) / len(S):.3f}")
