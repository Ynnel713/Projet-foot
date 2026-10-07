import pytest

from ligue1sim.pitch_geometry import (
    CANVAS_HEIGHT_PX,
    CANVAS_WIDTH_PX,
    GRID_COLUMNS,
    GRID_ROWS,
    THIRD_ATTACKING,
    THIRD_DEFENSIVE,
    THIRD_MIDDLE,
    PitchPoint,
    Zone,
    center_of,
    to_canvas_px,
    zone_of,
    zones_in_third,
)


class TestGridSize:
    def test_default_grid_is_96_zones(self):
        assert GRID_COLUMNS * GRID_ROWS == 96


class TestZoneOfBounds:
    def test_origin_is_zone_zero_zero(self):
        assert zone_of(0.0, 0.0) == Zone(col=0, row=0)

    def test_far_corner_clamps_to_last_zone_instead_of_overflowing(self):
        # x=1.0/y=1.0 tomberaient mathématiquement dans une colonne/ligne
        # GRID_COLUMNS/GRID_ROWS inexistante sans le clamp -- doit retomber
        # sur la dernière zone valide, pas lever une erreur d'index.
        assert zone_of(1.0, 1.0) == Zone(col=GRID_COLUMNS - 1, row=GRID_ROWS - 1)

    def test_just_under_one_lands_in_the_same_last_zone_as_exactly_one(self):
        assert zone_of(0.999999, 0.999999) == Zone(col=GRID_COLUMNS - 1, row=GRID_ROWS - 1)

    def test_midpoint_of_pitch(self):
        # Colonne/ligne médiane : 0.5 * 12 = 6 (colonne 6, la 7e), 0.5 * 8 = 4.
        assert zone_of(0.5, 0.5) == Zone(col=6, row=4)

    @pytest.mark.parametrize("x", [-0.01, 1.01, -1.0, 2.0])
    def test_x_out_of_unit_range_raises(self, x):
        with pytest.raises(ValueError):
            zone_of(x, 0.5)

    @pytest.mark.parametrize("y", [-0.01, 1.01, -1.0, 2.0])
    def test_y_out_of_unit_range_raises(self, y):
        with pytest.raises(ValueError):
            zone_of(0.5, y)

    def test_respects_custom_grid_size(self):
        assert zone_of(0.5, 0.5, columns=4, rows=2) == Zone(col=2, row=1)


class TestCenterOf:
    def test_center_of_first_zone(self):
        point = center_of(Zone(col=0, row=0))
        assert point == PitchPoint(x=pytest.approx(1 / 24), y=pytest.approx(1 / 16))

    def test_center_of_last_zone(self):
        point = center_of(Zone(col=GRID_COLUMNS - 1, row=GRID_ROWS - 1))
        assert point.x == pytest.approx(1 - 1 / 24)
        assert point.y == pytest.approx(1 - 1 / 16)

    def test_center_roundtrips_through_zone_of(self):
        # Le centre d'une zone doit systématiquement retomber dans CETTE
        # même zone une fois repassé par zone_of (pas de décalage
        # d'arrondi qui la ferait glisser dans la zone voisine).
        for col in range(GRID_COLUMNS):
            for row in range(GRID_ROWS):
                zone = Zone(col=col, row=row)
                point = center_of(zone)
                assert zone_of(point.x, point.y) == zone

    @pytest.mark.parametrize("zone", [Zone(col=-1, row=0), Zone(col=GRID_COLUMNS, row=0)])
    def test_col_out_of_grid_raises(self, zone):
        with pytest.raises(ValueError):
            center_of(zone)

    @pytest.mark.parametrize("zone", [Zone(col=0, row=-1), Zone(col=0, row=GRID_ROWS)])
    def test_row_out_of_grid_raises(self, zone):
        with pytest.raises(ValueError):
            center_of(zone)


class TestLeftRightSymmetry:
    """"Gauche/droite" = l'axe latéral (y), pas l'axe x (qui porte la
    progression vers le but adverse et n'a donc aucune raison d'être
    symétrique -- le tiers défensif et le tiers offensif sont volontairement
    différents, voir TestZonesInThird)."""

    @pytest.mark.parametrize("y, mirrored_y", [(0.0, 1.0), (0.1, 0.9), (0.3, 0.7), (0.49, 0.51)])
    def test_zone_of_row_is_mirrored_around_the_centre_line(self, y, mirrored_y):
        row = zone_of(0.5, y).row
        mirrored_row = zone_of(0.5, mirrored_y).row
        assert row + mirrored_row == GRID_ROWS - 1

    def test_center_of_y_is_mirrored_around_the_centre_line(self):
        for row in range(GRID_ROWS):
            mirrored_row = GRID_ROWS - 1 - row
            y = center_of(Zone(col=0, row=row)).y
            mirrored_y = center_of(Zone(col=0, row=mirrored_row)).y
            assert y + mirrored_y == pytest.approx(1.0)

    def test_grid_row_count_is_even_so_no_row_sits_on_the_axis(self):
        # Un nombre de lignes pair garantit une symétrie stricte sans ligne
        # centrale ambiguë (partagée par aucune zone, contrairement à un
        # nombre impair de lignes).
        assert GRID_ROWS % 2 == 0


