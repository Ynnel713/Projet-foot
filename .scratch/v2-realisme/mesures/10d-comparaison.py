"""Ticket 10d : comparaison avant/après des matchs appariés (`10d-{avant,apres}-*.json`, écrits par
`10d-ecran.py`). Moyennes par match, écarts, écarts appariés avec IC 95 % (approximation normale).
Sortie : `10d-comparaison.txt` et `.json` à côté de ce script."""
import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ("buts", "tirs", "tacles", "fautes", "hors-jeu", "passes", "passes reçues", "passes reçues en zone 14",
        "passes en profondeur", "passes en profondeur réussies", "appels dans le dos")


def load(mode):
    rows = {}
    for f in glob.glob(os.path.join(HERE, f"10d-{mode}-*.json")):
        for r in json.load(open(f)):
            r["buts"] = sum(r["score"])
            rows[r["k"]] = r
    return rows


before, after = load("avant"), load("apres")
common = sorted(set(before) & set(after))
lines = [f"{'(par match)':40s} {'avant':>9s} {'après':>9s} {'écart':>8s}", f"{'matchs appariés':40s} {len(common):9d}"]
out = {"matchs": len(common)}
for key in KEYS:
    a = sum(before[k].get(key, 0) for k in common) / len(common)
    b = sum(after[k].get(key, 0) for k in common) / len(common)
    diffs = [after[k].get(key, 0) - before[k].get(key, 0) for k in common]
    mean = sum(diffs) / len(diffs)
    sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)) if len(diffs) > 1 else 0.0
    half = 1.96 * sd / math.sqrt(len(diffs))
    pct = (100.0 * (b - a) / a) if a else float("nan")
    ci = (100.0 * (mean - half) / a, 100.0 * (mean + half) / a) if a else (float("nan"), float("nan"))
    lines.append(f"{key:40s} {a:9.3f} {b:9.3f} {pct:+7.1f}%   IC 95 % [{ci[0]:+.1f} % ; {ci[1]:+.1f} %]")
    out[key] = {"avant": a, "apres": b, "ecart_pct": pct, "ic95_pct": ci}
for mode, rows in (("avant", before), ("après", after)):
    zone, received = sum(rows[k]["passes reçues en zone 14"] for k in common), sum(rows[k]["passes reçues"] for k in common)
    lines.append(f"part des passes reçues en zone 14, {mode} : {100.0 * zone / received if received else 0:.2f} %")
    for key in ("passes en profondeur",):
        tried = sum(rows[k][key] for k in common)
        ok = sum(rows[k]["passes en profondeur réussies"] for k in common)
        lines.append(f"taux de réussite des passes en profondeur, {mode} : {100.0 * ok / tried if tried else 0:.1f} %")
text = "\n".join(lines)
print(text)
open(os.path.join(HERE, "10d-comparaison.txt"), "w").write(text + "\n")
json.dump(out, open(os.path.join(HERE, "10d-comparaison.json"), "w"), ensure_ascii=False, indent=1)
