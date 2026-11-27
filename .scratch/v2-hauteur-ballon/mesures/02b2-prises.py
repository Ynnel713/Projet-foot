"""Hauteur du ballon au moment où un joueur en prend possession (ticket 02b2, règle provisoire du 02a1 : pas au-dessus de 0,5 m)."""
import json, sys
t = json.load(open(sys.argv[1]))
tr = t["ball_track"]
takes = [(tr[i]["minute"], tr[i-1]["z"], tr[i]["holder"]) for i in range(1, len(tr)) if tr[i]["holder"] and not tr[i-1]["holder"] and not tr[i]["dead"]]
zs = sorted(z for _, z, _ in takes)
print("prises de balle libre", len(takes), "z du pas précédent : max", zs[-1], "au-dessus de 0,5 m", sum(z > 0.5 for z in zs),
      "entre 0 et 0,5 m", sum(0 < z <= 0.5 for z in zs), "sommet du match", max(p["z"] for p in tr))
for m, z, h in takes:
    if z > 0.5: print("  ", round(m, 4), z, h)
