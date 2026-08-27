"""Sélection de la meilleure compo possible pour un club, à un instant donné.

Il n'existe pas de "note de club" stockée : la force d'un club (utilisée pour
calibrer la simulation Poisson et pour les têtes de série) se calcule
toujours à la volée à partir de la meilleure compo que son effectif permet
d'aligner *aujourd'hui* (donc en tenant compte des indisponibilités), via
`club_strength`. C'est la même sélection de compo qui sert à afficher les
compos dans l'écran de détail d'un match : un seul calcul, deux usages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from ligue1sim.clubs import Club
from ligue1sim.coaches import preferred_formations
from ligue1sim.players import (
    ATTACKER,
    DEFENDER,
    GOALKEEPER,
    MIDFIELDER,
    Player,
    best_distance_to_group,
    poste_distance,
)

# --- Dispositifs tactiques : postes exacts par place -------------------
# Sourcés de l'onglet "Dispositifs tactiques" de data/joueurs.xlsx : une
# colonne par dispositif (ex. "4-2-3-1"), 11 lignes donnant le ou les postes
# acceptés pour chacune des 11 places (une cellule "MC ou MDC" veut dire que
# cette place accepte l'un ou l'autre). "MO" y est un raccourci pour MOC.
FORMATIONS_PATH = "data/joueurs.xlsx"
FORMATIONS_SHEET = "Dispositifs tactiques"
_POSTE_ALIASES = {"MO": "MOC"}


@lru_cache(maxsize=None)
def _load_formation_slots(path: str, sheet: str) -> dict[str, tuple[tuple[str, ...], ...]]:
    if not Path(path).exists():
        return {}
    df = pd.read_excel(path, sheet_name=sheet)
    slots: dict[str, tuple[tuple[str, ...], ...]] = {}
    for formation in df.columns:
        rows = []
        for cell in df[formation]:
            if pd.isna(cell):
                continue
            options = tuple(_POSTE_ALIASES.get(p.strip(), p.strip()) for p in str(cell).split(" ou "))
            rows.append(options)
        slots[str(formation)] = tuple(rows)
    return slots


def formation_slots(
    path: str = FORMATIONS_PATH, sheet: str = FORMATIONS_SHEET
) -> dict[str, tuple[tuple[str, ...], ...]]:
    """{nom du dispositif: 11-uplet de postes acceptés par place}, voir
    `_load_formation_slots`. Résultat mis en cache -- `clear_cache()` pour
    forcer un rechargement (tests, ou fichier modifié en cours de session)."""
    return _load_formation_slots(path, sheet)


def clear_cache() -> None:
    _load_formation_slots.cache_clear()


# Quotas génériques GK/DEF/MID/ATT, utilisés seulement en repli pour un
# dispositif absent de l'onglet "Dispositifs tactiques" (ex. une formation
# préférentielle Transfermarkt non répertoriée, voir `parse_formation` et
# `pick_best_formation`).
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
    # Moyenne globale des 11 -- toujours utilisée telle quelle pour les têtes
    # de série (groups.py/knockout.py) et l'affichage (force d'un club) :
    # c'est la moyenne PONDÉRÉE par secteur (gk/def/mid/att ci-dessous) qui
    # pilote la simulation des matchs, pas celle-ci (voir simulation.py).
    rating: float
    # Moyenne du secteur (gardien seul, défenseurs, milieux, attaquants) au
    # sein de CETTE compo précise -- retombe sur `rating` si le secteur est
    # vide dans le onze (effectif dégradé/synthétique sans joueur de ce
    # groupe). Voir simulation._match_strengths pour leur usage : le milieu
    # module légèrement l'attaque et la défense, la défense combine def+gk.
    gk_rating: float = 0.0
    def_rating: float = 0.0
    mid_rating: float = 0.0
    att_rating: float = 0.0
    # {nom du joueur: indice de ligne, 0 = gardien, 1 = ligne la plus reculée
    # des joueurs de champ, etc.} -- déduit des groupes à tirets du nom du
    # dispositif (ex. "3-4-2-1" -> lignes de 3, 4, 2 puis 1 joueurs), pour un
    # rendu de terrain fidèle à l'onglet "Dispositifs tactiques" (voir
    # `pitch_layout._group_into_lines`). Vide pour le repli par quotas
    # génériques (dispositif absent de l'onglet).
    bands: dict[str, int] = field(default_factory=dict)


_FORMATION_PREFIX = re.compile(r"^\s*(\d+(?:-\d+)+)")


def parse_formation(formation: str) -> dict[str, int]:
    """Convertit une notation à tirets (ex. "4-4-2", "4-2-3-1", "3-5-2") en
    quotas GK/DEF/MID/ATT : par convention tactique standard, le premier
    nombre est la défense, le dernier l'attaque, et tout ce qu'il y a entre
    les deux est additionné au milieu de terrain.

    Ne garde que le préfixe numérique à tirets : Transfermarkt qualifie
    parfois la formation préférentielle d'un entraîneur d'un adjectif
    (ex. "4-3-3 offensif", "3-4-3 plat") -- ce texte est ignoré pour le
    calcul des quotas, mais la chaîne d'origine reste affichée telle quelle
    ailleurs (fiche entraîneur, Excel)."""
    match = _FORMATION_PREFIX.match(formation)
    if match is None:
        raise ValueError(f"Dispositif invalide : {formation!r} (attendu une notation à tirets, ex. '4-2-3-1')")
    parts = [int(p) for p in match.group(1).split("-")]
    if sum(parts) != 10:
        raise ValueError(f"Dispositif invalide : {formation!r} (doit sommer à 10 joueurs de champ)")
    defense, *middle, attack = parts
    return {GOALKEEPER: 1, DEFENDER: defense, MIDFIELDER: sum(middle), ATTACKER: attack}


def _formation_prefix(formation: str) -> str | None:
    match = _FORMATION_PREFIX.match(formation)
    return match.group(1) if match else None


# Distance maximale (voir `players.poste_distance`) tolérée pour qu'un joueur
# dépanne hors de son poste naturel, dans le repli générique par quotas
# GK/DEF/MID/ATT (dispositif absent de l'onglet "Dispositifs tactiques").
_MAX_BRICOLAGE_DISTANCE = 1


def select_best_xi(club: Club, formation: str, unavailable: frozenset[str] = frozenset()) -> Lineup:
    """Meilleure compo pour `club` dans le dispositif `formation`, en excluant
    les joueurs de `unavailable` (blessés/suspendus).

    Si `formation` est un des dispositifs de l'onglet "Dispositifs
    tactiques", chacune des 11 places est pourvue par le meilleur joueur
    disponible dont le poste principal correspond exactement à ce qu'exige
    la place (ex. "RB" pour un latéral droit, "MC ou MDC" pour une place de
    milieu flexible) -- places les plus strictes (un seul poste accepté)
    pourvues en premier. Si personne au poste principal ne convient, on
    retombe sur un joueur dont un poste secondaire déclaré correspond (voir
    `Player.poste_secondaire`). En tout dernier recours, si des places
    restent vides et qu'il reste des joueurs éligibles, on les complète avec
    les meilleurs joueurs restants quel que soit leur poste -- une équipe de
    football aligne toujours 11 joueurs quand son effectif le permet, quitte
    à dépanner hors de position plutôt que jouer à 10.

    Si `formation` n'est PAS dans l'onglet (ex. formation préférentielle
    Transfermarkt non répertoriée), repli sur l'ancien système par quotas
    génériques GK/DEF/MID/ATT (voir `parse_formation`), avec un dépannage
    tolérant les postes tactiquement proches (`_MAX_BRICOLAGE_DISTANCE`)."""
    eligible = [p for p in club.players if p.name not in unavailable]

    slots = formation_slots(FORMATIONS_PATH, FORMATIONS_SHEET).get(_formation_prefix(formation) or formation)
    if slots is not None:
        bands = _formation_bands(formation, len(slots))
        xi, player_bands = _assign_slots(eligible, list(zip(slots, bands)))
    else:
        xi = _select_by_group_quota(eligible, parse_formation(formation))
        player_bands = {}

    rating = (sum(p.note for p in xi) / len(xi)) if xi else DEFAULT_RATING
    return Lineup(
        club_name=club.name,
        formation=formation,
        players=xi,
        rating=rating,
        gk_rating=_group_rating(xi, GOALKEEPER, rating),
        def_rating=_group_rating(xi, DEFENDER, rating),
        mid_rating=_group_rating(xi, MIDFIELDER, rating),
        att_rating=_group_rating(xi, ATTACKER, rating),
        bands=player_bands,
    )


def _group_rating(xi: list[Player], group: str, fallback: float) -> float:
    """Moyenne des notes des joueurs de `xi` appartenant à `group`
    (GK/DEF/MID/ATT). Retombe sur `fallback` (la moyenne globale de la compo)
    si aucun joueur de ce groupe n'est aligné -- un secteur totalement vide
    ne doit pas s'effondrer à 0 et fausser le calcul du match."""
    members = [p.note for p in xi if p.group == group]
    return sum(members) / len(members) if members else fallback


