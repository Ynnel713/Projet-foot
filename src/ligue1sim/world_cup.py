"""Coupe du Monde : les 32 meilleures sélections nationales (classement par
force actuelle, voir `lineup.club_strength`), réparties en 4 chapeaux de 8
par force, tirées au sort en 8 groupes de 4 -- une sélection de chaque
chapeau par groupe -- puis élimination directe pour les 2 premiers de
chaque groupe.

Contrairement à la Ligue des Champions (`champions_league.py`), il n'existe
aucune donnée de qualification/chapeaux curée dans le classeur pour les
sélections nationales : qualifiés et chapeaux sont dérivés dynamiquement de
la force actuelle de chaque sélection, pas d'un vrai processus de
qualification par confédération.

Équilibre des groupes (29/09/2026, retour utilisateur -- un groupe à 4
sélections UEFA constaté en jeu) : contrairement à la vraie Coupe du Monde
(qualification par confédération, jamais plus de ~16 UEFA sur 32), ce
classement PAR SEULE FORCE peut qualifier bien plus de 16 sélections UEFA
(20/32 mesuré sur le vivier actuel) -- un plafond dur "max 2 UEFA par
groupe" (16 places sur 8 groupes) serait donc mathématiquement irréalisable
ici. `_group_uefa_caps` calcule le plafond le plus serré RÉELLEMENT
atteignable (répartition la plus égale possible du nombre réel de
qualifiés UEFA sur les 8 groupes, ex. 20 -> quatre groupes à 3, quatre à 2)
plutôt qu'un plafond fixe qui échouerait ou dégénérerait en pire cas (voir
le bug initial : 4 UEFA dans un seul groupe). Les confédérations hors UEFA
sont, elles, plafonnées à 1 par groupe sans condition (jamais plus de 4
qualifiés pour une seule d'entre elles sur ce vivier, donc toujours
réalisable sur 8 groupes)."""

from __future__ import annotations

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.groups import Group
from ligue1sim.lineup import club_strength
from ligue1sim.nations import confederation, load_national_teams
from ligue1sim.schedule import generate_calendar

NB_TEAMS = 32
NB_POOLS = 8
NB_POTS = 4
_UEFA = "UEFA"


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


def _group_uefa_caps(uefa_count: int) -> list[int]:
    """Plafond de sélections UEFA par groupe, le plus proche possible de 2
    (répartition la plus égale du nombre RÉEL de qualifiés UEFA sur
    `NB_POOLS` groupes) -- voir docstring du module. Ordre mélangé pour ne
    pas toujours donner le plafond relevé aux mêmes groupes (A, B, C...)."""
    base, extra = divmod(uefa_count, NB_POOLS)
    caps = [base + 1] * extra + [base] * (NB_POOLS - extra)
    np.random.shuffle(caps)
    return caps


def _place_pot(
    pot: list[Club],
    confeds: dict[str, str],
    group_uefa_count: list[int],
    group_uefa_cap: list[int],
    group_confeds: list[set[str]],
) -> list[Club] | None:
    """Assigne chaque sélection de `pot` à un groupe distinct (une par
    groupe), en respectant `group_uefa_cap` (UEFA) et un plafond dur de 1
    par confédération non-UEFA -- recherche avec retour en arrière
    (backtracking), ordre aléatoire à chaque tentative. `group_uefa_count`/
    `group_confeds` sont mutés EN PLACE pour refléter l'affectation trouvée
    (uniquement en cas de succès -- toute branche abandonnée est annulée
    avant de remonter). Renvoie `None` si aucune affectation valide
    n'existe (ne devrait pas arriver avec des plafonds calculés par
    `_group_uefa_caps`, mais mieux vaut échouer proprement qu'boucler)."""
    teams = list(pot)
    np.random.shuffle(teams)
    assignment: list[Club | None] = [None] * NB_POOLS

    def backtrack(team_index: int, used_groups: set[int]) -> bool:
        if team_index == len(teams):
            return True
        team = teams[team_index]
        confed = confeds.get(team.name, "?")
        candidates = [g for g in range(NB_POOLS) if g not in used_groups]
        np.random.shuffle(candidates)
        for g in candidates:
            if confed == _UEFA:
                if group_uefa_count[g] >= group_uefa_cap[g]:
                    continue
            elif confed in group_confeds[g]:
                continue

            assignment[g] = team
            used_groups.add(g)
            if confed == _UEFA:
                group_uefa_count[g] += 1
            else:
                group_confeds[g].add(confed)

            if backtrack(team_index + 1, used_groups):
                return True

            assignment[g] = None
            used_groups.discard(g)
            if confed == _UEFA:
                group_uefa_count[g] -= 1
            else:
                group_confeds[g].discard(confed)
        return False

    if not backtrack(0, set()):
        return None
    return assignment  # type: ignore[return-value]


_MAX_DRAW_ATTEMPTS = 300


def _attempt_draw(pots: list[list[Club]], confeds: dict[str, str], group_uefa_cap: list[int]) -> list[list[Club]] | None:
    """Une tentative de répartition des `NB_POTS` chapeaux sur les
    `NB_POOLS` groupes. Contrairement à un retour en arrière limité à
    l'intérieur d'un seul chapeau, un chapeau qui échoue ici fait échouer
    TOUTE la tentative (voir `draw_pools`, qui relance depuis zéro) : le
    conflit vient souvent d'un choix fait sur un chapeau précédent, pas du
    chapeau qui échoue lui-même -- persévérer localement ne peut pas le
    résoudre."""
    buckets: list[list[Club]] = [[] for _ in range(NB_POOLS)]
    group_uefa_count = [0] * NB_POOLS
    group_confeds: list[set[str]] = [set() for _ in range(NB_POOLS)]

    for pot in pots:
        assignment = _place_pot(pot, confeds, group_uefa_count, group_uefa_cap, group_confeds)
        if assignment is None:
            return None
        for index, team in enumerate(assignment):
            buckets[index].append(team)
    return buckets


def draw_pools(path: str, legs: int = 1) -> list[Group]:
    """Tire au sort les `NB_POOLS` groupes de 4 : une sélection de chaque
    chapeau par groupe, au hasard au sein de chaque chapeau, sous réserve de
    l'équilibre des confédérations (voir docstring du module et
    `_place_pot`). Le plafond UEFA par groupe (`_group_uefa_caps`) est
    calculé pour rester globalement atteignable, mais une répartition
    précise entre chapeaux peut ponctuellement coincer une tentative --
    jusqu'à `_MAX_DRAW_ATTEMPTS` tirages complets sont essayés avant
    d'abandonner la contrainte (jamais observé nécessaire en pratique sur le
    vivier actuel, mais un vrai échec vaut mieux qu'une boucle infinie)."""
    qualified = qualified_teams(path)
    pots = _pots(qualified)
    confeds = {team.name: confederation(path, team.name) for team in qualified}
    uefa_count = sum(1 for c in confeds.values() if c == _UEFA)

    buckets = None
    for _ in range(_MAX_DRAW_ATTEMPTS):
        group_uefa_cap = _group_uefa_caps(uefa_count)
        buckets = _attempt_draw(pots, confeds, group_uefa_cap)
        if buckets is not None:
            break
    if buckets is None:
        # Repli ultime (voir docstring) : jamais déclenché en pratique --
        # un vrai tirage sans la contraine plutôt qu'une exception qui
        # empêcherait toute Coupe du Monde.
        buckets = [[] for _ in range(NB_POOLS)]
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
