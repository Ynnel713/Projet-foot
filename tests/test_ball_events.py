"""Phase 6, Bloc B4 (08/10/2026) : événements visuels du ballon (`engine/ball_events.py`) -- but, parade, poteau,
barre, corner, sortie de but, touche, dégagement.

Principe vérifié ici : le score est décidé en AMONT (moteur de Poisson). Une parade est la représentation visuelle
d'un non-but (`arret`) ; elle n'annule jamais un but, et n'est jamais décidée par une portée de gardien."""

import dataclasses
import math

import pytest

from ball_events import (
    ATTAQUANT,
    BALL_EVENT_TYPES,
    BARRE,
    BUT,
    CORNER,
    DEFENSEUR,
    DEGAGEMENT,
    LINE_CUT_S,
    PARADE,
    PARRY_AZIMUTH_JITTER_DEG,
    PARRY_RESTITUTION_RANGE,
    POTEAU,
    SORTIE_BUT,
    TOUCHE,
    BallPlan,
    _parry_exit_velocity,
    classify_line_exit,
    first_line_crossing,
    parry_trajectory,
    plan_ball_events,
)
from test_ball import _deflect_audit_lineup, _flight_event, _flight_start_positions

from ligue1sim.animation.templates import BUILDERS, TEMPLATES
from ligue1sim.animation.ball import ball_state_at
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

_GABARITS = sorted(TEMPLATES)
_NON_GOAL_MENU = {
    # issue visuelle (tirée en amont par `narrative.py`) -> types d'événements autorisés pour ce clip
    "arret": {PARADE, CORNER, TOUCHE},
    "hors_cadre": {SORTIE_BUT},
    "poteau": {POTEAU, TOUCHE, SORTIE_BUT},
    "barre": {BARRE, TOUCHE, SORTIE_BUT},
    "tacle": {DEGAGEMENT},
    "degagement": {DEGAGEMENT},
}


def _sequence(gabarit: str, outcome: str, minute: int = 34):
    event = dataclasses.replace(_flight_event(gabarit), minute=minute)
    return BUILDERS[gabarit](event, _deflect_audit_lineup(), _flight_start_positions(), outcome)


def _plan(gabarit: str, outcome: str, minute: int = 34) -> BallPlan:
    return plan_ball_events(_sequence(gabarit, outcome, minute), outcome, minute, "bu", "gk")


class TestNonGoalOutcomesBelongToTheVisualMenu:
    @pytest.mark.parametrize("gabarit", _GABARITS)
    @pytest.mark.parametrize("outcome", sorted(_NON_GOAL_MENU))
    def test_a_non_goal_produces_events_of_its_menu_entry(self, gabarit, outcome):
        for minute in (5, 21, 34, 58):
            plan = _plan(gabarit, outcome, minute)
            assert plan.events, f"{gabarit}/{outcome} : aucun événement"
            types = {e.type for e in plan.events}
            assert types <= _NON_GOAL_MENU[outcome], f"{gabarit}/{outcome}/{minute} : {types}"
            assert types <= set(BALL_EVENT_TYPES)
            assert BUT not in types  # un non-but ne produit jamais de but

    def test_the_first_event_names_the_visual_outcome(self):
        expected = {"arret": PARADE, "hors_cadre": SORTIE_BUT, "poteau": POTEAU, "barre": BARRE, "tacle": DEGAGEMENT,
                    "degagement": DEGAGEMENT}
        for outcome, event_type in expected.items():
            assert _plan("une_deux", outcome).events[0].type == event_type

    def test_events_carry_the_documented_fields_and_the_right_last_toucher(self):
        plan = _plan("corner", "arret")
        parade = plan.events[0]
        assert parade.joueur == "gk" and parade.last_toucher == DEFENSEUR and parade.t_minute == 34
        assert parade.event_ref and set(parade.to_dict()) == {
            "type", "t_minute", "t", "x", "y", "joueur", "direction_deg", "last_toucher", "event_ref"}
        assert _plan("corner", "poteau").events[0].last_toucher == ATTAQUANT
        assert _plan("corner", "hors_cadre").events[0].last_toucher == ATTAQUANT
        assert _plan("corner", "tacle").events[0].last_toucher == DEFENSEUR

    def test_unknown_or_missing_outcome_produces_nothing(self):
        assert plan_ball_events(_sequence("une_deux", "but"), None, 10, "bu", "gk") == BallPlan(())


