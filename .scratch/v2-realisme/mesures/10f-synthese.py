"""Synthèse de la série appariée du ticket v2-realisme/10f (moyennes par match, intervalle à 95 % de la différence
appariée). Usage : python3 .scratch/v2-realisme/mesures/10f-synthese.py > .scratch/v2-realisme/mesures/10f-serie-50-synthese.txt"""
import json
import math
import statistics as st
from pathlib import Path

d = Path(__file__).parent
A = {r["match"]: r for r in json.loads((d / "10f-avant-50.json").read_text(encoding="utf-8"))}
B = {r["match"]: r for r in json.loads((d / "10f-apres-50.json").read_text(encoding="utf-8"))}
ids = sorted(A)
n = len(ids)


def line(name, f):
    a, b = [f(A[i]) for i in ids], [f(B[i]) for i in ids]
    diff = [y - x for x, y in zip(a, b)]
    h = 1.96 * st.stdev(diff) / math.sqrt(n)
    print(f"{name:<58} avant {st.mean(a):8.2f}   après {st.mean(b):8.2f}   écart {st.mean(diff):+7.2f} ± {h:.2f}")


def ratio(name, num, den):
    for tag, D in (("avant", A), ("après", B)):
        x, y = sum(num(D[i]) for i in ids), sum(den(D[i]) for i in ids)
        print(f"[{tag}] {name} : {x / max(1, y):.3f}", end="   ")
    print()


def box(r, inside):
    return [s for s in r["tirs"] if s["surface"] == inside]


print(f"matchs {n} (mêmes graines et affiches avant / après)")
line("instants de possession sur l'aile du dernier tiers, par match", lambda r: r["instants_aile"])
ratio("défenseurs de champ dans la surface à ces instants", lambda r: r["défenseurs_surface"], lambda r: r["instants_aile"])
ratio("profondeur de l'avant-dernier défenseur à ces instants (m)", lambda r: r["profondeur_ligne"], lambda r: r["instants_aile"])
for z in ("premier poteau", "point de penalty", "second poteau", "retrait"):
    ratio(f"zone {z} tenue (part des instants où la règle la demande)", lambda r, z=z: r["zones_tenues"][z],
          lambda r, z=z: r["zones_demandées"][z])
line("tirs dans les 10 s après un passage sur l'aile, par match", lambda r: r["tirs_après_aile"])
line("buts dans les 10 s après un passage sur l'aile, par match", lambda r: r["buts_après_aile"])
line("tirs par équipe", lambda r: len(r["tirs"]) / 2)
line("tirs dans la surface par équipe", lambda r: len(box(r, True)) / 2)
line("tirs hors surface par équipe", lambda r: len(box(r, False)) / 2)
line("buts par match", lambda r: len(r["buts"]))
line("buts dans la surface par match", lambda r: sum(s["issue"] == "but" for s in box(r, True)))
line("xG neutre par match", lambda r: sum(s["xg"] or 0.0 for s in r["tirs"]))
line("hors-jeu par match", lambda r: r["hors_jeu"])
line("passes par match", lambda r: r["passes"])
line("pertes de balle par match", lambda r: r["pertes"])
ratio("conversion dans la surface", lambda r: sum(s["issue"] == "but" for s in box(r, True)), lambda r: len(box(r, True)))
ratio("conversion hors surface", lambda r: sum(s["issue"] == "but" for s in box(r, False)), lambda r: len(box(r, False)))
