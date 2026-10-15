import math
import random
from collections import Counter

import pytest

from ligue1sim.animation.ball import (
    CROSS,
    DEFLECT,
    PASS_GROUND,
    PASS_LOB,
    SHOT,
    _real_distance_m,
    _resolve_physics_tag,
)
from ligue1sim.animation.templates import (
    ANCHOR_STATIC,
    BUILDERS,
    TEMPLATES,
    TemplateContext,
    _flight_distance_m,
    _urgency_factor,
    build_from_template,
    pick_template,
)
from ligue1sim.animation import templates as tpl
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import GRID_COLUMNS, GRID_ROWS, PENALTY_AREA_DEPTH_M, PITCH_LENGTH_M, PitchPoint, Zone, center_of
from ligue1sim.players import Player

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)


def _chi_square_homogeneity(counts_a: Counter, counts_b: Counter) -> float:
    """Statistique du chi² pour un test d'homogénéité entre deux
    échantillons catégoriels indépendants (table de contingence 2xK) --
    implémentation directe (pas de scipy dans ce projet), formule standard :
    somme sur chaque cellule de (observé - attendu)² / attendu, attendu =
    (total ligne * total colonne) / total général."""
    categories = set(counts_a) | set(counts_b)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    grand_total = total_a + total_b
    chi2 = 0.0
    for category in categories:
        col_total = counts_a.get(category, 0) + counts_b.get(category, 0)
        for observed, row_total in ((counts_a.get(category, 0), total_a), (counts_b.get(category, 0), total_b)):
            expected = row_total * col_total / grand_total
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected
    return chi2


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _lineup() -> Lineup:
    players = [
        _player("GK", 70.0, "gk", 1),
        _player("DC", 70.0, "cb0", 2),
        _player("DC", 70.0, "cb1", 3),
        _player("LB", 70.0, "lb", 4),
        _player("RB", 70.0, "rb", 5),
        _player("MDC", 70.0, "mdc", 6),
        _player("MC", 70.0, "mc0", 7),
        _player("MC", 70.0, "mc1", 8),
        _player("AG", 70.0, "ag", 9),
        _player("AD", 70.0, "ad", 10),
        _player("BU", 70.0, "bu", 11),
    ]
    return Lineup(club_name="Test FC", formation="4-3-3", players=players, rating=70.0)


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    return {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _goal_event(*, scorer: str = "bu", assist: str | None = "mc0", minute: int = 34, penalty: bool = False) -> GoalEvent:
    return GoalEvent(
        club_name="Test FC",
        scorer=scorer,
        assist=assist,
        minute=minute,
        penalty=penalty,
        zone=_SCORER_ZONE,
        assist_zone=_ASSIST_ZONE if assist else None,
    )


class TestTemplateRichness:
    """Critère minimal de richesse (23/09/2026, suite à l'audit visuel de
    scripts/preview_templates.py) : chaque gabarit doit avoir au moins 3
    keyframes ET une phase de préparation visible (un `tag` avant la
    conclusion) -- universellement, un gabarit à 2 points (départ/arrivée)
    ne raconte rien. Le nombre de RÔLES, en revanche, n'est exigé qu'aux 4
    gabarits identifiés comme pauvres par l'audit (`corner`, `penalty`,
    `but_gag`, `recuperation_haute`, tous enrichis à 3 rôles ce jour) : un
    "une_deux" ou un "coup_franc" n'ont légitimement besoin que de peu
    d'acteurs, leur imposer un 3e rôle serait artificiel plutôt que
    réaliste."""

    _FORMERLY_POOR_TEMPLATES = {"corner", "penalty", "but_gag", "recuperation_haute"}

    def _nb_keyframes(self, template) -> int:
        return len({frame.t_ratio for role in template.roles for frame in role.frames})

    def test_every_template_has_at_least_three_keyframes(self):
        for name, template in TEMPLATES.items():
            assert self._nb_keyframes(template) >= 3, f"{name} n'a que {self._nb_keyframes(template)} keyframes"

    def test_every_template_has_a_visible_preparation_phase_before_the_conclusion(self):
        # Un tag non vide avant le dernier point -- pas juste "départ" puis
        # "tir" sans rien entre les deux.
        for name, template in TEMPLATES.items():
            tags_before_last = [tag for t_ratio, tag in template.tags if t_ratio < 1.0]
            assert any(tags_before_last), f"{name} n'a aucune phase de préparation étiquetée avant t=1.0"

    def test_formerly_poor_templates_now_have_at_least_three_named_roles(self):
        for name in self._FORMERLY_POOR_TEMPLATES:
            assert len(TEMPLATES[name].roles) >= 3, f"{name} a encore moins de 3 rôles"


class TestRegistryIntegrity:
    def test_at_least_eight_templates_are_registered(self):
        assert len(TEMPLATES) >= 8

    def test_twelve_templates_are_registered(self):
        assert len(TEMPLATES) == 12

    def test_every_template_has_a_matching_builder(self):
        assert set(TEMPLATES) == set(BUILDERS)

    def test_every_template_key_matches_its_own_name(self):
        for key, template in TEMPLATES.items():
            assert key == template.name

    def test_every_template_has_a_positive_weight_and_duration(self):
        for template in TEMPLATES.values():
            assert template.weight > 0
            assert template.duration > 0


class TestEveryTemplateProducesAValidSequence:
    """"Chaque template produit une Sequence valide pour un event synthétique"
    -- la validité (t croissant, même ensemble de joueurs à chaque keyframe)
    est déjà vérifiée par Sequence.__post_init__ : un template buggé lève
    une exception ici plutôt que produire un objet invalide en silence."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_builds_a_sequence_with_assisted_goal(self, name):
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))

        assert sequence.keyframes
        assert sequence.duration == TEMPLATES[name].duration
        assert sequence.meta["template"] == name

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_builds_a_sequence_with_an_unassisted_goal(self, name):
        # Les gabarits qui utilisent un rôle "assist" doivent continuer à
        # fonctionner sans passeur réel (event.assist=None) -- le rôle est
        # simplement absent, pas une erreur (voir _resolve_roles).
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(assist=None), lineup, _start_positions(lineup))
        assert sequence.keyframes

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_produced_sequence_serializes_to_json(self, name):
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        payload = sequence.to_json()
        assert payload["keyframes"]


class TestFreeKickIsSpecialCased:
    """Phase 6, B7-a : le ballon d'un coup franc direct est posé (z = 0, immobile) à un point tiré de `event_ref` (18 à 30 m du but,
    0 à 12 m de l'axe, hors de la surface), la zone de l'événement n'est plus lue, et le tireur s'élance de 4 à 7 m."""

    _REFS = [f"goal:Club{i % 18}:p{i}:{i % 90 + 1}" for i in range(3000)]

    def _build(self, **event_kwargs):
        lineup = _lineup()
        event = _goal_event(assist=None, minute=event_kwargs.pop("minute", 70), **event_kwargs)
        return BUILDERS["coup_franc"](event, lineup, _start_positions(lineup), "but"), lineup

    @staticmethod
    def _spot_metres(ref):
        from ligue1sim.animation.templates import free_kick_spot

        spot = free_kick_spot(ref)
        return (1.0 - spot.x) * PITCH_LENGTH_M, (spot.y - 0.5) * 68.0  # profondeur depuis la ligne de but, décalage latéral signé

    def test_the_spot_is_in_the_direct_free_kick_zone_and_outside_the_penalty_area(self):
        for ref in self._REFS:
            depth_m, lateral_m = self._spot_metres(ref)
            distance_m = (depth_m**2 + lateral_m**2) ** 0.5
            assert 18.0 - 1e-9 <= distance_m <= 30.0 + 1e-9, (ref, distance_m)
            assert abs(lateral_m) <= 12.0 + 1e-9, (ref, lateral_m)
            assert depth_m >= 16.5 - 1e-9, (ref, depth_m)  # sinon ce serait un penalty

    def test_the_spot_covers_both_sides_and_the_whole_range(self):
        spots = [self._spot_metres(ref) for ref in self._REFS]
        left = sum(1 for _, lateral in spots if lateral < 0)
        assert 0.45 <= left / len(spots) <= 0.55
        distances = [(d**2 + lat**2) ** 0.5 for d, lat in spots]
        assert min(distances) < 18.5 and max(distances) > 29.5
        assert max(abs(lat) for _, lat in spots) > 11.5

    def test_ball_is_at_rest_on_the_ground_at_the_spot_until_the_strike(self):
        from ligue1sim.animation.templates import free_kick_spot

        for minute in (5, 23, 41, 67, 88):
            sequence, _ = self._build(minute=minute)
            ref = f"goal:Test FC:bu:{minute}"
            spot = free_kick_spot(ref)
            before_flight = sequence.keyframes[:-1]  # la dernière keyframe est la cible du vol
            for kf in before_flight:
                assert kf.ball.x == pytest.approx(spot.x) and kf.ball.y == pytest.approx(spot.y) and kf.ball.z == 0.0
            scorer_x, scorer_y = sequence.keyframes[-2].players[11]  # id du "bu", au moment de la frappe
            assert scorer_x == pytest.approx(spot.x) and scorer_y == pytest.approx(spot.y)

    def test_zone_of_the_event_is_ignored(self):
        lineup = _lineup()
        base = _goal_event(assist=None, minute=70)
        other = GoalEvent(**{**base.__dict__, "zone": Zone(col=3, row=1)})
        a = BUILDERS["coup_franc"](base, lineup, _start_positions(lineup), "but")
        b = BUILDERS["coup_franc"](other, lineup, _start_positions(lineup), "but")
        assert [kf.ball for kf in a.keyframes] == [kf.ball for kf in b.keyframes]
        assert [kf.players for kf in a.keyframes] == [kf.players for kf in b.keyframes]

    def test_the_run_up_is_4_to_7_m_with_the_validated_angles(self):
        import math

        from ligue1sim.animation.templates import free_kick_runup_start, free_kick_spot, strike_type_for

        angles = {"coup_franc_frappe": [], "coup_franc_enroule": []}
        for ref in self._REFS:
            spot, start = free_kick_spot(ref), free_kick_runup_start(ref)
            dx, dy = (spot.x - start.x) * PITCH_LENGTH_M, (spot.y - start.y) * 68.0  # de l'élan vers le ballon
            assert 4.0 - 1e-6 <= math.hypot(dx, dy) <= 7.0 + 1e-6, ref
            depth_m, lateral_m = self._spot_metres(ref)
            to_goal = (depth_m, -lateral_m)  # ballon -> centre du but, dans le repère (x vers le but, y)
            cos_angle = (dx * to_goal[0] + dy * to_goal[1]) / (math.hypot(dx, dy) * math.hypot(*to_goal))
            angles[strike_type_for("coup_franc", ref).name].append(math.degrees(math.acos(min(1.0, cos_angle))))
        assert max(angles["coup_franc_frappe"]) <= 10.0 + 1e-6
        assert 20.0 - 1e-6 <= min(angles["coup_franc_enroule"]) and max(angles["coup_franc_enroule"]) <= 40.0 + 1e-6

    def test_the_scorer_starts_at_the_run_up_point_and_runs_85_percent_by_80_percent_of_the_clip(self):
        from ligue1sim.animation.templates import free_kick_runup_start, free_kick_spot

        sequence, _ = self._build(minute=41)
        ref = "goal:Test FC:bu:41"
        start, spot = free_kick_runup_start(ref), free_kick_spot(ref)
        assert [round(kf.t, 6) for kf in sequence.keyframes[:4]] == [0.0, 1.25, 4.0, 5.0]
        assert sequence.keyframes[0].players[11] == pytest.approx((start.x, start.y))
        assert sequence.keyframes[1].players[11] == pytest.approx((start.x, start.y))  # attente
        run_x = sequence.keyframes[2].players[11][0]
        assert run_x == pytest.approx(start.x + 0.85 * (spot.x - start.x))

    def test_type_distribution_and_the_nlg_names(self):
        from collections import Counter

        from ligue1sim.animation.templates import STRIKE_TYPES, strike_type_for

        counts = Counter(strike_type_for("coup_franc", ref).name for ref in self._REFS)
        assert set(counts) == {"coup_franc_enroule", "coup_franc_frappe"}
        assert abs(100.0 * counts["coup_franc_enroule"] / len(self._REFS) - 100 * 55 / 85) <= 3.0, counts  # 64,7 % (indirect renormalisé)
        assert STRIKE_TYPES["coup_franc_enroule"].nlg_name == "shot_enroule_leger"
        assert STRIKE_TYPES["coup_franc_frappe"].nlg_name == "shot_tendu"
        assert all(t.nlg_name == t.name for n, t in STRIKE_TYPES.items() if not n.startswith("coup_franc"))  # le contrat du NLG est inchangé

    def test_curve_is_inward_for_75_percent_of_the_curled_free_kicks(self):
        from ligue1sim.animation.templates import STRIKE_TYPES, free_kick_spot, strike_spin_for

        curled = [r for r in self._REFS if strike_spin_for(STRIKE_TYPES["coup_franc_enroule"], r) != 0.0]
        inward = 0
        for ref in curled:
            spin = strike_spin_for(STRIKE_TYPES["coup_franc_enroule"], ref)
            ball_side = 1.0 if free_kick_spot(ref).y >= 0.5 else -1.0
            inward += (spin > 0) == (ball_side > 0)  # spin > 0 gonfle vers y croissant (ball._perp_unit) : rentrant = du côté du ballon
        assert abs(inward / len(curled) - 0.75) <= 0.03


class TestPenaltyIsSpecialCased:
    """Phase 6, B6-a : le ballon est posé au point de penalty réglementaire (11 m de la ligne de but, y = 0), la zone de
    l'événement n'est plus lue, et le tireur s'élance depuis un point situé à 6-9 m, sous +-10 degrés."""

    _SPOT_X = 1.0 - 11.0 / PITCH_LENGTH_M

    def _build(self, **event_kwargs):
        lineup = _lineup()
        event = _goal_event(assist=None, penalty=True, minute=event_kwargs.pop("minute", 70), **event_kwargs)
        return BUILDERS["penalty"](event, lineup, _start_positions(lineup), "but"), lineup

    def test_penalty_template_places_the_scorer_at_the_penalty_spot(self):
        sequence, _ = self._build()
        scorer_x, scorer_y = sequence.keyframes[-2].players[11]  # id du "bu", au moment de la frappe
        assert scorer_x == pytest.approx(self._SPOT_X)
        assert scorer_y == pytest.approx(0.5)

    def test_ball_is_at_rest_on_the_spot_until_the_strike(self):
        for minute in (5, 23, 41, 67, 88):
            sequence, _ = self._build(minute=minute)
            before_flight = sequence.keyframes[:-1]  # la dernière keyframe est la cible du vol
            for kf in before_flight:
                assert kf.ball.x == pytest.approx(self._SPOT_X) and kf.ball.y == pytest.approx(0.5) and kf.ball.z == 0.0
            # 11 m de la ligne de but, a 0,1 m pres, y = 0 a 0,1 m pres.
            assert abs((1.0 - before_flight[-1].ball.x) * PITCH_LENGTH_M - 11.0) <= 0.1
            assert abs((before_flight[-1].ball.y - 0.5) * 68.0) <= 0.1

    def test_zone_of_the_event_is_ignored(self):
        lineup = _lineup()
        base = _goal_event(assist=None, penalty=True, minute=70)
        other = GoalEvent(**{**base.__dict__, "zone": Zone(col=3, row=1)})
        a = BUILDERS["penalty"](base, lineup, _start_positions(lineup), "but")
        b = BUILDERS["penalty"](other, lineup, _start_positions(lineup), "but")
        assert [kf.ball for kf in a.keyframes] == [kf.ball for kf in b.keyframes]
        assert [kf.players for kf in a.keyframes] == [kf.players for kf in b.keyframes]

    def test_runup_is_6_to_9_m_long_within_10_degrees_and_deterministic(self):
        lengths, angles = [], []
        for minute in range(1, 91):
            for scorer in ("bu", "ag", "ad"):
                sequence, _ = self._build(minute=minute, scorer=scorer)
                lineup = _lineup()
                scorer_id = next(p.id for p in lineup.players if p.name == scorer)
                start_x, start_y = sequence.keyframes[0].players[scorer_id]
                dx_m, dy_m = (self._SPOT_X - start_x) * PITCH_LENGTH_M, (0.5 - start_y) * 68.0
                lengths.append(math.hypot(dx_m, dy_m))
                angles.append(math.degrees(math.atan2(dy_m, dx_m)))
        assert all(6.0 - 1e-6 <= v <= 9.0 + 1e-6 for v in lengths) and max(lengths) - min(lengths) > 2.0
        assert all(-10.0 - 1e-6 <= a <= 10.0 + 1e-6 for a in angles) and max(angles) - min(angles) > 10.0
        again, _ = self._build(minute=23, scorer="ag")
        first, _ = self._build(minute=23, scorer="ag")
        assert [kf.players for kf in again.keyframes] == [kf.players for kf in first.keyframes]

    def test_supports_start_at_the_penalty_area_edge_on_opposite_sides_and_deterministic(self):
        # Chantier 1, 1f (15/10/2026) : avant cette migration, support1/support2 partaient de leur position de formation brute,
        # mesurée à 70 m en médiane de la surface sur le pipeline réel -- sans lien avec l'événement. Désormais au bord de la
        # surface (ligne des 16,5 m), décalés de 6 à 15 m de l'axe, toujours de part et d'autre (jamais le même côté).
        edge_x = 1.0 - PENALTY_AREA_DEPTH_M / PITCH_LENGTH_M
        sides, laterals_m = [], []
        for minute in range(1, 91):
            sequence, lineup = self._build(minute=minute)
            support1_id = next(p.id for p in lineup.players if p.name == "ad")  # premier nom alphabétique hors bu/gardien
            support2_id = next(p.id for p in lineup.players if p.name == "ag")  # second
            x1, y1 = sequence.keyframes[0].players[support1_id]
            x2, y2 = sequence.keyframes[0].players[support2_id]
            assert x1 == pytest.approx(edge_x) and x2 == pytest.approx(edge_x)
            lateral1_m, lateral2_m = (y1 - 0.5) * 68.0, (y2 - 0.5) * 68.0
            assert 6.0 - 1e-6 <= abs(lateral1_m) <= 15.0 + 1e-6
            assert 6.0 - 1e-6 <= abs(lateral2_m) <= 15.0 + 1e-6
            assert (lateral1_m > 0) != (lateral2_m > 0)  # jamais le même côté
            sides.append(lateral1_m > 0)
            laterals_m.append(abs(lateral1_m))
        assert any(sides) and not all(sides)  # le côté varie d'un événement à l'autre
        assert max(laterals_m) - min(laterals_m) > 2.0  # l'écart latéral varie aussi
        again, _ = self._build(minute=23)
        first, _ = self._build(minute=23)
        assert [kf.players for kf in again.keyframes] == [kf.players for kf in first.keyframes]


class TestBuildFromTemplateIsPure:
    def test_same_inputs_produce_an_identical_sequence(self):
        lineup = _lineup()
        start = _start_positions(lineup)
        event = _goal_event()

        first = build_from_template(TEMPLATES["contre_attaque"], event, lineup, start)
        second = build_from_template(TEMPLATES["contre_attaque"], event, lineup, start)

        assert first.to_json() == second.to_json()


class TestScorerReachesTheEventZone:
    def test_the_scorers_final_position_matches_the_event_zone_centre(self):
        lineup = _lineup()
        event = _goal_event()
        sequence = build_from_template(TEMPLATES["debordement_centre_tete"], event, lineup, _start_positions(lineup))

        expected = center_of(event.zone)
        last = sequence.keyframes[-1]
        scorer_x, scorer_y = last.players[11]  # "bu"
        assert scorer_x == pytest.approx(expected.x)
        assert scorer_y == pytest.approx(expected.y)


class TestPickTemplateHardConstraints:
    def _context(self, **overrides) -> TemplateContext:
        base = dict(
            minute=50, goal_diff_before=0, scorer_poste="BU", assist_poste="MC", penalty=False,
            competition_type="league",
        )
        base.update(overrides)
        return TemplateContext(**base)

    def test_a_penalty_context_always_picks_the_penalty_template(self):
        context = self._context(penalty=True, assist_poste=None)
        picks = {pick_template(context) for _ in range(30)}
        assert picks == {"penalty"}

    def test_a_non_penalty_context_never_picks_the_penalty_template(self):
        context = self._context(penalty=False)
        picks = {pick_template(context) for _ in range(60)}
        assert "penalty" not in picks


class TestPickTemplateContextScoring:
    def test_wide_scorer_with_no_assist_favors_the_individual_run_template(self):
        context = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="AG", assist_poste=None, penalty=False,
            competition_type="league",
        )
        percee = TEMPLATES["percee_individuelle"]
        recuperation = TEMPLATES["coup_franc"]
        assert percee.weight * percee.context_score(context) > recuperation.weight * recuperation.context_score(context)

    def test_aerial_scorer_with_wide_assist_favors_the_header_from_a_cross_template(self):
        favorable = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="DC", assist_poste="AG", penalty=False,
            competition_type="league",
        )
        neutral = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="MC", assist_poste="MC", penalty=False,
            competition_type="league",
        )
        debordement = TEMPLATES["debordement_centre_tete"]
        assert debordement.context_score(favorable) > debordement.context_score(neutral)

    def test_picking_many_times_over_varied_contexts_yields_more_than_one_template(self):
        # La diversité doit venir des gabarits eux-mêmes (voir objectif du
        # module), pas d'un seul gabarit qui écraserait tous les autres.
        contexts = [
            TemplateContext(
                minute=m, goal_diff_before=0, scorer_poste=poste, assist_poste=assist, penalty=False,
                competition_type="league",
            )
            for m in (5, 30, 60, 85)
            for poste in ("BU", "AG", "AD", "DC", "MOC")
            for assist in (None, "MC", "AG", "MDC")
        ]
        picks = {pick_template(context) for context in contexts}
        assert len(picks) > 3


