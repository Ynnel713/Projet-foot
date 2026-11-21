"""Analyse du ticket v2-realisme/29c : adversaires collés au receveur au départ de la passe (moins de 1,5 m, entre le
passeur et lui), suivis pendant le vol (`29c-diag-script.py`). Qui touche le premier, et pourquoi pas le défenseur.
Usage : uv run python .scratch/v2-realisme/mesures/29c-analyse.py fichiers.json..."""
import json
import math
import sys

rows = [r for f in sys.argv[1:] for r in json.load(open(f))]
marks = [(r, m) for r in rows for m in r.get("marks", {}).values() if m.get("dmin", 99) < 98]
print(f"passes {len(rows)}, adversaires collés suivis {len(marks)}")


def share(sub, pred):
    return f"{sum(1 for x in sub if pred(x)) / len(sub):.2f} ({len(sub)})" if sub else "- (0)"


first = lambda x: x[0].get("first") == x[1]["n"]
lost = lambda x: x[0].get("first_team") not in (None, x[0]["team"]) or (x[0].get("out") and x[0].get("out_team") != x[0]["team"])
print("ballon venu à moins de 1 m :", share(marks, lambda x: x[1]["dmin"] < 1.0))
near = [x for x in marks if x[1]["dmin"] < 1.0]
line = [x for x in near if x[1].get("ahead", -9) > 0 and x[1].get("side", 9) < 0.5]
print("parmi eux, devant le receveur (vers le ballon) et à moins de 0,5 m de son axe :", len(line))
for name, sub in (("tous à moins de 1 m", near), ("devant, axe < 0,5 m", line)):
    print(f"\n== {name} : touche le premier {share(sub, first)}, passe perdue {share(sub, lost)}")
    for lab, pred in (("lecteur", lambda m: m["reader"]),
                      ("non lecteur, faces_pass vrai, vue", lambda m: not m["reader"] and m["faces"] and m["seen"]),
                      ("non lecteur, faces_pass faux, cap < 90 du ballon qui vient", lambda m: not m["reader"] and not m["faces"] and m["ang_in"] < 90),
                      ("non lecteur, faces_pass faux, cap >= 90", lambda m: not m["reader"] and not m["faces"] and m["ang_in"] >= 90),
                      ("non lecteur, faces_pass vrai, pas encore vue", lambda m: not m["reader"] and m["faces"] and not m["seen"])):
        s = [x for x in sub if pred(x[1])]
        print(f"  {lab:58s} part {len(s) / max(1, len(sub)):.2f}  touche le premier {share(s, first)}")
    dm = sorted(x[1]["dmin"] for x in sub)
    if dm:
        print("  dmin quartiles", [dm[int(q * (len(dm) - 1))] for q in (0.25, 0.5, 0.75)])
    for lo, hi in ((0, 0.41), (0.41, 0.8), (0.8, 1.0)):
        s = [x for x in sub if lo <= x[1]["dmin"] < hi]
        print(f"  dmin [{lo} ; {hi}[ : touche le premier {share(s, first)}")
far = [x for x in marks if x[1]["dmin"] >= 1.0]
print("\nballon resté à 1 m et plus (receveur parti, passe à côté) : passe perdue", share(far, lost))
