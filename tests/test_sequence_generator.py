import pytest

from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.sequence_generator import (
    _GK_BASE_ADVANCE_M,
    _GK_BASE_Y,
    _GK_LATERAL_MAX_M,
    MatchState,
    _cb_line_drift,
    _forward_sign,
    _gk_base_position,
    _tactical_drift,
    deterministic_rng,
    enrich_with_background,
    generate_sequence,
)
from ligue1sim.animation.spatial import PitchLayoutState
from ligue1sim.animation.templates import player_id_of
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Zone, center_of
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
