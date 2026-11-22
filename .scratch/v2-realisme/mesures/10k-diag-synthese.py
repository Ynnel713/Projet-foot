"""Synthèse du diagnostic 10k. Usage : python3 10k-diag-synthese.py 10k-diag-20.json"""
import json, sys, statistics as st
d = json.load(open(sys.argv[1], encoding="utf-8"))
rows = [r for m in d for r in m["tirs"] if not r["coup franc"]]
n_m = len(d)
GOAL = "but"
def conv(rs): return (sum(r["issue"] == GOAL for r in rs) / len(rs)) if rs else float("nan")
def show(name, rs):
    if not rs: print(f"{name}: 0"); return
    nd = [r["plus proche (m)"] for r in rs]
    print(f"{name}: {len(rs)} tirs ({len(rs)/n_m/2:.2f}/équipe/match), conv {conv(rs):.1%}, xG moy {st.mean(r['xg'] for r in rs):.3f}, "
          f"qualité moy {st.mean(r['qualité'] for r in rs):.3f}")
    print(f"   plus proche défenseur : médiane {st.median(nd):.2f} m, <=1,5 m {sum(x<=1.5 for x in nd)/len(rs):.0%}, "
          f"<=3 m {sum(x<=3 for x in nd)/len(rs):.0%}, >5 m {sum(x>5 for x in nd)/len(rs):.0%}")
    line = [r for r in rs if r["sur la ligne (m)"]]
    cone0 = [r for r in rs if r["dans le cône"] == 0]
    pres = [r for r in rs if r["presseur (m)"] is not None and r["presseur (m)"] <= 5]
    print(f"   ligne de tir couverte : {len(line)/len(rs):.0%} (conv {conv(line):.1%}) ; non couverte conv {conv([r for r in rs if not r['sur la ligne (m)']]):.1%}")
    print(f"   cône tireur-poteaux vide : {len(cone0)/len(rs):.0%} (conv {conv(cone0):.1%}) ; cône occupé conv {conv([r for r in rs if r['dans le cône']]):.1%}")
    print(f"   défenseurs dans le cône : moyenne {st.mean(r['dans le cône'] for r in rs):.2f}")
    print(f"   presseur à 5 m ou moins : {len(pres)/len(rs):.0%} ; distance médiane du presseur {st.median([r['presseur (m)'] for r in pres]) if pres else float('nan'):.2f} m")
    from collections import Counter
    c = Counter(tuple(r["intention du plus proche"] or ("?", "?")) for r in rs)
    print("   intention du plus proche :", ", ".join(f"{k[0]}/{k[1]} {v/len(rs):.0%}" for k, v in c.most_common(5)))
    iss = Counter(r["issue"] for r in rs)
    print("   issues :", ", ".join(f"{k} {v/len(rs):.0%}" for k, v in iss.most_common()))
out = [r for r in rows if not r["surface"]]
band = [r for r in out if 16 <= r["distance"] <= 25]
axe = [r for r in band if r["axe (m)"] <= 9.16]
print(f"{n_m} matchs, {sum(sum(m['buts']) for m in d)/n_m:.2f} buts/match, {len(rows)/n_m/2:.2f} tirs de jeu/équipe")
show("Surface", [r for r in rows if r["surface"]])
show("Hors surface", out)
show("Hors surface 16-25 m", band)
show("Hors surface 16-25 m, axe (|y|<=9,16 m)", axe)
show("Hors surface >25 m", [r for r in out if r["distance"] > 25])
