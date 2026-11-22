"""Synthèse du ticket 03b3a : pour chaque fichier de série, buts par match, hauteur moyenne du gardien ballon loin,
sorties et prises hors surface par gardien et par match ; avec deux fichiers, écart apparié des buts (IC 95 %) ; en série
réelle, partage par Rushing Out ([0 ; 50[, [50 ; 65[, [65 ; 100])."""

import json
import statistics as st
import sys

files = sys.argv[1:]
data = [json.load(open(f, encoding="utf-8")) for f in files]
for f, rows in zip(files, data):
    keepers = [k for r in rows for k in r["gardiens"].values()]
    h = [k["hauteur"] for k in keepers if k["hauteur"] is not None]
    print(f"{f}: {len(rows)} matchs ; buts/match {st.mean(sum(r['score']) for r in rows):.2f} ; hauteur ballon loin "
          f"{st.mean(h):.2f} m ; sorties/gardien/match {st.mean(k['sorties'] for k in keepers):.2f} ; prises hors "
          f"surface/gardien/match {st.mean(k['prises hors surface'] for k in keepers):.3f}")
    for lo, hi in ((0, 50), (50, 65), (65, 101)):
        group = [k for k in keepers if k["rushing out"] is not None and lo <= k["rushing out"] < hi]
        if group and len({k["rushing out"] for k in keepers}) > 1:
            gh = [k["hauteur"] for k in group if k["hauteur"] is not None]
            print(f"   Rushing Out [{lo} ; {hi}[ : {len(group)} gardiens-matchs, hauteur {st.mean(gh):.2f} m, sorties "
                  f"{st.mean(k['sorties'] for k in group):.2f}, prises hors surface {st.mean(k['prises hors surface'] for k in group):.3f}")
if len(files) == 2:
    a = {r["match"]: sum(r["score"]) for r in data[0]}
    d = [sum(r["score"]) - a[r["match"]] for r in data[1] if r["match"] in a]
    m, se = st.mean(d), st.stdev(d) / len(d) ** 0.5
    print(f"écart apparié buts/match {m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}] ({len(d)} matchs)")