class TestPickTemplateReactsToScore:
    """Vérifie que `TemplateContext.goal_diff_before` a un effet RÉEL sur la
    distribution des gabarits -- avant le 23/09/2026, ce champ existait mais
    n'était lu par AUCUNE fonction `context_score`, donc `pick_template`
    "pondérait à vide" quel que soit l'écart au score transmis."""

    _URGENT_TEMPLATES = {"contre_attaque", "recuperation_haute", "percee_individuelle"}

    def _bucket(self, name: str) -> str:
        if name == "construction_placee":
            return "construction_placee"
        return name if name in self._URGENT_TEMPLATES else "autres"

    def _context(self, goal_diff_before: int) -> TemplateContext:
        return TemplateContext(
            minute=60, goal_diff_before=goal_diff_before, scorer_poste="BU", assist_poste="MC",
            penalty=False, competition_type="league",
        )

    def test_urgency_factor_is_higher_when_trailing_and_lower_when_leading_comfortably(self):
        assert _urgency_factor(-2) > _urgency_factor(-1) > _urgency_factor(0) > _urgency_factor(1) > _urgency_factor(2)

    def test_construction_placee_is_favored_over_contre_attaque_when_comfortably_ahead(self):
        context = self._context(goal_diff_before=3)
        construction = TEMPLATES["construction_placee"]
        contre_attaque = TEMPLATES["contre_attaque"]
        assert (
            construction.weight * construction.context_score(context)
            > contre_attaque.weight * contre_attaque.context_score(context)
        )

    def test_contre_attaque_is_favored_over_construction_placee_when_level(self):
        context = self._context(goal_diff_before=0)
        construction = TEMPLATES["construction_placee"]
        contre_attaque = TEMPLATES["contre_attaque"]
        assert (
            contre_attaque.weight * contre_attaque.context_score(context)
            > construction.weight * construction.context_score(context)
        )

    def test_template_distribution_differs_significantly_between_a_level_and_a_blowout_score(self):
        """Test statistique (chi² d'homogénéité, sans dépendance à scipy --
        non installé dans ce projet, voir valeur critique documentée) sur
        500 tirages par contexte : la distribution des gabarits (regroupés
        en 4 catégories pour garantir des effectifs attendus suffisants,
        voir `_bucket`) doit différer significativement entre un but à 0-0
        (goal_diff_before=0) et un but à 3-0 (goal_diff_before=3), même
        minute et mêmes postes."""
        context_level = self._context(goal_diff_before=0)
        context_blowout = self._context(goal_diff_before=3)

        counts_level = Counter(self._bucket(pick_template(context_level, rng=random.Random(seed))) for seed in range(500))
        counts_blowout = Counter(
            self._bucket(pick_template(context_blowout, rng=random.Random(seed + 1_000_000))) for seed in range(500)
        )

        chi2 = _chi_square_homogeneity(counts_level, counts_blowout)
        # Table du chi², df=3 (4 catégories - 1), alpha=1% -> 11.345 (valeur
        # standard, aucune dépendance à scipy nécessaire pour ce seuil fixe).
        assert chi2 > 11.345, f"chi2={chi2:.2f} ne dépasse pas le seuil de significativité (df=3, alpha=1%)"

        # Le sens de l'effet compte autant que son existence : une équipe
        # menée à 0-0 presse/contre plus, une équipe qui mène 3-0 construit.
        assert counts_level["recuperation_haute"] / 500 > counts_blowout["recuperation_haute"] / 500
        assert counts_blowout["construction_placee"] / 500 > counts_level["construction_placee"] / 500


class TestSegmentSpeedHeadroom:
    """"Point B" du brief du 23/09/2026 : un segment de gabarit qui exige
    RÉELLEMENT plus que v_max en moyenne ne peut pas être rattrapé par le
    repli linéaire de motion.py (voir sa docstring de module, "Limite connue
    et non corrigée" -- saut de position/vitesse à la transition). Aucun des
    12 gabarits actuels n'atteint ce seuil (`une_deux` est le plus proche,
    ~76% de v_max) -- ce test fige cette marge pour qu'une future édition
    d'un gabarit (nouveaux RoleFrame plus exigeants) ne la fasse pas
    silencieusement basculer en territoire "impossible"."""

    def _worst_ratio(self, name: str, lineup: Lineup) -> float:
        from ligue1sim.animation.motion import _real_distance_m, max_speed_normalized

        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        worst = 0.0
        for player_id, entry in sequence.roster.items():
            if entry.role is None:
                continue
            v_max = max_speed_normalized(entry.poste)
            for kf_a, kf_b in zip(sequence.keyframes, sequence.keyframes[1:]):
                duration = kf_b.t - kf_a.t
                if duration <= 0:
                    continue
                dist_m = _real_distance_m(kf_a.players[player_id], kf_b.players[player_id])
                required_avg_speed = (dist_m / 105.0) / duration
                worst = max(worst, required_avg_speed / v_max)
        return worst

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_no_template_ever_demands_more_than_v_max(self, name):
        ratio = self._worst_ratio(name, _lineup())
        assert ratio < 1.0, f"{name} exige {ratio:.2f}x v_max sur son segment le plus dur -- devient \"impossible\""

    def test_debordement_centre_tete_is_the_closest_to_the_critical_threshold(self):
        # Constat du 23/09/2026 (voir docs/simulation_physique_archi.md,
        # "Point B") -- "une_deux" était le pire jusqu'à sa migration en
        # Chantier 1, 1d (15/10/2026, géométrie de rôle sur scorer/assist) :
        # son pire ratio a baissé sous celui de "recuperation_haute", qui
        # n'était pas encore migré (famille C, sous-étape 1e-1) et prenait
        # donc sa place. Chantier 1, 1e-1 (15/10/2026) : "recuperation_haute"
        # puis "but_gag" migrés, leur pire ratio baisse (0,45 et 0,53 ->
        # inférieur) -- "debordement_centre_tete" (migré en 1c) prend leur
        # place, exactement au plafond de conception (`_RUN_RATIO_MAX` = 0,5,
        # quasi à égalité avec "une_deux" lui-même au plafond ; départagé par
        # l'ordre d'itération de `BUILDERS`, pas par un écart réel).
        # Re-vérifié, pas corrigé en silence -- si ce n'est plus vrai après
        # 1f, la table a de nouveau changé et mérite d'être revérifiée.
        lineup = _lineup()
        ratios = {name: self._worst_ratio(name, lineup) for name in BUILDERS}
        assert max(ratios, key=ratios.get) == "debordement_centre_tete"


