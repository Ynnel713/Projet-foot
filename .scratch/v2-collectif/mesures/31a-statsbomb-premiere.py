"""Délai entre la réception (Ball Receipt*) et la passe suivante du même joueur, données ouvertes StatsBomb.
Méthode de StatsBomb (« Identifying Fast Passers Using Data ») : un écart de 0,0 s = passe de première. Passes du
jeu courant (sans pass.type), au pied (body_part Left/Right Foot), précédées dans la même possession d'une réception
réussie du même joueur sans autre événement du ballon entre les deux (hors pression, duel subi)."""
import json, sys

def ts(e):
    h, m, s = e["timestamp"].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

SKIP = {"Pressure", "Duel", "Block", "Dribbled Past", "Foul Committed", "Foul Won", "Ball Recovery"}
for comp in sys.argv[1:]:
    ids = open(f"ids_{comp}.txt").read().split()
    gaps = []; passes = 0
    for i in ids:
        ev = sorted(json.load(open(f"e_{i}.json")), key=lambda e: e["index"])
        last_receipt = {}
        for e in ev:
            t = e["type"]["name"]
            if t == "Ball Receipt*" and "outcome" not in e.get("ball_receipt", {}):
                last_receipt = {"player": e["player"]["id"], "period": e["period"], "t": ts(e), "poss": e["possession"]}
                continue
            if t in SKIP or t == "Ball Receipt*":
                continue
            if t == "Pass" and "type" not in e["pass"] and e["pass"].get("body_part", {}).get("name") in ("Left Foot", "Right Foot"):
                passes += 1
                r = last_receipt
                if r and r["player"] == e["player"]["id"] and r["period"] == e["period"] and r["poss"] == e["possession"]:
                    gaps.append(ts(e) - r["t"])
            last_receipt = {}  # tout autre geste du ballon (conduite, passe...) coupe le lien
    n = len(gaps)
    first = sum(1 for g in gaps if g <= 0.0005)
    within = lambda x: sum(1 for g in gaps if g <= x) / passes
    print(f"compétition {comp} : {len(ids)} matchs, passes au pied du jeu courant {passes / len(ids):.0f} par match ; "
          f"précédées directement d'une réception {n / passes:.3f} ; de première (0,0 s) {first / passes:.3f} des passes "
          f"({first / n:.3f} des passes précédées d'une réception) ; au plus 0,5 s {within(0.5):.3f}, 1 s {within(1.0):.3f}")