def _formation_bands(formation: str, nb_slots: int) -> list[int]:
    """Indice de ligne pour chacune des `nb_slots` places de l'onglet
    "Dispositifs tactiques", dans son ordre d'origine (gardien d'abord, puis
    les groupes à tirets du nom du dispositif ex. "3-4-2-1" -> lignes de 3,
    4, 2 puis 1 joueurs). Le gardien est toujours seul en ligne 0."""
    prefix = _formation_prefix(formation) or formation
    band_sizes = [int(p) for p in prefix.split("-")]
    bands = [0]
    for band_index, size in enumerate(band_sizes, start=1):
        bands += [band_index] * size
    return bands[:nb_slots]


def _assign_slots(
    eligible: list[Player], slots: list[tuple[tuple[str, ...], int]]
) -> tuple[list[Player], dict[str, int]]:
    used: set[str] = set()
    xi: list[Player] = []
    player_bands: dict[str, int] = {}

    # places les plus strictes (un seul poste accepté) en premier, pour ne
    # pas laisser une place flexible ("MC ou MDC") consommer le seul joueur
    # capable de pourvoir une place rigide voisine.
    ordered_slots = sorted(slots, key=lambda s: len(s[0]))

    unfilled: list[tuple[tuple[str, ...], int]] = []
    for options, band in ordered_slots:
        pool = sorted((p for p in eligible if p.name not in used and p.poste in options), key=lambda p: -p.note)
        if pool:
            xi.append(pool[0])
            used.add(pool[0].name)
            player_bands[pool[0].name] = band
        else:
            unfilled.append((options, band))

    still_unfilled: list[tuple[tuple[str, ...], int]] = []
    for options, band in unfilled:
        pool = sorted(
            (p for p in eligible if p.name not in used and any(s in options for s in p.poste_secondaire)),
            key=lambda p: -p.note,
        )
        if pool:
            xi.append(pool[0])
            used.add(pool[0].name)
            player_bands[pool[0].name] = band
        else:
            still_unfilled.append((options, band))

    # Avant le dernier recours totalement aveugle : dépanner avec le joueur
    # tactiquement le plus proche du poste manquant (ex. un ailier pour
    # dépanner en pointe) plutôt que le meilleur joueur toutes positions
    # confondues, qui pourrait être un pur défenseur envoyé en attaque. Même
    # tolérance de distance et même graphe de proximité (`poste_distance`)
    # que le repli générique `_select_by_group_quota`.
    unfilled_far: list[tuple[tuple[str, ...], int]] = []
    for options, band in still_unfilled:
        candidates = [
            (p, distance)
            for p in eligible
            if p.name not in used
            and (distance := _closest_poste_distance((p.poste, *p.poste_secondaire), options)) is not None
            and distance <= _MAX_BRICOLAGE_DISTANCE
        ]
        candidates.sort(key=lambda c: (c[1], -c[0].note))
        if candidates:
            player = candidates[0][0]
            xi.append(player)
            used.add(player.name)
            player_bands[player.name] = band
        else:
            unfilled_far.append((options, band))

    if unfilled_far:
        backfill = sorted((p for p in eligible if p.name not in used), key=lambda p: -p.note)
        for player, (_, band) in zip(backfill, unfilled_far):
            xi.append(player)
            player_bands[player.name] = band

    return xi, player_bands


