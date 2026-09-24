"""Tests d'`engine/narrative_player.py` (brief "canvas player", 23/09/2026,
Tâche 3) -- `build_clips`. Mêmes helpers de simulation que
`tests/test_narrative.py` (dupliqués, pas importés depuis un autre fichier
de test -- même motif déjà établi dans ce projet, voir la docstring
d'`apps/streamlit_preview.py` sur l'indépendance volontaire des fichiers)."""

import pytest

from ligue1sim.animation import templates as templates_module
from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.sequence_generator import enrich_with_background
from ligue1sim.animation.templates import BUILDERS
from ligue1sim.clubs import Club
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup, pick_best_formation, select_best_xi
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Zone
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from narrative import BUT, build_timeline, match_result_from
from narrative_player import (
    build_clips,
    _apply_acceleration_constraint_to_frames,
    _build_clip_frames,
    _interval_events,
    _lineup_start_positions,
)

_N_MATCHES = 30


def _player(poste: str, note: float, name: str) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST")


def _squad(club_name: str, note: float = 70.0) -> list[Player]:
    squad = [_player("GK", note, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", note, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("LB", note, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", note, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", note, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("MOC", note, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", note, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", note, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", note, f"{club_name}_cf{i}") for i in range(4)]
    return squad


def _clubs() -> tuple[Club, Club]:
    return Club(name="Home FC", players=_squad("home")), Club(name="Away FC", players=_squad("away"))


def _simulate_n(n: int) -> list:
    home, away = _clubs()
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    results = []
    i = 0
    while len(results) < n:
        home_goals, away_goals, events = simulate_match(home, away, context)
        i += 1
        if events is None:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        results.append(match_result_from(match, events, home_lineup, away_lineup, date=str(i)))
    return results


class TestLineupStartPositionsRespectDeclaredFormationBands:
    """Fix "transmit band to lineup reconstruction" (24/09/2026) -- voir
    docs/render_diagnostic.md, Problème 1. `_lineup_start_positions`
    reconstruit un `PlayerMatchStat` par joueur pour `place_starting_xi` ;
    sans `band=lineup.bands.get(p.name)`, ce dernier retombe sur un
    regroupement générique GK/DEF/MID/ATT par grande famille de poste
    (`ligue1sim.players.POSITION_GROUP`), qui fusionne tous les DC/LB/RB sur
    UNE seule ligne -- sur le squad synthétique de ce fichier (4 DC/2 LB/2
    RB disponibles), la meilleure compo "4-3-3" sélectionne réellement 5
    joueurs de profil défenseur (mesuré dans le diagnostic), qui se
    retrouvaient TOUS à la même profondeur sans `band`. Avec `band`
    correctement transmis, `_formation_bands("4-3-3", 11)` assigne
    EXACTEMENT 4 slots à la ligne défensive, 3 à la ligne médiane, 3 à la
    ligne d'attaque, quel que soit le poste brut de chacun -- la répartition
    par profondeur DOIT donc être [1, 4, 3, 3] (GK/DEF/MID/ATT), jamais
    [1, 5, 2, 3] (l'ancien regroupement générique observé)."""

    def test_scorer_lineup_start_positions_group_into_4_3_3_not_a_generic_bucket(self):
        # `select_best_xi(club, "4-3-3")` directement (pas `pick_best_formation`,
        # qui choisirait adaptativement le dispositif donnant la meilleure note
        # -- pas forcement "4-3-3" pour ce squad synthetique, voir le rouge
        # observe en le testant : "4-2-3-1"). Ni l'un ni l'autre n'est modifie
        # ici, seulement appele avec un dispositif explicite.
        home, _away = _clubs()
        lineup = select_best_xi(home, "4-3-3")
        assert lineup.formation == "4-3-3", f"fixture attendue en 4-3-3, obtenu {lineup.formation!r}"

        positions = _lineup_start_positions(lineup)

        by_depth: dict[float, list[str]] = {}
        for player in lineup.players:
            x = round(positions[player.name].x, 6)
            by_depth.setdefault(x, []).append(player.name)

        line_sizes = [len(names) for _depth, names in sorted(by_depth.items())]
        assert line_sizes == [1, 4, 3, 3], (
            "lignes obtenues par profondeur croissante (GK/DEF/MID/ATT), attendu [1, 4, 3, 3] "
            f"pour un 4-3-3 -- obtenu {line_sizes} (detail : {sorted(by_depth.items())})"
        )


