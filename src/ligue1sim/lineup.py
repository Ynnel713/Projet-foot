"""Sélection de la meilleure compo possible pour un club, à un instant donné.

Il n'existe pas de "note de club" stockée : la force d'un club (utilisée pour
calibrer la simulation Poisson et pour les têtes de série) se calcule
toujours à la volée à partir de la meilleure compo que son effectif permet
d'aligner *aujourd'hui* (donc en tenant compte des indisponibilités), via
`club_strength`. C'est la même sélection de compo qui sert à afficher les
compos dans l'écran de détail d'un match : un seul calcul, deux usages.
"""

from __future__ import annotations

from dataclasses import dataclass

from ligue1sim.clubs import Club
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, Player

# Dispositifs tactiques : quotas par grande famille de poste (GK/DEF/MID/ATT),
# totalisant toujours 11. Le choix du dispositif d'un club n'est pas figé :
# il est recalculé à chaque match (voir pick_best_formation) selon l'effectif
# réellement disponible ce jour-là.
FORMATIONS: dict[str, dict[str, int]] = {
    "4-4-2": {GOALKEEPER: 1, DEFENDER: 4, MIDFIELDER: 4, ATTACKER: 2},
    "4-3-3": {GOALKEEPER: 1, DEFENDER: 4, MIDFIELDER: 3, ATTACKER: 3},
    "4-2-3-1": {GOALKEEPER: 1, DEFENDER: 4, MIDFIELDER: 5, ATTACKER: 1},
}

# Force de repli si un club n'a strictement aucun joueur éligible (aucun
# effectif chargé, ou indisponibilités couvrant tout l'effectif -- en
# pratique n'arrive que dans des scénarios de test synthétiques).
DEFAULT_RATING = 60.0


@dataclass(frozen=True)
class Lineup:
    club_name: str
    formation: str
    players: list[Player]
    rating: float


def select_best_xi(club: Club, formation: str, unavailable: frozenset[str] = frozenset()) -> Lineup:
    """Meilleure compo pour `club` dans le dispositif `formation`, en excluant
    les joueurs de `unavailable` (blessés/suspendus). Complète les postes
    incomplets par les meilleurs joueurs restants toutes catégories
    confondues (petit effectif, indisponibilités massives)."""
    quotas = FORMATIONS[formation]
    eligible = [p for p in club.players if p.name not in unavailable]

    by_group: dict[str, list[Player]] = {group: [] for group in quotas}
    for player in eligible:
        by_group.setdefault(player.group, []).append(player)
    for group_players in by_group.values():
        group_players.sort(key=lambda p: -p.note)

    xi: list[Player] = []
    used_names: set[str] = set()
    for group, slots in quotas.items():
        picks = by_group.get(group, [])[:slots]
        xi.extend(picks)
        used_names.update(p.name for p in picks)

    shortfall = 11 - len(xi)
    if shortfall > 0:
        backfill = sorted((p for p in eligible if p.name not in used_names), key=lambda p: -p.note)
        xi.extend(backfill[:shortfall])

    rating = (sum(p.note for p in xi) / len(xi)) if xi else DEFAULT_RATING
    return Lineup(club_name=club.name, formation=formation, players=xi, rating=rating)


def pick_best_formation(club: Club, unavailable: frozenset[str] = frozenset()) -> Lineup:
    """Essaie les 3 dispositifs avec l'effectif dispo aujourd'hui, retourne
    celui qui donne la meilleure note de compo moyenne -- un effectif riche
    en ailiers/attaquants penche vers le 4-3-3, un effectif riche au milieu
    vers le 4-2-3-1, etc., sans configuration manuelle par club."""
    candidates = [select_best_xi(club, formation, unavailable) for formation in FORMATIONS]
    return max(candidates, key=lambda lineup: lineup.rating)


def club_strength(club: Club, unavailable: frozenset[str] = frozenset()) -> float:
    """Force actuelle du club = note moyenne de sa meilleure compo possible
    aujourd'hui. Jamais stockée : recalculée à chaque appel."""
    return pick_best_formation(club, unavailable).rating


def bench(club: Club, lineup: Lineup, unavailable: frozenset[str] = frozenset()) -> list[Player]:
    """Joueurs disponibles non retenus dans `lineup` -- le vivier de
    remplacement pour les substitutions."""
    starters = {p.name for p in lineup.players}
    return [p for p in club.players if p.name not in unavailable and p.name not in starters]