def _closest_poste_distance(postes: tuple[str, ...], options: tuple[str, ...]) -> int | None:
    """Distance minimale (voir `players.poste_distance`) entre l'un des
    postes de `postes` (poste principal + secondaires) et l'un des postes
    acceptés par une place de dispositif. `None` si aucun chemin n'existe."""
    distances = [d for p in postes for o in options if (d := poste_distance(p, o)) is not None]
    return min(distances) if distances else None


def _select_by_group_quota(eligible: list[Player], quotas: dict[str, int]) -> list[Player]:
    """Ancien système par quotas GK/DEF/MID/ATT avec dépannage tolérant les
    postes tactiquement proches -- repli pour un dispositif absent de
    l'onglet "Dispositifs tactiques" (voir `select_best_xi`)."""
    by_group: dict[str, list[Player]] = {group: [] for group in quotas}
    for player in eligible:
        by_group.setdefault(player.group, []).append(player)
    for group_players in by_group.values():
        group_players.sort(key=lambda p: -p.note)

    xi: list[Player] = []
    used_names: set[str] = set()
    missing: dict[str, int] = {}
    for group, slots in quotas.items():
        picks = by_group.get(group, [])[:slots]
        xi.extend(picks)
        used_names.update(p.name for p in picks)
        missing[group] = slots - len(picks)

    for group, nb_missing in missing.items():
        if nb_missing <= 0:
            continue
        candidates = [
            (player, distance)
            for player in eligible
            if player.name not in used_names
            and (distance := best_distance_to_group((player.poste, *player.poste_secondaire), group)) is not None
            and distance <= _MAX_BRICOLAGE_DISTANCE
        ]
        candidates.sort(key=lambda c: (c[1], -c[0].note))
        picks = [player for player, _ in candidates[:nb_missing]]
        xi.extend(picks)
        used_names.update(p.name for p in picks)

    shortfall = 11 - len(xi)
    if shortfall > 0:
        backfill = sorted((p for p in eligible if p.name not in used_names), key=lambda p: -p.note)
        xi.extend(backfill[:shortfall])

    return xi