class TestContreAttaqueSupport1Carries:
    """Fix du 23/09/2026 (brief "contre_attaque carrier movement") :
    `support1` récupère le ballon à t=0, le conduit vers l'avant (ANCHOR_SCORER,
    plus ANCHOR_STATIC), puis le relâche à `assist` au ratio prévu -- voir le
    commentaire sur le rôle dans templates.py pour le raisonnement complet.

    Fix "suite 2" (même jour, brief "carrier continuation") : support1 ne
    s'arrête plus net après la passe (0.3 -> 0.3, figé) mais continue
    d'avancer en décélérant jusqu'à la fin (0.3 -> 0.4) -- voir
    `test_contre_attaque_support1_continues_after_the_relay`."""

    def _sequence(self):
        lineup = _lineup()
        return BUILDERS["contre_attaque"](_goal_event(), lineup, _start_positions(lineup))

    def test_contre_attaque_support1_moves(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        first = sequence.keyframes[0].players[support_id]
        last = sequence.keyframes[-1].players[support_id]
        delta_m = _real_distance_m(first, last)
        assert delta_m > 0.05 * PITCH_LENGTH_M, f"delta={delta_m:.2f}m, attendu > {0.05 * PITCH_LENGTH_M:.2f}m"

    def test_contre_attaque_support1_continues_after_the_relay(self):
        # Brief "carrier continuation" du 23/09/2026 : un arrêt net juste
        # après la passe (t_ratio=0.4) lisait comme "il a débranché" -- il
        # doit continuer d'avancer, même modestement, jusqu'à la fin.
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        at_relay = next(kf.players[support_id] for kf in sequence.keyframes if kf.t == pytest.approx(0.4 * sequence.duration))
        at_end = sequence.keyframes[-1].players[support_id]
        delta_m = _real_distance_m(at_relay, at_end)
        assert delta_m > 1.5, f"delta post-relais={delta_m:.2f}m, attendu > 1.5m (pas un arrêt net)"

    def test_contre_attaque_ball_follows_carrier(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        carried_keyframes = [kf for kf in sequence.keyframes if kf.ball.owner_id == support_id]
        assert carried_keyframes, "aucun keyframe où support1 porte le ballon -- ball_owner mal câblé"
        for kf in carried_keyframes:
            dist_m = _real_distance_m((kf.ball.x, kf.ball.y), kf.players[support_id])
            assert dist_m < 2.0, f"t={kf.t}: ballon à {dist_m:.2f}m de support1 (tolérance 2m)"

    def test_contre_attaque_ball_transfers_to_assist(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        assist_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "assist")
        transfer_ratio = next(ratio for ratio, role in TEMPLATES["contre_attaque"].ball_owner if role == "assist")
        transfer_kf = next(kf for kf in sequence.keyframes if kf.t == pytest.approx(transfer_ratio * sequence.duration))

        assert transfer_kf.ball.owner_id == assist_id
        dist_m = _real_distance_m((transfer_kf.ball.x, transfer_kf.ball.y), transfer_kf.players[assist_id])
        assert dist_m < 2.0, f"transfert : ballon à {dist_m:.2f}m de assist (tolérance 2m)"


class TestNoDeadProgressOnStaticAnchor:
    """Tâche 2 du brief du 23/09/2026 : un ANCHOR_STATIC fige la cible = le
    départ (voir `_anchor_point`) -- tout `RoleFrame.progress` non nul à
    côté est donc du code mort, exactement le bug qui rendait `support1`
    immobile dans `contre_attaque` (voir `TestContreAttaqueSupport1Carries`).

    Exclusion au niveau du RÔLE, PAS du gabarit (voir brief du 23/09/2026,
    "suite 2" : un frozenset de noms de gabarits sautait le gabarit ENTIER,
    masquant tout futur rôle mort ajouté ailleurs dans ce même gabarit --
    angle mort démontré par modification temporaire + revert, voir
    docs/simulation_physique_archi.md pour la preuve). Les 8 cas trouvés le
    23/09/2026 ont tous été corrigés le jour même : cette liste est donc
    vide -- elle ne le reste que si un futur cas est délibérément laissé
    statique ET documenté comme tel, jamais par défaut."""

    _KNOWN_DEAD_PROGRESS_OFFENDERS: frozenset[tuple[str, str]] = frozenset()
    _EPSILON = 0.01

    def test_no_dead_progress_on_static_anchor(self):
        violations = []
        for name, template in TEMPLATES.items():
            for role in template.roles:
                if (name, role.name) in self._KNOWN_DEAD_PROGRESS_OFFENDERS:
                    continue
                if role.end_anchor != ANCHOR_STATIC:
                    continue
                for frame in role.frames:
                    if frame.progress is not None and frame.progress > self._EPSILON:
                        violations.append(f"{name}.{role.name} @ t_ratio={frame.t_ratio} progress={frame.progress}")

        assert not violations, "progress non nul sur ANCHOR_STATIC (code mort) : " + "; ".join(violations)

    def test_the_known_offenders_list_is_not_stale(self):
        # Contre-vérification : si un (gabarit, rôle) de la liste ne viole
        # plus rien (corrigé sans mettre à jour cette liste), on veut le
        # savoir -- sinon la liste se fige et masque un futur vrai fix.
        # Vide aujourd'hui (voir docstring de classe) -- cette boucle ne
        # s'exécute donc sur rien, elle redevient utile dès qu'une entrée y
        # est réintroduite.
        for name, role_name in self._KNOWN_DEAD_PROGRESS_OFFENDERS:
            template = TEMPLATES[name]
            role = next(r for r in template.roles if r.name == role_name)
            found = (
                role.end_anchor == ANCHOR_STATIC
                and any(f.progress is not None and f.progress > self._EPSILON for f in role.frames)
            )
            assert found, f"{name}.{role_name} est listé comme dette connue mais ne viole plus rien -- retire-le"


class TestNoRoleReliesOnReactionDelay:
    """Vérification demandée après le fix de `motion._reacts_immediately`
    (23/09/2026, "reaction delay only for background players") : preuve
    MÉCANIQUE, au niveau des DONNÉES de `templates.py` (pas du comportement
    de `motion.py` -- aucun import de `motion` ni d'`interpolate` ici), qu'
    aucun rôle scripté ne dépendait du délai de réaction supprimé pour
    "arriver à l'heure".

    Deux invariants structurels :
    1. Un rôle qui possède le ballon dès `t_ratio=0.0` (`Template.ball_owner`)
       doit être à sa position de formation à ce même instant -- son premier
       `RoleFrame` doit avoir `progress=0.0` -- SAUF si `Template.
       starts_at_restart` (coup franc, penalty : la séquence démarre une
       fois le tireur déjà en position, pas à sa position de formation, voir
       le champ sur `Template`). Un progress non nul à t=0 pour un porteur
       immédiat, sur un gabarit qui N'EST PAS un restart, serait le signe
       qu'on a compensé un retard (l'ancien délai de réaction) en
       pré-décalant sa position -- exactement l'anti-pattern signalé dans le
       brief. Version "suite 6" (23/09/2026) : remplace la liste
       d'exclusion `(gabarit, rôle)` d'origine par ce champ STRUCTUREL --
       une liste de noms aurait avalé en silence un futur gabarit légitime
       (ex. une contre-attaque éclair où le buteur est déjà lancé), alors
       que `starts_at_restart` force à qualifier explicitement le gabarit
       lui-même, pas à whitelister un cas après coup.
    2. La séquence de `progress` déclarée pour CHAQUE rôle doit être
       non-décroissante (jamais un saut en arrière) -- un rôle scripté ne
       doit jamais "reculer" pour ensuite rattraper une position, ce qui
       trahirait une dépendance à un mécanisme externe de correction de
       timing plutôt qu'une trajectoire cohérente en elle-même. Aucune
       exception ici, gabarit restart ou non.

    `coup_franc`/`penalty` portent `starts_at_restart=True`. `corner` --
    aussi un restart -- n'a PAS besoin du flag : son porteur à t=0
    (`assist`) a bien `progress=0.0` (le gabarit place déjà le tireur de
    corner à son point de départ réel), donc il ne viole rien de toute
    façon ; lui ajouter le flag n'aurait aucun effet observable."""

    _EPSILON = 0.01

    def test_no_role_relies_on_reaction_delay(self):
        violations = []
        for name, template in TEMPLATES.items():
            ball_owner_by_ratio = dict(template.ball_owner)
            for role in template.roles:
                frames_sorted = sorted(role.frames, key=lambda f: f.t_ratio)

                # Invariant 1 : porteur dès t=0 -> position de formation à
                # t=0, sauf gabarit "restart" (coup franc, penalty).
                if not template.starts_at_restart and ball_owner_by_ratio.get(0.0) == role.name:
                    first_progress = frames_sorted[0].progress
                    if first_progress is not None and first_progress > self._EPSILON:
                        violations.append(
                            f"{name}.{role.name} porte le ballon à t=0 mais progress={first_progress} (attendu 0.0)"
                        )

                # Invariant 2 : progress jamais décroissant (pas de saut en
                # arrière) -- s'applique À TOUS les gabarits, restart ou non.
                progresses = [f.progress for f in frames_sorted if f.progress is not None]
                for a, b in zip(progresses, progresses[1:]):
                    if b < a - self._EPSILON:
                        violations.append(f"{name}.{role.name} : progress décroît {progresses} -- saut en arrière")
                        break

        assert not violations, "rôle scripté potentiellement dépendant d'un délai externe : " + "; ".join(violations)


class TestTemplateStructureUnchangedByPhysicsTags:
    """Garde-fou demandé avant la Modification B du brief "tag-driven
    trajectory" (23/09/2026, phase 3.2) : l'ajout des `physics_tag`
    explicites doit être une modification CHIRURGICALE -- rien d'autre
    (nombre de keyframes, positions, tags narratifs, `ball_owner`,
    `ball_height`) ne doit bouger sur les 12 gabarits.

    Empreinte SHA256 du JSON de chaque gabarit, `physics_tag` neutralisé à
    `None` avant hachage (c'est justement le seul champ qu'on attend voir
    changer) -- capturée AVANT d'appliquer la Modification B, sur la
    fixture standard de ce fichier (`_lineup`/`_goal_event`/
    `_start_positions`). Si ce test échoue, quelque chose d'AUTRE que les
    `physics_tag` a changé dans un gabarit -- à traiter comme une
    régression, pas comme un test à mettre à jour à la légère.

    Exception délibérée (brief "ball_owner=None debt", 23/09/2026, Tâche 2) :
    `corner` et `recuperation_haute` ont une empreinte mise à jour -- leur
    ballon change RÉELLEMENT de position (x/y) sur la keyframe "disputée"
    (`Template.ball_position`), ce n'est plus le repli figé sur la dernière
    position connue. Recalculée et vérifiée manuellement à cette occasion,
    pas une régression.

    Deuxième exception délibérée (brief "real Magnus effect", 23/09/2026,
    Tâche 3) : `decalage_enroulee` a une empreinte mise à jour -- sa keyframe
    de tir porte désormais un `spin` non nul (`build_decalage_enroulee`,
    `templates.py`), remplaçant le `spin=0.0` par défaut. Recalculée et
    vérifiée manuellement, pas une régression.

    Troisième exception délibérée (Phase 6, B5, 08/10/2026) : `decalage_enroulee` a de nouveau une empreinte mise à jour --
    le spin n'est plus posé sur la conduite `shot` (fixture sans issue, donc sans vol : `spin = 0.0` partout) mais sur le seul
    vol, selon le type de frappe (`STRIKE_TYPES`). Recalculée et vérifiée : seul le spin de la keyframe de tir a changé.

    Quatrième exception délibérée (Phase 6, B6-a, 08/10/2026) : `penalty` a une empreinte mise à jour -- le ballon est posé au
    point de penalty réglementaire (`ball_position`) au lieu de suivre le tireur, et le tireur part d'un point d'élan (6 à 9 m)
    au lieu de sa position de formation avancée de 85 %. Recalculée et vérifiée manuellement, pas une régression.

    Cinquième exception délibérée (Phase 6, B7-a, 14/10/2026) : `coup_franc` a une empreinte mise à jour -- même mécanisme que le
    penalty : le ballon est posé au point du coup franc (`ball_position`, tiré de `event_ref`) au lieu de suivre le tireur, et le
    tireur part d'un point d'élan (4 à 7 m) au lieu de sa position de formation avancée de 80 %, avec les keyframes 0.25 (attente)
    et 0.8 (élan). Preuve de cause unique : avec l'ancien gabarit remis, le code redonne exactement l'ancienne empreinte
    (65652dc1...).

    Sixième exception délibérée (Phase 6, B8-a, 14/10/2026) : sept gabarits ont une empreinte mise à jour (`but_gag`, `construction_placee`,
    `contre_attaque`, `decalage_enroulee`, `profondeur_1v1`, `recuperation_haute`, `une_deux`) -- chaque réception au sol reçoit un segment de
    contrôle (keyframes insérés, ballon décalé du joueur, tags `controle_<geste>`). Preuve de cause unique : avec `Template.ground_control`
    à `False` sur les 12 gabarits, le code redonne exactement les 12 anciennes empreintes. `corner` et `debordement_centre_tete` (réception aérienne,
    B8-c), `coup_franc`, `penalty` et `percee_individuelle` (aucune réception) gardent la leur.

    Septième exception délibérée (Phase 6, B8-c1, 14/10/2026) : `corner` et `debordement_centre_tete` ont une empreinte mise à jour -- leur dernier
    keyframe est un contact AÉRIEN (`Template.aerial_contact`) : sa hauteur `ball.z` (1,6 à 2,2 m pour une tête, 0,4 à 1,0 m pour une volée) remplace le
    `ball_height` de 0,3 m ; `corner` est en plus retimé (durée 7,0 s inchangée, keyframe « ballon disputé » supprimé, centre de 2,1 s qui part à
    4,9 s et arrive au contact à 7,0 s, nouveau keyframe à t_ratio 0,7). Preuve de cause unique : avec les anciennes définitions des deux gabarits (durée, rôles, tags, `ball_owner`, `ball_height`, `ball_position` et
    `physics_tags` d'avant) et `aerial_contact=False`, le code redonne exactement les anciennes empreintes (`corner` cfc64237...,
    `debordement_centre_tete` 06543fdd...) ; avec le nouveau gabarit mais `aerial_contact=False`, `corner` donne une troisième empreinte (3bce8e74...),
    et l'ancien gabarit avec `aerial_contact=True` une quatrième (d9d7cffc...) : la durée et la hauteur du contact y contribuent chacune. Pour
    `debordement_centre_tete`, le seul changement de `physics_tags` (`shot` -> `cross`) ne change pas l'empreinte (le champ est neutralisé) : seule la
    hauteur du contact la modifie.

    Huitième exception délibérée (Chantier 1, 1c, 15/10/2026) : `percee_individuelle`, `debordement_centre_tete`, `profondeur_1v1` et
    `decalage_enroulee` ont une empreinte mise à jour -- chacun reçoit une géométrie de rôle (`Role.geometry`) sur son (ou ses) rôle(s)
    scorer/assist : la CIBLE d'arrivée ne change pas (toujours `event.zone`/`event.assist_zone`, comme avant), seul le DÉPART devient
    réaliste (dérivé de la position de formation, plafonné par la course réalisable sur la durée du gabarit -- voir `geometry_start`).
    `percee_individuelle` et `profondeur_1v1` portent en plus une durée allongée (7,0 -> 8,0 s et 6,0 -> 7,0 s). Preuve de cause unique :
    avec les anciennes durées et `geometry=None` sur tous les rôles de ces 4 gabarits, le code redonne exactement les 4 anciennes
    empreintes ci-dessus.

    Neuvième exception délibérée (Chantier 1, 1d, 15/10/2026) : `une_deux`, `contre_attaque` et `construction_placee` ont une empreinte
    mise à jour -- même mécanisme que la huitième exception (cible inchangée, seul le départ devient réaliste), avec deux nouveautés :
    `support1` de `contre_attaque`/`construction_placee` reçoit en plus une géométrie et devient un rôle TACTIQUE (`_resolve_roles` le
    tire désormais par poste attendu et proximité, au lieu de l'ordre alphabétique -- voir `TestTacticalSupports`), ce qui peut changer
    QUEL joueur tient ce rôle, pas seulement sa position. `une_deux` porte en plus une durée allongée (4,0 -> 5,0 s) ; `contre_attaque`
    aussi (8,0 -> 9,0 s) ; `construction_placee` est inchangée (14,0 s). Preuve de cause unique : avec les anciennes durées et
    `geometry=None` sur tous les rôles de ces 3 gabarits, le code redonne exactement les 3 anciennes empreintes ci-dessus.

    Dixième exception délibérée (Chantier 1, 1e-1, 15/10/2026) : `but_gag` et `recuperation_haute` ont une empreinte mise à jour --
    même mécanisme que la huitième/neuvième exception (cible inchangée, seul le départ devient réaliste), avec une nouveauté : les
    DEUX rôles génériques (`support1` ET `support2`) deviennent tactiques dans le même gabarit, PREMIER cas du chantier à puiser
    deux rôles dans le même pool de postes (voir `TestTacticalSupports`). `recuperation_haute` porte en plus une durée allongée
    (5,0 -> 6,0 s) ; `but_gag` est inchangée (5,0 s). Preuve de cause unique : avec l'ancienne durée et `geometry=None` sur tous les
    rôles de ces 2 gabarits, le code redonne exactement les 2 anciennes empreintes ci-dessus.

    Onzième exception délibérée (Chantier 1, 1f, 15/10/2026) : `corner` a une empreinte mise à jour -- cibles inchangées (assist ->
    zone d'assist = poteau de corner, scorer -> zone de tir), seul le départ devient réaliste, avec deux nouveautés par rapport aux
    gabarits précédents : `assist` et `scorer` portent chacun un `run_cap_m` explicite (8 et 15 m, plafonds proposés en conception)
    en plus de leur cible habituelle ; `support1` (l'appel au premier poteau) devient tactique via `GEOM_BEHIND_ZONE` (cible recalée
    à 6 m de la zone de tir vers le poteau de corner, pas `GEOM_ZONE`/`GEOM_ASSIST_ZONE` -- première utilisation réelle de cette
    cible dans un gabarit du chantier). Preuve de cause unique : avec `geometry=None` sur les trois rôles, le code redonne
    exactement l'ancienne empreinte ci-dessus.

    Douzième exception délibérée (Chantier 1, 1f, 15/10/2026) : `penalty` a une empreinte mise à jour -- mécanisme différent des
    autres exceptions (pas de `Role.geometry`, incompatible avec `ANCHOR_LATERAL_SHIFT` déjà porté par support1/support2) : leur
    position de départ est remplacée dans `build_penalty`, comme celle du tireur (`penalty_runup_start`) l'est déjà, par un point
    au bord de la surface (`penalty_support_position`), mesuré à 70 m en médiane de la surface avant cette migration -- sans lien
    avec l'événement. Preuve de cause unique : avec l'ancien `build_penalty` (positions de départ non remplacées pour support1/
    support2), le code redonne exactement l'ancienne empreinte ci-dessus.

    Treizième exception délibérée (Chantier 1, 1e-2, 15/10/2026) : `recuperation_haute` a une empreinte mise à jour -- la position
    fixe du ballon disputé à t_ratio=0,3 (posée le 23/09/2026 juste pour éviter un ballon immobile, jamais une vraie position)
    devient le MILIEU des deux presseurs (`support1`/`support2`) à ce même t_ratio (`Template.dynamic_ball_position`, nouveau
    champ, vide par défaut sur les 11 autres gabarits). Preuve de cause unique : avec `dynamic_ball_position=()` et l'ancien
    `ball_position=((0.3, (0.6, 0.5)),)` remis, le code redonne exactement l'ancienne empreinte ci-dessus."""

    _EXPECTED_STRUCTURE_HASH = {
        "but_gag": "c982c7c9f8905b2d948ecbc21c2009643fb30661471acfd64352f604a8801ecf",
        "construction_placee": "4e9db51913eab6c3181ad30a473c9d583c634bc410db8807eed2fcb9ebc7f452",
        "contre_attaque": "76bacb1b0545a25c661dc61635984d2cb042ed0ee29cc928881da8eb7b810a39",
        "corner": "81b011f67a82794ee034a3ec5cecd123bba67d90957bc0aa0bb69d67cb963917",
        "coup_franc": "ff70b15275eb85d5baefeb5acea5f4a81e25319618a6e25cc978600aca72f959",
        "debordement_centre_tete": "9a5039d4b4d9112586b7676f475bc7e7cec54ce265278006814c3dae681a95f8",
        "decalage_enroulee": "f2f8eae8553986557f62b7e938429e5ac182fef09c21f4d87fb2c0f158ff1090",
        "penalty": "f2e5e8f763161da656bf4080c7991701714085723a65e69fe23af4ba4e883f28",
        "percee_individuelle": "7dda924ea183a11583d3539da5cadd0b95d46733059d7d6901729da617f28021",
        "profondeur_1v1": "72001bb8a4e7e0a03cbc38616bc13fa468f342f5adce9e38c2327126666ad988",
        "recuperation_haute": "bd403efaca280ffc63eab15b92c795468fc094a17e303c75e67d69639ebb4d62",
        "une_deux": "670afd1bace6fc57f1e267ece1b16cf73a94954c2bc5de3272646f382071adbc",
    }

    def _structure_hash(self, name: str) -> str:
        import hashlib
        import json

        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        payload = sequence.to_json()
        for kf in payload["keyframes"]:
            kf["physics_tag"] = None  # neutralisé : seul champ qu'on autorise à changer
        stable = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(stable.encode()).hexdigest()

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_structure_unchanged_except_physics_tag(self, name):
        assert self._structure_hash(name) == self._EXPECTED_STRUCTURE_HASH[name], (
            f"{name} : structure changée au-delà de physics_tag (positions/tags narratifs/"
            "ball_owner/ball_height/nombre de keyframes) -- vérifier le diff"
        )


class TestNoImmobileSegmentInFlightActions:
    """Brief "ball_owner=None debt" (23/09/2026), Tâche 2.4 : un segment dont
    le comportement RÉSOLU (`physics_tag` explicite ou inféré, voir
    `animation.ball._resolve_physics_tag`) est `cross`/`shot`/`pass_ground`/
    `pass_lob`/`deflect` doit RÉELLEMENT déplacer le ballon de plus d'1cm --
    sinon c'est le bug "ballon immobile en plein vol" causé par le repli
    silencieux de `build_from_template` sur la dernière position connue
    quand `ball_owner=None` (voir DETTE en tête de `templates.py`). Aucune
    liste d'exclusion : si un gabarit échoue, on le corrige (`ball_position`),
    on ne l'exclut pas.

    SEULE exception, Phase 6 B6-a (08/10/2026) puis B7-a (14/10/2026) : les gabarits `penalty` et `coup_franc`. Un penalty et un coup
    franc ont, par le règlement, un ballon POSÉ immobile tant que le tireur n'a pas frappé ; leurs segments d'attente et d'élan sont
    donc immobiles par construction (réalisme, pas la dette ball_owner=None). L'exception est limitée à ces deux NOMS
    (`_EXEMPT_GABARITS`) et prouvée par `test_the_exemption_is_limited_to_the_posed_ball_templates` : tout autre gabarit avec un
    segment immobile échoue."""

    _IN_FLIGHT_TAGS = {CROSS, SHOT, PASS_GROUND, PASS_LOB, DEFLECT}
    _MIN_DISPLACEMENT_M = 0.01  # 1 cm
    _EXEMPT_GABARITS = {"penalty", "coup_franc"}  # ballon posé immobile avant la frappe (règlement), voir la docstring

    def _immobile_segments(self, name, sequence):
        """Segments « en vol » dont le ballon bouge de moins d'1 cm (liste de (t_a, t_b, tag, distance en m)) ; vide pour
        le gabarit exempté (ballon posé)."""
        found = []
        for kf_a, kf_b in zip(sequence.keyframes, sequence.keyframes[1:]):
            is_last_segment = kf_b.t == sequence.keyframes[-1].t
            tag = _resolve_physics_tag(sequence, kf_a, is_last_segment=is_last_segment)
            if tag not in self._IN_FLIGHT_TAGS:
                continue
            distance_m = _real_distance_m((kf_a.ball.x, kf_a.ball.y), (kf_b.ball.x, kf_b.ball.y))
            if distance_m > self._MIN_DISPLACEMENT_M:
                continue
            if name in self._EXEMPT_GABARITS:
                continue  # B6-a / B7-a : ballon POSÉ tant que le tireur n'a pas frappé (voir TestPenaltyIsSpecialCased, TestFreeKickIsSpecialCased)
            found.append((kf_a.t, kf_b.t, tag, distance_m))
        return found

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_no_immobile_segment_in_flight_actions(self, name):
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        assert self._immobile_segments(name, sequence) == [], (
            f"{name} : segment tagué en vol mais ballon immobile (< 1 cm) -- dette ball_owner=None ?"
        )

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_the_exemption_is_limited_to_the_posed_ball_templates(self, name):
        """On FIGE le ballon sur le premier segment en vol du gabarit : tout gabarit autre que `penalty` et `coup_franc` doit
        alors être signalé ; seuls ces deux-là ne le sont pas (ballon posé)."""
        from dataclasses import replace

        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        keyframes = list(sequence.keyframes)
        for i, (kf_a, kf_b) in enumerate(zip(keyframes, keyframes[1:])):
            tag = _resolve_physics_tag(sequence, kf_a, is_last_segment=(kf_b.t == keyframes[-1].t))
            if tag in self._IN_FLIGHT_TAGS:
                keyframes[i + 1] = replace(kf_b, ball=replace(kf_b.ball, x=kf_a.ball.x, y=kf_a.ball.y))
                frozen = replace(sequence, keyframes=keyframes)
                flagged = self._immobile_segments(name, frozen)
                assert (flagged == []) == (name in self._EXEMPT_GABARITS), (name, flagged)
                return
        raise AssertionError(f"{name} : aucun segment en vol trouvé")


class TestDynamicBallPosition:
    """Chantier 1, 1e-2 (15/10/2026) : `Template.dynamic_ball_position` recalcule la position du ballon à un `t_ratio` donné
    comme le MILIEU de deux rôles nommés, au lieu d'une position fixe posée -- seulement quand `ball_owner` y vaut `None`
    (même usage que `ball_position`, voir sa docstring sur `Template`). Vide par défaut : aucun effet sur les gabarits qui ne
    l'utilisent pas (vérifié par l'empreinte de structure des 11 autres, `TestTemplateStructureUnchangedByPhysicsTags`)."""

    def test_the_ball_sits_at_the_exact_midpoint_on_the_real_gabarit(self):
        lineup = _lineup()
        sequence = BUILDERS["recuperation_haute"](_goal_event(), lineup, _start_positions(lineup))
        kf = next(k for k in sequence.keyframes if k.t == pytest.approx(0.3 * 6.0))
        support1_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        support2_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support2")
        (x1, y1), (x2, y2) = kf.players[support1_id], kf.players[support2_id]
        assert kf.ball.x == pytest.approx((x1 + x2) / 2.0)
        assert kf.ball.y == pytest.approx((y1 + y2) / 2.0)
        assert kf.ball.owner_id is None  # ballon disputé, toujours sans porteur à ce t_ratio

    def test_build_from_template_uses_the_dynamic_midpoint(self):
        times = (0.0, 1.0)
        template = tpl.Template(
            name="dynamic_ball_test", weight=1.0, duration=10.0, tags=tuple((t, "x") for t in times),
            ball_owner=((0.0, "scorer"), (1.0, None)),
            roles=(
                tpl.Role("scorer", ANCHOR_STATIC, (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 0.0))),
                tpl.Role("support1", ANCHOR_STATIC, (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 0.0))),
                tpl.Role("support2", ANCHOR_STATIC, (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 0.0))),
            ),
            dynamic_ball_position=((1.0, "support1", "support2"),),
            context_score=lambda _: 1.0, ground_control=False,
        )
        lineup = _lineup()
        sequence = tpl.build_from_template(template, _goal_event(), lineup, _start_positions(lineup))
        last = sequence.keyframes[-1]
        support1_id = next(p.id for p in lineup.players if p.name == "ad")  # 1er nom alphabétique hors bu/mc0/gardien
        support2_id = next(p.id for p in lineup.players if p.name == "ag")  # 2e
        (x1, y1), (x2, y2) = last.players[support1_id], last.players[support2_id]
        assert last.ball.x == pytest.approx((x1 + x2) / 2.0)
        assert last.ball.y == pytest.approx((y1 + y2) / 2.0)

    def test_an_unknown_role_is_rejected_at_build_time(self):
        import dataclasses

        orig = TEMPLATES["recuperation_haute"]
        broken = dataclasses.replace(orig, dynamic_ball_position=((0.3, "support1", "introuvable"),))
        with pytest.raises(ValueError):
            tpl.build_from_template(broken, _goal_event(), _lineup(), _start_positions(_lineup()))