class TestBuildClipsScoreSequence:
    @pytest.mark.integration
    def test_build_clips_preserves_score_sequence(self):
        # Tache 3.3 -- sur plusieurs matchs (pas un seul, voir la limite
        # documentee dans narrative_timeline_schema.md/narrative_player.py :
        # un but marque par un remplacant non resolu par home_lineup/
        # away_lineup ferait manquer ce but au dernier clip retenu). Verifie
        # la monotonie sur TOUS les matchs (garantie inconditionnelle), et
        # l'egalite au score final UNIQUEMENT quand tous les buts reels sont
        # resolubles (pas une liste d'exclusion codee en dur -- un calcul
        # fait a chaque match, sur les donnees reelles produites).
        results = _simulate_n(_N_MATCHES)
        monotonicity_violations = []
        final_score_checks = 0
        final_score_violations = []

        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=None)
            if not clips:
                continue

            # Un but omis (buteur remplacant non resoluble, voir la limite
            # documentee) cree un saut LEGITIME entre deux clips retenus
            # (score_before du suivant > score_after du precedent) -- ce
            # n'est PAS une violation de monotonie, seulement une baisse le
            # serait. On aplatit la sequence complete (avant/apres de chaque
            # clip retenu, dans l'ordre) et on verifie qu'elle ne redescend
            # jamais, sans exiger de contiguite stricte entre deux clips.
            flat_scores = [score for c in clips for score in (c.score_before, c.score_after)]
            for prev, nxt in zip(flat_scores, flat_scores[1:]):
                if nxt[0] < prev[0] or nxt[1] < prev[1]:
                    monotonicity_violations.append(timeline.match_id)

            starter_names = {p.name for p in timeline.home_lineup.players} | {p.name for p in timeline.away_lineup.players}
            all_goals_resolvable = all(
                g.scorer in starter_names and (g.assist is None or g.assist in starter_names) for g in match.goals
            )
            if all_goals_resolvable:
                final_score_checks += 1
                if clips[-1].score_after != (timeline.home_goals, timeline.away_goals):
                    final_score_violations.append(timeline.match_id)

        assert not monotonicity_violations, f"score non monotone sur {monotonicity_violations[:3]}"
        assert final_score_checks > 0, "aucun match avec tous les buts resolubles -- echantillon insuffisant pour verifier l'invariant"
        assert not final_score_violations, f"score final non atteint sur {final_score_violations[:3]} (buts pourtant tous resolubles)"


class TestBuildClipsMaxOccasions:
    @pytest.mark.integration
    def test_build_clips_max_occasions(self):
        # Tache 3.4 -- sur plusieurs matchs (les timelines comptent >= 10
        # evenements par construction, voir narrative._POISSON_MIN, donc 4
        # clips resolubles doivent quasi-toujours etre atteignables).
        results = _simulate_n(_N_MATCHES)
        n_with_four = 0
        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=4)
            assert len(clips) <= 4
            minutes = [c.minute for c in clips]
            assert minutes == sorted(minutes), f"{timeline.match_id} : clips pas en ordre chronologique ({minutes})"
            if len(clips) == 4:
                n_with_four += 1
        assert n_with_four > 0, "aucun match n'a atteint 4 clips construisibles -- echantillon insuffisant"


