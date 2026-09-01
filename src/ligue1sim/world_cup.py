"""Coupe du Monde : les 32 meilleures sélections nationales (classement par
force actuelle, voir `lineup.club_strength`), réparties en 4 chapeaux de 8
par force, tirées au sort en 8 groupes de 4 -- une sélection de chaque
chapeau par groupe -- puis élimination directe pour les 2 premiers de
chaque groupe.

Contrairement à la Ligue des Champions (`champions_league.py`), il n'existe
aucune donnée de qualification/chapeaux curée dans le classeur pour les
sélections nationales : qualifiés et chapeaux sont dérivés dynamiquement de
la force actuelle de chaque sélection, pas d'un vrai processus de
qualification par confédération. Même simplification assumée que la Ligue
des Champions pour le tirage : ne cherche pas à éviter deux sélections de la
même confédération dans le même groupe (le vrai tirage l'évite en partie) --
réutilise tel quel le moteur poules + élimination (`groups.py`/`knockout.py`
via `CustomCompetition` en format HYBRID)."""

from __future__ import annotations

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.groups import Group
from ligue1sim.lineup import club_strength
from ligue1sim.nations import load_national_teams
from ligue1sim.schedule import generate_calendar

NB_TEAMS = 32
NB_POOLS = 8
NB_POTS = 4


def qualified_teams(path: str) -> list[Club]:
    """Les `NB_TEAMS` sélections les mieux notées (force actuelle), triées
    par force décroissante -- l'ordre est réutilisé tel quel par
    `_pots` pour répartir les chapeaux."""
    teams = load_national_teams(path)
    return sorted(teams, key=lambda t: -club_strength(t))[:NB_TEAMS]


def _pots(teams: list[Club]) -> list[list[Club]]:
    """`teams` déjà trié par force décroissante (voir `qualified_teams`) :
    découpé en `NB_POTS` tranches contiguës de force comparable (chapeau 1 =
    les plus fortes)."""
    pot_size = len(teams) // NB_POTS
    return [teams[i * pot_size : (i + 1) * pot_size] for i in range(NB_POTS)]


def draw_pools(path: str, legs: int = 1) -> list[Group]:
    """Tire au sort les `NB_POOLS` groupes de 4 : une sélection de chaque
    chapeau par groupe, au hasard au sein de chaque chapeau."""
    pots = _pots(qualified_teams(path))

    buckets: list[list[Club]] = [[] for _ in range(NB_POOLS)]
    for pot in pots:
        shuffled = list(pot)
        np.random.shuffle(shuffled)
        for index, team in enumerate(shuffled):
            buckets[index].append(team)

    groups = []
    for index, group_teams in enumerate(buckets):
        name = f"Groupe {chr(ord('A') + index)}"
        calendar = generate_calendar(group_teams, legs=legs)
        groups.append(Group(name=name, clubs=group_teams, calendar=calendar))
    return groups


def start_world_cup(path: str, legs: int = 1) -> CustomCompetition:
    """Nouvelle Coupe du Monde : les 32 meilleures sélections, groupes tirés
    au sort par chapeau, prête à simuler (même état/API que
    `CustomCompetition` HYBRID -- voir `champions_league.start_champions_league`
    pour le même schéma côté clubs)."""
    teams = qualified_teams(path)
    groups = draw_pools(path, legs=legs)
    return CustomCompetition(
        format=CompetitionFormat.HYBRID, legs=legs, clubs=teams, preset_groups=groups, label="Coupe du Monde"
    )
