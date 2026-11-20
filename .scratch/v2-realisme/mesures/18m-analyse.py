"""Analyse du ticket v2-realisme/18m sur la sortie de `18m-diag-script.py`. Perdue (définition du 18h) : un adversaire
touche le ballon le premier, ou le ballon sort / est sifflé avec remise pour l'adversaire.
1. calibration de la chance évaluée : par tranche de chance, par niveau de Passing du passeur, par marquage du receveur ;
2. méthode du 18g : part des adversaires NON comptés par la coupe (`cut` = 0) qui touchent le ballon le premier, par
   tranche de distance au receveur, selon qu'ils arrivent au point visé avant lui ou non, et selon leur position
   (devant le receveur, sur le trajet ; à côté ; derrière lui) ;
3. si demandé (--ajuste FIT --controle CTRL) : table ajustée sur FIT, calibration avant / après sur CTRL.
Usage : uv run python .scratch/v2-realisme/mesures/18m-analyse.py lot1.json [lot2.json ...] [--controle c1.json ...]
(rapport du ticket : fit-2200 à fit-2218 en ajustement, ctrl-2300 à ctrl-2336 en contrôle, sortie `18m-rapport.txt`)"""
import json
import math
import sys
from collections import defaultdict

SHARES = (0.99, 0.98, 0.98, 0.70)  # `possession._LATERAL_NOT_LOST`
DIST = (1.0, 2.0, 3.0, 4.0, 6.0)  # tranches de distance au receveur (m)
MIN_N = 500


def load(paths):
    return [r for p in paths for r in json.load(open(p))]


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def where(o, L):
    if o["along"] >= L:
        return "derrière"
    if o["along"] > L - 2.0:
        return "à côté"
    return "devant"


def key(o, L):
    """Catégorie d'un adversaire non compté par la coupe, près du receveur ; None sinon."""
    if o["cut"] > 0.0 or o["to_recv"] >= DIST[-1]:
        return None
    lim = next(x for x in DIST if o["to_recv"] < x)
    return lim, o["dt_aim"] < 0.0


def factor(r, table):
    k = 1.0
    for o in r["opp"]:
        b = key(o, r["L"])
        if b is not None:
            k *= 1.0 - table.get(b, 0.0)
    return k


def base(r):
    return r["keep"] * sum(w * s for w, s in zip(r["w"], SHARES))


def fit(R):
    n, hit = defaultdict(int), defaultdict(int)
    for r in R:
        for o in r["opp"]:
            b = key(o, r["L"])
            if b is not None:
                n[b] += 1
                hit[b] += r.get("first") == o["n"]
    return {b: hit[b] / n[b] for b in n}, n, hit


def calib(R, pred, label, parts=10):
    """Calibration par tranche de chance évaluée : `parts` tranches égales (10 ; 7 pour le découpage du 23a)."""
    print(f"  {label}")
    bins = defaultdict(list)
    for r in R:
        bins[min(parts - 1, int(pred(r) * parts))].append(r)
    worst, tot = 0.0, []
    for b in sorted(bins):
        S = bins[b]
        p = sum(map(pred, S)) / len(S)
        o = sum(not lost(r) for r in S) / len(S)
        se = math.sqrt(max(o * (1 - o), 1e-9) / len(S))
        if len(S) >= MIN_N:
            worst = max(worst, abs(p - o))
        print(f"    [{b / parts:.2f} ; {(b + 1) / parts:.2f}[  n {len(S):6d}  évaluée {p:.3f}  non perdue {o:.3f}  "
              f"écart {100 * (p - o):+.1f} ± {196 * se:.1f}")
    p = sum(map(pred, R)) / len(R)
    o = sum(not lost(r) for r in R) / len(R)
    print(f"    toutes n {len(R)}  évaluée {p:.3f}  non perdue {o:.3f}  écart {100 * (p - o):+.2f} ; "
          f"pire tranche (n >= {MIN_N}) {100 * worst:.1f} points")


def by_group(R, pred, label, groups):
    print(f"  {label}")
    for name, sel in groups:
        S = [r for r in R if sel(r)]
        if not S:
            continue
        p = sum(map(pred, S)) / len(S)
        o = sum(not lost(r) for r in S) / len(S)
        se = math.sqrt(max(o * (1 - o), 1e-9) / len(S))
        print(f"    {name:<34} n {len(S):6d}  évaluée {p:.3f}  non perdue {o:.3f}  écart {100 * (p - o):+.1f} ± {196 * se:.1f}")


def marked(r, d=2.0):
    return any(o["cut"] == 0.0 and o["to_recv"] < d for o in r["opp"])


