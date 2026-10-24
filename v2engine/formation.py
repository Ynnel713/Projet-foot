"""Positions de coup d'envoi des 11 titulaires d'une équipe, dérivées de la Lineup déjà calculée
par la V1 (`ligue1sim.lineup.pick_best_formation`, réutilisée en lecture seule, voir D-V02).

Volontairement simple (bandes régulièrement espacées en largeur) -- pas une reprise de
`pitch_layout.place_starting_xi`, qui dépend du pipeline de résultats déjà joué
(`PlayerMatchStat`, buts/cartons/entrées en jeu) et ne convient pas à un placement AVANT match."""

from __future__ import annotations

from ligue1sim.lineup import Lineup
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, position_group

from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2

_WIDTH_MARGIN_M = 5.0
_DEPTH_MARGIN_M = 5.0
_DEPTH_SPAN_M = 40.0  # du gardien à la ligne la plus avancée -- reste dans sa moitié de terrain au coup d'envoi
_GENERIC_BAND = {GOALKEEPER: 0, DEFENDER: 1, MIDFIELDER: 2, ATTACKER: 3}


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

    nb_bands = max(by_band) + 1
    positions: dict[str, Vec2] = {}
    for band, names in by_band.items():
        depth_ratio = band / max(nb_bands - 1, 1)  # 0 = gardien, 1 = ligne la plus avancée
        x = (_DEPTH_MARGIN_M + depth_ratio * _DEPTH_SPAN_M) if attacking_right else (
            PITCH_LENGTH_M - _DEPTH_MARGIN_M - depth_ratio * _DEPTH_SPAN_M
        )
        usable_width = PITCH_WIDTH_M - 2 * _WIDTH_MARGIN_M
        step = usable_width / (len(names) + 1)
        for i, name in enumerate(sorted(names), start=1):
            positions[name] = Vec2(x, _WIDTH_MARGIN_M + i * step)
    return positions
