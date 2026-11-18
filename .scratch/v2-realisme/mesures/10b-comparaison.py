"""Ticket 10b : comparaison avant/après des sorties de `10b-central-couvert.py`.
Usage : uv run python .scratch/v2-realisme/mesures/10b-comparaison.py"""
import glob
import json
from collections import defaultdict

D = ".scratch/v2-realisme/mesures"


def load(mode):
    return sorted((r for f in glob.glob(f"{D}/10b-{mode}-*.json") for r in json.load(open(f))), key=lambda r: r["k"])


def summary(rows):
    n = len(rows)
    out = {"matchs": n, "buts": sum(sum(r["score"]) for r in rows) / n}
    for key in ("shots", "tackles", "fouls", "offsides"):
        out[key] = sum(r[key] for r in rows) / n
    exits = defaultdict(float)
    for r in rows:
        for k, v in r["exits"].items():
            exits[k] += v / n
    out["exits"] = dict(exits)
    for role in ("presseur", "marquage", "couverture"):
        out[f"{role} non couvert"] = sum(v for k, v in exits.items() if k.startswith(f"{role}|False"))
        out[f"{role} non couvert menacé"] = exits.get(f"{role}|False|True", 0.0)
        out[f"{role} sortie"] = sum(v for k, v in exits.items() if k.startswith(f"{role}|"))
    out["non couvert (presse+marque)"] = out["presseur non couvert"] + out["marquage non couvert"]
    out["non couvert menacé (presse+marque)"] = out["presseur non couvert menacé"] + out["marquage non couvert menacé"]
    out["DC hors zone (min)"] = sum(r["press"].get("DC|False", 0.0) for r in rows) / n
    out["DC presse (min)"] = sum(r["press"].get("DC|False", 0.0) + r["press"].get("DC|True", 0.0) for r in rows) / n
    return out


a_rows, b_rows = load("avant"), load("apres")
a, b = summary(a_rows), summary(b_rows)
keys = ["matchs", "buts", "shots", "tackles", "fouls", "offsides", "non couvert (presse+marque)",
        "non couvert menacé (presse+marque)", "presseur sortie", "presseur non couvert", "marquage sortie",
        "marquage non couvert", "couverture sortie", "couverture non couvert", "couverture non couvert menacé",
        "DC presse (min)", "DC hors zone (min)"]
lines = [f"{'(minutes par match sauf compteurs)':38}{'avant':>10}{'après':>10}{'écart':>9}"]
for key in keys:
    va, vb = a[key], b[key]
    lines.append(f"{key:38}{va:10.3f}{vb:10.3f}{(vb - va) / va * 100 if va else 0:+8.1f}%")
# contrôle : le mode « avant » rejoue le moteur du 10a (mêmes scores que 10a-apres)
ref = {r["k"]: r["score"] for f in glob.glob(f"{D}/10a-apres-*.json") for r in json.load(open(f))}
same = sum(1 for r in a_rows if ref.get(r["k"]) == r["score"])
lines.append(f"\ncontrôle : scores du mode avant identiques au 10a livré : {same}/{sum(1 for r in a_rows if r['k'] in ref)}"
             " (graines communes aux deux bancs)")
# écarts appariés (mêmes matchs), intervalle de confiance à 95 % par approximation normale
import statistics as st
pairs = {r["k"]: r for r in a_rows}
lines.append("\nécarts appariés (après - avant), IC 95 % :")
for name, f in (("buts", lambda r: sum(r["score"])), ("tirs", lambda r: r["shots"]), ("tacles", lambda r: r["tackles"]),
                ("hors-jeu", lambda r: r["offsides"]), ("fautes", lambda r: r["fouls"])):
    d = [f(r) - f(pairs[r["k"]]) for r in b_rows if r["k"] in pairs]
    m = st.mean(f(pairs[r["k"]]) for r in b_rows if r["k"] in pairs)
    half = 1.96 * st.stdev(d) / len(d) ** 0.5
    lines.append(f"  {name:9} {st.mean(d):+.2f} ({st.mean(d) / m * 100:+.1f} %), IC [{(st.mean(d) - half) / m * 100:+.1f} % ;"
                 f" {(st.mean(d) + half) / m * 100:+.1f} %], n = {len(d)}")
print("\n".join(lines))
open(f"{D}/10b-comparaison.txt", "w").write("\n".join(lines) + "\n")
json.dump({"avant": a, "apres": b}, open(f"{D}/10b-comparaison.json", "w"), ensure_ascii=False, indent=1)
