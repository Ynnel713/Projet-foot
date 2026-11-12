"""Synthèse des lots de 50 matchs (18i contre 18j, mêmes graines) : indicateurs généraux et calibration de la passe.
Usage : uv run python .scratch/v2-realisme/mesures/18j-synthese.py"""
import json
import glob

M = ".scratch/v2-realisme/mesures/"
KEYS = ["passes par match", "passes par minute de jeu effectif", "passes réussies (part)", "passes chez l'adversaire (part)",
        "receveur visé (part)", "passes par possession", "possession d'équipe (s)", "temps par possession de joueur (s)",
        "buts par match", "conduite : intervalles par match", "conduite : pertes par match",
        "solutions de passe ouvertes (nombre)", "une-deux par équipe et par match", "passes longues (part)",
        "passes longues réussies (part)", "face-à-face : tirs par match", "corners par match", "fautes par match",
        "tirs par équipe et par match"]
BANDS = ["[0 ; 0.1[", "[0.1 ; 0.2[", "[0.2 ; 0.3[", "[0.3 ; 0.4[", "[0.4 ; 0.5[", "[0.5 ; 0.6[", "[0.6 ; 0.7[",
         "[0.7 ; 0.8[", "[0.8 ; 0.9[", "[0.9 ; +["]


def lots(tag):
    out = []
    for f in sorted(glob.glob(f"{M}{tag}-50-lot*.json")):
        d = json.load(open(f, encoding="utf-8"))
        out.append(d)
    return out


def mean(ds, key):  # moyenne pondérée par le nombre de matchs
    vals = [(d["matchs"], d.get(key)) for d in ds if isinstance(d.get(key), (int, float))]
    n = sum(w for w, _ in vals)
    return sum(w * v for w, v in vals) / n if n else float("nan")


def calib(ds, band):
    pre = f"calibration passe, chance évaluée {band} : "
    w = [d["matchs"] * d.get(pre + "passes par match", 0.0) for d in ds]
    tot = sum(w)
    if not tot:
        return None
    f = lambda k: sum(wi * d.get(pre + k, 0.0) for wi, d in zip(w, ds)) / tot
    return tot / sum(d["matchs"] for d in ds), f("chance évaluée (part)"), f("non perdue (part)"), f("reçue par le receveur visé (part)")


A, B = lots("18i"), lots("18j")
print("Indicateurs généraux, 50 matchs (mêmes graines) : 18i -> 18j (portée du lecteur et table remesurée)")
for k in KEYS:
    print(f"  {k:<42} {mean(A, k):10.3f} -> {mean(B, k):10.3f}")
for tag, ds in (("18i", A), ("18j", B)):
    print(f"\nCalibration de la passe ({tag})")
    print("tranche                      passes/match  évaluée non perdue   écart reçue visé")
    for band in BANDS:
        c = calib(ds, band)
        if c:
            print(f"chance évaluée {band:<13} {c[0]:10.1f} {c[1]:8.3f} {c[2]:10.3f} {100 * (c[1] - c[2]):+7.1f} {c[3]:10.3f}")