class TestBuildClipsIntervalEvents:
    """Brief "canvas player consolidation" (23/09/2026), Tache 1."""

    def test_interval_events_populated(self):
        # Tache 1.4 -- sur 100 matchs simules, au moins X% des clips ont un
        # interval_events non vide. Utilise directement
        # narrative_player._interval_events sur la timeline BRUTE (pas
        # build_clips) : interval_events ne depend que de
        # Timeline.cards/.substitutions et des minutes des evenements, JAMAIS
        # des frames -- construire les frames de TOUS les evenements de 100
        # matchs (build_clips(..., max_occasions=None)) couterait des
        # dizaines de minutes pour un resultat statistiquement identique
        # depuis la Tache 2 (quasi aucune occasion n'est plus omise, voir
        # test_all_clips_rendered_no_omission). Reutilise la fonction REELLE
        # de production, seule la source (evenements bruts vs Clips retenus)
        # differe.
        #
        # Seuil 25% (pas 50%, brief initial -- ecarte apres escalade et
        # decision du proprietaire du 23/09/2026) : le seuil de 50% etait
        # arbitraire, fixe sans verifier la contrainte structurelle du
        # moteur de resultats (non modifiable ici, voir PRIORITE DES
        # CONTRAINTES). SUB_MIN_MINUTE=46 dans src/ligue1sim/events.py:65 --
        # les substitutions (8/match en moyenne, seule source d'interval_
        # events avec les cartons pour une bonne partie du match) ne
        # surviennent JAMAIS en 1ere mi-temps, alors que les occasions/clips
        # sont reparties sur les 90 minutes. Mesure sur 4 runs consecutifs
        # (100 matchs chacun, non seedes) : 36.0%-38.5%, jamais proche de
        # 50%. Plafond structurel, pas un bug (cartons/substitutions
        # correctement extraits de Timeline.cards/.substitutions, verifie
        # par ailleurs). A REEVALUER A LA HAUSSE quand ce brief passera a 15
        # clips couvrant les 90 minutes : les intervalles 46-90' contiendront
        # alors les substitutions et le taux remontera mecaniquement.
        results = _simulate_n(100)
        total = 0
        non_empty = 0
        for match in results:
            timeline = build_timeline(match)
            prev_minute = 0
            for event in timeline.events:
                total += 1
                if _interval_events(timeline, prev_minute, event.minute):
                    non_empty += 1
                prev_minute = event.minute

        assert total > 0
        ratio = non_empty / total
        assert ratio >= 0.25, f"ratio={ratio:.2%} ({non_empty}/{total}) sous le seuil de 25% -- a remonter"

    @pytest.mark.integration
    def test_interval_events_chronological(self):
        # Tache 1.5 -- sur les Clips REELLEMENT retenus par build_clips
        # cette fois (echantillon plus modeste pour rester rapide, voir
        # _N_MATCHES).
        results = _simulate_n(_N_MATCHES)
        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=4)
            for clip in clips:
                minutes = [item["minute"] for item in clip.interval_events]
                assert minutes == sorted(minutes), (
                    f"{timeline.match_id} clip {clip.minute}' : interval_events non trie ({minutes})"
                )


class TestNoOmissionAfterSubstitutesFix:
    """Brief "canvas player consolidation" (23/09/2026), Tache 2."""

    @pytest.mark.integration
    def test_all_clips_rendered_no_omission(self):
        # Tache 2.4 -- sur 100 matchs simules, 100% des occasions generees
        # (timeline.events) sont rendues par build_clips (aucune omission).
        results = _simulate_n(100)
        omitted: list[tuple[str, int, str, str]] = []
        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=None)
            if len(clips) != len(timeline.events):
                rendered_keys = {(c.minute, c.gabarit, c.main_player) for c in clips}
                for event in timeline.events:
                    key = (event.minute, event.gabarit, event.main_player)
                    if key not in rendered_keys:
                        omitted.append((timeline.match_id, event.minute, event.gabarit, event.main_player))

        assert not omitted, f"{len(omitted)} occasion(s) omise(s) -- exemples: {omitted[:5]}"

    @pytest.mark.integration
    def test_substitute_placed_correctly(self):
        # Tache 2.5 -- un evenement dont main_player est un remplacant
        # produit des frames valides (positions definies, dans [0, 1]).
        results = _simulate_n(100)
        checked = 0
        for match in results:
            timeline = build_timeline(match)
            substitute_names = {p.name for p in timeline.home_lineup.substitutes} | {
                p.name for p in timeline.away_lineup.substitutes
            }
            if not substitute_names:
                continue
            substitute_events = [e for e in timeline.events if e.main_player in substitute_names]
            if not substitute_events:
                continue
            clips = build_clips(timeline, max_occasions=None)
            for event in substitute_events:
                matching = [c for c in clips if c.minute == event.minute and c.main_player == event.main_player]
                assert matching, f"{timeline.match_id} : remplacant {event.main_player!r} (minute {event.minute}) omis"
                clip = matching[0]
                assert clip.frames
                # Tolerance faible (evitement des collisions entre joueurs,
                # animation.motion._apply_avoidance, peut legerement pousser
                # une position au-dela de 0/1 pres du bord du terrain) --
                # pas un test "exactement dans [0,1]", juste "pas de valeur
                # aberrante/hors carte" (None, NaN, tres hors limites).
                margin = 0.1
                for frame in clip.frames:
                    assert frame.ball is not None
                    for state in frame.players.values():
                        assert state is not None
                        assert -margin <= state.x <= 1.0 + margin, f"x={state.x} hors terrain"
                        assert -margin <= state.y <= 1.0 + margin, f"y={state.y} hors terrain"
                checked += 1
        assert checked > 0, "aucun evenement avec un remplacant comme protagoniste trouve sur 100 matchs -- echantillon insuffisant"


