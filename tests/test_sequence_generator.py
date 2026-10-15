import math
import pytest

from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.sequence_generator import (
    _GK_BASE_ADVANCE_M,
    _GK_BASE_Y,
    _GK_LATERAL_MAX_M,
    _MAX_DRIFT_FLOOR_M,
    _MIN_DRIFT_MAGNITUDE_M,
    MatchState,
    _cb_line_drift,
    _forward_sign,
    _gk_base_position,
    _start_positions,
    _tactical_drift,
    deterministic_rng,
    enrich_with_background,
    generate_sequence,
)
from ligue1sim.animation.spatial import PitchLayoutState
from ligue1sim.animation.templates import BUILDERS, player_id_of
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint, Zone, center_of
from ligue1sim.pitch_layout import place_starting_xi
from ligue1sim.players import Player

# Dimensions réglementaires FIFA (voir docs/visual_backlog.md #4/#5), utilisées
# ici pour vérifier que le gardien reste "entre les poteaux" et "dans sa
# surface de but" -- pas dupliquées comme constantes de prod, uniquement des
# bornes de test.
_GOAL_HALF_WIDTH_M = 7.32 / 2.0
_GOAL_AREA_DEPTH_M = 5.5


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


def _opponent_lineup() -> Lineup:
    players = [
        _player("GK", 65.0, "opp-gk", 101),
        _player("DC", 65.0, "opp-cb0", 102),
        _player("DC", 65.0, "opp-cb1", 103),
        _player("LB", 65.0, "opp-lb", 104),
        _player("RB", 65.0, "opp-rb", 105),
        _player("MDC", 65.0, "opp-mdc", 106),
        _player("MC", 65.0, "opp-mc0", 107),
        _player("MC", 65.0, "opp-mc1", 108),
        _player("AG", 65.0, "opp-ag", 109),
        _player("AD", 65.0, "opp-ad", 110),
        _player("BU", 65.0, "opp-bu", 111),
    ]
    return Lineup(club_name="Opponent FC", formation="4-3-3", players=players, rating=65.0)


def _pitch_layout_state(lineup: Lineup, *, attacking_up: bool = False) -> PitchLayoutState:
    stats = [
        PlayerMatchStat(player_name=p.name, club_name="Test FC", poste=p.poste, started=True) for p in lineup.players
    ]
    placed = place_starting_xi(stats, attacking_up=attacking_up)
    return PitchLayoutState(placed_players=tuple(placed), attacking_up=attacking_up)


def _match_state(*, goal_diff_before: int = 0, minute: int = 41, competition_type: str = "league") -> MatchState:
    return MatchState(goal_diff_before=goal_diff_before, minute=minute, competition_type=competition_type)


def _goal_event(*, scorer: str = "bu", assist: str | None = "mc0", minute: int = 41) -> GoalEvent:
    return GoalEvent(
        club_name="Test FC",
        scorer=scorer,
        assist=assist,
        minute=minute,
        penalty=False,
        zone=Zone(col=10, row=4),
        assist_zone=Zone(col=7, row=3) if assist else None,
    )


class TestGenerateSequenceHonoursTheKnownResult:
    def test_the_scorer_ends_up_at_the_real_scoring_zone(self):
        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)
        rng = deterministic_rng("match-1", 0)

        sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-1", event_index=0)

        scorer_id = player_id_of(next(p for p in lineup.players if p.name == "bu"))
        expected = center_of(event.zone)
        final_x, final_y = sequence.keyframes[-1].players[scorer_id]
        assert final_x == pytest.approx(expected.x)
        assert final_y == pytest.approx(expected.y)

    def test_the_assist_provider_ends_up_at_the_real_assist_zone_when_a_role_uses_it(self):
        # "debordement_centre_tete" utilise le rôle "assist" avec
        # ANCHOR_ASSIST jusqu'à progress=1.0 -- gabarit fixe plutôt que
        # pick_template pour un test déterministe et ciblé sur le calage
        # assist_zone (tous les gabarits n'amènent pas le passeur à 100% de
        # l'ancrage -- "une_deux" par ex. le laisse à mi-chemin, réaliste
        # pour une remise -- celui-ci si).
        from ligue1sim.animation.sequence_generator import _start_positions
        from ligue1sim.animation.templates import BUILDERS

        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)
        positions = _start_positions(lineup, state)
        sequence = BUILDERS["debordement_centre_tete"](event, lineup, positions)

        assist_id = player_id_of(next(p for p in lineup.players if p.name == "mc0"))
        expected = center_of(event.assist_zone)
        final_x, final_y = sequence.keyframes[-1].players[assist_id]
        assert final_x == pytest.approx(expected.x)
        assert final_y == pytest.approx(expected.y)

    def test_the_real_minute_is_recorded_in_the_metadata(self):
        lineup = _lineup()
        event = _goal_event(minute=57)
        state = _pitch_layout_state(lineup)
        rng = deterministic_rng("match-1", 3)

        sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-1", event_index=3)

        assert sequence.meta["minute"] == 57
        assert sequence.meta["match_id"] == "match-1"
        assert sequence.meta["event_index"] == 3

    def test_scorer_zone_is_reached_even_without_an_assist(self):
        lineup = _lineup()
        event = _goal_event(assist=None, minute=12)
        state = _pitch_layout_state(lineup)
        rng = deterministic_rng("match-2", 0)

        sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-2", event_index=0)

        scorer_id = player_id_of(next(p for p in lineup.players if p.name == "bu"))
        expected = center_of(event.zone)
        final_x, final_y = sequence.keyframes[-1].players[scorer_id]
        assert final_x == pytest.approx(expected.x)
        assert final_y == pytest.approx(expected.y)


class TestDeterministicRng:
    def test_same_match_id_and_event_index_pick_the_same_template_every_time(self):
        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)

        picked_templates = set()
        for _ in range(5):
            rng = deterministic_rng("match-7", 2)
            sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-7", event_index=2)
            picked_templates.add(sequence.meta["template"])

        assert len(picked_templates) == 1

    def test_a_different_event_index_can_pick_a_different_template(self):
        # Pas garanti à 100% (même gabarit possible par coïncidence), mais
        # sur un large échantillon d'event_index la sélection doit varier --
        # sinon ce n'est plus un tirage pondéré mais une constante.
        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)

        picked = set()
        for event_index in range(30):
            rng = deterministic_rng("match-8", event_index)
            sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-8", event_index=event_index)
            picked.add(sequence.meta["template"])

        assert len(picked) > 1


class TestMatchStateReachesPickTemplate:
    def test_goal_diff_before_changes_the_template_distribution_end_to_end(self):
        # Vérifie le branchement de bout en bout (pas seulement au niveau de
        # templates.pick_template, voir tests/test_templates.py) : le même
        # (match_id, event_index) mais un match_state différent doit pouvoir
        # aboutir à un gabarit différent, sur un échantillon assez large.
        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)

        picked_level = set()
        picked_blowout = set()
        for event_index in range(60):
            picked_level.add(
                generate_sequence(
                    event, lineup, state, _match_state(goal_diff_before=0), deterministic_rng("m", event_index),
                ).meta["template"]
            )
            picked_blowout.add(
                generate_sequence(
                    event, lineup, state, _match_state(goal_diff_before=3), deterministic_rng("m", event_index + 500),
                ).meta["template"]
            )

        assert picked_level != picked_blowout


