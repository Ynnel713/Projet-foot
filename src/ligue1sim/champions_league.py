"""Ligue des Champions : 36 clubs répartis en 4 chapeaux de 9 (onglet "Ligue
des Champions" de data/joueurs.xlsx), tirés au sort en 9 poules de 4 -- un
club de chaque chapeau par poule -- puis élimination directe pour les 2
premiers de chaque poule.

Approximation du vrai format (phase de ligue façon Swiss à 36, classement
unique, barrages 9e-24e) : reconstruire ce format exact demanderait un
système de compétition entièrement nouveau. Le choix retenu (poules +
élimination) réutilise tel quel le moteur déjà construit et testé pour la
Compétition Perso (`groups.py`/`knockout.py`, via `CustomCompetition` en
format HYBRID) -- validé avec l'utilisateur.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ligue1sim.clubs import Club, load_all_clubs
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.groups import Group
from ligue1sim.schedule import generate_calendar

CL_SHEET = "Ligue des Champions"
CL_HEADER_ROW = 14
NB_CLUBS = 36
NB_POOLS = 9

POT_COLUMN = "Chapeau"
# Colonne à utiliser pour charger les effectifs : elle correspond exactement
# à la colonne "Club" de "Infos principales" (vérifié), contrairement à
# "Club" (nom d'affichage usuel, différent pour certains clubs -- ex. "FC
# Bruges" vs "Club Brugge KV").
CLUB_ROSTER_COLUMN = "Club (base joueurs)"


def _read_pots(path: str) -> dict[int, list[str]]:
    """{numéro de chapeau (1-4) : noms de club (colonne CLUB_ROSTER_COLUMN)}."""
    df = pd.read_excel(path, sheet_name=CL_SHEET, header=CL_HEADER_ROW, nrows=NB_CLUBS)
    return {int(pot): group[CLUB_ROSTER_COLUMN].tolist() for pot, group in df.groupby(POT_COLUMN)}


def load_champions_league_clubs(path: str) -> list[Club]:
    """Effectifs complets des 36 clubs qualifiés, chargés depuis le vivier
    complet (voir `clubs.load_all_clubs`)."""
    pots = _read_pots(path)
    names = {name for pot_clubs in pots.values() for name in pot_clubs}
    options = {o.name: o for o in load_all_clubs(path) if o.name in names}
    missing = names - options.keys()
    if missing:
        raise ValueError(f"Clubs de la Ligue des Champions introuvables dans le vivier : {sorted(missing)}")
    return [options[name].as_club() for name in names]


def draw_pools(path: str, legs: int = 1) -> list[Group]:
    """Tire au sort les 9 poules de 4 : un club de chaque chapeau par poule,
    au hasard au sein de chaque chapeau (n'évite pas les clubs d'un même
    championnat dans la même poule, contrairement au vrai tirage -- non
    reproduit ici, voir le docstring du module)."""
    pots = _read_pots(path)
    clubs_by_name = {o.name: o.as_club() for o in load_all_clubs(path)}

    buckets: list[list[Club]] = [[] for _ in range(NB_POOLS)]
    for pot_number in sorted(pots):
        names = list(pots[pot_number])
        np.random.shuffle(names)
        for index, name in enumerate(names):
            buckets[index].append(clubs_by_name[name])

    groups = []
    for index, group_clubs in enumerate(buckets):
        name = f"Poule {chr(ord('A') + index)}"
        calendar = generate_calendar(group_clubs, legs=legs)
        groups.append(Group(name=name, clubs=group_clubs, calendar=calendar))
    return groups


def start_champions_league(path: str, legs: int = 1) -> CustomCompetition:
    """Nouvelle Ligue des Champions : les 36 clubs, poules tirées au sort par
    chapeau, prête à simuler (même état/API que `CustomCompetition` HYBRID)."""
    clubs = load_champions_league_clubs(path)
    groups = draw_pools(path, legs=legs)
    return CustomCompetition(
        format=CompetitionFormat.HYBRID, legs=legs, clubs=clubs, preset_groups=groups, label="Ligue des Champions"
    )