class TestBuildClipsFramesNeverEmpty:
    @pytest.mark.integration
    def test_no_clip_has_empty_frames(self):
        results = _simulate_n(_N_MATCHES)
        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=4)
            for clip in clips:
                assert clip.frames, f"{timeline.match_id} : clip {clip.minute}/{clip.gabarit} sans frames"
                assert clip.duration_s > 0


class TestOutcomeTransmittedToTemplate:
    """Brief "ball flight after shot" (24/09/2026), Tache 2.4 -- sur 100
    matchs, tous les appels a `templates.build_from_template` depuis
    `_build_clip_frames` recoivent bien l'`outcome` de l'evenement
    correspondant. Espionne `build_from_template` lui-meme (pas
    `BUILDERS[gabarit]`) pour verifier que le transit traverse TOUTE la
    chaine (wrapper build_xxx inclus), pas seulement l'appel de surface.
    Appelle `_build_clip_frames` directement (pas `build_clips`) pour
    garder une correspondance 1-appel-pour-1-evenement sans ambiguite
    d'ordre (build_clips peut tenter des evenements ensuite omis)."""

    @pytest.mark.integration
    def test_outcome_transmitted_to_template(self, monkeypatch):
        results = _simulate_n(100)
        original = templates_module.build_from_template
        captured: list = []

        def spy(template, event, lineup, start_positions, outcome=None):
            captured.append(outcome)
            return original(template, event, lineup, start_positions, outcome)

        monkeypatch.setattr(templates_module, "build_from_template", spy)

        checked = 0
        for match in results:
            timeline = build_timeline(match)
            for event in timeline.events:
                captured.clear()
                _build_clip_frames(timeline, event)
                assert len(captured) == 1, (
                    f"{timeline.match_id} minute={event.minute} : {len(captured)} appels a "
                    "build_from_template (attendu exactement 1 par evenement)"
                )
                assert captured[0] == event.outcome, (
                    f"{timeline.match_id} minute={event.minute} : outcome transmis {captured[0]!r} "
                    f"!= event.outcome {event.outcome!r}"
                )
                checked += 1

        assert checked > 0


# --- Brief "acceleration constraint on rendered frames" (24/09/2026) -----
# Option D : `motion.interpolate` reste pur, INTOUCHÉ, `tests/test_motion.py`
# n'est pas modifié (voir sa suite, notamment `TestImpossibleSegment`/
# `TestDeterminism`, toujours vrais tels quels). La contrainte vit dans
# `_apply_acceleration_constraint_to_frames`, appelée par `_build_clip_frames`
# -- ces tests exercent cette fonction directement sur les 12 gabarits réels
# (mêmes `BUILDERS`/`enrich_with_background` que `_build_clip_frames`
# utilise réellement), sans reconstruire tout le pipeline `Timeline`/match
# simulé -- inutile ici, la contrainte ne dépend que des frames produites.

_ACCEL_SCORER_ZONE = Zone(col=10, row=4)
_ACCEL_ASSIST_ZONE = Zone(col=7, row=3)
_ACCEL_STEP_S = 1.0 / 30.0
_ACCEL_A_MAX = 10.0