class TestBallFlightDurationUses3DDistance:
    """Brief "structural test for 2D->3D flight duration" (24/09/2026) --
    test STRUCTUREL, indépendant du résidu Magnus (qui affecte seulement
    `decalage_enroulee`, voir DETTE en tête de `ball.py`) : vérifie
    directement que `_flight_distance_m` (LA fonction dont dépend le calcul
    de la durée du vol dans `build_from_template`, voir `templates.py`)
    calcule une distance 3D (`sqrt(dx²+dy²+dz²)`), pas 2D
    (`sqrt(dx²+dy²)`). `build_from_template` ne définit pas de fonction
    "durée" séparée -- la durée est `distance_m / vitesse_cible`, un
    calcul direct à partir de cette seule fonction -- donc la tester ICI
    couvre exactement le mécanisme, sans qu'une extraction de fonction
    supplémentaire soit nécessaire (aucun refacto).

    Conçu pour échouer si `_flight_distance_m` repassait à une distance 2D :
    vérifié localement (voir le retour de tâche) en remettant temporairement
    `return math.hypot(dx_m, dy_m)` (sans `dz_m`) -- le test devient rouge,
    remis en place ensuite."""

    def test_ball_flight_duration_uses_3d_distance(self):
        # Cas du brief : dx=10m, dy=0, dz=15m, vitesse_cible=20 m/s ->
        # distance_3D = sqrt(10² + 0² + 15²) = sqrt(325) ≈ 18.0278m,
        # durée ≈ 0.90139s. `a`/`b` sont des points (x normalisé, y
        # normalisé, z en mètres) -- x construit pour que
        # (b.x - a.x) * PITCH_LENGTH_M == 10 exactement.
        dx_m, dy_m, dz_m = 10.0, 0.0, 15.0
        vitesse_cible = 20.0
        a = (0.0, 0.0, 0.0)
        b = (dx_m / PITCH_LENGTH_M, dy_m, dz_m)

        distance_m = _flight_distance_m(a, b)
        expected_distance_3d = math.sqrt(dx_m**2 + dy_m**2 + dz_m**2)
        assert distance_m == pytest.approx(expected_distance_3d, abs=1e-9)
        assert distance_m == pytest.approx(18.0278, abs=1e-3)

        duration = distance_m / vitesse_cible
        expected_duration = expected_distance_3d / vitesse_cible
        assert duration == pytest.approx(expected_duration, abs=1e-9)
        assert duration == pytest.approx(0.90139, abs=1e-4)

        # Distance 2D (sans dz) donnerait une valeur STRICTEMENT différente
        # -- la formule 3D n'est donc pas accidentellement équivalente ici.
        distance_2d_only = math.hypot(dx_m, dy_m)
        assert distance_m != pytest.approx(distance_2d_only, abs=1e-6)


# --- Phase 6, B5 : types de frappe (spin et vitesse du vol par type, tirage déterministe par `event_ref`) -------------