class TestZonesInThird:
    def test_thirds_partition_the_grid_without_overlap(self):
        defensive = set(zones_in_third(THIRD_DEFENSIVE))
        middle = set(zones_in_third(THIRD_MIDDLE))
        attacking = set(zones_in_third(THIRD_ATTACKING))

        assert defensive.isdisjoint(middle)
        assert defensive.isdisjoint(attacking)
        assert middle.isdisjoint(attacking)
        assert len(defensive) + len(middle) + len(attacking) == GRID_COLUMNS * GRID_ROWS

    def test_defensive_third_is_closest_to_the_defended_goal(self):
        defensive_cols = {zone.col for zone in zones_in_third(THIRD_DEFENSIVE)}
        assert defensive_cols == {0, 1, 2, 3}

    def test_attacking_third_is_closest_to_the_opponents_goal(self):
        attacking_cols = {zone.col for zone in zones_in_third(THIRD_ATTACKING)}
        assert attacking_cols == {8, 9, 10, 11}

    def test_unknown_third_raises(self):
        with pytest.raises(ValueError):
            zones_in_third("gauche")

    def test_columns_not_a_multiple_of_three_raises(self):
        with pytest.raises(ValueError):
            zones_in_third(THIRD_DEFENSIVE, columns=10)


class TestToCanvasPx:
    def test_default_canvas_size_is_1200x780(self):
        assert (CANVAS_WIDTH_PX, CANVAS_HEIGHT_PX) == (1200, 780)

    def test_bottom_left_pitch_origin_maps_to_bottom_left_of_canvas(self):
        # y=0 (touche basse) doit finir en BAS du canvas (px_y = hauteur),
        # car l'axe Y d'un canvas pointe vers le bas -- pas px_y = 0.
        px_x, px_y = to_canvas_px(PitchPoint(x=0.0, y=0.0))
        assert (px_x, px_y) == (0.0, CANVAS_HEIGHT_PX)

    def test_far_corner_towards_opponent_goal_maps_to_top_right_of_canvas(self):
        px_x, px_y = to_canvas_px(PitchPoint(x=1.0, y=1.0))
        assert (px_x, px_y) == (CANVAS_WIDTH_PX, 0.0)

    def test_pitch_centre_maps_to_canvas_centre_exactly(self):
        px_x, px_y = to_canvas_px(PitchPoint(x=0.5, y=0.5))
        assert (px_x, px_y) == (CANVAS_WIDTH_PX / 2, CANVAS_HEIGHT_PX / 2)

    def test_respects_a_custom_canvas_size(self):
        px_x, px_y = to_canvas_px(PitchPoint(x=0.5, y=0.0), canvas_width=600, canvas_height=400)
        assert (px_x, px_y) == (300.0, 400.0)


# --- Cotes du terrain (Phase 5, sous-étape 1) : source unique -----------------------------------------------------

import json
import math
from pathlib import Path

from ligue1sim import pitch_geometry as pg

_UI_JSON = Path(__file__).resolve().parent.parent / "ui" / "src" / "utils" / "pitchGeometry.json"


class TestFifaDimensions:
    def test_official_values_in_meters(self):
        assert (pg.PITCH_LENGTH_M, pg.PITCH_WIDTH_M) == (105.0, 68.0)
        assert (pg.PENALTY_AREA_DEPTH_M, pg.PENALTY_AREA_WIDTH_M) == (16.5, 40.32)
        assert (pg.GOAL_AREA_DEPTH_M, pg.GOAL_AREA_WIDTH_M) == (5.5, 18.32)
        assert pg.PENALTY_SPOT_DISTANCE_M == 11.0
        assert (pg.CENTER_CIRCLE_RADIUS_M, pg.PENALTY_ARC_RADIUS_M, pg.CORNER_ARC_RADIUS_M) == (9.15, 9.15, 1.0)
        assert (pg.GOAL_WIDTH_M, pg.GOAL_HEIGHT_M) == (7.32, 2.44)

    def test_exported_keys_match_declared_list(self):
        assert tuple(sorted(pg.pitch_dimensions())) == tuple(sorted(pg._EXPORTED_DIMENSIONS))

    def test_ui_json_is_derived_from_this_module(self):
        # Garde-fou de dérive : PitchField.jsx lit ce fichier. Régénérer :
        # python -m ligue1sim.pitch_geometry > ui/src/utils/pitchGeometry.json
        assert json.loads(_UI_JSON.read_text(encoding="utf-8")) == pg.pitch_dimensions()

    def test_corner_posts_are_the_four_pitch_corners(self):
        assert set(pg.corner_posts_m()) == {(0.0, 0.0), (0.0, 68.0), (105.0, 68.0), (105.0, 0.0)}

    def test_penalty_arc_half_angle(self):
        # Le cercle de 9,15 m centré à 11 m de la ligne coupe la ligne de surface (16,5 m) à 5,5 m du point.
        assert math.degrees(pg.penalty_arc_half_angle_rad()) == pytest.approx(53.05, abs=0.01)


class TestPitchProjection:
    def test_default_scale_is_isotropic_and_centered(self):
        scale, ox, oy = pg.pitch_rect_px()
        assert scale == pytest.approx(10.882, abs=1e-3)  # min(1160/105, 740/68), limité par la hauteur
        assert oy == 20.0 and ox == pytest.approx((1200 - 105 * scale) / 2)
        assert ox >= 20.0  # marge minimale respectée

    def test_normalized_corners_land_on_the_drawn_pitch_rectangle(self):
        scale, ox, oy = pg.pitch_rect_px()
        assert pg.to_pitch_px(pg.PitchPoint(0.0, 1.0)) == pytest.approx((ox, oy))
        assert pg.to_pitch_px(pg.PitchPoint(1.0, 0.0)) == pytest.approx((ox + 105 * scale, oy + 68 * scale))

    def test_goal_center_is_on_the_goal_line_mid_height(self):
        px, py = pg.to_pitch_px(pg.PitchPoint(0.0, 0.5))
        assert px == pytest.approx(pg.pitch_rect_px()[1]) and py == pytest.approx(390.0)

    def test_to_canvas_px_is_unchanged(self):
        assert to_canvas_px(PitchPoint(x=0.0, y=0.0)) == (0.0, CANVAS_HEIGHT_PX)