class TestTheScoreIsNeverChanged:
    @pytest.mark.parametrize("gabarit", _GABARITS)
    def test_a_goal_is_a_goal_event_and_never_a_parade(self, gabarit):
        plan = _plan(gabarit, "but")
        assert [e.type for e in plan.events] == [BUT]
        assert plan.trajectory is None  # pas de rebond ni de parade après un but
        goal = plan.events[0]
        assert goal.x == 1.0 and goal.last_toucher == ATTAQUANT and goal.joueur == "bu"

    @pytest.mark.parametrize("gabarit", _GABARITS)
    def test_a_parry_never_sends_the_ball_into_the_goal(self, gabarit):
        for minute in range(1, 41):
            plan = _plan(gabarit, "arret", minute)
            crossing = first_line_crossing(plan.trajectory)
            if crossing is not None and crossing.kind == "goal_line":
                assert classify_line_exit("goal_line", crossing.y, crossing.z, DEFENSEUR) != BUT, (gabarit, minute)
            assert BUT not in {e.type for e in plan.events}

    def test_the_guard_holds_even_for_extreme_shots(self):
        contact = ball_state_at(_sequence("une_deux", "arret"), _sequence("une_deux", "arret").duration)
        for y in (0.47, 0.485, 0.5, 0.515, 0.53):
            for index in range(60):
                shot = dataclasses.replace(contact, y=y)
                crossing = first_line_crossing(parry_trajectory(shot, f"seed-{index}"))
                if crossing is not None and crossing.kind == "goal_line":
                    assert classify_line_exit("goal_line", crossing.y, crossing.z, DEFENSEUR) != BUT


class TestParryDirection:
    def test_exit_direction_is_varied(self):
        directions = set()
        for minute in range(1, 11):  # 10 tirs
            parade = _plan("profondeur_1v1", "arret", minute).events[0]
            directions.add(round(parade.direction_deg / 30.0))
        assert len(directions) >= 3, f"directions trop peu variées : {sorted(directions)}"

    def test_exit_speed_is_the_incoming_speed_times_a_restitution_in_the_validated_range(self):
        sequence = _sequence("une_deux", "arret")
        contact = ball_state_at(sequence, sequence.duration)
        incoming = math.hypot(contact.vx * PITCH_LENGTH_M, contact.vy * PITCH_WIDTH_M)
        low, high = PARRY_RESTITUTION_RANGE
        ratios = []
        for index in range(100):
            vx, vy, _ = _parry_exit_velocity(contact, f"event-{index}", 60.0)
            ratios.append(math.hypot(vx, vy) / incoming)
        assert all(low - 1e-9 <= r <= high + 1e-9 for r in ratios)
        assert min(ratios) < low + 0.05 and max(ratios) > high - 0.05  # toute la plage est utilisée
        # un tir à 30 m/s repart à 15-21 m/s
        assert 30.0 * low == 15.0 and 30.0 * high == pytest.approx(21.0)

    def test_azimuth_jitter_is_bounded_and_deterministic(self):
        sequence = _sequence("une_deux", "arret")
        contact = ball_state_at(sequence, sequence.duration)
        base = _parry_exit_velocity(contact, "x", 60.0, jitter=False)
        deviations = []
        for index in range(300):
            out = _parry_exit_velocity(contact, f"event-{index}", 60.0)
            delta = math.degrees(math.atan2(out[1], out[0]) - math.atan2(base[1], base[0]))
            deviations.append((delta + 180.0) % 360.0 - 180.0)
        # la restitution varie aussi (l'azimut non) : on compare des caps, pas des vitesses
        assert max(abs(d) for d in deviations) <= PARRY_AZIMUTH_JITTER_DEG + 1e-6
        assert min(deviations) < -5.0 and max(deviations) > 5.0
        assert _parry_exit_velocity(contact, "event-7", 60.0) == _parry_exit_velocity(contact, "event-7", 60.0)