_STRIKE_SPEC = {
    # type : (spin min, spin max, vitesse min, vitesse max) -- décisions de l'architecte du 08/10/2026
    "shot_tendu": (0.0, 0.0, 30.0, 35.0),
    "shot_enroule_leger": (20.0, 30.0, 20.0, 28.0),
    "shot_enroule_fort": (50.0, 80.0, 20.0, 28.0),
    "shot_exterieur_pied": (-30.0, -20.0, 22.0, 30.0),
    "reprise_vollee": (10.0, 15.0, 25.0, 32.0),
    "tete": (0.0, 0.0, 12.0, 18.0),
    # Phase 6, B6-b : types de penalty (constantes validées par le propriétaire)
    "penalty_fort": (0.0, 0.0, 29.0, 33.0),
    "penalty_place": (20.0, 30.0, 21.0, 25.0),
    "penalty_contre_pied": (0.0, 0.0, 24.0, 28.0),
    # Phase 6, B7-a : types de coup franc direct (constantes validées par le propriétaire) ; spin de l'enroulé en MODULE, signe tiré.
    "coup_franc_enroule": (45.0, 70.0, 24.0, 30.0),
    "coup_franc_frappe": (-5.0, 5.0, 28.0, 35.0),
}
# Placement des penaltys convertis : (|y| min, |y| max, z min, z max) en mètres.
_PENALTY_PLACEMENT = {
    "penalty_fort": (2.4, 3.4, 1.0, 2.0),
    "penalty_place": (2.8, 3.5, 0.1, 0.8),
    "penalty_contre_pied": (1.0, 2.8, 0.3, 1.2),
}
_PENALTY_TYPES = tuple(_PENALTY_PLACEMENT)
# Vols par gabarit sur 100 matchs (graines 1 à 100, B5) : sert de mélange réaliste pour les tests de répartition.
_FLIGHTS_PER_100_MATCHES = {
    "contre_attaque": 166, "construction_placee": 142, "debordement_centre_tete": 205, "percee_individuelle": 137,
    "une_deux": 92, "coup_franc": 35, "corner": 70, "profondeur_1v1": 95, "recuperation_haute": 134,
    "decalage_enroulee": 122, "penalty": 34, "but_gag": 27,
}


def _build_with_flight(gabarit: str, minute: int, scorer: str = "bu", outcome: str | None = "but"):
    lineup = _lineup()
    event = _goal_event(scorer=scorer, minute=minute, penalty=(gabarit == "penalty"))
    sequence = BUILDERS[gabarit](event, lineup, _start_positions(lineup), outcome)
    event_ref = f"goal:{event.club_name}:{event.scorer}:{event.minute}"
    return sequence, event_ref


def _flight_speed_mps(sequence) -> float:
    start, end = sequence.keyframes[-2], sequence.keyframes[-1]
    distance_m = _flight_distance_m((start.ball.x, start.ball.y, start.ball.z), (end.ball.x, end.ball.y, end.ball.z))
    return distance_m / (end.t - start.t)


def test_strike_type_table_matches_the_architect_decisions():
    from ligue1sim.animation.templates import STRIKE_TYPES

    assert set(STRIKE_TYPES) == set(_STRIKE_SPEC)
    for name, (spin_min, spin_max, speed_min, speed_max) in _STRIKE_SPEC.items():
        strike = STRIKE_TYPES[name]
        assert (strike.spin_min, strike.spin_max, strike.speed_min, strike.speed_max) == (spin_min, spin_max, speed_min, speed_max)


@pytest.mark.parametrize("name", sorted(_STRIKE_SPEC))
def test_each_strike_type_produces_the_expected_spin_and_speed(name):
    from ligue1sim.animation.templates import STRIKE_TYPES, strike_speed_for, strike_spin_for

    spin_min, spin_max, speed_min, speed_max = _STRIKE_SPEC[name]
    strike = STRIKE_TYPES[name]
    spins = [strike_spin_for(strike, f"goal:Test FC:p{i}:{i % 90}") for i in range(300)]
    if strike.curve_side_drawn:  # B7-a : coup franc enroulé, fourchette en module, signe rentrant / sortant
        assert {s > 0 for s in spins} == {True, False}
        spins = [abs(s) for s in spins]
    speeds = [strike_speed_for(strike, f"goal:Test FC:p{i}:{i % 90}") for i in range(300)]
    assert all(spin_min <= s <= spin_max for s in spins)
    assert all(speed_min <= v <= speed_max for v in speeds)
    if spin_min == spin_max == 0.0:
        assert set(spins) == {0.0}  # tendu et tête : aucun spin, donc aucune traînée
    else:
        assert max(spins) - min(spins) > 0.5 * (spin_max - spin_min)  # le spin varie réellement dans la fourchette
    assert max(speeds) - min(speeds) > 0.5 * (speed_max - speed_min)


def test_built_sequences_apply_the_drawn_type_spin_on_the_flight_only():
    from ligue1sim.animation.ball import BALL_FLIGHT
    from ligue1sim.animation.templates import strike_spin_for, strike_type_for

    for gabarit in sorted(BUILDERS):
        for minute in (5, 23, 41, 67, 88):
            sequence, event_ref = _build_with_flight(gabarit, minute)
            strike = strike_type_for(gabarit, event_ref)
            flight_start = sequence.keyframes[-2]
            assert flight_start.physics_tag == BALL_FLIGHT
            assert flight_start.ball.spin == strike_spin_for(strike, event_ref)
            speed_min, speed_max = _STRIKE_SPEC[strike.name][2:]
            assert speed_min - 1e-6 <= _flight_speed_mps(sequence) <= speed_max + 1e-6
            # Le spin n'est posé que sur le vol : la conduite et les autres keyframes gardent 0.
            assert all(kf.ball.spin == 0.0 for kf in sequence.keyframes if kf is not flight_start)


def test_decalage_enroulee_always_produces_shot_enroule_fort():
    from ligue1sim.animation.templates import strike_type_for

    for minute in range(1, 91):
        for scorer in ("bu", "ag", "ad"):
            sequence, event_ref = _build_with_flight("decalage_enroulee", minute, scorer=scorer)
            assert strike_type_for("decalage_enroulee", event_ref).name == "shot_enroule_fort"
            assert 50.0 <= sequence.keyframes[-2].ball.spin <= 80.0  # toujours |spin| > 5 : traînée visible
            assert 20.0 - 1e-6 <= _flight_speed_mps(sequence) <= 28.0 + 1e-6


def test_type_is_coherent_with_the_gabarit():
    from ligue1sim.animation.templates import strike_type_for

    allowed = {
        "decalage_enroulee": {"shot_enroule_fort"},
        "debordement_centre_tete": {"tete", "reprise_vollee"},
        "corner": {"tete", "reprise_vollee"},
        "recuperation_haute": {"reprise_vollee"},
        "but_gag": {"reprise_vollee"},
        "penalty": set(_PENALTY_TYPES),
        "coup_franc": {"coup_franc_enroule", "coup_franc_frappe"},
    }
    foot = {"shot_tendu", "shot_enroule_leger", "shot_exterieur_pied"}
    for gabarit in BUILDERS:
        seen = {strike_type_for(gabarit, f"goal:Test FC:p{i}:{i % 90}").name for i in range(400)}
        assert seen <= allowed.get(gabarit, foot), (gabarit, seen)
        # Une tête n'est produite que par les gabarits de tête ; le fort que par decalage_enroulee.
        assert ("tete" in seen) == (gabarit in {"debordement_centre_tete", "corner"})
        assert ("shot_enroule_fort" in seen) == (gabarit == "decalage_enroulee")
        # Les types de penalty ne sortent que du gabarit penalty, et lui ne produit rien d'autre.
        assert (seen & set(_PENALTY_TYPES) != set()) == (gabarit == "penalty")


def test_strike_type_distribution_over_1000_strikes():
    from collections import Counter

    from ligue1sim.animation.templates import strike_type_for

    # Le gabarit penalty a ses propres types depuis B6-b : il sort de ce mélange (voir test_penalty_type_distribution...).
    mix = {g: n for g, n in _FLIGHTS_PER_100_MATCHES.items() if g != "penalty"}
    total = sum(mix.values())
    counts: Counter = Counter()
    strikes = 0
    for gabarit, flights in mix.items():
        n = round(1000 * flights / total)
        for i in range(n):
            counts[strike_type_for(gabarit, f"goal:Test FC:{gabarit}{i}:{(i * 7) % 90 + 1}").name] += 1
            strikes += 1
    assert 990 <= strikes <= 1010
    # Cibles de l'architecte (parts de l'ensemble des frappes hors penaltys), marge de 4 points ; `shot_tendu` resserré à ±2,5 points
    # (bruit d'échantillonnage de 1 000 frappes : environ ±1,5 point). Sa cible est rebasée à 32,3 % depuis B6-b : les penaltys,
    # qui pesaient 2,7 points de `shot_tendu` dans la cible historique de 35 %, ont leurs propres types et sortent du mélange.
    # B7-a : les coups francs (2,8 points des frappes) ont leurs 2 types internes (1,8 + 1,0 point) et sortent de `shot_enroule_leger` (12,0 -> 9,2).
    targets = {"shot_tendu": 32.3, "shot_enroule_leger": 9.2, "shot_enroule_fort": 9.7, "shot_exterieur_pied": 5.5, "reprise_vollee": 16.0, "tete": 21.8,
               "coup_franc_enroule": 1.8, "coup_franc_frappe": 1.0}
    for name, target in targets.items():
        share = 100.0 * counts[name] / strikes
        assert abs(share - target) <= 4.0, f"{name} : {share:.1f} % pour une cible de {target} %"
    assert abs(100.0 * counts["shot_enroule_fort"] / strikes - 9.7) <= 0.6  # decalage_enroulee seul : 122 vols sur 1 259
    assert abs(100.0 * counts["shot_tendu"] / strikes - 32.3) <= 2.5, counts


def test_strike_type_is_deterministic_and_independent_of_the_global_random_state():
    from ligue1sim.animation.templates import strike_type_for

    refs = [f"goal:Test FC:p{i}:{i % 90}" for i in range(200)]
    random.seed(1)
    first = [strike_type_for("contre_attaque", r).name for r in refs]
    random.seed(999)
    random.random()
    second = [strike_type_for("contre_attaque", r).name for r in refs]
    assert first == second


def test_no_spin_without_flight_and_the_carry_is_straight():
    for gabarit in sorted(BUILDERS):
        for outcome in (None, "tacle", "degagement"):
            sequence, _ = _build_with_flight(gabarit, 34, outcome=outcome)
            assert all(kf.ball.spin == 0.0 for kf in sequence.keyframes), (gabarit, outcome)


# --- Phase 6, B6-b : types de penalty (fort 30 %, placé 50 %, contre-pied 20 %) ------------------------------------------


def _penalty_sequence(minute, scorer="bu", outcome="but"):
    sequence, event_ref = _build_with_flight("penalty", minute, scorer=scorer, outcome=outcome)
    return sequence, event_ref


def test_penalty_type_distribution_over_1000_penalties():
    from collections import Counter

    from ligue1sim.animation.templates import strike_type_for

    counts = Counter(strike_type_for("penalty", f"goal:Test FC:taker{i}:{i % 90 + 1}").name for i in range(1000))
    assert set(counts) == set(_PENALTY_TYPES)
    for name, target in (("penalty_fort", 30.0), ("penalty_place", 50.0), ("penalty_contre_pied", 20.0)):
        assert abs(counts[name] / 10.0 - target) <= 4.0, (name, counts)


def test_each_penalty_type_respects_its_speed_spin_and_placement():
    from ligue1sim.animation.templates import strike_type_for

    seen = set()
    sides = set()
    for minute in range(1, 91):
        for scorer in ("bu", "ag", "ad"):
            sequence, event_ref = _penalty_sequence(minute, scorer)
            strike = strike_type_for("penalty", event_ref)
            seen.add(strike.name)
            spin_min, spin_max, speed_min, speed_max = _STRIKE_SPEC[strike.name]
            flight_start, target = sequence.keyframes[-2], sequence.keyframes[-1]
            assert spin_min <= flight_start.ball.spin <= spin_max
            assert speed_min - 1e-6 <= _flight_speed_mps(sequence) <= speed_max + 1e-6
            y_min, y_max, z_min, z_max = _PENALTY_PLACEMENT[strike.name]
            y_m = (target.ball.y - 0.5) * 68.0
            assert y_min - 1e-6 <= abs(y_m) <= y_max + 1e-6, (strike.name, y_m)
            assert z_min - 1e-6 <= target.ball.z <= z_max + 1e-6, (strike.name, target.ball.z)
            assert 1.0 <= target.ball.x <= 1.02  # le ballon franchit la ligne : c'est bien un but
            sides.add(y_m > 0)
    assert seen == set(_PENALTY_TYPES)
    assert sides == {True, False}  # les deux côtés du but sont utilisés
    # Le placé a un spin (traînée) ; le fort et le contre-pied n'en ont pas.
    assert _STRIKE_SPEC["penalty_place"][0] > 5 and _STRIKE_SPEC["penalty_fort"][1] == _STRIKE_SPEC["penalty_contre_pied"][1] == 0.0


def test_the_penalty_type_never_chooses_the_outcome():
    """Le type ne dépend que de `event_ref` ; l'issue, elle, décide de la cible : arrêt, hors cadre, poteau et barre gardent
    la cible d'avant B6-b (`_flight_target`), seul le BUT reçoit le placement du type."""
    from ligue1sim.animation.templates import _flight_target, strike_type_for

    for minute in (5, 23, 41, 67, 88):
        for outcome in ("but", "arret", "hors_cadre", "poteau", "barre"):
            sequence, event_ref = _penalty_sequence(minute, outcome=outcome)
            assert strike_type_for("penalty", event_ref).name == strike_type_for("penalty", event_ref).name
            target = sequence.keyframes[-1].ball
            if outcome != "but":
                expected = _flight_target(outcome, event_ref)
                assert (target.x, target.y, target.z) == pytest.approx(expected)
    # Même événement, quelle que soit l'issue : même type.
    for minute in range(1, 40):
        types = {strike_type_for("penalty", f"goal:Test FC:bu:{minute}").name for _ in ("but", "arret", "hors_cadre")}
        assert len(types) == 1


def test_penalty_ball_side_is_deterministic_and_balanced():
    from ligue1sim.animation.templates import penalty_ball_side

    refs = [f"goal:Test FC:p{i}:{i % 90 + 1}" for i in range(400)]
    sides = [penalty_ball_side(r) for r in refs]
    assert sides == [penalty_ball_side(r) for r in refs] and set(sides) == {1, -1}
    assert abs(sum(1 for v in sides if v > 0) - 200) <= 40


