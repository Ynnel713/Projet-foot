"""Profil de hauteur du ballon après une remise (ticket 02b2) : sommet, rebonds successifs, roulement."""
import json, sys
t = json.load(open(sys.argv[1]))
tr = t["ball_track"]
def profile(m0, span_s=9.0):
    pts = [p for p in tr if m0 <= p["minute"] <= m0 + span_s / 60]
    apexes, k = [], 1
    for i in range(1, len(pts) - 1):
        if pts[i]["z"] > 0 and pts[i]["z"] >= pts[i-1]["z"] and pts[i]["z"] > pts[i+1]["z"]:
            apexes.append((round(pts[i]["minute"], 4), pts[i]["z"]))
    top = max(pts, key=lambda p: p["z"]) if pts else None
    return top, apexes
for m in map(float, sys.argv[2:]):
    top, ap = profile(m)
    print(m, "sommet", round(top["minute"], 4), top["z"], "sommets successifs", ap[:6])