class TestGenerateSequenceIsPureGivenAFixedRng:
    def test_same_inputs_and_seed_produce_an_identical_sequence(self):
        lineup = _lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)

        first = generate_sequence(event, lineup, state, _match_state(), deterministic_rng("match-9", 1), match_id="match-9", event_index=1)
        second = generate_sequence(event, lineup, state, _match_state(), deterministic_rng("match-9", 1), match_id="match-9", event_index=1)

        assert first.to_json() == second.to_json()


# --- Point 1 du bilan simulation physique (23/09/2026) : les 22 joueurs --


def _enriched_sequence(*, event_index: int = 0, minute: int = 41):
    lineup = _lineup()
    opponent = _opponent_lineup()
    event = _goal_event(minute=minute)
    state = _pitch_layout_state(lineup)
    rng = deterministic_rng("match-bg", event_index)
    sequence = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-bg", event_index=event_index)
    return enrich_with_background(sequence, opponent), lineup, opponent


class TestEnrichWithBackground:
    def test_templates_are_untouched_the_active_players_keep_their_generated_trajectory(self):
        # Ne modifie PAS templates.py : les positions des joueurs ACTIFS
        # (keyframes) doivent être EXACTEMENT celles que le gabarit a
        # produites, enrich_with_background ne fait que les extraire/copier,
        # jamais les recalculer.
        lineup = _lineup()
        opponent = _opponent_lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)
        rng = deterministic_rng("match-bg", 0)
        raw = generate_sequence(event, lineup, state, _match_state(), rng, match_id="match-bg", event_index=0)
        active_ids = {pid for pid, entry in raw.roster.items() if entry.role is not None}

        enriched = enrich_with_background(raw, opponent)

        for kf_raw, kf_enriched in zip(raw.keyframes, enriched.keyframes):
            for player_id in active_ids:
                assert kf_enriched.players[player_id] == kf_raw.players[player_id]

    def test_acceptance_at_least_20_players_are_referenced(self):
        # Test d'acceptation du bilan : tolérance pour les cas où un joueur
        # serait absent (compo désynchronisée), mais toujours proche des 22
        # (11 + 11) attendus pour une vraie scène façon Football Manager.
        sequence, _lineup_, _opponent = _enriched_sequence()
        tracked_ids = set(sequence.keyframes[0].players) | set(sequence.background)
        assert len(tracked_ids) >= 20

    def test_exactly_22_players_in_the_ordinary_case(self):
        sequence, lineup, opponent = _enriched_sequence()
        tracked_ids = set(sequence.keyframes[0].players) | set(sequence.background)
        assert len(tracked_ids) == len(lineup.players) + len(opponent.players) == 22

    def test_roster_has_an_entry_for_every_tracked_player_with_the_right_team_side(self):
        sequence, _lineup_, _opponent = _enriched_sequence()
        scorer_ids = {pid for pid, entry in sequence.roster.items() if entry.team_side == "scorer"}
        opponent_ids = {pid for pid, entry in sequence.roster.items() if entry.team_side == "opponent"}
        assert len(scorer_ids) == 11
        assert len(opponent_ids) == 11
        assert scorer_ids.isdisjoint(opponent_ids)

    def test_numeros_are_1_to_11_and_unique_within_each_team(self):
        sequence, _lineup_, _opponent = _enriched_sequence()
        scorer_numeros = sorted(e.numero for e in sequence.roster.values() if e.team_side == "scorer")
        opponent_numeros = sorted(e.numero for e in sequence.roster.values() if e.team_side == "opponent")
        assert scorer_numeros == list(range(1, 12))
        assert opponent_numeros == list(range(1, 12))

    def test_the_opponent_goalkeeper_wears_number_one(self):
        sequence, _lineup_, opponent = _enriched_sequence()
        gk_id = player_id_of(next(p for p in opponent.players if p.poste == "GK"))
        assert sequence.roster[gk_id].numero == 1

    def test_no_player_is_tracked_by_both_keyframes_and_background(self):
        sequence, _lineup_, _opponent = _enriched_sequence()
        assert set(sequence.keyframes[0].players).isdisjoint(sequence.background)

    def test_the_11_opponents_are_all_background_never_active(self):
        sequence, _lineup_, opponent = _enriched_sequence()
        opponent_ids = {player_id_of(p) for p in opponent.players}
        assert opponent_ids <= set(sequence.background)
        assert opponent_ids.isdisjoint(sequence.keyframes[0].players)

    def test_drift_statistics_over_100_goals_stay_close_to_formation_positions(self):
        # "Test statistique" du bilan : sur 100 buts (contexte/gabarit
        # variés via event_index), la position finale de CHAQUE joueur
        # décor doit rester cohérente avec sa position de formation -- jamais
        # à plus de ~5% du terrain (voir sequence_generator._MAX_DRIFT_MAGNITUDE),
        # jamais un téléport ailleurs sur le terrain.
        max_allowed = 0.05 + 1e-9
        for event_index in range(100):
            sequence, _lineup_, _opponent = _enriched_sequence(event_index=event_index, minute=1 + event_index % 90)
            for track in sequence.background.values():
                drift_magnitude = (track.drift[0] ** 2 + track.drift[1] ** 2) ** 0.5
                assert drift_magnitude <= max_allowed

    def test_goalkeepers_only_drift_laterally(self):
        for event_index in range(20):
            sequence, lineup, opponent = _enriched_sequence(event_index=event_index)
            for gk_lineup in (lineup, opponent):
                gk_id = player_id_of(next(p for p in gk_lineup.players if p.poste == "GK"))
                if gk_id in sequence.background:
                    assert sequence.background[gk_id].drift[0] == 0.0