GROUPS = (("Passing < 50", lambda r: r["passing"] < 50), ("Passing 50-70", lambda r: 50 <= r["passing"] < 70),
          ("Passing >= 70", lambda r: r["passing"] >= 70),
          ("receveur libre (rien < 4 m hors coupe)", lambda r: not marked(r, 4.0)),
          ("adversaire hors coupe < 2 m", lambda r: marked(r, 2.0)),
          ("adversaire hors coupe 2-4 m", lambda r: marked(r, 4.0) and not marked(r, 2.0)),
          ("hors coupe < 2 m, arrive avant", lambda r: any(o["cut"] == 0.0 and o["to_recv"] < 2.0 and o["dt_aim"] < 0 for o in r["opp"])),
          ("passes < 15 m", lambda r: r["L"] < 15), ("passes 15-30 m", lambda r: 15 <= r["L"] < 30),
          ("passes >= 30 m", lambda r: r["L"] >= 30))


def main(argv):
    ctrl_at = argv.index("--controle") if "--controle" in argv else len(argv)
    FIT, CTRL = load(argv[:ctrl_at]), load(argv[ctrl_at + 1:])
    print(f"Ajustement : {len(FIT)} passes au sol" + (f" ; contrôle : {len(CTRL)} passes" if CTRL else ""))
    print("\n1. Chance évaluée actuelle (ajustement)")
    calib(FIT, lambda r: r["chance"], "par tranche de chance")
    by_group(FIT, lambda r: r["chance"], "par groupe", GROUPS)
    print("  pertes, par premier toucheur adverse (tous / Passing < 50)")
    for label, S in (("toutes", FIT), ("Passing < 50", [r for r in FIT if r["passing"] < 50])):
        cause = defaultdict(int)
        for r in S:
            if not lost(r):
                continue
            if not r.get("first"):
                cause["sortie / sifflée"] += 1
                continue
            o = next((o for o in r["opp"] if o["n"] == r["first"]), None)
            if o is None:
                cause["gardien loin (non suivi)"] += 1
            elif o["cut"] > 0.0:
                cause["compté par la coupe"] += 1
            elif o["to_recv"] < 6.0:
                cause[f"hors coupe, < 6 m du receveur ({where(o, r['L'])})"] += 1
            else:
                cause["hors coupe, loin du receveur"] += 1
        tot = sum(cause.values())
        print(f"    {label} : {tot} pertes sur {len(S)} passes ; " + ", ".join(
            f"{k} {v} ({100 * v / tot:.0f} %)" for k, v in sorted(cause.items(), key=lambda kv: -kv[1])))
    table, n, hit = fit(FIT)
    print("\n2. Adversaires hors coupe près du receveur : part qui touche le ballon le premier (méthode du 18g)")
    for lim in DIST:
        for before in (True, False):
            b = (lim, before)
            if n[b]:
                print(f"    < {lim:.0f} m, {'arrive avant' if before else 'arrive après'} : n {n[b]:6d}  touche le premier {hit[b] / n[b]:.3f}")
    pos_n, pos_hit = defaultdict(int), defaultdict(int)
    for r in FIT:
        for o in r["opp"]:
            if o["cut"] == 0.0 and o["to_recv"] < 3.0:
                w = where(o, r["L"])
                pos_n[w] += 1
                pos_hit[w] += r.get("first") == o["n"]
    print("    position (< 3 m) : " + ", ".join(f"{w} {pos_hit[w] / pos_n[w]:.3f} (n {pos_n[w]})" for w in pos_n))
    # ce qui reste après la table : les parts par bande la contenaient déjà en partie, on les redivise par la moyenne
    mean_f = sum(factor(r, table) for r in FIT) / len(FIT)
    print(f"    facteur moyen de la table sur l'ajustement : {mean_f:.3f}")

    def new(r):
        return min(1.0, base(r) * factor(r, table) / mean_f)
    print("\n3. Chance avec la table (parts par bande renormalisées par le facteur moyen), ajustement")
    calib(FIT, new, "par tranche")
    by_group(FIT, new, "par groupe", GROUPS)
    if CTRL:
        print("\n4. Contrôle hors échantillon")
        calib(CTRL, lambda r: r["chance"], "chance actuelle")
        calib(CTRL, lambda r: r["chance"], "chance actuelle, 7 tranches (découpage du contrôle du 23a)", parts=7)
        by_group(CTRL, lambda r: r["chance"], "chance actuelle, par groupe", GROUPS)
        calib(CTRL, new, "chance avec la table")
        by_group(CTRL, new, "chance avec la table, par groupe", GROUPS)


main(sys.argv[1:])
