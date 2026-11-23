"""Synthèse du ticket 03b3b : pour chaque fichier de série (format de `03b3b-serie.py`, ou de `03b3a-serie.py` pour la
référence d'avant), buts par match, sorties et sorties inattendues par gardien et par match, part des inattendues où il
a le ballon, buts encaissés dans les 15 s ; avec deux fichiers, écart apparié des buts (IC 95 %) ; en série réelle,
partage par Eccentricity ([0 ; 41[, [41 ; 60[, [60 ; 100])."""

import json
import statistics as st
import sys

files = sys.argv[1:]
data = [json.load(open(f, encoding="utf-8")) for f in files]
for f, rows in zip(files, data):
    keepers = [k for r in rows for k in r["gardiens"].values()]
    line = f"{f}: {len(rows)} matchs ; buts/match {st.mean(sum(r['score']) for r in rows):.2f} ; sorties/gardien/match " \
           f"{st.mean(k['sorties'] for k in keepers):.2f}"
    if "inattendues" in keepers[0]:
        w = sum(k["inattendues"] for k in keepers)
        line += (f" ; inattendues/gardien/match {w / len(keepers):.3f} ; ballon gagné {sum(k['gagnees'] for k in keepers)}"
                 f"/{w} ; buts encaissés dans les 15 s {sum(k['buts apres'] for k in keepers)}")
    print(line)
    notes = {k.get("eccentricity") for k in keepers}
    if len(notes) > 1 and "inattendues" in keepers[0]:
        for lo, hi in ((0, 41), (41, 60), (60, 101)):
            group = [k for k in keepers if k["eccentricity"] is not None and lo <= k["eccentricity"] < hi]
            if group:
                print(f"   Eccentricity [{lo} ; {hi}[ : {len(group)} gardiens-matchs, sorties "
                      f"{st.mean(k['sorties'] for k in group):.2f}, inattendues {st.mean(k['inattendues'] for k in group):.3f}")
if len(files) == 2:
    a = {r["match"]: sum(r["score"]) for r in data[0]}
    d = [sum(r["score"]) - a[r["match"]] for r in data[1] if r["match"] in a]
    m, se = st.mean(d), st.stdev(d) / len(d) ** 0.5
    print(f"écart apparié buts/match {m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}] ({len(d)} matchs)")