class TestGroundControls:
    """Phase 6, B8-a : chaque réception AU SOL reçoit un segment de contrôle explicite (geste tiré par sha256 : pied naturel, pied faible,
    semelle) -- ballon à 0,3-0,6 m du joueur du côté du pied, geste de 0,15 à 0,30 s, ballon échappé de 1 à 3 m puis repris (0,4 à 0,8 s) pour un
    contrôle approximatif ou lourd, EFFET VISUEL SEUL (le porteur ne change pas). `corner` et `debordement_centre_tete` (réception aérienne :
    B8-c), `coup_franc`, `penalty` et `percee_individuelle` (aucune réception) ne changent pas."""

    _CONTROLLED = ("but_gag", "construction_placee", "contre_attaque", "decalage_enroulee", "profondeur_1v1", "recuperation_haute", "une_deux")
    _UNTOUCHED = ("corner", "debordement_centre_tete", "coup_franc", "penalty", "percee_individuelle")
    _GESTURES = ("pied_naturel", "pied_faible", "semelle")

    @staticmethod
    def _lineup_with_foot(foot):
        import dataclasses

        lineup = _lineup()
        if foot is None:
            return lineup
        return dataclasses.replace(lineup, players=[dataclasses.replace(p, pied=foot) for p in lineup.players])

    def _build(self, name, minute=34, club="Test FC", foot=None, controls=True, outcome="but"):
        import dataclasses

        lineup = self._lineup_with_foot(foot)
        event = dataclasses.replace(_goal_event(penalty=(name == "penalty"), minute=minute), club_name=club)
        starts = _start_positions(lineup)
        if controls:
            return BUILDERS[name](event, lineup, starts, outcome)
        return build_from_template(dataclasses.replace(TEMPLATES[name], ground_control=False), event, lineup, starts, outcome)

    @staticmethod
    def _is_control_tag(tag):
        return tag.startswith("controle_pied") or tag.startswith("controle_semelle")

    @staticmethod
    def _metres(kf, player_id):
        x, y = kf.players[player_id]
        return x * PITCH_LENGTH_M, y * 68.0

    @staticmethod
    def _ball_player_distance_m(kf):
        px, py = kf.players[kf.ball.owner_id]
        return math.hypot((kf.ball.x - px) * PITCH_LENGTH_M, (kf.ball.y - py) * 68.0)

    def _windows(self, sequence):
        """(indice, geste, qualité, final) de chaque contrôle, lu sur les tags des keyframes."""
        windows = []
        for j, kf in enumerate(sequence.keyframes):
            if not self._is_control_tag(kf.tag):
                continue
            body = kf.tag[len("controle_"):]
            quality = "propre"
            for suffix, label in (("_approximatif", "approximatif"), ("_lourd", "lourd")):
                if body.endswith(suffix):
                    body, quality = body[: -len(suffix)], label
            owner_changed = j >= 1 and sequence.keyframes[j - 1].ball.owner_id != kf.ball.owner_id
            windows.append((j, body, quality, owner_changed))
        return windows

    def test_every_ground_reception_has_an_explicit_control_of_positive_duration(self):
        for name in self._CONTROLLED:
            for minute in range(1, 41):
                sequence = self._build(name, minute)
                frames = sequence.keyframes
                receptions = [j for j in range(1, len(frames)) if frames[j].ball.owner_id is not None and frames[j].ball.owner_id != frames[j - 1].ball.owner_id]
                assert receptions, (name, minute)
                for j in receptions:
                    at_reception = self._is_control_tag(frames[j].tag)  # réception finale : la fenêtre précède le keyframe de frappe
                    following = j + 1 < len(frames) and self._is_control_tag(frames[j + 1].tag)
                    assert at_reception or following, (name, minute, j, frames[j].tag)
                    nxt = frames[j + 1] if j + 1 < len(frames) else None
                    assert nxt is not None and nxt.t - frames[j].t > 0.0

    def test_templates_without_ground_reception_have_no_control(self):
        for name in self._UNTOUCHED:
            for minute in range(1, 21):
                assert not any(self._is_control_tag(kf.tag) for kf in self._build(name, minute).keyframes), name

    def test_other_keyframes_players_and_owners_are_unchanged(self):
        for name in self._CONTROLLED:
            for minute in (5, 41, 77):
                with_controls, without = self._build(name, minute), self._build(name, minute, controls=False)
                original = {kf.t: kf for kf in without.keyframes}
                kept = [kf for kf in with_controls.keyframes if kf.t in original]
                assert len(kept) == len(without.keyframes), (name, minute)  # aucun keyframe d'origine n'a bougé dans le temps
                for kf in kept:
                    assert kf.players == original[kf.t].players
                    assert kf.ball.owner_id == original[kf.t].ball.owner_id

    def test_times_strictly_increase_and_inserted_players_lie_between_their_neighbours(self):
        for name in self._CONTROLLED:
            for minute in range(1, 31):
                sequence = self._build(name, minute)
                times = [kf.t for kf in sequence.keyframes]
                assert all(b > a for a, b in zip(times, times[1:])), (name, minute)
                original = {kf.t for kf in self._build(name, minute, controls=False).keyframes}
                for j, kf in enumerate(sequence.keyframes):
                    if kf.t in original:
                        continue
                    a, b = sequence.keyframes[j - 1], sequence.keyframes[j + 1]
                    f = (kf.t - a.t) / (b.t - a.t)
                    for pid, (x, y) in kf.players.items():
                        assert x == pytest.approx(a.players[pid][0] + (b.players[pid][0] - a.players[pid][0]) * f)
                        assert y == pytest.approx(a.players[pid][1] + (b.players[pid][1] - a.players[pid][1]) * f)

    def test_control_keyframes_keep_the_receiver_as_carrier_on_the_ground(self):
        for name in self._CONTROLLED:
            for minute in range(1, 31):
                sequence = self._build(name, minute)
                for j, *_ in self._windows(sequence):
                    kf = sequence.keyframes[j]
                    assert kf.ball.owner_id is not None and kf.ball.z == 0.0 and kf.ball.spin == 0.0

    def test_distances_and_durations_follow_the_validated_constants(self):
        seen = Counter()
        for name in self._CONTROLLED:
            for minute in range(1, 91):
                for club in ("Test FC", "Club B", "Club C"):
                    sequence = self._build(name, minute, club)
                    frames = sequence.keyframes
                    for j, gesture, quality, final in self._windows(sequence):
                        if quality != "propre" and self._is_control_tag(frames[j - 1].tag):
                            # ballon échappé d'une réception FINALE : le keyframe de frappe sert de reprise (le ballon revient au joueur)
                            low, high = (1.0, 2.0) if quality == "approximatif" else (2.0, 3.0)
                            assert low - 1e-6 <= self._ball_player_distance_m(frames[j]) <= high + 1e-6
                            assert 0.2 - 1e-6 <= frames[j + 1].t - frames[j].t <= 0.8 + 1e-6
                            continue
                        seen[(gesture, quality)] += 1
                        duration_range = (0.20, 0.30) if gesture == "semelle" else (0.15, 0.25)
                        if final:
                            if quality == "propre":
                                assert 0.55 - 1e-6 <= self._ball_player_distance_m(frames[j]) <= 0.85 + 1e-6  # arrivée : 0,25 m de plus que l'amorti
                                assert duration_range[0] - 1e-6 <= frames[j + 1].t - frames[j].t <= duration_range[1] + 1e-6
                            continue
                        arrival = self._ball_player_distance_m(frames[j - 1])  # keyframe de réception (juste avant le premier inséré)
                        assert 0.55 - 1e-6 <= arrival <= 0.85 + 1e-6
                        gesture_duration = frames[j].t - frames[j - 1].t
                        assert duration_range[0] - 1e-6 <= gesture_duration <= duration_range[1] + 1e-6
                        distance = self._ball_player_distance_m(frames[j])
                        if quality == "propre":
                            assert 0.30 - 1e-6 <= distance <= 0.60 + 1e-6
                        else:
                            low, high = (1.0, 2.0) if quality == "approximatif" else (2.0, 3.0)
                            assert low - 1e-6 <= distance <= high + 1e-6
                            assert frames[j + 1].tag == "reprise_conduite"
                            assert 0.2 - 1e-6 <= frames[j + 1].t - frames[j].t <= 0.8 + 1e-6  # reprise de 0,4 à 0,8 s (réduite si l'intervalle manque de place)
                            assert 0.30 - 1e-6 <= self._ball_player_distance_m(frames[j + 1]) <= 0.60 + 1e-6
        assert {g for g, _ in seen} == set(self._GESTURES)
        assert {q for _, q in seen} == {"propre", "approximatif", "lourd"}

    def test_gesture_distribution_and_the_sole_speed_limit(self):
        from ligue1sim.animation.templates import _control_gesture, _flight_unit

        n = 20000
        slow = Counter(_control_gesture(5.0, _flight_unit(f"ref{i}", "gesture")) for i in range(n))
        assert abs(slow["pied_naturel"] / n - 0.85) <= 0.01 and abs(slow["pied_faible"] / n - 0.10) <= 0.01 and abs(slow["semelle"] / n - 0.05) <= 0.01
        fast = Counter(_control_gesture(8.01, _flight_unit(f"ref{i}", "gesture")) for i in range(n))
        assert fast["semelle"] == 0  # jamais de semelle au-delà de 8 m/s
        assert abs(fast["pied_naturel"] / n - 0.85 / 0.95) <= 0.01
        assert _control_gesture(8.0, 0.99) == "semelle"  # 8 m/s exactement : permis

    def test_side_follows_the_strong_foot_and_flips_for_the_weak_foot(self):
        checked = Counter()
        for foot in ("D", "G"):
            for name in self._CONTROLLED:
                for minute in range(1, 61):
                    sequence = self._build(name, minute, foot=foot)
                    frames = sequence.keyframes
                    for j, gesture, quality, final in self._windows(sequence):
                        owner = frames[j].ball.owner_id
                        if final:
                            if quality != "propre":
                                continue
                            before, after = frames[j], frames[j + 1]
                        else:
                            if quality != "propre":
                                continue
                            before, after = frames[j - 1], frames[j]
                        (ax, ay), (bx, by) = self._metres(before, owner), self._metres(after, owner)
                        move = math.hypot(bx - ax, by - ay)
                        if move < 0.05:
                            continue  # joueur immobile : cap par défaut, côté non mesurable ici
                        hx, hy = (bx - ax) / move, (by - ay) / move
                        probe = frames[j] if final else frames[j]
                        px, py = self._metres(probe, owner)
                        off_x, off_y = probe.ball.x * PITCH_LENGTH_M - px, probe.ball.y * 68.0 - py
                        right = off_x * (-hy) + off_y * hx  # > 0 : à droite du joueur (axe y vers le bas à l'écran)
                        strong_right = foot == "D"
                        expected_right = strong_right if gesture != "pied_faible" else not strong_right
                        assert (right > -1e-9) if expected_right else (right < 1e-9), (foot, name, minute, gesture, right)
                        checked[(foot, gesture)] += 1
        assert checked[("D", "pied_naturel")] > 20 and checked[("G", "pied_naturel")] > 20
        assert checked[("D", "pied_faible")] > 0 and checked[("G", "pied_faible")] > 0

    def test_unknown_foot_is_drawn_by_hash_about_78_percent_right_footed(self):
        from ligue1sim.animation.templates import _strong_foot

        players = [_player("MC", 70.0, f"p{i}", 1000 + i) for i in range(4000)]
        right = sum(_strong_foot(p, p.id) == "D" for p in players)
        assert abs(right / len(players) - 0.78) <= 0.03
        assert all(_strong_foot(p, p.id) == _strong_foot(p, p.id) for p in players[:50])  # déterministe

    def test_known_foot_is_used_as_is(self):
        import dataclasses

        from ligue1sim.animation.templates import _strong_foot

        base = _player("MC", 70.0, "x", 1)
        assert _strong_foot(dataclasses.replace(base, pied="G"), 1) == "G"
        assert _strong_foot(dataclasses.replace(base, pied="D"), 1) == "D"

    def test_controls_are_deterministic(self):
        for name in self._CONTROLLED:
            assert self._build(name, 41).to_json() == self._build(name, 41).to_json()


