"""Ticket 10a : comparaison avant/après des sorties de `10a-presseur-zone.py`.
Usage : uv run python .scratch/v2-realisme/mesures/10a-comparaison.py"""
import glob
import json
from collections import defaultdict

D = ".scratch/v2-realisme/mesures"


def load(mode):
    return [r for f in sorted(glob.glob(f"{D}/10a-{mode}-*.json")) for r in json.load(open(f))]


def summary(rows):
    n = len(rows)
    out = {"matchs": n}
    for key in ("shots", "offsides", "fouls", "tackles", "changes"):
        out[key] = sum(r[key] for r in rows) / n
    out["buts"] = sum(sum(r["score"]) for r in rows) / n
    time, dist = defaultdict(float), defaultdict(float)
    for r in rows:
        for k, v in r["time"].items():
            time[k] += v
        for k, v in r["dist"].items():
            dist[k] += v
    postes = sorted({k.split("|")[0] for k in time})
    out["postes"] = {}
    for p in postes:
        t_in, t_out = time.get(f"{p}|True", 0.0), time.get(f"{p}|False", 0.0)
        tot = t_in + t_out
        out["postes"][p] = {"min_par_match": tot / n, "hors_zone_min_par_match": t_out / n,
                            "part_hors_zone": t_out / tot if tot else 0.0, "distance_ref_m": dist[p] / tot if tot else 0.0}
    t_all = sum(time.values())
    out["part_hors_zone_tous"] = sum(v for k, v in time.items() if k.endswith("False")) / t_all
    return out


a, b = summary(load("avant")), summary(load("apres"))
print(f"{'':28}{'avant':>10}{'après':>10}{'écart':>9}")
for key in ("matchs", "buts", "shots", "tackles", "fouls", "offsides", "changes", "part_hors_zone_tous"):
    va, vb = a[key], b[key]
    print(f"{key:28}{va:10.3f}{vb:10.3f}{(vb - va) / va * 100 if va else 0:+8.1f}%")
print()
print(f"{'poste':6}{'presse (min/m)':>18}{'hors zone (min/m)':>22}{'part hors zone':>20}{'dist. à sa place (m)':>24}")
for p in sorted(set(a["postes"]) | set(b["postes"])):
    pa, pb = a["postes"].get(p, {}), b["postes"].get(p, {})
    f = lambda d, k, fmt: format(d.get(k, 0.0), fmt)
    print(f"{p:6}{f(pa,'min_par_match','6.2f'):>9}{f(pb,'min_par_match','6.2f'):>9}"
          f"{f(pa,'hors_zone_min_par_match','6.2f'):>11}{f(pb,'hors_zone_min_par_match','6.2f'):>11}"
          f"{f(pa,'part_hors_zone','6.1%'):>10}{f(pb,'part_hors_zone','6.1%'):>10}"
          f"{f(pa,'distance_ref_m','6.1f'):>12}{f(pb,'distance_ref_m','6.1f'):>12}")
json.dump({"avant": a, "apres": b}, open(f"{D}/10a-comparaison.json", "w"), ensure_ascii=False, indent=1)
