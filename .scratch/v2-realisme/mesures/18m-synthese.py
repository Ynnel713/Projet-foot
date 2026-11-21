"""Synthèse de la série appariée du ticket v2-realisme/18m (moyennes par match ou par équipe, intervalle à 95 % de la
différence appariée, match par match). Usage : python3 .scratch/v2-realisme/mesures/18m-synthese.py
.scratch/v2-realisme/mesures 18m-apres-005-50.json > 18m-serie-50-synthese-005.txt (idem 003)."""
import json
import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
A = {r["match"]: r for r in json.loads((d / "18m-avant-50.json").read_text(encoding="utf-8"))}
B = {r["match"]: r for r in json.loads((d / (sys.argv[2] if len(sys.argv) > 2 else "18m-apres-005-50.json")).read_text(encoding="utf-8"))}
ids = sorted(A)
n = len(ids)


def line(name, f, scale=1.0):
    a = [f(A[i]) * scale for i in ids]
    b = [f(B[i]) * scale for i in ids]
    diff = [y - x for x, y in zip(a, b)]
    h = 1.96 * st.stdev(diff) / math.sqrt(n)
    print(f"{name:<48} avant {st.mean(a):7.2f}   après {st.mean(b):7.2f}   écart {st.mean(diff):+7.2f} ± {h:.2f}")


def shots(r, box=None):
    return [s for s in r["tirs"] if box is None or s["surface"] == box]


def goals_(r, box=None):
    return sum(s["issue"] == "but" for s in shots(r, box))


print(f"matchs {n} (mêmes graines et affiches avant / après)")
line("tirs par équipe", lambda r: len(shots(r)) / 2)
line("tirs dans la surface par équipe", lambda r: len(shots(r, True)) / 2)
line("tirs hors surface par équipe", lambda r: len(shots(r, False)) / 2)
line("tirs 16,5-25 m dans l'axe hors surface, par équipe",
     lambda r: sum(1 for s in shots(r, False) if s["distance"] < 25) / 2)
line("buts par match", lambda r: len(r["buts"]))
line("buts dans la surface par match", lambda r: goals_(r, True))
line("buts hors surface par match", lambda r: goals_(r, False))
line("xG neutre par match", lambda r: sum(s["xg"] or 0.0 for s in shots(r)))
line("xG neutre hors surface par match", lambda r: sum(s["xg"] or 0.0 for s in shots(r, False)))
line("passes par match", lambda r: r["passes"])
line("pertes de balle par match", lambda r: r["pertes"])
for tag, D in (("avant", A), ("après", B)):
    allshots = [s for i in ids for s in D[i]["tirs"]]
    goals = [g for i in ids for g in D[i]["buts"]]
    out = [s for s in allshots if not s["surface"]]
    inn = [s for s in allshots if s["surface"]]
    gout, ginn = sum(s["issue"] == "but" for s in out), sum(s["issue"] == "but" for s in inn)
    print(f"\n[{tag}] part des tirs hors surface {100 * len(out) / len(allshots):.1f} % ; conversion hors surface "
          f"{100 * gout / max(1, len(out)):.1f} %, dans la surface {100 * ginn / max(1, len(inn)):.1f} % ; "
          f"part des buts marqués sur tir hors surface {100 * gout / max(1, gout + ginn):.1f} %")
    fam = Counter(g["famille"] for g in goals)
    print(f"[{tag}] origine des buts : " + ", ".join(f"{k} {100 * v / len(goals):.1f} %" for k, v in fam.most_common()))
    fast = sum(1 for g in goals if g["famille"] == "récupération" and (g["délai (s)"] or 99) <= 15)
    print(f"[{tag}] buts sur récupération en 15 s au plus : {fast / n:.2f} par match")
    print(f"[{tag}] profil Long Shots (tirs hors surface) :")
    for lo, hi in ((0, 40), (40, 55), (55, 70), (70, 101)):
        ss = [s for s in out if s["long_shots"] is not None and lo <= s["long_shots"] < hi]
        g = sum(s["issue"] == "but" for s in ss)
        print(f"   Long Shots {lo}-{hi - 1} : {len(ss) / (2 * n):5.2f} tirs par équipe, part {100 * len(ss) / max(1, len(out)):5.1f} %, "
              f"conversion {100 * g / max(1, len(ss)):5.1f} %")