class TestTacticalDrift:
    """Point 2 du brief du 23/09/2026 : les règles de drift sont réglées PAR
    RÔLE TACTIQUE, pas uniformément "vers le ballon" -- ces tests vérifient
    les invariants tactiques eux-mêmes (pas juste l'absence de crash), sur
    un échantillon de joueurs pour absorber le choix seedé (ailier/BU:
    tient/appel)."""

    _NO_CB_DRIFT = (0.0, 0.0)
    _BALL_ON_THE_RIGHT = (0.9, 0.8)  # y=0.8 > 0.5 -- ballon côté droit
    _BALL_ON_THE_LEFT = (0.9, 0.2)  # y=0.2 < 0.5 -- ballon côté gauche

    def test_winger_on_the_ball_side_drifts_towards_the_ball(self):
        # AD (y=0.75, même côté que le ballon à 0.8) : soutien proche du
        # porteur, en x ET en y.
        for player_id in range(20):
            dx, dy = _tactical_drift("AD", player_id, "scorer", (0.6, 0.75), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
            assert dx > 0  # ballon plus avancé (x=0.9 > 0.6)
            assert dy >= 0  # ballon du même côté (y=0.8 > 0.75) ou déjà aligné

    def test_winger_off_the_ball_side_never_drifts_toward_the_ball_laterally(self):
        # AG (y=0.25) alors que le ballon est à droite (y=0.8) : "tient la
        # largeur" (s'éloigne du centre, donc du ballon) OU appel en
        # profondeur (dy=0) -- jamais un dy qui le rapproche du ballon.
        for player_id in range(30):
            dx, dy = _tactical_drift("AG", player_id, "scorer", (0.5, 0.25), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
            assert dy <= 0  # jamais vers le ballon (y croissant) -- 0 (appel) ou négatif (tient la largeur, s'écarte)

    def test_winger_off_the_ball_side_forward_run_is_never_backwards(self):
        for team_side in ("scorer", "opponent"):
            forward = _forward_sign(team_side)
            for player_id in range(30):
                dx, _dy = _tactical_drift("AD", player_id, team_side, (0.5, 0.25), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
                assert dx * forward >= 0  # jamais vers son propre but

    def test_striker_never_moves_back_towards_its_own_goal(self):
        for team_side in ("scorer", "opponent"):
            forward = _forward_sign(team_side)
            for poste in ("BU", "SA", "ATT"):
                for player_id in range(20):
                    dx, dy = _tactical_drift(poste, player_id, team_side, (0.8, 0.5), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
                    assert dx * forward >= 0
                    assert dy == 0.0

    def test_fullback_off_the_ball_side_tucks_inside_never_towards_the_ball(self):
        # RB (y=0.25) alors que le ballon est à droite (y=0.8, donc du côté
        # du LB) : rentre dans l'axe (vers 0.5), jamais vers le ballon (0.8).
        for poste in ("LB", "RB"):
            dx, dy = _tactical_drift(poste, 1, "scorer", (0.7, 0.25), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
            assert dx == 0.0
            assert dy > 0  # vers 0.5, donc croissant depuis 0.25

    def test_fullback_on_the_ball_side_pushes_up_only_when_attacking(self):
        # LB (y=0.75, même côté que le ballon à 0.8).
        forward = _forward_sign("scorer")
        dx_attacking, _dy = _tactical_drift("LB", 1, "scorer", (0.5, 0.75), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
        assert dx_attacking * forward > 0  # monte

        dx_defending, dy_defending = _tactical_drift("RB", 1, "opponent", (0.5, 0.75), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
        assert dx_defending == 0.0  # ne monte pas en phase défensive
        assert abs(dy_defending) <= 0.02  # couvre sur place, léger ajustement latéral seulement

    def test_the_whole_center_back_line_shares_the_exact_same_drift(self):
        # Compactage de ligne (Point 2) : PAS un drift individuel par DC.
        cb_drift = _cb_line_drift("team-x", avg_cb_y=0.4, ball_y=0.7)
        for player_id, start in ((2, (0.15, 0.35)), (3, (0.15, 0.45))):
            assert _tactical_drift("DC", player_id, "scorer", start, self._BALL_ON_THE_RIGHT, cb_drift) == cb_drift

    def test_center_back_line_compacts_towards_the_ball_side(self):
        cb_drift_right = _cb_line_drift("team-x", avg_cb_y=0.4, ball_y=0.8)
        cb_drift_left = _cb_line_drift("team-x", avg_cb_y=0.4, ball_y=0.1)
        assert cb_drift_right[1] > 0  # ballon à droite (y augmente) -> ligne se décale vers y croissant
        assert cb_drift_left[1] < 0

    def test_goalkeeper_never_moves_off_its_line(self):
        for player_id in range(10):
            dx, _dy = _tactical_drift("GK", player_id, "scorer", (0.02, 0.5), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
            assert dx == 0.0

    def test_goalkeeper_lateral_shift_never_exceeds_its_dedicated_cap(self):
        # Brief "gardien actif" 1/2 (24/09/2026), Tâche 2 -- amplitude
        # dédiée (_GK_LATERAL_MAX_M), distincte des fourchettes tactiques
        # "données par Olivier" testées ci-dessus pour les autres postes.
        max_shift_normalized = _GK_LATERAL_MAX_M / PITCH_WIDTH_M
        for player_id in range(50):
            _dx, dy = _tactical_drift("GK", player_id, "scorer", (0.028, 0.5), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
            assert abs(dy) <= max_shift_normalized + 1e-9

    def test_center_mid_moves_towards_the_ball_in_both_axes(self):
        dx, dy = _tactical_drift("MC", 1, "scorer", (0.4, 0.4), self._BALL_ON_THE_RIGHT, self._NO_CB_DRIFT)
        assert dx > 0
        assert dy > 0

    def test_opponent_fullbacks_never_push_forward_end_to_end(self):
        # `team_side="opponent"` désigne, dans ce modèle, l'équipe qui
        # ENCAISSE le but -- toujours en phase défensive sur cette séquence
        # précise (le modèle ne capture qu'une seule phase de jeu, voir
        # docs/simulation_physique_archi.md) : ses latéraux ne "montent"
        # donc jamais, quel que soit le côté du ballon, sur un vrai but
        # généré de bout en bout.
        sequence, _lineup_, opponent = _enriched_sequence()
        for player in opponent.players:
            if player.poste not in ("LB", "RB"):
                continue
            player_id = player_id_of(player)
            if player_id not in sequence.background:
                continue
            dx, _dy = sequence.background[player_id].drift
            assert dx == 0.0


# --- Brief "gardien actif" 1/2 (24/09/2026) : position de base + réaction --
# latérale passive. Le gardien reste un joueur "décor" (voir bloc de
# constantes _GK_* dans sequence_generator.py) -- ces tests couvrent (1) le
# calcul de sa position de base (`_gk_base_position`), (2) le fait qu'il ne
# sort jamais de sa surface ni des poteaux une fois le drift appliqué, (3)
# que son déplacement reste progressif -- ce dernier point s'appuie sur le
# mécanisme générique `BackgroundTrack`/`motion._background_position_at`,
# DÉJÀ testé indépendamment (voir tests/test_motion.py::TestBackgroundInterpolation)
# : le test ci-dessous vérifie seulement que LE GARDIEN emprunte bien ce
# mécanisme de bout en bout, pas la formule d'accélération elle-même.


class TestTacticalDriftVariesByEvent:
    """Phase 6, B6-c : le tirage de drift est clé `player_id|event_ref|sel` -- un même joueur dérive différemment d'un
    événement à l'autre, dans les mêmes fourchettes qu'avant."""

    _BALL = (0.9, 0.8)
    _NO_CB_DRIFT = (0.0, 0.0)

    def test_same_player_drifts_differently_on_different_events(self):
        for poste, start in (("MC", (0.4, 0.4)), ("AD", (0.6, 0.75)), ("BU", (0.7, 0.25)), ("RB", (0.5, 0.75))):
            drifts = {
                _tactical_drift(poste, 7, "scorer", start, self._BALL, self._NO_CB_DRIFT, f"goal:Test FC:p{i}:{i + 1}")
                for i in range(30)
            }
            assert len(drifts) >= 25, (poste, len(drifts))

    def test_is_deterministic_for_a_player_and_an_event(self):
        args = ("MC", 7, "scorer", (0.4, 0.4), self._BALL, self._NO_CB_DRIFT, "goal:Test FC:p1:12")
        assert _tactical_drift(*args) == _tactical_drift(*args)

    def test_amplitudes_are_unchanged(self):
        # Mêmes bornes qu'avant B6-c (voir TestTacticalDrift) : milieu -> vers le ballon, jamais au-delà du plafond de drift.
        for i in range(200):
            dx, dy = _tactical_drift("MC", i, "scorer", (0.4, 0.4), self._BALL, self._NO_CB_DRIFT, f"goal:Test FC:p{i}:{i % 90 + 1}")
            assert dx > 0 and dy >= 0
            assert math.hypot(dx, dy) <= 0.05 + 1e-9

    def test_enrich_with_background_uses_the_sequence_event_ref(self):
        from ligue1sim.animation.sequence_generator import _event_unit

        assert _event_unit(7, "goal:A:x:1", "drift_x") != _event_unit(7, "goal:B:y:2", "drift_x")
        assert _event_unit(7, "goal:A:x:1", "drift_x") != _event_unit(7, "goal:A:x:1", "drift_y")


class TestGkBasePosition:
    def test_scorer_side_goalkeeper_sits_in_front_of_its_own_goal_line_at_x_zero(self):
        x, y = _gk_base_position("scorer")
        assert x == pytest.approx(_GK_BASE_ADVANCE_M / PITCH_LENGTH_M)
        assert y == _GK_BASE_Y

    def test_opponent_goalkeeper_sits_in_front_of_its_own_goal_line_at_x_one(self):
        x, y = _gk_base_position("opponent")
        assert x == pytest.approx(1.0 - _GK_BASE_ADVANCE_M / PITCH_LENGTH_M)
        assert y == _GK_BASE_Y

    def test_base_is_centered_between_the_posts(self):
        assert _GK_BASE_Y == 0.5

    def test_base_advance_stays_within_the_goal_area_depth(self):
        assert 0.0 < _GK_BASE_ADVANCE_M < _GOAL_AREA_DEPTH_M

    def test_lateral_cap_never_reaches_the_posts(self):
        assert 0.0 < _GK_LATERAL_MAX_M < _GOAL_HALF_WIDTH_M


class TestGoalkeepersStartAtTheirBasePosition:
    def test_both_goalkeepers_start_a_few_meters_forward_and_centered(self):
        sequence, lineup, opponent = _enriched_sequence()
        scorer_gk_id = player_id_of(next(p for p in lineup.players if p.poste == "GK"))
        opponent_gk_id = player_id_of(next(p for p in opponent.players if p.poste == "GK"))

        assert sequence.background[scorer_gk_id].start == pytest.approx(_gk_base_position("scorer"))
        assert sequence.background[opponent_gk_id].start == pytest.approx(_gk_base_position("opponent"))


class TestGoalkeeperStaysWithinItsGoalAreaAndPosts:
    def test_never_passes_the_posts_or_leaves_the_goal_area_over_100_goals(self):
        # Même protocole que test_drift_statistics_over_100_goals_stay_close_to_formation_positions
        # ci-dessus, ciblé sur l'invariant propre au gardien : sa position
        # finale (base + drift) ne doit JAMAIS dépasser les poteaux ni
        # sortir de sa surface de but, quel que soit le tirage.
        for event_index in range(100):
            sequence, lineup, opponent = _enriched_sequence(event_index=event_index, minute=1 + event_index % 90)
            for gk_lineup, own_goal_x in ((lineup, 0.0), (opponent, 1.0)):
                gk_id = player_id_of(next(p for p in gk_lineup.players if p.poste == "GK"))
                if gk_id not in sequence.background:
                    continue
                track = sequence.background[gk_id]
                final_x = track.start[0] + track.drift[0]
                final_y = track.start[1] + track.drift[1]

                depth_from_own_line_m = abs(final_x - own_goal_x) * PITCH_LENGTH_M
                assert depth_from_own_line_m <= _GOAL_AREA_DEPTH_M + 1e-9

                lateral_shift_m = abs(final_y - 0.5) * PITCH_WIDTH_M
                assert lateral_shift_m <= _GK_LATERAL_MAX_M + 1e-6
                assert lateral_shift_m < _GOAL_HALF_WIDTH_M


class TestGoalkeeperLateralReactionIsProgressive:
    def test_the_conceding_goalkeeper_moves_smoothly_not_instantly_towards_its_final_position(self):
        # Cherche un tirage où le gardien adverse a effectivement un drift
        # latéral non nul (sinon rien à observer) -- amplitude déterministe
        # par joueur (voir _deterministic_unit), donc pas garanti dès le
        # premier event_index.
        for event_index in range(30):
            sequence, _lineup_, opponent = _enriched_sequence(event_index=event_index)
            gk_id = player_id_of(next(p for p in opponent.players if p.poste == "GK"))
            track = sequence.background.get(gk_id)
            if track is None or track.drift[1] == 0.0:
                continue

            y_start = interpolate(sequence, 0.0).players[gk_id].y
            y_mid = interpolate(sequence, sequence.duration / 2.0).players[gk_id].y
            y_end = interpolate(sequence, sequence.duration).players[gk_id].y

            assert y_start == pytest.approx(track.start[1])
            assert y_end == pytest.approx(track.start[1] + track.drift[1])
            # Progressif : à mi-parcours, ni encore à sa position de base ni
            # déjà arrivé à sa position finale -- pas de saut instantané.
            assert min(y_start, y_end) < y_mid < max(y_start, y_end)
            return

        pytest.fail(
            "aucun des 30 tirages n'a produit de drift latéral pour le gardien adverse -- "
            "amplitude ou logique de _tactical_drift à revérifier"
        )


class TestDriftFloor:
    """Fix "enforce 0.5m minimum for all figurants" (24/09/2026), voir
    docs/render_diagnostic.md, Problème 2 réévalué en majeur -- sur les 12
    gabarits réels, aucun figurant (`sequence.background`) ne doit avoir un
    drift de magnitude < `_MIN_DRIFT_MAGNITUDE_M`, quel que soit le tirage
    déterministe par joueur."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_every_figurant_drift_meets_the_minimum(self, name):
        lineup = _lineup()
        opponent = _opponent_lineup()
        event = _goal_event()
        state = _pitch_layout_state(lineup)
        positions = _start_positions(lineup, state)
        sequence = BUILDERS[name](event, lineup, positions)
        sequence = enrich_with_background(sequence, opponent)

        for player_id, track in sequence.background.items():
            dx, dy = track.drift
            magnitude_m = (dx * PITCH_LENGTH_M) ** 2 + (dy * PITCH_WIDTH_M) ** 2
            magnitude_m **= 0.5
            entry = sequence.roster[player_id]
            assert magnitude_m >= _MIN_DRIFT_MAGNITUDE_M - 1e-9, (
                f"{name} : figurant {player_id} ({entry.team_side}, {entry.poste}, #{entry.numero}) "
                f"drift={magnitude_m:.4f} m, sous le plancher {_MIN_DRIFT_MAGNITUDE_M} m"
            )


class TestDriftFloorVariesByEvent:
    """Phase 6, B6-c, décision A3 : le plancher est tiré dans [0,2 ; 0,5] m par couple (joueur, événement) -- plus de valeur fixe à
    0,5 m qui rendait identiques 20 % des dérives d'un événement à l'autre."""

    def test_the_floor_range_is_0_2_to_0_5_m(self):
        assert (_MIN_DRIFT_MAGNITUDE_M, _MAX_DRIFT_FLOOR_M) == (0.2, 0.5)

    def test_a_tiny_drift_is_raised_to_a_floor_inside_the_range_and_varies_by_event(self):
        from ligue1sim.animation.sequence_generator import _floor_drift_magnitude

        floors = set()
        for i in range(200):
            dx, dy = _floor_drift_magnitude(0.0, 0.0, 7, f"goal:Test FC:p{i}:{i % 90 + 1}")
            floors.add(round(abs(dy) * PITCH_WIDTH_M, 9))
            assert _MIN_DRIFT_MAGNITUDE_M - 1e-9 <= abs(dy) * PITCH_WIDTH_M <= _MAX_DRIFT_FLOOR_M + 1e-9
            assert dx == 0.0  # cas dégénéré : latéral seulement
        assert len(floors) >= 190  # plancher continu, quasi aucune collision

    def test_a_drift_above_the_largest_floor_is_never_modified(self):
        from ligue1sim.animation.sequence_generator import _floor_drift_magnitude

        dx, dy = 0.02, 0.01  # ~2,1 m en x : au-dessus de 0,5 m
        for i in range(50):
            assert _floor_drift_magnitude(dx, dy, 7, f"goal:Test FC:p{i}:{i + 1}") == (dx, dy)

    def test_a_non_degenerate_drift_keeps_its_direction_when_floored(self):
        from ligue1sim.animation.sequence_generator import _floor_drift_magnitude

        dx, dy = 0.0001, 0.0002  # direction (1, 2), ~0,03 m : sous tous les planchers
        for i in range(50):
            fx, fy = _floor_drift_magnitude(dx, dy, 3, f"goal:Test FC:p{i}:{i + 1}")
            assert fx > 0 and fy / fx == pytest.approx(dy / dx)  # mise à l'échelle uniforme : même direction
            magnitude_m = math.hypot(fx * PITCH_LENGTH_M, fy * PITCH_WIDTH_M)
            assert _MIN_DRIFT_MAGNITUDE_M - 1e-9 <= magnitude_m <= _MAX_DRIFT_FLOOR_M + 1e-9


class TestFreeKickWallGuard:
    """Phase 6, B7-b, garde-fou A3 : sur toute la durée d'un coup franc, aucun joueur du mur (`_free_kick_wall`) n'est à moins de 1,5 m d'un
    autre joueur -- `motion._apply_avoidance` n'a donc jamais à le pousser. Positions BRUTES (`_raw_position_at`) : `interpolate` applique
    l'évitement, qui masquerait une collision."""

    def test_the_wall_stays_at_least_1_5_m_from_every_other_player_for_the_whole_clip(self):
        from ligue1sim.animation.motion import _raw_position_at
        from ligue1sim.animation.sequence_generator import _free_kick_wall, _opponent_positions

        lineup, opponent = _lineup(), _opponent_lineup()
        by_id = {player_id_of(p): p for p in opponent.players}
        for minute in range(1, 91):
            sequence = BUILDERS["coup_franc"](_goal_event(assist=None, minute=minute), lineup, _start_positions(lineup, _pitch_layout_state(lineup)))
            members, _drift = _free_kick_wall(sequence, _opponent_positions(opponent), by_id)
            assert 3 <= len(members) <= 5
            enriched = enrich_with_background(sequence, opponent)
            everyone = set(enriched.keyframes[0].players) | set(enriched.background)
            for step in range(101):
                t = sequence.duration * step / 100
                positions = {pid: _raw_position_at(enriched, pid, t) for pid in everyone}
                for wall_pid in members:
                    wx, wy = positions[wall_pid]
                    for other, (ox, oy) in positions.items():
                        if other != wall_pid:
                            d = math.hypot((wx - ox) * PITCH_LENGTH_M, (wy - oy) * PITCH_WIDTH_M)
                            assert d >= 1.5, (minute, round(t, 2), wall_pid, other, d)


class TestFreeKickWall:
    """Phase 6, B7-b : mur d'un coup franc direct -- 3 / 4 / 5 adversaires de champ à 9,15 m du ballon sur la ligne ballon -> but, espacés de
    1,5 m + 1 µm, dérive latérale PARTAGÉE de 0,2 à 0,5 m ; les autres gabarits ne sont pas touchés. Le garde-fou de non-collision est dans
    `TestFreeKickWallGuard`."""

    _MINUTES = range(1, 91)

    def _enriched(self, minute):
        from ligue1sim.animation.motion import _raw_position_at  # positions BRUTES : `interpolate` applique l'évitement, qui masquerait une collision
        from ligue1sim.animation.sequence_generator import _free_kick_wall, _opponent_positions

        lineup, opponent = _lineup(), _opponent_lineup()
        sequence = BUILDERS["coup_franc"](_goal_event(assist=None, minute=minute), lineup, _start_positions(lineup, _pitch_layout_state(lineup)))
        opp_positions = _opponent_positions(opponent)
        by_id = {player_id_of(p): p for p in opponent.players}
        members, drift = _free_kick_wall(sequence, opp_positions, by_id)
        enriched = enrich_with_background(sequence, opponent)
        return sequence, enriched, members, drift, _raw_position_at

    @staticmethod
    def _metres(point):
        return point[0] * PITCH_LENGTH_M, point[1] * PITCH_WIDTH_M

    def test_size_follows_the_distance_rule_and_the_goalkeeper_is_excluded(self):
        sizes = set()
        for minute in self._MINUTES:
            sequence, enriched, members, _drift, _raw = self._enriched(minute)
            ball = sequence.keyframes[0].ball
            distance_m = math.hypot((1.0 - ball.x) * PITCH_LENGTH_M, (0.5 - ball.y) * PITCH_WIDTH_M)
            expected = 5 if distance_m <= 20.0 else 4 if distance_m <= 26.0 else 3
            assert len(members) == expected, (minute, distance_m, len(members))
            assert all(enriched.roster[pid].poste != "GK" for pid in members)
            sizes.add(expected)
        assert sizes == {3, 4, 5}

    def test_the_wall_is_aligned_at_9_15_m_on_the_ball_goal_line_with_1_5_m_spacing_for_the_whole_clip(self):
        for minute in self._MINUTES:
            sequence, enriched, members, _drift, raw = self._enriched(minute)
            ball = self._metres((sequence.keyframes[0].ball.x, sequence.keyframes[0].ball.y))
            goal = (PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)
            line = math.hypot(goal[0] - ball[0], goal[1] - ball[1])
            ux, uy = (goal[0] - ball[0]) / line, (goal[1] - ball[1]) / line
            for t in (0.0, sequence.duration / 2.0, sequence.duration):
                points = sorted((self._metres(raw(enriched, pid, t)) for pid in members), key=lambda p: -uy * p[0] + ux * p[1])
                centre = (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))
                for p in points:  # perpendiculaire à la ligne du tir : projection sur l'axe du tir identique pour tous
                    assert (p[0] - ball[0]) * ux + (p[1] - ball[1]) * uy == pytest.approx(9.15, abs=0.6)  # la dérive (<= 0,5 m) est latérale
                for a, b in zip(points, points[1:]):
                    assert math.hypot(b[0] - a[0], b[1] - a[1]) == pytest.approx(1.5 + 1e-6, abs=1e-9), (minute, t)
                assert abs((centre[0] - ball[0]) * -uy + (centre[1] - ball[1]) * ux) <= 0.5 + 1e-6  # centré sur la ligne, au décalage de dérive près

    def test_the_drift_is_shared_lateral_and_respects_the_floor(self):
        for minute in self._MINUTES:
            sequence, enriched, members, drift, _raw = self._enriched(minute)
            assert members
            for pid in members:
                assert enriched.background[pid].drift == drift
            magnitude_m = math.hypot(drift[0] * PITCH_LENGTH_M, drift[1] * PITCH_WIDTH_M)
            assert _MIN_DRIFT_MAGNITUDE_M - 1e-9 <= magnitude_m <= _MAX_DRIFT_FLOOR_M + 1e-9
            ball = sequence.keyframes[0].ball
            to_goal = ((1.0 - ball.x) * PITCH_LENGTH_M, (0.5 - ball.y) * PITCH_WIDTH_M)
            along_m = (drift[0] * PITCH_LENGTH_M * to_goal[0] + drift[1] * PITCH_WIDTH_M * to_goal[1]) / math.hypot(*to_goal)
            assert abs(along_m) < 1e-9  # latérale : aucune composante le long du tir

    def test_other_templates_are_untouched(self):
        lineup, opponent = _lineup(), _opponent_lineup()
        for name in sorted(BUILDERS):
            if name == "coup_franc":
                continue
            sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup, _pitch_layout_state(lineup)))
            tracks = enrich_with_background(sequence, opponent).background
            assert all(math.hypot(t.drift[0] * PITCH_LENGTH_M, t.drift[1] * PITCH_WIDTH_M) >= _MIN_DRIFT_MAGNITUDE_M - 1e-9 for t in tracks.values())


class TestFreeKickWallBlocksTackleAndClearance:
    """Phase 6, B7-c : un coup franc d'issue `tacle` / `degagement` est BLOQUÉ par le mur -- le ballon part vers le mur, le heurte à moins
    de 2,0 m de haut et dans l'emprise du mur, puis repart vers le terrain (restitution 0,30 à 0,50, d'au moins 1 m/s). Les autres issues
    (décidées en amont) et les autres gabarits ne changent pas. Trace : l'événement `degagement` existant, placé au point d'impact."""

    _MINUTES = range(1, 91)

    @staticmethod
    def _plan(minute, outcome, gabarit="coup_franc"):
        from ball_events import plan_ball_events

        lineup = _lineup()
        sequence = BUILDERS[gabarit](_goal_event(assist=None, minute=minute), lineup, _start_positions(lineup, _pitch_layout_state(lineup)), outcome)
        return sequence, plan_ball_events(sequence, outcome, minute, "bu", None)

    def test_every_tackle_and_clearance_is_blocked_by_the_wall(self):
        for minute in self._MINUTES:
            for outcome in ("tacle", "degagement"):
                sequence, plan = self._plan(minute, outcome)
                assert plan.trajectory is not None and plan.trajectory.surface == "wall", (minute, outcome)
                assert plan.events[0].type == "degagement" and plan.events[0].last_toucher == "defenseur"

    def test_the_impact_is_on_the_wall_face_inside_its_footprint_and_below_the_top(self):
        for minute in self._MINUTES:
            for outcome in ("tacle", "degagement"):
                sequence, plan = self._plan(minute, outcome)
                spot = sequence.keyframes[-1].ball
                hit_x, hit_y, hit_z = plan.trajectory.contact
                goal = (PITCH_LENGTH_M - spot.x * PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0 - spot.y * PITCH_WIDTH_M)
                norm = math.hypot(*goal)
                along = ((hit_x - spot.x) * PITCH_LENGTH_M * goal[0] + (hit_y - spot.y) * PITCH_WIDTH_M * goal[1]) / norm
                lateral = (-(hit_x - spot.x) * PITCH_LENGTH_M * goal[1] + (hit_y - spot.y) * PITCH_WIDTH_M * goal[0]) / norm
                size = 5 if norm <= 20.0 else 4 if norm <= 26.0 else 3
                assert along == pytest.approx(9.15 - 0.25, abs=1e-6)  # face du mur côté tireur (épaisseur 0,5 m)
                assert abs(lateral) <= size * 0.75 - 0.5 + 1e-9
                assert 0.3 - 1e-9 <= hit_z <= 1.7 + 1e-9  # sous le haut du mur (1,80 m + marge 0,20 m)
                assert plan.events[0].t == pytest.approx(sequence.duration + plan.trajectory.arcs[0].duration)
                assert (plan.events[0].x, plan.events[0].y) == pytest.approx((hit_x, hit_y))

    def test_the_ball_leaves_toward_the_pitch_with_the_validated_restitution(self):
        for minute in self._MINUTES:
            for outcome in ("tacle", "degagement"):
                sequence, plan = self._plan(minute, outcome)
                arrival = plan.trajectory.arcs[0].at(plan.trajectory.arcs[0].duration)[1]
                exit_x, exit_y, _ = plan.trajectory.exit_velocity
                assert exit_x <= -1.0 + 1e-9, (minute, outcome, exit_x)  # vers le terrain, au moins 1 m/s
                assert 0.30 - 1e-9 <= math.hypot(exit_x, exit_y) / math.hypot(arrival[0], arrival[1]) <= 0.50 + 1e-9
                assert plan.end_tau > 0.0

    def test_the_wall_deflects_within_22_5_degrees_of_the_normal(self):
        """B7-d : normale tournée de 22,5 degrés au plus -> le ballon repart près de l'axe de retour (médiane ~22 degrés, jamais au-delà de ~61)."""
        import dataclasses

        from ball_events import plan_ball_events

        lineup = _lineup()
        starts = _start_positions(lineup, _pitch_layout_state(lineup))
        angles = []
        for club in ("A", "B", "C", "D"):
            for minute in self._MINUTES:
                event = dataclasses.replace(_goal_event(assist=None, minute=minute), club_name=f"Club{club}")
                sequence = BUILDERS["coup_franc"](event, lineup, starts, "tacle")
                exit_x, exit_y, _ = plan_ball_events(sequence, "tacle", minute, "bu", None).trajectory.exit_velocity
                spot = sequence.keyframes[-1].ball
                back = math.degrees(math.atan2(PITCH_WIDTH_M / 2.0 - spot.y * PITCH_WIDTH_M, PITCH_LENGTH_M - spot.x * PITCH_LENGTH_M)) + 180.0
                angles.append(abs((math.degrees(math.atan2(exit_y, exit_x)) - back + 180.0) % 360.0 - 180.0))
        angles.sort()
        assert 15.0 <= angles[len(angles) // 2] <= 30.0
        assert angles[-1] <= 62.0  # 2 x 22,5 degrés + angle d'arrivée (au plus ~16 degrés)
        assert sum(a > 60.0 for a in angles) / len(angles) < 0.10

    def test_the_trajectory_is_continuous_and_deterministic(self):
        sequence, plan = self._plan(41, "tacle")
        _, again = self._plan(41, "tacle")
        assert plan.trajectory == again.trajectory
        previous = plan.trajectory.state_at(0.0)
        assert (previous.x, previous.y, previous.z) == pytest.approx(
            (sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y, 0.0))  # le ballon part du point posé
        tau = 0.0
        while tau < plan.end_tau:
            tau += 1.0 / 120.0
            current = plan.trajectory.state_at(tau)
            assert math.hypot((current.x - previous.x) * PITCH_LENGTH_M, (current.y - previous.y) * PITCH_WIDTH_M) < 0.5
            previous = current

    def test_other_issues_and_other_templates_are_unchanged(self):
        from ligue1sim.animation.ball import SURFACE_BAR, SURFACE_POST

        for minute in (5, 41, 88):
            for outcome in ("but", "hors_cadre"):
                assert self._plan(minute, outcome)[1].trajectory is None  # inchangé : pas de rebond après un but ou un hors cadre
            assert self._plan(minute, "poteau")[1].trajectory.surface == SURFACE_POST
            assert self._plan(minute, "barre")[1].trajectory.surface == SURFACE_BAR
            assert self._plan(minute, "arret")[1].trajectory.surface == "keeper"
            for gabarit in ("construction_placee", "contre_attaque"):
                sequence, plan = self._plan(minute, "tacle", gabarit)
                assert plan.trajectory is None and [e.type for e in plan.events] == ["degagement"]
                assert plan.events[0].t == pytest.approx(sequence.duration)  # au point de contact, comme avant B7-c


class TestFreeKickGoalkeeper:
    """Phase 6, B7-d : gardien adverse d'un coup franc direct -- départ à 1,0-2,0 m de sa ligne (au lieu de 3,0 m), décalé de 1,0-2,0 m du
    côté du ballon, et dérive latérale cohérente avec l'issue (même logique que B6-d, `_free_kick_gk_drift`). Les autres gabarits ne changent pas."""

    _N = 4000

    @staticmethod
    def _unit(i, k):
        return (i * 0.6180339887498949 * (k + 1)) % 1.0

    def _case(self, i):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_start

        ref = f"goal:Club{i % 18}:p{i}:{i % 90 + 1}"
        ball_y = 0.5 + (self._unit(i, 1) - 0.5) * 0.7  # y du ballon posé : jusqu'à 12 m de l'axe
        start = _free_kick_gk_start(7, ref, ball_y)
        return ref, ball_y, start

    def test_start_is_1_to_2_m_from_the_line_and_1_to_2_m_off_centre_on_the_ball_side(self):
        advances = []
        for i in range(self._N):
            ref, ball_y, (x, y) = self._case(i)
            advance_m = (1.0 - x) * PITCH_LENGTH_M
            offset_m = (y - 0.5) * PITCH_WIDTH_M
            assert 1.0 - 1e-9 <= advance_m <= 2.0 + 1e-9
            assert 1.0 - 1e-9 <= abs(offset_m) <= 2.0 + 1e-9
            assert (offset_m > 0) == (ball_y > 0.5), ref
            advances.append(advance_m)
        assert abs(sorted(advances)[len(advances) // 2] - 1.5) <= 0.05  # médiane ~ 1,5 m

    def test_the_goalkeeper_of_a_free_kick_starts_there_and_other_templates_keep_the_standard_position(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_start

        lineup, opponent = _lineup(), _opponent_lineup()
        gk_id = player_id_of(next(p for p in opponent.players if p.poste == "GK"))
        for name in sorted(BUILDERS):
            sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup, _pitch_layout_state(lineup)))
            start = enrich_with_background(sequence, opponent).background[gk_id].start
            if name == "coup_franc":
                assert start == pytest.approx(_free_kick_gk_start(gk_id, sequence.event_ref, sequence.keyframes[0].ball.y))
            else:
                assert start == pytest.approx(_gk_base_position("opponent")), name

    def test_save_goes_the_right_way_and_reaches_the_ball_height(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift

        reached = 0
        for i in range(self._N):
            ref, _ball_y, (_x, start_y) = self._case(i)
            target_y = 0.5 + (self._unit(i, 2) - 0.5) * (4.0 / PITCH_WIDTH_M)  # cible d'un arrêt : +-2 m
            _, dy = _free_kick_gk_drift(7, ref, start_y, target_y, "arret")
            need = target_y - start_y
            assert dy * need >= 0.0, ref  # bon côté, toujours
            if abs(need) * PITCH_WIDTH_M <= 2.8:  # à portée (déplacement plafonné à 2,8 m) : il atteint exactement le y du ballon
                assert dy == pytest.approx(need), ref
                reached += 1
            else:
                assert abs(dy) * PITCH_WIDTH_M == pytest.approx(2.8)  # hors de portée : il va au bout de son plafond
        assert reached / self._N > 0.8

    def test_goal_beats_the_wrong_side_with_the_probability_of_the_strike_type(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift
        from ligue1sim.animation.templates import strike_type_for

        wrong = {"coup_franc_enroule": [0, 0], "coup_franc_frappe": [0, 0]}
        for i in range(self._N * 2):
            ref, _ball_y, (_x, start_y) = self._case(i)
            target_y = 0.5 + (self._unit(i, 3) - 0.5) * (7.32 / PITCH_WIDTH_M) * 0.9
            need = target_y - start_y
            if abs(need * PITCH_WIDTH_M) < 0.3:
                continue  # trop près : « côté » sans objet
            _, dy = _free_kick_gk_drift(7, ref, start_y, target_y, "but")
            counter = wrong[strike_type_for("coup_franc", ref).name]
            counter[0] += 1
            counter[1] += (dy * need < 0.0)
        for name, p in (("coup_franc_enroule", 0.35), ("coup_franc_frappe", 0.25)):
            n, k = wrong[name]
            assert abs(k / n - p) <= 0.03, (name, k / n)

    def test_miss_goes_either_side_half_of_the_time(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift

        for outcome in ("hors_cadre", "poteau", "barre"):
            toward = n = 0
            for i in range(self._N):
                ref, _ball_y, (_x, start_y) = self._case(i)
                target_y = 0.5 + (self._unit(i, 4) - 0.5) * (7.32 / PITCH_WIDTH_M)
                need = target_y - start_y
                if abs(need * PITCH_WIDTH_M) < 0.3:
                    continue
                n += 1
                toward += (_free_kick_gk_drift(7, ref, start_y, target_y, outcome)[1] * need > 0.0)
            assert abs(toward / n - 0.5) <= 0.03, (outcome, toward / n)

    def test_amplitude_never_exceeds_2_8_m_and_the_final_position_stays_within_2_5_m_of_the_centre(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift

        for outcome in ("arret", "but", "poteau", "hors_cadre", "barre", "tacle", "degagement", None):
            for i in range(self._N // 4):
                ref, _ball_y, (_x, start_y) = self._case(i)
                target_y = 0.5 + (self._unit(i, 5) - 0.5) * (14.0 / PITCH_WIDTH_M)
                _, dy = _free_kick_gk_drift(7, ref, start_y, target_y, outcome)
                assert abs(dy) * PITCH_WIDTH_M <= 2.8 + 1e-9, (outcome, ref)
                assert abs(start_y + dy - 0.5) * PITCH_WIDTH_M <= 2.5 + 1e-9, (outcome, ref)

    def test_without_outcome_the_drift_floor_is_kept(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift

        for i in range(500):
            ref, _ball_y, (_x, start_y) = self._case(i)
            _, dy = _free_kick_gk_drift(7, ref, start_y, 0.5, None)
            assert abs(dy) * PITCH_WIDTH_M >= _MIN_DRIFT_MAGNITUDE_M - 1e-9

    def test_the_enriched_goalkeeper_follows_the_function_and_has_no_depth_drift(self):
        from ligue1sim.animation.sequence_generator import _free_kick_gk_drift

        lineup, opponent = _lineup(), _opponent_lineup()
        gk_id = player_id_of(next(p for p in opponent.players if p.poste == "GK"))
        for minute in range(1, 91):
            for outcome in ("arret", "but", "hors_cadre", "tacle"):
                sequence = BUILDERS["coup_franc"](_goal_event(assist=None, minute=minute), lineup, _start_positions(lineup, _pitch_layout_state(lineup)), outcome)
                track = enrich_with_background(sequence, opponent, outcome).background[gk_id]
                expected = _free_kick_gk_drift(gk_id, sequence.event_ref, track.start[1], sequence.keyframes[-1].ball.y, outcome)
                assert track.drift == pytest.approx(expected)
                assert track.drift[0] == 0.0  # aucune sortie en profondeur (renvoyée au Bloc A)


class TestOpponentFieldTracks:
    """Phase 6, B8-b : `opponent_field_tracks` / `nearest_opponent_distance_m` recalculent, avant l'enrichissement, les pistes des adversaires de
    champ -- elles DOIVENT égaler celles que `enrich_with_background` pose dans `Sequence.background`."""

    _NAMES = ("contre_attaque", "construction_placee", "decalage_enroulee", "profondeur_1v1", "recuperation_haute", "une_deux", "corner")

    @staticmethod
    def _built(name, minute, outcome):
        lineup = _lineup()
        starts = {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
        return BUILDERS[name](_goal_event(minute=minute), lineup, starts, outcome)

    def test_tracks_equal_the_background_of_the_enriched_sequence(self):
        from ligue1sim.animation.sequence_generator import opponent_field_tracks

        opponent = _opponent_lineup()
        for name in self._NAMES:
            for minute, outcome in ((12, "but"), (34, "arret"), (77, "poteau"), (88, None)):
                sequence = self._built(name, minute, outcome)
                enriched = enrich_with_background(sequence, opponent, outcome)
                tracks = opponent_field_tracks(opponent, sequence.event_ref, (sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y))
                assert tracks, name
                for player_id, track in tracks.items():
                    assert enriched.background[player_id] == track, (name, minute, outcome, player_id)

    def test_the_goalkeeper_is_not_a_field_opponent(self):
        from ligue1sim.animation.sequence_generator import opponent_field_tracks

        tracks = opponent_field_tracks(_opponent_lineup(), "goal:Test FC:bu:41", (1.0, 0.5))
        assert 101 not in tracks and len(tracks) == 10

    def test_distance_matches_the_rendered_background_position(self):
        from ligue1sim.animation.motion import _raw_position_at
        from ligue1sim.animation.sequence_generator import nearest_opponent_distance_m, opponent_field_tracks

        opponent = _opponent_lineup()
        sequence = self._built("contre_attaque", 41, "but")
        enriched = enrich_with_background(sequence, opponent, "but")
        tracks = opponent_field_tracks(opponent, sequence.event_ref, (sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y))
        point = (0.55, 0.45)
        for t in (0.0, 0.7 * sequence.duration, sequence.duration):
            expected = min(
                math.hypot((x - point[0]) * PITCH_LENGTH_M, (y - point[1]) * PITCH_WIDTH_M)
                for x, y in (_raw_position_at(enriched, player_id, t) for player_id in tracks)
            )
            assert nearest_opponent_distance_m(tracks, point, t, sequence.duration) == pytest.approx(expected, abs=1e-9)

    def test_no_track_gives_no_distance(self):
        from ligue1sim.animation.sequence_generator import nearest_opponent_distance_m

        assert nearest_opponent_distance_m({}, (0.5, 0.5), 1.0, 5.0) is None


class TestOpponentEnJeu:
    """Étape 0b-2 du Bloc A : `en_jeu` sépare « effectif complet pour la formation » et « joueurs présents pour le rendu ». Sans lui, comportement
    historique ; avec lui, aucune ligne n'est recalée quand un titulaire sort, et un remplaçant est placé à sa propre position (reflétée)."""

    @staticmethod
    def _with_substitute():
        import dataclasses

        return dataclasses.replace(_opponent_lineup(), substitutes=[_player("BU", 65.0, "opp-sub", 112)])

    def test_without_en_jeu_nothing_changes(self):
        from ligue1sim.animation.sequence_generator import _opponent_positions

        opponent = self._with_substitute()
        default = _opponent_positions(opponent)
        assert len(default) == 11 and 112 not in default  # les remplaçants ne sont pas placés
        assert _opponent_positions(opponent, None) == default
        starters_only = {p.name: None for p in opponent.players}
        assert _opponent_positions(opponent, starters_only) == default
        sequence = TestOpponentFieldTracks._built("contre_attaque", 41, "but")
        assert enrich_with_background(sequence, opponent, "but") == enrich_with_background(sequence, opponent, "but", None)

    def test_a_missing_starter_does_not_move_the_others_and_the_entrant_gets_its_own_mirrored_position(self):
        from ligue1sim.animation.sequence_generator import _opponent_positions

        opponent = self._with_substitute()
        default = _opponent_positions(opponent)
        present = {p.name: None for p in opponent.players if p.name != "opp-mc0"}
        present["opp-sub"] = PitchPoint(x=0.75, y=0.31)
        positions = _opponent_positions(opponent, present)
        assert 107 not in positions  # opp-mc0 absent
        assert all(positions[player_id] == default[player_id] for player_id in default if player_id != 107)  # aucune ligne recalée
        assert positions[112] == PitchPoint(x=0.25, y=0.31)

    def test_enrich_places_the_entrant_and_drops_the_absent_with_stable_numbers(self):
        opponent = self._with_substitute()
        en_jeu = {p.name: None for p in opponent.players if p.name != "opp-mc0"}
        en_jeu["opp-sub"] = PitchPoint(x=0.75, y=0.31)
        sequence = TestOpponentFieldTracks._built("contre_attaque", 41, "but")
        full = enrich_with_background(sequence, opponent, "but")
        enriched = enrich_with_background(sequence, opponent, "but", en_jeu)
        assert 107 not in enriched.background and 112 in enriched.background and len(enriched.background) == len(full.background)
        assert enriched.background[112].start == (0.25, 0.31)
        assert enriched.roster[112].team_side == "opponent" and enriched.roster[112].poste == "BU"
        assert enriched.roster[102].numero == full.roster[102].numero  # numéros dérivés de l'effectif complet
        assert enriched.background[102] == full.background[102]

    def test_field_tracks_read_en_jeu_from_the_argument_or_from_the_lineup(self):
        import dataclasses

        from ligue1sim.animation.sequence_generator import opponent_field_tracks

        opponent = self._with_substitute()
        en_jeu = {p.name: None for p in opponent.players if p.name != "opp-mc0"}
        en_jeu["opp-sub"] = PitchPoint(x=0.75, y=0.31)
        sequence = TestOpponentFieldTracks._built("contre_attaque", 41, "but")
        target = (sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y)
        enriched = enrich_with_background(sequence, opponent, "but", en_jeu)
        tracks = opponent_field_tracks(opponent, sequence.event_ref, target, en_jeu)
        assert 107 not in tracks and 112 in tracks
        for player_id, track in tracks.items():
            assert enriched.background[player_id] == track

        class _Carrier(Lineup):
            pass

        carrier = _Carrier(**{f.name: getattr(opponent, f.name) for f in dataclasses.fields(Lineup)})
        object.__setattr__(carrier, "en_jeu", en_jeu)
        assert opponent_field_tracks(carrier, sequence.event_ref, target) == tracks
