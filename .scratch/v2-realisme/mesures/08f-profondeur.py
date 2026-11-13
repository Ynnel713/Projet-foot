"""08f : chiffres reconstruits depuis les JSON des lots (valeurs en pleine précision, pas les parts arrondies de la synthèse).
Usage : python .scratch/v2-realisme/mesures/08f-profondeur.py  (depuis la racine du dépôt)
1. Passes en profondeur tentées et réussies, cumul sur 50 matchs, avec et sans perception de la défense.
2. Durée réelle d'un match (temps additionnel compris) et scans par minute et par joueur sur cette durée."""
import glob
import json
import math

M = ".scratch/v2-realisme/mesures/"


def lots(pattern):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(M + pattern))]


for name, pattern in (("avec perception", "08f-50-lot*.json"), ("sans perception", "08f-sans-lot*.json")):
    ds = lots(pattern)
    matches = sum(d["matchs"] for d in ds)
    passes = sum(d["matchs"] * d["passes par match"] for d in ds)
    deep = sum(d["matchs"] * d["passes par match"] * d["passes en profondeur (part)"] for d in ds)
    won = sum(d["matchs"] * d["passes par match"] * d["passes en profondeur (part)"] * d["passes en profondeur réussies (part)"] for d in ds)
    lot_mean = sum(d["matchs"] * d["passes en profondeur réussies (part)"] for d in ds) / matches
    print(f"{name} : {matches} matchs, {passes:.0f} passes, passes en profondeur {deep:.1f} ({deep / matches:.2f} par match), "
          f"réussies {won:.1f} = {won / deep:.1%} (écart-type binomial {math.sqrt(won / deep * (1 - won / deep) / deep):.1%}) ; "
          f"moyenne des parts par lot : {lot_mean:.1%} ; hors-jeu {sum(d['matchs'] * d['hors-jeu par match'] for d in ds):.0f}")

ds = lots("08f-50-lot*.json")
matches = sum(d["matchs"] for d in ds)
minutes = 0.0
for d in ds:  # durée = passes par match / (passes par minute de jeu effectif x part de jeu effectif)
    minutes += d["matchs"] * d["passes par match"] / d["passes par minute de jeu effectif"] / d["temps de jeu effectif (part)"]
duration = minutes / matches
scans = sum(d["matchs"] * d["scans par match"] for d in ds) / matches
print(f"durée réelle moyenne d'un match : {duration:.1f} min ; scans par match {scans:.0f} ; "
      f"par joueur et par minute : {scans / (22 * 90):.2f} sur 90 min nominales, {scans / (22 * duration):.2f} sur la durée réelle")
