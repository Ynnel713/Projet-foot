"""Synthèse 08f : validation de la perception, indicateurs agrégés sur les lots (moyenne pondérée par le nombre de matchs).
Usage : python .scratch/v2-realisme/mesures/08f-synthese.py '<glob lots>' ['<glob lots de comparaison>']
Avec deux séries : colonne 1 = première, colonne 2 = seconde (A/B : avec puis sans perception de la défense)."""
import glob
import json
import sys

KEYS = [
    # champ de vision et mémoire du porteur (08a, 08b)
    "vision : adversaires non vus par le porteur à la décision (moyenne)",
    "vision : adversaires à 5 m au plus par décision (moyenne)",
    "vision : adversaires à 5 m au plus non vus à la décision (part des adversaires proches)",
    "vision : décisions avec un adversaire non vu à 5 m au plus (part)",
    "mémoire : âge de la dernière vue des adversaires non vus, porteur (s)",
    "mémoire : erreur de position perçue des adversaires non vus, porteur (m)",
    "mémoire : fantômes perçus par décision (adversaires perçus avec plus de 4 s de retard et 10 m d'erreur)",
    # pertes au contact (08f)
    "pertes de balle au contact par match (tacle, conduite, rotation)",
    "pertes au contact sur adversaire non vu (part des pertes au contact)",
    "pertes au contact : tacle, par match", "pertes au contact : tacle, sur adversaire non vu (part)",
    "pertes au contact : conduite, par match", "pertes au contact : conduite, sur adversaire non vu (part)",
    "pertes au contact : rotation, par match", "pertes au contact : rotation, sur adversaire non vu (part)",
    "pertes de balle par match",
    # scans
    "scans par match", "scans par minute et par joueur", "scans du porteur (part des scans)",
    "scans dans les 10 s avant la réception (moyenne par réception)",
    # ligne et marquage perçus (08e, 08f)
    "ligne perçue : écart absolu à la ligne sur vraies positions (moyenne, m)",
    "ligne perçue : écart signé, perçue - réelle (moyenne, m ; positif = ligne plus haute)",
    "ligne perçue : ticks avec un écart de plus de 0.1 m (part)", "ligne perçue : ticks avec un écart de plus de 0.5 m (part)",
    "ligne perçue : ticks avec un écart de plus de 1 m (part)", "ligne perçue : ticks avec un écart de plus de 2 m (part)",
    "ligne perçue : écart absolu, 95e centile (m)", "ligne perçue : écart maximal (m)",
    "ligne perçue : variation moyenne d'un tick à l'autre (m)", "ligne réelle : variation moyenne d'un tick à l'autre (m)",
    "ligne perçue : variation efficace d'un tick à l'autre (m)", "ligne réelle : variation efficace d'un tick à l'autre (m)",
    "ligne perçue : sauts de plus de 0.5 m par match", "ligne réelle : sauts de plus de 0.5 m par match",
    "ligne perçue : changements de sens par match", "ligne réelle : changements de sens par match",
    "marquage : attaquant non vu par son marqueur (part des marqueur-ticks)",
    "marquage : erreur de place de l'attaquant (moyenne, m)",
    "marquage : erreur de place quand l'attaquant n'est pas vu (moyenne, m)",
    "marquage : erreur de plus de 2 m (part des marqueur-ticks)", "marquage : erreur maximale (m)",
    "marquage : marqueur différent de celui des vraies positions (part des choix)",
    # effets de jeu (A/B)
    "hors-jeu par match", "passes en profondeur réussies (part)", "passes en profondeur (part)", "passes par match",
    "passes réussies (part)", "passes chez l'adversaire (part)", "buts par match", "tirs tracés par équipe",
    "conversion des tirs (part)", "xG neutre par match", "grosses occasions par match", "fautes par match",
    "temps de calcul par match (s)",
]


def lots(pattern):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(pattern))]


def mean(ds, key):
    vals = [(d["matchs"], d.get(key)) for d in ds if isinstance(d.get(key), (int, float))]
    n = sum(w for w, _ in vals)
    return sum(w * v for w, v in vals) / n if n else float("nan")


def maximum(ds, key):
    vals = [d[key] for d in ds if isinstance(d.get(key), (int, float))]
    return max(vals) if vals else float("nan")


A = lots(sys.argv[1])
B = lots(sys.argv[2]) if len(sys.argv) > 2 else None
print(f"série 1 : {sum(d['matchs'] for d in A)} matchs" + (f" ; série 2 : {sum(d['matchs'] for d in B)} matchs" if B else ""))
for k in KEYS:
    agg = maximum if k.endswith("maximal (m)") or k.endswith("maximale (m)") else mean
    line = f"  {k:<110} {agg(A, k):10.3f}"
    if B:
        line += f" {agg(B, k):10.3f}"
    print(line)
print("\nScans par minute et par joueur, par poste")
postes = sorted({k.split(" : ")[1] for k in A[0] if k.startswith("scans par minute et par joueur : ")})
for p in postes:
    k = f"scans par minute et par joueur : {p}"
    print(f"  {p:<6} {mean(A, k):8.2f}" + (f" {mean(B, k):8.2f}" if B else ""))
