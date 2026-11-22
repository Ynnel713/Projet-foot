"""Effet causal de l'élan sur les mêmes tirs (série après du 03f) : arrêt jugé avec et sans élan (même écart, même
temps), et écart à la portée immobile selon l'élan (effet de sélection).
Usage : uv run python .scratch/v2-realisme/mesures/03f-bascules.py <après.json>"""
import json, statistics, sys
sys.path.insert(0, ".")
from v2engine.shooting import keeper_reach_m

rows = json.load(open(sys.argv[1], encoding="utf-8"))
shots = [s for r in rows for s in r["tirs"] if s["écart"] is not None and s["issue"] in ("capté", "repoussé", "claqué", "but")]
gained = sum(keeper_reach_m(s["temps"]) < s["écart"] <= keeper_reach_m(s["temps"], s["élan"]) for s in shots)
lost = sum(keeper_reach_m(s["temps"], s["élan"]) < s["écart"] <= keeper_reach_m(s["temps"]) for s in shots)
consistent = sum((s["issue"] != "but") == (s["écart"] <= keeper_reach_m(s["temps"], s["élan"])) for s in shots)
print(f"{len(shots)} cadrés jugés ; issue conforme à la portée avec élan : {consistent}")
print(f"arrêts gagnés par l'élan : {gained} ; perdus (contre-pied) : {lost}")
for lo, hi, label in ((-99, -0.5, "contre-pied"), (-0.5, 0.5, "quasi immobile"), (0.5, 99, "lancé vers le ballon")):
    g = [s for s in shots if lo <= s["élan"] < hi]
    print(f"  {label}: {len(g)} tirs, écart médian {statistics.median(s['écart'] for s in g):.2f} m, "
          f"écart - portée immobile médian {statistics.median(s['écart'] - keeper_reach_m(s['temps']) for s in g):+.2f} m")
