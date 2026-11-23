"""Synthèse des tickets 03c1 et 03c2 : par fichier de série (`03c-serie.py`), buts par match et, par type de ballon du
gardien (long au pied, à la main, autre), nombre par gardien et par match, longueur moyenne, part gardée par son équipe
(ballon mort exclu) ; avec deux fichiers, écart apparié des buts (IC 95 %)."""

import json
import statistics as st
import sys

files = sys.argv[1:]
data = [json.load(open(f, encoding="utf-8")) for f in files]
for f, rows in zip(files, data):
    print(f"{f}: {len(rows)} matchs ; buts/match {st.mean(sum(r['score']) for r in rows):.2f}")
    balls = [b for r in rows for b in r["ballons"]]
    for kind in ("long", "main", "autre"):
        group = [b for b in balls if b["type"] == kind]
        if not group:
            continue
        alive = [b for b in group if b["gardé"] is not None]
        kept = sum(b["gardé"] for b in alive) / len(alive) if alive else float("nan")
        print(f"   {kind}: {len(group) / (2 * len(rows)):.2f} par gardien et par match, longueur {st.mean(b['longueur'] for b in group):.1f} m"
              f" (90e centile {sorted(b['longueur'] for b in group)[int(0.9 * len(group))]:.1f}), gardé {100 * kept:.1f} %"
              f" ({len(alive)} vivants)")
    gk = [b for b in balls if b["type"] == "long" and b["remise"] == "sortie de but"]
    if gk:
        alive = [b for b in gk if b["gardé"] is not None]
        print(f"   dont sorties de but longues : {len(gk) / (2 * len(rows)):.2f}, gardées {100 * sum(b['gardé'] for b in alive) / max(1, len(alive)):.1f} %")
    kicks = [b for b in balls if b["remise"] == "sortie de but"]
    if kicks:
        print(f"   sorties de but : {len(kicks) / (2 * len(rows)):.2f} par gardien et par match, part longue "
              f"{100 * sum(b['type'] == 'long' for b in kicks) / len(kicks):.1f} %")
if len(files) == 2:
    a = {r["match"]: sum(r["score"]) for r in data[0]}
    d = [sum(r["score"]) - a[r["match"]] for r in data[1] if r["match"] in a]
    m, se = st.mean(d), st.stdev(d) / len(d) ** 0.5
    print(f"écart apparié buts/match {m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}] ({len(d)} matchs)")
