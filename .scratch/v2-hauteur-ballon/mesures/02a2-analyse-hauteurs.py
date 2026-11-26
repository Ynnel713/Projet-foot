import json, sys
from collections import Counter
r = json.load(open(sys.argv[1]))
sh = [s for m in r for s in m["shots"]]
print("matchs", len(r), "tirs", len(sh), dict(Counter(s["outcome"] for s in sh)))
fly = [s for s in sh if s["plan"]]
SAVED = {"capté", "repoussé", "claqué"}
cad = [s for s in fly if s["outcome"] == "but" or s["outcome"] in SAVED]
over = [s for s in fly if s["outcome"] == "au-dessus"]
top = lambda s: (s["line_z"] if s["line_z"] is not None else max(0.0, s["plan"][0])) + 0.22
print("critère 1 : cadrés", len(cad), "haut sous 2,44 :", sum(1 for s in cad if top(s) < 2.44),
      "| au-dessus", len(over), "bas au-dessus de 2,44 :", sum(1 for s in over if s["line_z"] > 2.44))
low = [s for s in fly if s["plan"][0] < 0]
print(f"tirs en vol {len(fly)} ; visée sous le sol (droite visée sous 0 à la ligne, après ramenée) {len(low)} "
      f"({100*len(low)/len(fly):.1f} %) ; brute {sum(1 for s in fly if s['plan'][1] < 0)}")
up = [s for s in fly if s["plan"][0] >= 0 and s["line_z"] is not None]
print("visée au-dessus du sol : écart max hauteur prévue / ligne", max(abs(s["line_z"] - s["plan"][0]) for s in up))
crossed = [s for s in fly if s["line_z"] is not None]
lowc = [s for s in low if s["line_z"] is not None]
print(f"franchissent la ligne {len(crossed)} ; dont visés sous le sol {len(lowc)} : roulent (z=0) "
      f"{sum(1 for s in lowc if s['line_z'] == 0.0)}, en rebond {sum(1 for s in lowc if s['line_z'] > 0.0)}")
print("bande 2,22-2,44 à la ligne :", sum(1 for s in crossed if 2.22 < s["line_z"] <= 2.44))
def hist(vals, edges, label):
    print(label)
    c = Counter()
    for z in vals:
        if z == 0.0: c["= 0"] += 1; continue
        for a, b in zip(edges, edges[1:]):
            if a <= z < b: c[f"{a:.2f}-{b:.2f}"] += 1; break
        else: c[f"≥ {edges[-1]:.2f}"] += 1
    for k in ["= 0"] + [f"{a:.2f}-{b:.2f}" for a, b in zip(edges, edges[1:])] + [f"≥ {edges[-1]:.2f}"]:
        print(f"  {k:>11} {c[k]:5d} {'#' * (c[k] // 5)}")
hist([s["line_z"] for s in crossed], [round(0.2 * k, 2) for k in range(16)], "histogramme, hauteur réelle à la ligne (tirs qui la franchissent), pas 0,2 m :")
hist([s["line_z"] for s in crossed if s["line_z"] < 0.5], [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5], "zoom 0-0,5 m :")
hist([max(0.0, s["plan"][0]) for s in cad], [round(0.2 * k, 2) for k in range(13)], "cadrés (buts et arrêtés), hauteur prévue à la ligne 0-2,44 m (négatives -> 0) :")
print("détail 2,00-2,50 par cm :", sorted(Counter(round(s["line_z"], 2) for s in crossed if 2.0 <= s["line_z"] <= 2.5).items()))
print("z max en vol", max(m["zmax_flight"] for m in r), "ticks z<0", sum(m["zneg"] for m in r))
print("empreintes", [(m["i"], m["fp"]) for m in r[:2]])