class TestControlPressureModulation:
    """Phase 6, B8-b : la probabilité d'un contrôle approximatif / lourd dépend de la pression adverse (proximité, vitesse d'arrivée, contexte)
    et de la qualité technique du récepteur (First Touch, Technique, Composure, weak_foot). Sans `opponent_lineup`, comportement de B8-a."""

    _CONTROLLED = TestGroundControls._CONTROLLED

    @staticmethod
    def _context(distance_m=None, pressing=False, recuperation_haute=False):
        from ligue1sim.animation.templates import _PressureContext

        return _PressureContext(distance_at=lambda _point, _t: distance_m, pressing_style=pressing, recuperation_haute=recuperation_haute)

    @staticmethod
    def _opponents():
        postes = ["DC", "DC", "LB", "RB", "MDC", "MC", "MC", "AG", "AD", "BU"]
        players = [_player("GK", 65.0, "opp-gk", 101)] + [_player(poste, 65.0, f"opp-{i}", 102 + i) for i, poste in enumerate(postes)]
        return Lineup(club_name="Opponent FC", formation="4-3-3", players=players, rating=65.0)

    # --- indice de pression p ---------------------------------------------------------------------------------------------------------
    def test_pressure_index_follows_the_validated_weights_and_thresholds(self):
        from ligue1sim.animation.templates import _pressure_index

        none = self._context(distance_m=20.0)
        assert _pressure_index(20.0, 5.0, none) == 0.0
        assert _pressure_index(8.0, 12.0, none) == 0.0  # seuils : 8 m -> 0 ; 12 m/s -> 0
        assert _pressure_index(1.5, 5.0, none) == pytest.approx(0.5)  # proximité seule
        assert _pressure_index(20.0, 24.0, none) == pytest.approx(0.3)  # vitesse seule
        assert _pressure_index(20.0, 5.0, self._context(pressing=True)) == pytest.approx(0.1)  # contexte : 0,2 x 0,5
        assert _pressure_index(20.0, 5.0, self._context(pressing=True, recuperation_haute=True)) == pytest.approx(0.2)  # cumulables
        assert _pressure_index(1.0, 40.0, self._context(pressing=True, recuperation_haute=True)) == pytest.approx(1.0)
        assert _pressure_index(4.75, 18.0, none) == pytest.approx(0.5 * 0.5 + 0.3 * 0.5)  # interpolation linéaire
        assert _pressure_index(None, 5.0, none) == 0.0  # aucun adversaire de champ

    def test_pressure_index_stays_within_zero_and_one(self):
        from ligue1sim.animation.templates import _pressure_index

        context = self._context(pressing=True, recuperation_haute=True)
        for distance in (None, 0.0, 1.5, 3.0, 8.0, 50.0):
            for arrival in (0.0, 12.0, 18.0, 24.0, 60.0):
                assert 0.0 <= _pressure_index(distance, arrival, context) <= 1.0

    # --- qualité technique q ----------------------------------------------------------------------------------------------------------
    def test_technical_quality_is_neutral_without_attributes(self):
        import dataclasses

        from ligue1sim.animation.templates import _technical_quality

        bare = _player("MC", 70.0, "x", 1)
        assert _technical_quality(bare, 0.0) == 59.0 and _technical_quality(bare, 1.0) == 59.0
        partial = dataclasses.replace(bare, attributes={"First Touch": 90, "Technique": 90})  # Composure manquante
        assert _technical_quality(partial, 0.5) == 59.0

    def test_technical_quality_mixes_composure_only_under_pressure(self):
        import dataclasses

        from ligue1sim.animation.templates import _technical_quality

        player = dataclasses.replace(_player("MC", 70.0, "x", 1), attributes={"First Touch": 80, "Technique": 60, "Composure": 40})
        assert _technical_quality(player, 0.0) == pytest.approx(0.6 * 80 + 0.4 * 60)  # 72 : Composure n'entre pas
        assert _technical_quality(player, 1.0) == pytest.approx(0.5 * 72 + 0.5 * 40)  # 56 : pour moitié sous pression pleine
        assert _technical_quality(player, 0.5) == pytest.approx(0.75 * 72 + 0.25 * 40)

    # --- modulation du tirage ---------------------------------------------------------------------------------------------------------
    def test_neutral_pressure_and_quality_keep_the_base_rates(self):
        from ligue1sim.animation.templates import _modulated_loose_heavy

        assert _modulated_loose_heavy("pied_naturel", 0.15, 59.0, None) == pytest.approx((0.10, 0.02))
        assert _modulated_loose_heavy("pied_faible", 0.15, 59.0, 3.0) == pytest.approx((0.35, 0.10))

    def test_modulation_formula_uses_the_validated_effects(self):
        from ligue1sim.animation.templates import _modulated_loose_heavy

        loose, heavy = _modulated_loose_heavy("pied_naturel", 0.75, 59.0, None)  # +0,25 x 0,60
        assert loose == pytest.approx(0.25) and heavy == pytest.approx(0.02 * 0.25 / 0.10)  # lourd proportionnel : 5 %
        assert _modulated_loose_heavy("pied_naturel", 0.15, 79.0, None)[0] == 0.01  # -0,12 pour +20 de qualité : 10 % -> plancher de 1 %
        assert _modulated_loose_heavy("pied_naturel", 0.15, 49.0, None)[0] == pytest.approx(0.10 + 0.06)  # -10 de qualité : +6 points
        assert _modulated_loose_heavy("pied_faible", 0.15, 59.0, 1.0)[0] == pytest.approx(0.35 + 0.12)
        assert _modulated_loose_heavy("pied_faible", 0.15, 59.0, 5.0)[0] == pytest.approx(0.35 - 0.12)
        assert _modulated_loose_heavy("pied_naturel", 0.15, 59.0, 1.0)[0] == pytest.approx(0.10)  # weak_foot : pied faible seulement

    def test_modulation_is_bounded_and_heavy_is_capped(self):
        from ligue1sim.animation.templates import _modulated_loose_heavy

        assert _modulated_loose_heavy("pied_faible", 1.0, 0.0, 1.0)[0] == 0.60  # plafond de l'approximatif
        assert _modulated_loose_heavy("pied_naturel", 0.0, 99.0, None)[0] == 0.01  # plancher
        for gesture in ("pied_naturel", "pied_faible"):
            for pressure in (0.0, 0.5, 1.0):
                for quality in (0.0, 59.0, 99.0):
                    for weak_foot in (None, 1.0, 3.0, 5.0):
                        loose, heavy = _modulated_loose_heavy(gesture, pressure, quality, weak_foot)
                        assert 0.01 <= loose <= 0.60 and 0.0 <= heavy <= 0.25

    def test_sole_is_never_modulated(self):
        from ligue1sim.animation.templates import _modulated_loose_heavy

        assert _modulated_loose_heavy("semelle", 1.0, 0.0, 1.0) == (0.0, 0.0)

    # --- effet sur les gabarits -------------------------------------------------------------------------------------------------------
    def _loose_rate(self, context, attributes=None, count=240):
        """Part des contrôles au pied naturel qui ne sont pas propres, sur `count` événements, avec un contexte de pression imposé."""
        import dataclasses

        from ligue1sim.animation.templates import TEMPLATES, _insert_ground_controls

        lineup = _lineup()
        if attributes is not None:
            lineup = dataclasses.replace(lineup, players=[dataclasses.replace(p, attributes=attributes) for p in lineup.players])
        players_by_id = {p.id: p for p in lineup.players}
        loose = total = 0
        for minute in range(1, count + 1):
            club = f"club{minute}"
            bare = TestGroundControls()._build("contre_attaque", minute, club=club, controls=False)
            for kf in _insert_ground_controls(TEMPLATES["contre_attaque"], list(bare.keyframes), players_by_id, bare.event_ref, context):
                if kf.tag.startswith("controle_pied_naturel"):
                    total += 1
                    loose += kf.tag.endswith(("_approximatif", "_lourd"))
        assert total > 100
        return loose / total

    def test_strong_pressure_raises_and_calm_lowers_the_loose_control_rate(self):
        calm = self._loose_rate(self._context(distance_m=30.0))
        pressed = self._loose_rate(self._context(distance_m=1.5, pressing=True, recuperation_haute=True))
        assert pressed > calm + 0.10

    def test_a_technical_player_without_pressure_rarely_loses_the_ball(self):
        technical = {"First Touch": 90, "Technique": 90, "Composure": 90}
        clumsy = {"First Touch": 25, "Technique": 25, "Composure": 25}
        calm = self._context(distance_m=30.0)
        assert self._loose_rate(calm, technical) < 0.05
        assert self._loose_rate(calm, clumsy) > self._loose_rate(calm, technical) + 0.05

    # --- branchement dans les gabarits ------------------------------------------------------------------------------------------------
    def test_every_builder_accepts_the_opponent_lineup_and_none_keeps_b8a(self):
        lineup, opponents = _lineup(), self._opponents()
        for name in BUILDERS:
            event = _goal_event(penalty=(name == "penalty"))
            starts = _start_positions(lineup)
            default = BUILDERS[name](event, lineup, starts, "but")
            explicit_none = BUILDERS[name](event, lineup, starts, "but", None)
            with_opponents = BUILDERS[name](event, lineup, starts, "but", opponents)
            assert default.to_json() == explicit_none.to_json(), name
            assert with_opponents.duration == default.duration, name  # la pression ne change jamais la durée
            assert with_opponents.event_ref == default.event_ref, name

    def test_templates_without_ground_control_ignore_the_opponent_lineup(self):
        lineup, opponents = _lineup(), self._opponents()
        for name in TestGroundControls._UNTOUCHED:
            event = _goal_event(penalty=(name == "penalty"))
            starts = _start_positions(lineup)
            assert BUILDERS[name](event, lineup, starts, "but", opponents).to_json() == BUILDERS[name](event, lineup, starts, "but").to_json(), name

    def test_modulation_with_opponents_is_deterministic(self):
        lineup, opponents = _lineup(), self._opponents()
        for name in self._CONTROLLED:
            for minute in range(1, 21):
                event = _goal_event(minute=minute)
                starts = _start_positions(lineup)
                assert BUILDERS[name](event, lineup, starts, "but", opponents).to_json() == BUILDERS[name](event, lineup, starts, "but", opponents).to_json()

    def test_the_sporting_outcome_and_the_receivers_are_never_modified_by_the_pressure(self):
        lineup, opponents = _lineup(), self._opponents()
        for name in self._CONTROLLED:
            for minute in range(1, 11):
                event = _goal_event(minute=minute)
                starts = _start_positions(lineup)
                plain, pressed = BUILDERS[name](event, lineup, starts, "but"), BUILDERS[name](event, lineup, starts, "but", opponents)
                assert plain.keyframes[0].ball == pressed.keyframes[0].ball and plain.keyframes[-1].ball == pressed.keyframes[-1].ball
                original = lambda sequence: [(kf.t, kf.ball.owner_id) for kf in sequence.keyframes if not kf.tag.startswith(("controle_", "reprise_"))]
                assert original(plain) == original(pressed), (name, minute)


class TestAerialContactHeight:
    """Phase 6, B8-c1 : le dernier keyframe de `corner` et de `debordement_centre_tete` est un contact aérien dont la hauteur dépend du type de frappe
    (tête 1,6 à 2,2 m, volée 0,4 à 1,0 m), tirée par sha256 de `event_ref` ; aucun autre gabarit n'est concerné."""

    _AERIAL = ("corner", "debordement_centre_tete")

    def test_only_the_two_header_templates_have_an_aerial_contact(self):
        assert {name for name, template in TEMPLATES.items() if template.aerial_contact} == set(self._AERIAL)

    def test_the_contact_height_follows_the_strike_type(self):
        import dataclasses

        from ligue1sim.animation.templates import strike_type_for

        lineup = _lineup()
        kinds = Counter()
        for name in self._AERIAL:
            for minute in range(1, 201):
                event = dataclasses.replace(_goal_event(minute=minute), club_name=f"c{minute}")
                sequence = BUILDERS[name](event, lineup, _start_positions(lineup))
                strike = strike_type_for(name, sequence.event_ref).name
                lo, hi = (0.4, 1.0) if strike == "reprise_vollee" else (1.6, 2.2)
                assert lo <= sequence.keyframes[-1].ball.z <= hi, (name, minute, strike)
                kinds[strike] += 1
        assert 0.04 <= kinds["reprise_vollee"] / sum(kinds.values()) <= 0.16  # la volée reste ~10 % des frappes de ces gabarits

    def test_the_contact_height_is_deterministic_and_varies_with_the_event(self):
        from ligue1sim.animation.templates import _contact_height_m

        heights = [_contact_height_m("corner", f"goal:c{i}:bu:34") for i in range(300)]
        assert heights == [_contact_height_m("corner", f"goal:c{i}:bu:34") for i in range(300)]
        assert len({round(h, 6) for h in heights}) > 200

    def test_other_templates_keep_a_ground_final_keyframe(self):
        lineup = _lineup()
        for name in sorted(set(BUILDERS) - set(self._AERIAL)):
            sequence = BUILDERS[name](_goal_event(penalty=(name == "penalty")), lineup, _start_positions(lineup))
            assert sequence.keyframes[-1].ball.z == 0.0, name

    def test_the_corner_contact_is_the_arrival_of_the_cross(self):
        lineup = _lineup()
        sequence = BUILDERS["corner"](_goal_event(), lineup, _start_positions(lineup))
        assert [kf.t for kf in sequence.keyframes] == pytest.approx([0.0, 2.1, 4.2, 4.9, 7.0])  # option B : durée 7,0 s, centre de 4,9 à 7,0 s
        assert all(kf.ball.owner_id is not None for kf in sequence.keyframes)  # plus de « ballon disputé » (owner=None)
        assert sequence.keyframes[3].physics_tag == "cross"
        assert sequence.roster[sequence.keyframes[-1].ball.owner_id].role == "scorer"  # le buteur reçoit le centre


class TestRoleGeometry:
    """Chantier 1, sous-étape 1a : géométrie de rôle (`Role.geometry`). Le départ d'un rôle avec géométrie est dérivé de sa cible et de sa
    position de formation ; sa course respecte, sur CHAQUE segment, le ratio (<= 0,55 de la vitesse max du poste) et l'accélération
    (D <= 2,25 x T²). Un rôle sans géométrie reste inchangé (voir aussi les empreintes de structure). Depuis 1c, quatre gabarits en
    portent déjà une (voir `test_templates_not_yet_migrated_carry_no_geometry`, qui vérifie les autres)."""

    _PROFILE = ((0.0, 0.0), (0.4, 0.4), (1.0, 1.0))
    _ASSIST_PROFILE = ((0.0, 0.0), (0.4, 0.85), (1.0, 1.0))

    def _template(self, duration: float, assist: bool = True) -> "tpl.Template":
        roles = [tpl.Role("scorer", ANCHOR_STATIC, tuple(tpl.RoleFrame(t, p) for t, p in self._PROFILE), geometry=tpl.RoleGeometry(tpl.GEOM_ZONE))]
        if assist:
            geometry = tpl.RoleGeometry(tpl.GEOM_BEHIND_ZONE, cap_m=30.0)
            roles.append(tpl.Role("assist", ANCHOR_STATIC, tuple(tpl.RoleFrame(t, p) for t, p in self._ASSIST_PROFILE), geometry=geometry))
        times = [t for t, _ in self._PROFILE]
        return tpl.Template(
            name="geom_test", weight=1.0, duration=duration, roles=tuple(roles), tags=tuple((t, "x") for t in times),
            ball_owner=tuple((t, "scorer") for t in times), context_score=lambda _: 1.0, ground_control=False,
        )

    def _build(self, duration: float, scorer: str, start: PitchPoint, zone: Zone = _SCORER_ZONE):
        lineup = _lineup()
        by_name = {p.name: p for p in lineup.players}
        starts = {**_start_positions(lineup), by_name[scorer].id: start}
        event = GoalEvent(club_name="Test FC", scorer=scorer, assist="mc1", minute=34, penalty=False, zone=zone, assist_zone=_ASSIST_ZONE)
        return tpl.build_from_template(self._template(duration), event, lineup, starts), by_name[scorer].id

    def _worst_ratios(self, sequence) -> tuple[float, float]:
        """(pire ratio vitesse, pire D / (2,25 x T²)) sur tous les segments des rôles scriptés."""
        from ligue1sim.animation.motion import MAX_SPEED_MPS
        from ligue1sim.pitch_geometry import PITCH_WIDTH_M

        worst_ratio = worst_accel = 0.0
        for pid, entry in sequence.roster.items():
            if entry.role is None:
                continue
            for a, b in zip(sequence.keyframes, sequence.keyframes[1:]):
                seconds = b.t - a.t
                distance = math.hypot((b.players[pid][0] - a.players[pid][0]) * PITCH_LENGTH_M, (b.players[pid][1] - a.players[pid][1]) * PITCH_WIDTH_M)
                worst_ratio = max(worst_ratio, distance / seconds / MAX_SPEED_MPS[entry.poste])
                worst_accel = max(worst_accel, distance / (2.25 * seconds**2))
        return worst_ratio, worst_accel

    @pytest.mark.parametrize("scorer", ["cb0", "mc0", "bu"])
    @pytest.mark.parametrize("duration", [8.0, 2.5])
    def test_matrix_zones_and_postes_respect_ratio_and_acceleration(self, scorer, duration):
        # Zones de base (col 9, row 4) +-1 colonne, +-2 lignes ; départs de formation lointain, médian et proche ; DC (7 m/s), MC (8), BU (9).
        for col in (8, 9, 10):
            for row in (2, 3, 4, 5, 6):
                for start in (PitchPoint(0.05, 0.5), PitchPoint(0.5, 0.2), PitchPoint(0.85, 0.8)):
                    sequence, _ = self._build(duration, scorer, start, Zone(col=col, row=row))
                    ratio, accel = self._worst_ratios(sequence)
                    assert ratio <= 0.55, (scorer, duration, col, row, start, ratio)
                    assert accel <= 1.0 + 1e-9, (scorer, duration, col, row, start, accel)

    def test_a_player_already_within_range_keeps_his_formation_position(self):
        close = PitchPoint(x=center_of(_SCORER_ZONE).x - 0.05, y=center_of(_SCORER_ZONE).y)  # 5,25 m de la zone
        sequence, pid = self._build(8.0, "bu", close)
        assert sequence.keyframes[0].players[pid] == (close.x, close.y)
        assert sequence.keyframes[-1].players[pid] == pytest.approx((center_of(_SCORER_ZONE).x, center_of(_SCORER_ZONE).y))

    def test_a_very_distant_player_is_brought_to_exactly_the_run_limit(self):
        far = PitchPoint(0.02, 0.5)
        sequence, pid = self._build(8.0, "cb0", far)
        target = center_of(_SCORER_ZONE)
        run_m = math.hypot((sequence.keyframes[0].players[pid][0] - target.x) * PITCH_LENGTH_M, (sequence.keyframes[0].players[pid][1] - target.y) * 68.0)
        limit = tpl.role_run_limit_m(self._template(8.0).roles[0].frames, 8.0, 7.0)  # DC : 7 m/s
        assert run_m == pytest.approx(limit)
        assert limit == pytest.approx(0.5 * 7.0 * 8.0)  # le ratio mord (segment 0,4 -> 1,0 : progression 0,6 en 0,6 de la durée)
        start = sequence.keyframes[0].players[pid]  # sur la droite cible -> formation
        assert (start[1] - target.y) * (far.x - target.x) == pytest.approx((start[0] - target.x) * (far.y - target.y), abs=1e-9)

    def test_a_short_segment_makes_the_acceleration_criterion_bind(self):
        frames = (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 1.0))
        assert tpl.role_run_limit_m(frames, 1.0, 9.0) == pytest.approx(2.25)  # ratio : 4,5 m ; accélération : 2,25 m
        assert tpl.role_run_limit_m(frames, 10.0, 9.0) == pytest.approx(45.0)  # ratio : 45 m ; accélération : 225 m

    def test_the_limit_takes_the_tightest_segment_and_the_optional_run_cap(self):
        frames = (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(0.1, 0.5), tpl.RoleFrame(1.0, 1.0))
        limit = tpl.role_run_limit_m(frames, 10.0, 9.0)  # segment 1 : 1 s, progression 0,5 -> min(9, 4,5) ; segment 2 : 9 s, 0,5 -> loin
        assert limit == pytest.approx(4.5)
        assert tpl.role_run_limit_m(frames, 10.0, 9.0, run_cap_m=3.0) == pytest.approx(3.0)
        assert tpl.role_run_limit_m((tpl.RoleFrame(0.0, 0.3), tpl.RoleFrame(1.0, 0.3)), 5.0, 9.0) == 0.0  # ne bouge jamais

    def test_targets(self):
        zone, assist = center_of(_SCORER_ZONE), center_of(_ASSIST_ZONE)
        event = _goal_event()
        assert tpl.geometry_target(tpl.RoleGeometry(tpl.GEOM_ZONE), event) == zone
        assert tpl.geometry_target(tpl.RoleGeometry(tpl.GEOM_ASSIST_ZONE), event) == assist
        behind = tpl.geometry_target(tpl.RoleGeometry(tpl.GEOM_BEHIND_ZONE, cap_m=10.0), event)
        assert math.hypot((behind.x - zone.x) * PITCH_LENGTH_M, (behind.y - zone.y) * 68.0) == pytest.approx(10.0)
        assert (behind.x - zone.x) * (assist.x - zone.x) + (behind.y - zone.y) * (assist.y - zone.y) > 0  # côté de la zone d'assist
        goal = tpl.geometry_target(tpl.RoleGeometry(tpl.GEOM_TOWARD_GOAL, cap_m=5.0), event)
        assert math.hypot((goal.x - zone.x) * PITCH_LENGTH_M, (goal.y - zone.y) * 68.0) == pytest.approx(5.0)
        assert goal.x > zone.x
        with pytest.raises(ValueError):
            tpl.geometry_target(tpl.RoleGeometry("inconnue"), event)

    def test_behind_zone_keeps_at_least_six_metres_from_the_zone_even_when_zone_and_assist_zone_coincide(self):
        event = GoalEvent(club_name="Test FC", scorer="bu", assist="mc0", minute=34, penalty=False, zone=_SCORER_ZONE, assist_zone=_SCORER_ZONE)
        zone = center_of(_SCORER_ZONE)
        behind = tpl.geometry_target(tpl.RoleGeometry(tpl.GEOM_BEHIND_ZONE, cap_m=30.0), event)
        assert math.hypot((behind.x - zone.x) * PITCH_LENGTH_M, (behind.y - zone.y) * 68.0) == pytest.approx(6.0)
        assert behind.x < zone.x  # sans direction, vers son propre but

    def test_build_is_deterministic(self):
        first, _ = self._build(8.0, "cb0", PitchPoint(0.1, 0.4))
        second, _ = self._build(8.0, "cb0", PitchPoint(0.1, 0.4))
        assert first.to_json() == second.to_json()

    # Chantier 1, 1c (15/10/2026) : liste DÉCROISSANTE au fil des sous-étapes (1e-1 et 1f ont retiré les leurs) -- garde-fou qu'un
    # gabarit pas encore migré ne reçoive pas de géométrie par erreur. Ne jamais revenir à "aucun gabarit" : un gabarit migré doit
    # sortir de cette liste, pas la faire disparaître. "penalty" y reste : ses supports sont désormais repositionnés (1f), mais via
    # une position de départ remplacée dans `build_penalty`, jamais via `Role.geometry` (incompatible avec `ANCHOR_LATERAL_SHIFT`).
    _NOT_YET_MIGRATED = ("coup_franc", "penalty")

    def test_templates_not_yet_migrated_carry_no_geometry(self):
        assert set(self._NOT_YET_MIGRATED) <= set(TEMPLATES)
        for name in self._NOT_YET_MIGRATED:
            assert all(role.geometry is None for role in TEMPLATES[name].roles), name


