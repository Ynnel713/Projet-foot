"""Synthèse de la série appariée 10k. Usage : PYTHONPATH=. python 10k-synthese.py avant.json après.json"""
import json, sys
from scripts.bench_series import summary

A, B = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
assert [m["match"] for m in A] == [m["match"] for m in B]


def jeu(m): return [r for r in m["tirs"] if not r["coup franc"]]
def hors(m): return [r for r in jeu(m) if not r["surface"]]
def dans(m): return [r for r in jeu(m) if r["surface"]]
def band(m): return [r for r in hors(m) if 16 <= r["distance"] <= 25]
def share(rs, f): return sum(map(f, rs)) / len(rs) if rs else None
def but(r): return r["issue"] == "but"


METRICS = {
    "buts par match": lambda m: sum(m["score"]),
    "tirs par équipe": lambda m: len(m["tirs"]) / 2,
    "tirs hors surface par équipe": lambda m: len(hors(m)) / 2,
    "tirs dans la surface par équipe": lambda m: len(dans(m)) / 2,
    "buts hors surface par match": lambda m: sum(map(but, hors(m))),
    "buts dans la surface par match": lambda m: sum(map(but, dans(m))),
    "conversion hors surface": lambda m: share(hors(m), but),
    "conversion dans la surface": lambda m: share(dans(m), but),
    "contrés hors surface (part)": lambda m: share(hors(m), lambda r: r["issue"] == "contré"),
    "contrés dans la surface (part)": lambda m: share(dans(m), lambda r: r["issue"] == "contré"),
    "16-25 m : ligne de tir couverte": lambda m: share(band(m), lambda r: bool(r["sur la ligne (m)"])),
    "16-25 m : cône vide": lambda m: share(band(m), lambda r: r["dans le cône"] == 0),
    "16-25 m : xG neutre moyen": lambda m: share(band(m), lambda r: r["xg"]),
    "surface : ligne de tir couverte": lambda m: share(dans(m), lambda r: bool(r["sur la ligne (m)"])),
    "passes par match": lambda m: m["passes"],
    "pertes par match": lambda m: m["pertes"],
}
for name, f in METRICS.items():
    pairs = [(f(a), f(b)) for a, b in zip(A, B)]
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    sa, sb = summary([x for x, _ in pairs]), summary([y for _, y in pairs])
    d = summary([y - x for x, y in pairs])
    lo, hi = d["ic95"]
    flag = "" if lo <= 0 <= hi else "  <- significatif"
    print(f"{name} : avant {sa['moyenne']:.4g}, après {sb['moyenne']:.4g}, écart {d['moyenne']:+.4g} "
          f"[{lo:+.4g} ; {hi:+.4g}] (n={len(pairs)}){flag}")
# totaux poolés (conversion sur l'ensemble des tirs)
for lab, S in (("avant", A), ("après", B)):
    h = [r for m in S for r in hors(m)]; s = [r for m in S for r in dans(m)]
    print(f"{lab} poolé : hors surface {len(h)} tirs, conv {share(h, but):.1%}, contrés {share(h, lambda r: r['issue']=='contré'):.1%} ; "
          f"surface {len(s)} tirs, conv {share(s, but):.1%}, contrés {share(s, lambda r: r['issue']=='contré'):.1%}")
