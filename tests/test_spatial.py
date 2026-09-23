import pytest

from ligue1sim.animation.spatial import (
    GRID_COLUMNS,
    PitchLayoutState,
    THIRD_DEFENSIVE,
    normalized_to_placed_player_xy,
    placed_player_to_normalized,
    zone_of,
    zones_in_third,
)
from ligue1sim.events import PlayerMatchStat
from ligue1sim.pitch_layout import PlacedPlayer, place_starting_xi


def _stat(poste: str, name: str) -> PlayerMatchStat:
    return PlayerMatchStat(player_name=name, club_name="Test FC", poste=poste, started=True)


def _four_three_three() -> list[PlayerMatchStat]:
    return [
        _stat("GK", "gk"),
        _stat("LB", "lb"),
        _stat("DC", "cb0"),
        _stat("DC", "cb1"),
        _stat("RB", "rb"),
        _stat("MDC", "mdc"),
        _stat("MC", "mc0"),
        _stat("MC", "mc1"),
        _stat("AG", "ag"),
        _stat("AD", "ad"),
        _stat("BU", "bu"),
    ]


class TestPlacedPlayerToNormalizedIsBijective:
    @pytest.mark.parametrize("attacking_up", [True, False])
    @pytest.mark.parametrize("x, y", [(12.0, 10.0), (50.0, 50.0), (88.0, 90.0), (0.0, 0.0), (100.0, 100.0)])
    def test_round_trips_exactly(self, x, y, attacking_up):
        placed = PlacedPlayer(stat=_stat("MC", "p"), x=x, y=y)
        point = placed_player_to_normalized(placed, attacking_up=attacking_up)
        back_x, back_y = normalized_to_placed_player_xy(point, attacking_up=attacking_up)
        assert back_x == pytest.approx(x)
        assert back_y == pytest.approx(y)

    def test_normalized_coordinates_stay_in_the_unit_range(self):
        for x in (0.0, 12.0, 50.0, 88.0, 100.0):
            for y in (0.0, 10.0, 50.0, 90.0, 100.0):
                point = placed_player_to_normalized(PlacedPlayer(stat=_stat("MC", "p"), x=x, y=y), attacking_up=True)
                assert 0.0 <= point.x <= 1.0
                assert 0.0 <= point.y <= 1.0

    def test_attacking_up_flips_the_progression_axis_only(self):
        placed = PlacedPlayer(stat=_stat("MC", "p"), x=50.0, y=20.0)
        up = placed_player_to_normalized(placed, attacking_up=True)
        down = placed_player_to_normalized(placed, attacking_up=False)
        # Même position latérale (y normalisé) des deux côtés -- seul le
        # sens de progression (x normalisé) dépend de attacking_up.
        assert up.y == pytest.approx(down.y)
        assert up.x == pytest.approx(1.0 - down.x)


class TestFormationLandsInPlausibleZones:
    """Vérifie que les 11 positions de formation d'un 4-3-3 réel (via
    pitch_layout.place_starting_xi) tombent, une fois converties, dans des
    zones cohérentes -- le gardien dans son propre tiers défensif, et une
    progression strictement croissante ligne par ligne vers l'attaque.

    Note : `pitch_layout._line_y` arrête volontairement les lignes
    offensives à 42% de profondeur (pour ne pas chevaucher visuellement le
    dispositif adverse sur le terrain partagé, voir son docstring) -- même
    la ligne d'attaque d'une formation de coup d'envoi ne tombe donc jamais
    dans le tiers OFFENSIF (>=66,7%) une fois convertie, seulement dans le
    tiers médian. C'est fidèle au vrai football (un attaquant démarre au
    coup d'envoi vers le milieu de terrain, pas déjà dans la surface
    adverse), donc ce test vérifie la progression croissante par ligne,
    pas une appartenance au tiers offensif."""

    @pytest.mark.parametrize("attacking_up", [True, False])
    def test_goalkeeper_is_deep_in_the_defensive_third(self, attacking_up):
        placed = place_starting_xi(_four_three_three(), attacking_up=attacking_up)
        state = PitchLayoutState(placed_players=tuple(placed), attacking_up=attacking_up)

        gk = next(p for p in state.placed_players if p.stat.poste == "GK")
        point = placed_player_to_normalized(gk, attacking_up=state.attacking_up)
        zone = zone_of(point.x, point.y)

        assert zone in zones_in_third(THIRD_DEFENSIVE)
        assert zone.col <= 1  # au ras de sa propre ligne de but (progression 0.1 -> colonne 1 sur 12)

    @pytest.mark.parametrize("attacking_up", [True, False])
    def test_progression_increases_strictly_from_goalkeeper_to_attack(self, attacking_up):
        placed = place_starting_xi(_four_three_three(), attacking_up=attacking_up)
        state = PitchLayoutState(placed_players=tuple(placed), attacking_up=attacking_up)
        by_poste = {p.stat.poste: p for p in state.placed_players}

        gk_x = placed_player_to_normalized(by_poste["GK"], attacking_up=attacking_up).x
        def_x = placed_player_to_normalized(by_poste["DC"], attacking_up=attacking_up).x
        mid_x = placed_player_to_normalized(by_poste["MC"], attacking_up=attacking_up).x
        att_x = placed_player_to_normalized(by_poste["BU"], attacking_up=attacking_up).x

        assert gk_x < def_x < mid_x < att_x

    @pytest.mark.parametrize("attacking_up", [True, False])
    def test_no_placed_player_reaches_the_attacking_third_from_kickoff_positions(self, attacking_up):
        # Voir la note de la classe : conséquence attendue de pitch_layout,
        # pas un défaut de la conversion -- documenté explicitement plutôt
        # que découvert en silence si pitch_layout change un jour.
        placed = place_starting_xi(_four_three_three(), attacking_up=attacking_up)
        for player in placed:
            point = placed_player_to_normalized(player, attacking_up=attacking_up)
            zone = zone_of(point.x, point.y)
            assert zone.col < GRID_COLUMNS * 2 // 3  # jamais dans le tiers offensif (colonnes 8-11)

    @pytest.mark.parametrize("attacking_up", [True, False])
    def test_wingers_land_on_opposite_lateral_halves(self, attacking_up):
        placed = place_starting_xi(_four_three_three(), attacking_up=attacking_up)
        by_poste = {p.stat.poste: p for p in placed}

        ag_y = placed_player_to_normalized(by_poste["AG"], attacking_up=attacking_up).y
        ad_y = placed_player_to_normalized(by_poste["AD"], attacking_up=attacking_up).y

        assert (ag_y < 0.5) != (ad_y < 0.5)  # de part et d'autre de l'axe central