# Marge qu'un dispositif alternatif doit dépasser sur le dispositif imposé
# par le coach pour justifier d'y basculer (voir `pick_best_formation`) : un
# effectif au complet garde toujours le dispositif du coach (pas de bascule
# tant qu'il n'y a aucune indisponibilité, voir plus bas), et un écart trop
# faible ne doit pas faire changer de système à la moindre fluctuation. 3%
# absorbe le bruit habituel entre deux compos proches tout en laissant un vrai
# trou d'effectif (plusieurs titulaires clés absents à un secteur) faire
# basculer sur un système mieux adapté à l'effectif du jour, plutôt que de
# forcer un jeune totalement hors niveau à un poste qu'il ne tient pas.
_FORMATION_LOYALTY_FACTOR = 1.03


def pick_best_formation(club: Club, unavailable: frozenset[str] = frozenset()) -> Lineup:
    """Si l'entraîneur du club a une formation préférentielle connue (voir
    `coaches.preferred_formations`, sourcé de Transfermarkt), le club joue
    dans ce dispositif par défaut -- quitte à dépanner certains postes (voir
    `select_best_xi`). Effectif au complet (`unavailable` vide) : le
    dispositif du coach s'applique sans condition, comportement historique
    inchangé.

    Si des joueurs sont indisponibles (blessure, suspension) ET qu'un autre
    dispositif connu donne une compo nettement meilleure avec l'effectif du
    jour (au-delà de `_FORMATION_LOYALTY_FACTOR`, voir plus haut), le club
    bascule sur ce dispositif alternatif plutôt que de s'entêter sur un
    système qu'il n'a plus les moyens de tenir.

    Si le club n'a pas de dispositif préférentiel connu (championnat pas
    encore recherché), retombe sur le choix adaptatif historique : essaie
    tous les dispositifs de l'onglet "Dispositifs tactiques" avec l'effectif
    dispo aujourd'hui, retourne celui qui donne la meilleure note de compo
    moyenne -- un effectif riche en ailiers/attaquants penche vers un
    dispositif à 3 attaquants, un effectif riche au milieu vers un 4-2-3-1,
    etc."""
    known_formations = list(formation_slots(FORMATIONS_PATH, FORMATIONS_SHEET).keys()) or list(FORMATIONS.keys())

    forced_formation = preferred_formations().get(club.name)
    if forced_formation is None:
        candidates = [select_best_xi(club, formation, unavailable) for formation in known_formations]
        return max(candidates, key=lambda lineup: lineup.rating)

    forced_lineup = select_best_xi(club, forced_formation, unavailable)
    if not unavailable:
        return forced_lineup

    alternatives = [
        select_best_xi(club, formation, unavailable) for formation in known_formations if formation != forced_formation
    ]
    if not alternatives:
        return forced_lineup
    best_alternative = max(alternatives, key=lambda lineup: lineup.rating)
    if best_alternative.rating > forced_lineup.rating * _FORMATION_LOYALTY_FACTOR:
        return best_alternative
    return forced_lineup


def club_strength(club: Club, unavailable: frozenset[str] = frozenset()) -> float:
    """Force actuelle du club = note moyenne de sa meilleure compo possible
    aujourd'hui. Jamais stockée : recalculée à chaque appel."""
    return pick_best_formation(club, unavailable).rating


def bench(club: Club, lineup: Lineup, unavailable: frozenset[str] = frozenset()) -> list[Player]:
    """Joueurs disponibles non retenus dans `lineup` -- le vivier de
    remplacement pour les substitutions."""
    starters = {p.name for p in lineup.players}
    return [p for p in club.players if p.name not in unavailable and p.name not in starters]
