"""Synthèse du ticket v2-hauteur-ballon/02a1 : par fichier de série (`02a1-serie.py`), buts et tirs par match ; avec la
hauteur : contrôles (hauteur minimale, modes incohérents), vols (nombre, durée, sommet, distance au premier impact,
part gardée des vols de plus de 25 m) ; avec deux fichiers, écarts appariés (IC 95 %) des buts et des tirs."""

import json
import statistics as st
import sys


def q(values, share):
    values = sorted(values)
    return values[min(len(values) - 1, int(share * len(values)))]


files = sys.argv[1:]
data = [json.load(open(f, encoding="utf-8")) for f in files]
for f, rows in zip(files, data):
    print(f"{f}: {len(rows)} matchs ; buts/match {st.mean(sum(r['score']) for r in rows):.2f} ; "
          f"tirs/match {st.mean(r['tirs'] for r in rows):.1f}")
    if "vols" not in rows[0]:
        continue
    print(f"   hauteur minimale {min(r['z_min'] for r in rows):.3f} m ; modes incohérents "
          f"{sum(r['mode_incohérent'] for r in rows)}")
    flights = [v for r in rows for v in r["vols"]]
    print(f"   vols : {len(flights) / len(rows):.1f} par match")
    for label, lo, hi in (("courts (< 25 m)", 0.0, 25.0), ("25-40 m", 25.0, 40.0), ("longs (>= 40 m)", 40.0, 1e9)):
        g = [v for v in flights if lo <= v["distance"] < hi]
        if not g:
            continue
        alive = [v for v in g if v["gardé"] is not None]
        kept = 100 * sum(v["gardé"] for v in alive) / len(alive) if alive else float("nan")
        print(f"   {label} : {len(g) / len(rows):.1f}/match, durée méd. {st.median(v['durée'] for v in g):.2f} s "
              f"(max {max(v['durée'] for v in g):.2f}), sommet méd. {st.median(v['sommet'] for v in g):.1f} m "
              f"(90e {q([v['sommet'] for v in g], 0.9):.1f}, max {max(v['sommet'] for v in g):.1f}), "
              f"gardé {kept:.1f} %, pris avant le premier impact {100 * sum(v['pris_en_l_air'] for v in g) / len(g):.1f} %")
if len(files) == 2:
    for key, val in (("buts", lambda r: sum(r["score"])), ("tirs", lambda r: r["tirs"])):
        a = {r["match"]: val(r) for r in data[0]}
        d = [val(r) - a[r["match"]] for r in data[1] if r["match"] in a]
        m, se = st.mean(d), st.stdev(d) / len(d) ** 0.5
        print(f"écart apparié {key}/match {m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}] ({len(d)} matchs)")