def _accel_lineup(prefix: str, id_offset: int) -> Lineup:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    players = [
        Player(
            prenom=f"{prefix}_{name}", nom="", nationalite="France", age=25, poste=poste, note=70.0,
            club="Test FC", championnat="TEST", id=id_offset + i,
        )
        for i, (poste, name) in enumerate(postes_names)
    ]
    return Lineup(club_name=f"{prefix} FC", formation="4-3-3", players=players, rating=70.0)


def _accel_goal_event() -> GoalEvent:
    return GoalEvent(
        club_name="home FC", scorer="home_bu", assist="home_mc0", minute=41, penalty=False,
        zone=_ACCEL_SCORER_ZONE, assist_zone=_ACCEL_ASSIST_ZONE,
    )


def _accel_start_positions(lineup: Lineup):
    from ligue1sim.pitch_geometry import PitchPoint
    return {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _raw_and_corrected_frames(name: str):
    """Reproduit exactement ce que fait `_build_clip_frames` pour un
    gabarit donné (construction du gabarit + `enrich_with_background` +
    boucle `interpolate`), puis compare AVANT/APRÈS
    `_apply_acceleration_constraint_to_frames` -- la même fonction que
    `_build_clip_frames` appelle réellement."""
    lineup = _accel_lineup("home", 1)
    opponent = _accel_lineup("away", 101)
    sequence = BUILDERS[name](_accel_goal_event(), lineup, _accel_start_positions(lineup))
    sequence = enrich_with_background(sequence, opponent)

    raw_frames = []
    t = 0.0
    while t <= sequence.duration + 1e-9:
        raw_frames.append(interpolate(sequence, t))
        t += _ACCEL_STEP_S

    corrected_frames = _apply_acceleration_constraint_to_frames(raw_frames, _ACCEL_STEP_S)
    return raw_frames, corrected_frames


def _positions_m(frame) -> dict:
    return {pid: (s.x * PITCH_LENGTH_M, s.y * PITCH_WIDTH_M) for pid, s in frame.players.items()}


class TestAccelerationConstraintOnRealGabarits:
    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_no_instantaneous_acceleration_exceeds_a_max(self, name):
        _raw_frames, corrected_frames = _raw_and_corrected_frames(name)
        positions_m = [_positions_m(f) for f in corrected_frames]

        for player_id in positions_m[0]:
            velocities = []
            for i in range(1, len(positions_m)):
                dx = positions_m[i][player_id][0] - positions_m[i - 1][player_id][0]
                dy = positions_m[i][player_id][1] - positions_m[i - 1][player_id][1]
                velocities.append((dx / _ACCEL_STEP_S, dy / _ACCEL_STEP_S))
            for j in range(1, len(velocities)):
                ax = (velocities[j][0] - velocities[j - 1][0]) / _ACCEL_STEP_S
                ay = (velocities[j][1] - velocities[j - 1][1]) / _ACCEL_STEP_S
                accel = (ax * ax + ay * ay) ** 0.5
                assert accel <= _ACCEL_A_MAX + 1e-6, f"{name} joueur={player_id} accel={accel:.2f} m/s^2"

    def test_at_least_one_gabarit_gets_its_positions_actually_corrected(self):
        # Tache 3.3 -- preuve que le fix agit reellement. Verifie sur les 12
        # gabarits (pas un par un : rien n'exige qu'un segment "impossible"/
        # une arrivee anticipee se produise sur CHAQUE gabarit avec ce jeu
        # de positions de depart minimal -- `tests/test_physics.py` prouve
        # deja, sur un cas synthetique garanti spikey, que la fonction agit;
        # ici on verifie qu'au moins un vrai gabarit en beneficie reellement).
        gabarits_with_a_correction = []
        for name in sorted(BUILDERS):
            raw_frames, corrected_frames = _raw_and_corrected_frames(name)
            raw_positions = [_positions_m(f) for f in raw_frames]
            corrected_positions = [_positions_m(f) for f in corrected_frames]
            if any(
                corrected_positions[i][pid] != raw_positions[i][pid]
                for i in range(len(raw_positions))
                for pid in raw_positions[i]
            ):
                gabarits_with_a_correction.append(name)

        assert gabarits_with_a_correction, "aucun des 12 gabarits n'a ete corrige -- la contrainte n'agit sur rien"