class TestTacticalSupports:
    """Chantier 1, sous-étape 1b : un rôle générique (support) dont `Role.geometry` est renseignée est tiré par `_resolve_roles` selon sa
    cible : parmi les postes attendus (repli : tous les joueurs de champ), le plus proche de la cible d'après la position de formation ;
    égalité : nom ; support1 avant support2. Sans géométrie, le tri alphabétique d'origine est conservé (aucun gabarit n'est migré)."""

    _TARGET = center_of(_SCORER_ZONE)

    def _at(self, dx_m: float, dy_m: float = 0.0) -> PitchPoint:
        return PitchPoint(x=self._TARGET.x + dx_m / PITCH_LENGTH_M, y=self._TARGET.y + dy_m / 68.0)

    def _starts(self, lineup: Lineup, **near: PitchPoint) -> dict[int, PitchPoint]:
        """Tous les joueurs loin de la cible (de plus en plus loin dans l'ordre de la compo), sauf ceux de `near` (par nom)."""
        starts = {p.id: self._at(-30.0 - 2.0 * i) for i, p in enumerate(lineup.players)}
        starts.update({next(p.id for p in lineup.players if p.name == name): point for name, point in near.items()})
        return starts

    def _support(self, name: str, postes: tuple[str, ...] = ()) -> "tpl.Role":
        frames = (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 1.0))
        return tpl.Role(name, ANCHOR_STATIC, frames, geometry=tpl.RoleGeometry(tpl.GEOM_ZONE, preferred_postes=frozenset(postes)))

    def _resolve(self, roles, starts, lineup: Lineup | None = None) -> dict[str, str]:
        lineup = lineup or _lineup()
        names = ("scorer", "assist") + tuple(r.name for r in roles)
        return {k: p.name for k, p in tpl._resolve_roles(_goal_event(), lineup, names, tuple(roles), starts).items()}

    def test_the_pool_is_filtered_by_expected_poste_before_distance(self):
        lineup = _lineup()  # le LB est le plus proche, mais seuls les DC sont attendus
        starts = self._starts(lineup, lb=self._at(-2.0), cb0=self._at(-20.0), cb1=self._at(-30.0))
        assert self._resolve([self._support("support1", ("DC",))], starts)["support1"] == "cb0"

    def test_the_nearest_player_of_the_pool_is_chosen(self):
        lineup = _lineup()
        starts = self._starts(lineup, cb0=self._at(-20.0), cb1=self._at(-12.0))
        assert self._resolve([self._support("support1", ("DC",))], starts)["support1"] == "cb1"

    def test_a_tie_is_broken_by_name(self):
        lineup = _lineup()
        starts = self._starts(lineup, cb0=self._at(-10.0, 3.0), cb1=self._at(-10.0, -3.0))  # même distance : 10,44 m
        assert self._resolve([self._support("support1", ("DC",))], starts)["support1"] == "cb0"
        starts = self._starts(lineup, cb0=self._at(-10.0, -3.0), cb1=self._at(-10.0, 3.0))
        assert self._resolve([self._support("support1", ("DC",))], starts)["support1"] == "cb0"  # indépendant de la position

    def test_an_empty_pool_falls_back_to_every_field_player(self):
        lineup = _lineup()  # aucun ATT dans la compo : le MDC, le plus proche, est tiré
        starts = self._starts(lineup, mdc=self._at(-5.0), cb0=self._at(-15.0))
        assert self._resolve([self._support("support1", ("ATT",))], starts)["support1"] == "mdc"

    def test_without_expected_postes_every_field_player_is_a_candidate(self):
        lineup = _lineup()
        starts = self._starts(lineup, ag=self._at(-4.0))
        assert self._resolve([self._support("support1")], starts)["support1"] == "ag"

    def test_support1_is_drawn_before_support2_whatever_the_order_of_the_roles(self):
        lineup = _lineup()
        starts = self._starts(lineup, cb0=self._at(-20.0), cb1=self._at(-10.0))
        for roles in (
            [self._support("support1", ("DC",)), self._support("support2", ("DC",))],
            [self._support("support2", ("DC",)), self._support("support1", ("DC",))],
        ):
            resolved = self._resolve(roles, starts)
            assert (resolved["support1"], resolved["support2"]) == ("cb1", "cb0")

    def test_a_support_is_never_the_scorer_the_assist_a_keeper_or_already_drawn(self):
        lineup = _lineup()  # buteur bu, passeur mc0 : tous les deux, avec le gardien, sont les plus proches de la cible
        starts = self._starts(lineup, bu=self._at(-1.0), mc0=self._at(-2.0), gk=self._at(-3.0), cb0=self._at(-20.0), cb1=self._at(-21.0))
        resolved = self._resolve([self._support("support1"), self._support("support2")], starts)
        assert {resolved["support1"], resolved["support2"]}.isdisjoint({"bu", "mc0", "gk"})
        assert resolved["support1"] != resolved["support2"]

    def test_a_substitute_is_a_candidate_and_a_player_without_position_is_not(self):
        from dataclasses import replace

        lineup = replace(_lineup(), substitutes=[_player("DC", 70.0, "sub", 12)])
        starts = {**self._starts(lineup, cb0=self._at(-20.0)), 12: self._at(-8.0)}
        assert self._resolve([self._support("support1", ("DC",))], starts, lineup)["support1"] == "sub"
        del starts[12]
        assert self._resolve([self._support("support1", ("DC",))], starts, lineup)["support1"] == "cb0"
        only_scorer_and_assist = {p.id: self._at(-10.0) for p in lineup.players if p.name in ("bu", "mc0")}
        assert "support1" not in self._resolve([self._support("support1")], only_scorer_and_assist, lineup)

    def test_resolution_is_deterministic(self):
        lineup = _lineup()
        starts = self._starts(lineup, cb0=self._at(-10.0, 3.0), cb1=self._at(-10.0, -3.0))
        roles = [self._support("support1", ("DC",)), self._support("support2")]
        assert self._resolve(roles, starts) == self._resolve(roles, starts)

    def test_build_from_template_uses_the_tactical_draw(self):
        lineup = _lineup()
        times = (0.0, 1.0)
        template = tpl.Template(
            name="geom_test", weight=1.0, duration=8.0, tags=tuple((t, "x") for t in times), ball_owner=tuple((t, "scorer") for t in times),
            roles=(
                tpl.Role("scorer", ANCHOR_STATIC, (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 1.0))),
                self._support("support1", ("DC",)),
            ),
            context_score=lambda _: 1.0, ground_control=False,
        )
        starts = self._starts(lineup, cb0=self._at(-20.0), cb1=self._at(-12.0))
        assert tpl.build_from_template(template, _goal_event(), lineup, starts).meta["roles"]["support1"] == "cb1"

    @pytest.mark.parametrize("name", ["contre_attaque", "construction_placee", "corner"])
    def test_support1_is_drawn_tactically_on_the_real_migrated_templates(self, name):
        # Chantier 1, 1d (15/10/2026) : support1 de contre_attaque/construction_placee est tactique (postes attendus DC/LB/RB/MDC/MC).
        # Chantier 1, 1f (15/10/2026) : support1 de corner aussi (postes attendus DC/BU/SA/ATT, cible GEOM_BEHIND_ZONE plutôt que
        # GEOM_ZONE -- le DC le plus proche de la zone de tir reste le DC le plus proche de la cible recalée à 6 m de cette zone,
        # l'écart entre les deux DC de la fixture (8 m) est assez grand pour ne pas être affecté par ce recalage).
        lineup = _lineup()
        starts = self._starts(lineup, cb0=self._at(-20.0), cb1=self._at(-12.0))
        assert tpl.build_from_template(TEMPLATES[name], _goal_event(), lineup, starts).meta["roles"]["support1"] == "cb1"

    def test_two_tactical_roles_in_the_same_template_never_draw_the_same_player(self):
        # Chantier 1, 1e-1 (15/10/2026) : support1 ET support2 de recuperation_haute/but_gag sont désormais tactiques, PREMIER cas du
        # chantier à puiser deux rôles génériques dans le même pool de postes (tirés dans l'ordre alphabétique des noms de rôle --
        # support1 avant support2 -- chacun exclu du pool restant pour l'autre, mécanisme 1b inchangé, jamais encore exercé avec deux
        # rôles tactiques simultanés). Ce test l'exerce sur les deux gabarits réels.
        lineup = _lineup()
        starts = self._starts(lineup)
        roles = tpl.build_from_template(TEMPLATES["recuperation_haute"], _goal_event(), lineup, starts).meta["roles"]
        assert roles["support1"] != roles["support2"]
        by_name = {p.name: p for p in lineup.players}
        assert by_name[roles["support1"]].poste in {"MOC", "MC", "AG", "AD", "SA", "ATT", "BU"}
        assert by_name[roles["support2"]].poste in {"MOC", "MC", "AG", "AD", "SA", "ATT", "BU"}

    def test_two_tactical_roles_restricted_to_a_thin_pool_still_never_collide(self):
        # but_gag (postes attendus BU, SA, ATT, MOC) : la compo standard de ce fichier n'a qu'un seul de ces postes hors buteur (aucun
        # SA/ATT/MOC) -- le pool tomberait sur le repli "tous les joueurs de champ" (`_pick_support`) et ne testerait pas vraiment le
        # filtre par poste. Compo dédiée avec deux joueurs attendus (SA, ATT) en plus du buteur (BU, déjà exclu comme scorer).
        from dataclasses import replace

        base = _lineup()
        players = [
            replace(p, poste="SA") if p.name == "ag" else replace(p, poste="ATT") if p.name == "ad" else p for p in base.players
        ]
        lineup = replace(base, players=players)
        starts = self._starts(lineup)
        roles = tpl.build_from_template(TEMPLATES["but_gag"], _goal_event(), lineup, starts).meta["roles"]
        assert roles["support1"] != roles["support2"]
        by_name = {p.name: p for p in lineup.players}
        assert by_name[roles["support1"]].poste in {"BU", "SA", "ATT", "MOC"}
        assert by_name[roles["support2"]].poste in {"BU", "SA", "ATT", "MOC"}

    def test_roles_without_geometry_stay_alphabetical(self):
        lineup = _lineup()
        starts = self._starts(lineup, lb=self._at(-1.0))  # sans géométrie, la proximité n'intervient pas
        plain = tpl.Role("support1", ANCHOR_STATIC, (tpl.RoleFrame(0.0, 0.0), tpl.RoleFrame(1.0, 1.0)))
        assert self._resolve([plain], starts)["support1"] == "ad"  # premier nom par ordre alphabétique hors buteur, passeur et gardien
        assert tpl._resolve_roles(_goal_event(), lineup, ("scorer", "assist", "support1"))["support1"].name == "ad"  # appel d'avant 1b
        # Précondition de CE test : "penalty" n'est pas migré au sens de `Role.geometry` (son support1 n'en a pas -- voir
        # test_templates_not_yet_migrated_carry_no_geometry pour la liste à jour) ; ses supports ont bien une position de départ
        # remplacée par 1f (`build_penalty`/`penalty_support_position`), mais QUI tient le rôle reste alphabétique, inchangé.
        # "corner" a migré son support1 en 1f, qui ne peut donc plus servir d'exemple ici.
        assert all(role.geometry is None for role in TEMPLATES["penalty"].roles if role.name not in ("scorer", "assist"))
        sequence = BUILDERS["penalty"](_goal_event(), lineup, _start_positions(lineup))
        assert sequence.meta["roles"]["support1"] == "ad"
