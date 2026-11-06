"""Positions de coup d'envoi des 11 titulaires d'une équipe, dérivées de la Lineup déjà calculée
par la V1 (`ligue1sim.lineup.pick_best_formation`, réutilisée en lecture seule, voir D-V02).

Volontairement simple (bandes régulièrement espacées en largeur) -- pas une reprise de
`pitch_layout.place_starting_xi`, qui dépend du pipeline de résultats déjà joué
(`PlayerMatchStat`, buts/cartons/entrées en jeu) et ne convient pas à un placement AVANT match."""

from __future__ import annotations

from ligue1sim.lineup import Lineup
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, position_group

from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2

_DEPTH_MARGIN_M = 5.0
_DEPTH_SPAN_M = 40.0  # du gardien à la ligne la plus avancée -- reste dans sa moitié de terrain au coup d'envoi
_GENERIC_BAND = {GOALKEEPER: 0, DEFENDER: 1, MIDFIELDER: 2, ATTACKER: 3}
# Couloir de chaque poste, vu de son propre but (0 = gauche de l'équipe, 1 = axe, 2 = droite) -- même convention que
# `pitch_layout._LANE`. Les postes absents sont axiaux. Le côté ne dépend jamais du nom du joueur (ticket v2-realisme/02a).
_LANE = {"LB": 0, "AG": 0, "RB": 2, "AD": 2}
# Distance à l'axe du terrain des postes latéraux (m), ticket v2-realisme/02b. Le latéral tient le couloir à 12 m de la
# touche, l'ailier plus haut à 8 m. Ordres de grandeur sur terrain de 68 m, source chiffrée non trouvée ; constantes
# proposées par Claude, validées par délégation du propriétaire (05/11/2026). `bloc.py` met ensuite la forme entière à
# l'échelle (40 m de large sans ballon) : seuls les rapports entre postes comptent. Deux latéraux du même côté dans
# une même bande (LB et AG) se décalent de `_INNER_STEP_M` vers l'axe.
_WIDE_DISTANCE_M = {"AG": 26.0, "AD": 26.0, "LB": 22.0, "RB": 22.0}
_INNER_STEP_M = 8.0
# Écart (m) entre deux joueurs d'un même poste axial, répartis symétriquement autour de l'axe : deux DC à ± 8 m,
# trois à 0 et ± 16 m. Une bande qui mêle plusieurs postes axiaux prend la moyenne de leurs écarts. Même statut que
# les distances ci-dessus.
_AXIAL_SPACING_M = {"DC": 16.0, "MDC": 12.0, "MC": 16.0, "MOC": 14.0, "SA": 14.0, "BU": 14.0, "ATT": 14.0}
_DEFAULT_SPACING_M = 14.0


def _bands(lineup: Lineup) -> dict[str, int]:
    """{nom du joueur: indice de bande}, du gardien (0) vers l'attaque -- `lineup.bands` si connu
    (dispositif reconnu dans l'onglet "Dispositifs tactiques"), repli générique par groupe de
    poste sinon (même principe de repli que `pitch_layout.actual_formation_label`)."""
    if lineup.bands:
        return lineup.bands
    return {p.name: _GENERIC_BAND.get(position_group(p.poste), 2) for p in lineup.players}


def initial_positions(lineup: Lineup, *, attacking_right: bool) -> dict[str, Vec2]:
    """Position de formation de chaque titulaire au coup d'envoi, en mètres. `attacking_right`
    (convention de ce moteur, voir `match.py`) : True = l'équipe défend x=0 et attaque vers
    x=PITCH_LENGTH_M (domicile) ; False = inverse (extérieur)."""
    bands = _bands(lineup)
    by_band: dict[int, list[str]] = {}
    for name, band in bands.items():
        by_band.setdefault(band, []).append(name)
    if not by_band:
        return {}

    # ordre de la lineup = ordre stable à poste égal (affectation des places, jamais le nom)
    rank = {p.name: i for i, p in enumerate(lineup.players)}
    poste = {p.name: p.poste for p in lineup.players}
    nb_bands = max(by_band) + 1
    centre_y = PITCH_WIDTH_M / 2.0
    # y croît vers le bas de l'écran (viewBox en mètres) : en attaquant vers +x, la gauche de l'équipe est en y
    # petit ; en attaquant vers x=0, tout est en miroir autour de l'axe.
    sign = 1.0 if attacking_right else -1.0
    positions: dict[str, Vec2] = {}
    for band, names in by_band.items():
        depth_ratio = band / max(nb_bands - 1, 1)  # 0 = gardien, 1 = ligne la plus avancée
        x = (_DEPTH_MARGIN_M + depth_ratio * _DEPTH_SPAN_M) if attacking_right else (
            PITCH_LENGTH_M - _DEPTH_MARGIN_M - depth_ratio * _DEPTH_SPAN_M
        )
        by_lane: dict[int, list[str]] = {0: [], 1: [], 2: []}
        for name in sorted(names, key=lambda n: rank.get(n, len(rank))):
            by_lane[_LANE.get(poste.get(name, ""), 1)].append(name)
        for lane, side in ((0, -1.0), (2, 1.0)):
            # le poste le plus large prend le couloir extérieur (ailier avant latéral), puis l'ordre de la lineup
            wide = sorted(by_lane[lane], key=lambda n: -_WIDE_DISTANCE_M[poste[n]])
            for k, name in enumerate(wide):
                distance = _WIDE_DISTANCE_M[poste[name]] - k * _INNER_STEP_M
                positions[name] = Vec2(x, centre_y + sign * side * distance)
        axial = by_lane[1]
        if axial:
            # le poste le plus resserré prend la place la plus proche de l'axe (un MDC entre deux MC, quel que soit
            # l'ordre de la lineup) ; à écart égal, l'ordre de la lineup. Places prises du centre vers l'extérieur,
            # la gauche avant la droite.
            spacings = [_AXIAL_SPACING_M.get(poste.get(n, ""), _DEFAULT_SPACING_M) for n in axial]
            spacing = sum(spacings) / len(spacings)
            slots = sorted(((i - (len(axial) - 1) / 2.0) * spacing for i in range(len(axial))), key=lambda o: (abs(o), o))
            by_narrowness = sorted(zip(axial, spacings), key=lambda t: t[1])  # tri stable : lineup à écart égal
            for (name, _), offset in zip(by_narrowness, slots):
                positions[name] = Vec2(x, centre_y + sign * offset)
    return positions