class TestCornerAndGoalKickRules:
    def test_outside_the_posts_a_defender_touch_gives_a_corner(self):
        assert classify_line_exit("goal_line", 0.70, 0.5, DEFENSEUR) == CORNER
        assert classify_line_exit("goal_line", 0.20, 0.5, DEFENSEUR) == CORNER

    def test_outside_the_posts_an_attacker_touch_gives_a_goal_kick(self):
        assert classify_line_exit("goal_line", 0.70, 0.5, ATTAQUANT) == SORTIE_BUT
        assert classify_line_exit("goal_line", 0.20, 0.5, ATTAQUANT) == SORTIE_BUT

    def test_between_the_posts_and_under_the_bar_it_is_a_goal_whoever_touched_it_last(self):
        assert classify_line_exit("goal_line", 0.50, 1.0, DEFENSEUR) == BUT
        assert classify_line_exit("goal_line", 0.52, 2.43, ATTAQUANT) == BUT

    def test_over_the_bar_is_out_not_a_goal(self):
        assert classify_line_exit("goal_line", 0.50, 2.60, DEFENSEUR) == CORNER
        assert classify_line_exit("goal_line", 0.50, 2.60, ATTAQUANT) == SORTIE_BUT

    def test_the_touchline_gives_a_throw_in(self):
        assert classify_line_exit("touch_line", 0.0, 0.0, DEFENSEUR) == TOUCHE
        assert classify_line_exit("touch_line", 1.0, 0.0, ATTAQUANT) == TOUCHE

    def test_a_real_parry_leaving_by_the_goal_line_is_a_corner_and_a_wide_shot_is_a_goal_kick(self):
        corners = [
            e for g in _GABARITS for m in range(1, 31) for e in _plan(g, "arret", m).events if e.type == CORNER
        ]
        assert corners, "aucune parade ne sort en corner sur 360 tirs"
        assert all(e.last_toucher == DEFENSEUR and e.x in (0.0, 1.0) for e in corners)
        assert {e.type for e in _plan("une_deux", "hors_cadre").events} == {SORTIE_BUT}
        assert _plan("une_deux", "hors_cadre").events[0].last_toucher == ATTAQUANT

    def test_a_post_rebound_can_stay_in_play_or_leave_by_the_touchline(self):
        kinds = {tuple(e.type for e in _plan(g, "poteau", m).events) for g in _GABARITS for m in range(1, 31)}
        assert (POTEAU,) in kinds  # le ballon revient en jeu
        assert (POTEAU, TOUCHE) in kinds  # ou sort par la touche


class TestClipCut:
    def test_a_clip_that_leaves_the_pitch_stops_one_second_after_the_line(self):
        cuts = 0
        for g in _GABARITS:
            for m in range(1, 21):
                plan = _plan(g, "arret", m)
                crossing = first_line_crossing(plan.trajectory)
                if crossing is None:
                    assert plan.end_tau == pytest.approx(plan.trajectory.duration)
                else:
                    assert plan.end_tau == pytest.approx(min(plan.trajectory.duration, crossing.tau + LINE_CUT_S))
                    cuts += 1
        assert cuts > 0

    def test_the_exit_event_is_dated_at_the_crossing_not_at_the_end(self):
        for g in _GABARITS:
            for m in range(1, 21):
                sequence = _sequence(g, "arret", m)
                plan = plan_ball_events(sequence, "arret", m, "bu", "gk")
                if len(plan.events) > 1:
                    assert sequence.duration < plan.events[1].t <= sequence.duration + plan.trajectory.duration
                    return
        pytest.fail("aucune sortie trouvée")


class TestDeterminism:
    def test_same_inputs_give_the_same_events_and_trajectory(self):
        for outcome in sorted(_NON_GOAL_MENU) + ["but"]:
            assert _plan("recuperation_haute", outcome, 17) == _plan("recuperation_haute", outcome, 17)

    def test_different_events_do_not_all_give_the_same_parry(self):
        directions = {_plan("une_deux", "arret", m).events[0].direction_deg for m in range(1, 21)}
        assert len(directions) > 10
