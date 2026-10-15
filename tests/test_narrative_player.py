"""Tests d'`engine/narrative_player.py` (brief "canvas player", 23/09/2026,
Tâche 3) -- `build_clips`. Mêmes helpers de simulation que
`tests/test_narrative.py` (dupliqués, pas importés depuis un autre fichier
de test -- même motif déjà établi dans ce projet, voir la docstring
d'`apps/streamlit_preview.py` sur l'indépendance volontaire des fichiers)."""

import dataclasses
from types import SimpleNamespace

import pytest

from ligue1sim.animation import templates as templates_module
from ligue1sim.animation.ball import REBOUND_MAX_DURATION_S
from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.sequence_generator import enrich_with_background
from ligue1sim.animation.templates import BUILDERS, numeros_by_player_id
from ligue1sim.clubs import Club
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup, pick_best_formation, select_best_xi
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Zone
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from ball_events import BALL_EVENT_TYPES, plan_ball_events
from narrative import BUT, build_timeline, match_result_from
from narrative_player import (
    build_clips,
    clips_to_json,
    _apply_acceleration_constraint_to_frames,
    _build_clip_frames,
    _extend_with_rebound,
    _interval_events,
    _lineup_start_positions,
    _names_on_pitch,
    _opponent_view,
    _scorer_view,
    _substitute_start_position,
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


class TestNamesOnPitch:
    """Étapes 0a et 0b-2 du Bloc A : effectif affiché = joueurs sur le terrain à la minute de l'événement (`Timeline.substitutions` et
    `Timeline.cards` font foi). Remplacements de même minute en bloc, blessures sans effet, `keep` pour les buts réels de frontière (ticket 44)."""

    @staticmethod
    def _setup():
        home, _away = _clubs()
        lineup = select_best_xi(home, "4-2-3-1")
        gk = next(p for p in lineup.players if p.poste == "GK")
        outfield = [p for p in lineup.players if p.poste != "GK"]
        mc, bu = next(p for p in outfield if p.poste == "MC"), next(p for p in outfield if p.poste == "BU")
        others = [p for p in outfield if p not in (mc, bu)]
        reserve_gk = next(p for p in home.players if p.poste == "GK" and p.name != gk.name)
        reserve_cb, reserve_cm = (next(p for p in home.players if p.poste == poste and p.name not in {q.name for q in lineup.players}) for poste in ("DC", "MC"))
        lineup = dataclasses.replace(lineup, substitutes=[reserve_gk, reserve_cb, reserve_cm])
        timeline = SimpleNamespace(
            substitutions=[
                SimpleNamespace(club_name="Home FC", player_off=gk.name, player_on=reserve_gk.name, minute=43),
                SimpleNamespace(club_name="Home FC", player_off=mc.name, player_on=reserve_cb.name, minute=60),
                SimpleNamespace(club_name="Home FC", player_off=bu.name, player_on=reserve_cm.name, minute=60),
            ],
            cards=[
                SimpleNamespace(club_name="Home FC", player=others[0].name, minute=75, card_type="direct"),
                SimpleNamespace(club_name="Home FC", player=others[1].name, minute=20, card_type="yellow"),
            ],
        )
        return lineup, timeline, dict(gk=gk, reserve_gk=reserve_gk, mc=mc, bu=bu, reserve_cb=reserve_cb, reserve_cm=reserve_cm, red=others[0], yellow=others[1])

    def test_before_any_substitution_the_eleven_starters_stay_and_no_reserve_is_present(self):
        lineup, timeline, who = self._setup()
        assert _names_on_pitch(timeline, lineup, "Home FC", 42) == {p.name for p in lineup.players}

    def test_substitutions_of_the_same_minute_apply_together_from_that_minute(self):
        lineup, timeline, who = self._setup()
        assert who["reserve_gk"].name in _names_on_pitch(timeline, lineup, "Home FC", 43) and who["gk"].name not in _names_on_pitch(timeline, lineup, "Home FC", 43)
        at_60 = _names_on_pitch(timeline, lineup, "Home FC", 60)
        assert {who["reserve_cb"].name, who["reserve_cm"].name} <= at_60 and not ({who["mc"].name, who["bu"].name} & at_60)
        assert len(at_60) == 11

    def test_red_card_removes_the_player_from_its_minute_and_a_yellow_does_not(self):
        lineup, timeline, who = self._setup()
        assert who["red"].name in _names_on_pitch(timeline, lineup, "Home FC", 74)
        assert who["red"].name not in _names_on_pitch(timeline, lineup, "Home FC", 75)
        assert len(_names_on_pitch(timeline, lineup, "Home FC", 90)) == 10
        assert who["yellow"].name in _names_on_pitch(timeline, lineup, "Home FC", 90)

    def test_kept_names_stay_even_when_absent(self):
        lineup, timeline, who = self._setup()
        names = _names_on_pitch(timeline, lineup, "Home FC", 80, frozenset({who["mc"].name, who["red"].name}))
        assert {who["mc"].name, who["red"].name, who["reserve_cb"].name} <= names and len(names) == 12

    def test_other_team_keeps_its_starters(self):
        lineup, timeline, _who = self._setup()
        assert _names_on_pitch(timeline, lineup, "Away FC", 90) == {p.name for p in lineup.players}

    def test_scorer_view_restricts_positions_without_recomputing_the_formation(self):
        lineup, timeline, who = self._setup()
        full = _lineup_start_positions(lineup)
        shown, positions = _scorer_view(timeline, lineup, "Home FC", 90, frozenset())
        assert shown.substitutes == [] and set(positions) == {p.name for p in shown.players} and len(positions) == 10  # 11 joueurs après les remplacements, moins l'expulsé
        for name, point in positions.items():
            assert point == full[name]  # aucun recalage : même point qu'avec l'effectif complet
        assert positions[who["reserve_cb"].name] == full[who["reserve_cb"].name]  # le remplaçant garde sa position propre

    def test_a_substitute_enters_on_the_formation_line_of_its_poste_and_in_its_natural_lane(self):
        lineup, _timeline, who = self._setup()
        positions = _lineup_start_positions(lineup)
        starter_xs = {}
        for player in lineup.players:
            starter_xs.setdefault(player.poste, []).append(positions[player.name].x)
        for key, poste in (("reserve_cb", "DC"), ("reserve_cm", "MC")):
            point = positions[who[key].name]
            assert point.x == pytest.approx(sum(starter_xs[poste]) / len(starter_xs[poste]))  # même profondeur que la ligne de son poste
            assert 0.15 + 0.70 / 3 <= point.y <= 0.15 + 0.70 * 2 / 3  # couloir axial : tiers central
        starters_alone = _lineup_start_positions(dataclasses.replace(lineup, substitutes=[]))
        assert all(positions[p.name] == starters_alone[p.name] for p in lineup.players)  # les titulaires ne bougent pas
        wide = _substitute_start_position(dataclasses.replace(who["reserve_cb"], poste="LB"), 0.2)
        assert 0.15 <= wide.y <= 0.15 + 0.70 / 3 and wide.x == 0.2
        right = _substitute_start_position(dataclasses.replace(who["reserve_cb"], poste="AD"), 0.2)
        assert 0.15 + 0.70 * 2 / 3 <= right.y <= 0.85

    def test_opponent_view_keeps_the_complete_lineup_and_carries_en_jeu(self):
        lineup, timeline, who = self._setup()
        view, present = _opponent_view(timeline, lineup, "Home FC", 60)
        assert [p.name for p in view.players] == [p.name for p in lineup.players] and [p.name for p in view.substitutes] == [p.name for p in lineup.substitutes]
        assert set(view.en_jeu) == present and who["mc"].name not in view.en_jeu
        assert view.en_jeu[who["reserve_cb"].name] == _lineup_start_positions(lineup)[who["reserve_cb"].name]


class TestClipsShowExactlyThePlayersOnThePitch:
    @staticmethod
    def _expected(timeline, lineup, team, minute):
        on = {p.name for p in lineup.players}
        for sub in sorted((x for x in timeline.substitutions if x.club_name == team), key=lambda x: x.minute):
            if minute >= sub.minute:
                on.discard(sub.player_off)
                on.add(sub.player_on)
        for card in timeline.cards:
            if card.club_name == team and card.card_type in ("direct", "second_yellow") and minute >= card.minute:
                on.discard(card.player)
        return on

    def test_composition_positions_and_shirt_numbers(self):
        checked = 0
        for match in _simulate_n(3):
            timeline = build_timeline(match)
            clips = build_clips(timeline)
            assert len(clips) == len(timeline.events)
            numbers_by_player: dict = {}
            for event, clip in zip(timeline.events, clips):
                scorer_is_home = event.team == timeline.home_team
                lineups = {"scorer": timeline.home_lineup if scorer_is_home else timeline.away_lineup, "opponent": timeline.away_lineup if scorer_is_home else timeline.home_lineup}
                teams = {"scorer": event.team, "opponent": timeline.away_team if scorer_is_home else timeline.home_team}
                for side in ("scorer", "opponent"):
                    shown = [entry.nom for entry in clip.roster.values() if entry.team_side == side]
                    assert len(shown) == len(set(shown))
                    expected = self._expected(timeline, lineups[side], teams[side], event.minute)
                    named = {event.main_player, *event.involved_players} if side == "scorer" else set()
                    assert expected <= set(shown) and set(shown) - expected <= named, (timeline.match_id, event.minute, side)
                numbers = {side: numeros_by_player_id(lineups[side]) for side in lineups}
                for pid, entry in clip.roster.items():
                    assert entry.numero == numbers[entry.team_side][pid]  # numéro dérivé de l'effectif complet
                    assert numbers_by_player.setdefault(entry.nom, entry.numero) == entry.numero  # stable d'un clip à l'autre
                checked += 1
        assert checked > 0


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
                # Tolerance recalibree (Phase 5 sous-etape 1, ticket 1) : 0,5 % de la
                # longueur du terrain (0,525 m), au lieu de 0,1 (~10 m). Les positions
                # brutes et la sortie de motion._apply_avoidance sont dans [0, 1] ; le
                # depassement (jusqu'a ~60 m) venait de physics.apply_acceleration_
                # constraint, desormais bornee au terrain (freinage anticipe, param. bounds).
                # La marge ne sert plus que de garde-fou d'arrondi : en pratique 0.
                margin_m = 0.005 * PITCH_LENGTH_M
                margin_x, margin_y = margin_m / PITCH_LENGTH_M, margin_m / PITCH_WIDTH_M
                for frame in clip.frames:
                    assert frame.ball is not None
                    for state in frame.players.values():
                        assert state is not None
                        assert -margin_x <= state.x <= 1.0 + margin_x, f"x={state.x} hors terrain"
                        assert -margin_y <= state.y <= 1.0 + margin_y, f"y={state.y} hors terrain"
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

        opponents: list = []

        def spy(template, event, lineup, start_positions, outcome=None, opponent_lineup=None):
            captured.append(outcome)
            opponents.append(opponent_lineup)
            return original(template, event, lineup, start_positions, outcome, opponent_lineup)

        monkeypatch.setattr(templates_module, "build_from_template", spy)

        checked = 0
        for match in results:
            timeline = build_timeline(match)
            for event in timeline.events:
                captured.clear()
                opponents.clear()
                _build_clip_frames(timeline, event)
                assert len(captured) == 1, (
                    f"{timeline.match_id} minute={event.minute} : {len(captured)} appels a "
                    "build_from_template (attendu exactement 1 par evenement)"
                )
                assert captured[0] == event.outcome, (
                    f"{timeline.match_id} minute={event.minute} : outcome transmis {captured[0]!r} "
                    f"!= event.outcome {event.outcome!r}"
                )
                # B8-b : la compo de l'équipe qui encaisse est transmise au gabarit (pression adverse sur les contrôles).
                opponent_club = timeline.away_lineup if event.team == timeline.home_team else timeline.home_lineup
                assert opponents[0] is opponent_club, f"{timeline.match_id} minute={event.minute} : compo adverse non transmise"
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


# --- Ticket 4 (08/10/2026) : optimisation d'`interpolate` (mémoïsation de
# `_ease_progress`, sortie anticipée d'`_apply_avoidance`) ---------------------
# Contrat : résultat BIT-À-BIT identique au code d'origine. Les empreintes ci-dessous
# ont été calculées avec le code AVANT optimisation (HEAD 7eb8fe8) sur 5 clips témoins
# (gabarits réels + `enrich_with_background` + `interpolate`, sans simulation donc sans
# aléa) ; `_reference_avoidance` est une copie de l'ancienne `_apply_avoidance`.

# Phase 6, B6-c : les décalages de départ et les dérives des joueurs sont désormais clés sur `player_id|event_ref|sel` (et non plus
# `player_id` seul) ; les positions des joueurs changent donc, et ces 5 empreintes ont été recalculées. Preuve que B6-c est la SEULE cause :
# en remettant temporairement l'ancienne clé (`player_id` seul), le code actuel redonne exactement les empreintes d'avant (HEAD 7eb8fe8) :
# but_gag ("6b3877c7e00cfc9e", "30bef88bb8d089cd"), construction_placee ("2dbe69316b810342", ...), contre_attaque ("269d6156d88bef7b", ...),
# corner ("0b781d5c5bc9f220", "f5705f4abb4a75e8"), percee_individuelle ("d61261efa5c6fb1c", ...). L'équivalence d'`interpolate` avec le code
# d'origine reste vérifiée par `_reference_avoidance` et les tests ci-dessous.
# Phase 6, B6-c, décision A3 (plancher des dérives tiré dans [0,1 ; 0,5] m par couple (joueur, événement), au lieu de 0,5 m fixe) : les
# dérives des joueurs décor changent, les 5 empreintes ont été recalculées une seconde fois. Preuve que A3 est la SEULE cause : avec le
# plancher remis à 0,5 m fixe (`_MIN_DRIFT_MAGNITUDE_M = 0.5`), le code actuel redonne exactement les empreintes de B6-c :
# but_gag ("72e992e33871f1a1", "986c877d0f40e3cc"), construction_placee ("2fdf4a837c8f86ae", ...), contre_attaque ("eba806b8f8345992", ...),
# corner ("8667086b93f53cda", "c2a0a0579fb60eae"), percee_individuelle ("6d8d8580707ed082", ...).
# Phase 6, B6-c, décision 1B (14/10/2026) : borne basse du plancher des dérives relevée de 0,1 à 0,2 m ; 5 empreintes recalculées une troisième fois.
# Preuve que ce relèvement est la SEULE cause : avec `_MIN_DRIFT_MAGNITUDE_M = 0.1`, le code actuel redonne exactement les empreintes d'A3 :
# but_gag ("178cb5423d50d5e5", "625839a8feaefc0b"), construction_placee ("154a539bf8f77445", ...), contre_attaque ("fb2cd12d94c9a31c", ...),
# corner ("8b9f3e342c4d0d34", "b9a32dd3ebd7562e"), percee_individuelle ("72fa884e6d046ec8", ...).
# Phase 6, B8-a (14/10/2026) : chaque réception au sol reçoit un segment de contrôle (`templates._insert_ground_controls`), ce qui ajoute des
# keyframes et déplace les joueurs actifs pendant le geste ; les empreintes de but_gag, construction_placee et contre_attaque sont recalculées
# (corner et percee_individuelle inchangés : réception aérienne / aucune réception). Preuve que B8-a est la SEULE cause : avec
# `_insert_ground_controls` neutralisé (identité), le code actuel redonne exactement les empreintes d'avant :
# but_gag ("d08dadff3471f811", "c7acfb230b442645"), construction_placee ("9e0fcb91c8afb6f8", ...), contre_attaque ("06d519a0433e127a", ...).
# Mesure sur 100 matchs : le déplacement du porteur pendant la fenêtre vient des gabarits (max 5,85 m sans contrôle, 6,30 m avec) ; aucune exception motion.py.
# Phase 6, B8-c1 (14/10/2026) : `corner` est retimé (durée 7,0 s inchangée ; le centre part à 4,9 s et le contact a lieu à son arrivée, plus de « ballon
# disputé » ; un keyframe de plus à t_ratio 0,7), ce qui change les trajectoires des joueurs : l'empreinte de `corner` est recalculée. Preuve que B8-c1 est la SEULE cause : avec l'ancienne définition du gabarit
# (durée, rôles, tags, `ball_owner`, `ball_height`, `ball_position`, `physics_tags` d'avant), le code actuel redonne exactement l'empreinte précédente
# ("f05064d66238d5db", "39a32789ddad7788"). L'empreinte ne contient que les joueurs : `ball.py` n'y intervient pas.
# Chantier 1, 1c (15/10/2026) : `percee_individuelle` reçoit une géométrie de rôle sur son scorer (durée 7,0 -> 8,0 s, départ dérivé de
# la formation au lieu de la position brute) -- l'empreinte est recalculée, et redevient identique avant/après contrainte d'accélération
# (comme avant la migration) : la course du scorer est désormais réalisable sans correction. Preuve que 1c est la SEULE cause : avec
# l'ancienne durée et `geometry=None` sur son rôle, le code actuel redonne exactement l'empreinte précédente ("e81f855c96b7ccfe", idem).
# Chantier 1, 1d (15/10/2026) : `contre_attaque` (durée 8,0 -> 9,0 s) et `construction_placee` (durée inchangée) reçoivent une géométrie
# de rôle sur leurs trois rôles ; `support1` devient en plus tactique (poste attendu, voir `TestTacticalSupports`). Empreintes
# recalculées. Preuve que 1d est la SEULE cause : avec les anciennes durées, `geometry=None` sur tous les rôles et le tirage
# alphabétique d'origine pour support1, le code actuel redonne exactement les empreintes précédentes ("b08cb2b75e7031cd"/
# "a23371edfce032df" pour contre_attaque, "ff696c5902800e79"/"b89f6245b693bd81" pour construction_placee).
# Chantier 1, 1e-1 (15/10/2026) : `but_gag` reçoit une géométrie de rôle sur ses trois rôles (durée inchangée, 5,0 s) ; `support1` et
# `support2` deviennent en plus tactiques (poste attendu, voir `TestTacticalSupports`). Empreinte recalculée. Preuve que 1e-1 est la
# SEULE cause : avec `geometry=None` sur tous les rôles et le tirage alphabétique d'origine pour support1/support2, le code actuel
# redonne exactement l'empreinte précédente ("2adb64758544b738"/"5413574bb0047c48").
_WITNESS_DIGESTS = {
    # gabarit: (empreinte des images brutes `interpolate`, empreinte après contrainte d'accélération)
    "but_gag": ("0ff6fe3304d23938", "7671f77e105c6115"),
    "construction_placee": ("0858943d9f3a7e55", "7ace6109febe5566"),
    "contre_attaque": ("1b546dda1ca4f3d8", "867086d4e95127b3"),
    "corner": ("2e573082648af3d4", "46b52565c7ea2d7b"),
    "percee_individuelle": ("4a00cea671b14edd", "4a00cea671b14edd"),
}


def _trajectory_digest(frames) -> str:
    import hashlib

    digest = hashlib.sha256()
    for frame in frames:
        for player_id in sorted(frame.players, key=str):
            s = frame.players[player_id]
            digest.update(
                f"{player_id}|{s.x:.9f}|{s.y:.9f}|{s.vx:.6f}|{s.vy:.6f}|{int(s.is_ball_carrier)};".encode()
            )
    return digest.hexdigest()[:16]


def _reference_avoidance(positions):
    """Copie de `motion._apply_avoidance` AVANT le ticket 4 : 4 passes complètes, sans sortie anticipée."""
    import math

    from ligue1sim.animation import motion

    ids = sorted(positions, key=str)
    adjusted = dict(positions)
    for _pass in range(motion._AVOIDANCE_PASSES):
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                ax, ay = adjusted[a]
                bx, by = adjusted[b]
                dist_m = motion._real_distance_m((ax, ay), (bx, by))
                if dist_m >= motion._AVOIDANCE_TRIGGER_M:
                    continue
                if dist_m < 1e-9:
                    angle = motion._stable_repulsion_angle(a, b)
                    dir_x, dir_y = math.cos(angle), math.sin(angle)
                else:
                    dx_m = (bx - ax) * motion.PITCH_LENGTH_M
                    dy_m = (by - ay) * motion.PITCH_WIDTH_M
                    dir_x, dir_y = dx_m / dist_m, dy_m / dist_m
                missing_m = motion._AVOIDANCE_TRIGGER_M - dist_m
                push_x = (dir_x * missing_m / 2) / motion.PITCH_LENGTH_M
                push_y = (dir_y * missing_m / 2) / motion.PITCH_WIDTH_M
                adjusted[a] = (ax - push_x, ay - push_y)
                adjusted[b] = (bx + push_x, by + push_y)
    return adjusted


class TestInterpolateOptimisation:
    @pytest.mark.parametrize("name", sorted(_WITNESS_DIGESTS))
    def test_witness_clips_match_the_frozen_pre_optimisation_reference(self, name):
        raw_frames, corrected_frames = _raw_and_corrected_frames(name)
        assert (_trajectory_digest(raw_frames), _trajectory_digest(corrected_frames)) == _WITNESS_DIGESTS[name]

    def test_cached_ease_progress_is_bit_identical_to_a_fresh_computation(self):
        from ligue1sim.animation.motion import _ease_progress

        fresh = _ease_progress.__wrapped__  # fonction non mémoïsée
        samples = [-1.0, 0.0, 1e-9, 0.25, 0.5, 0.999999, 1.0, 2.0] + [k / 997 for k in range(998)]
        _ease_progress.cache_clear()
        for _ in range(2):  # 1re passe : calculs frais ; 2e passe : tout vient du cache
            for s in samples:
                assert _ease_progress(s) == fresh(s)

    def test_ease_cache_is_bounded_and_does_not_change_results_between_clips(self):
        from ligue1sim.animation.motion import _ease_progress

        _ease_progress.cache_clear()
        cold = [_trajectory_digest(_raw_and_corrected_frames(n)[0]) for n in sorted(_WITNESS_DIGESTS)]
        info = _ease_progress.cache_info()
        assert info.currsize <= info.maxsize  # borné : pas de fuite entre clips
        warm = [_trajectory_digest(_raw_and_corrected_frames(n)[0]) for n in sorted(_WITNESS_DIGESTS)]
        assert warm == cold  # un cache chaud (clips précédents) ne change aucun résultat
        for _ in range(info.maxsize + 50):  # même saturé, la taille reste bornée
            _ease_progress(__import__("random").random())
        assert _ease_progress.cache_info().currsize <= info.maxsize

    def test_avoidance_early_exit_is_bit_identical_to_the_four_full_passes(self):
        import random

        from ligue1sim.animation.motion import _apply_avoidance

        rng = random.Random(20261008)
        for case in range(300):
            spread = rng.choice([0.002, 0.01, 0.05, 0.4])  # du paquet dense à l'écart total
            positions = {
                f"p{k}": (0.5 + rng.uniform(-spread, spread), 0.5 + rng.uniform(-spread, spread)) for k in range(26)
            }
            if case % 7 == 0:  # deux joueurs exactement superposés (branche `_stable_repulsion_angle`)
                positions["p1"] = positions["p0"]
            assert _apply_avoidance(positions) == _reference_avoidance(positions)

    def test_avoidance_leaves_well_separated_players_untouched(self):
        from ligue1sim.animation.motion import _apply_avoidance

        positions = {f"p{k}": (0.04 * k, 0.04 * k) for k in range(20)}
        assert _apply_avoidance(positions) == positions


# --- Phase 6, Bloc B2 (08/10/2026) : prolongation des clips par le rebond ----------------------
# `_extend_with_rebound` ajoute les images du rebond APRÈS la séquence (poteau, barre) sans toucher aux images
# existantes : allonger `Sequence.duration` décalerait presque toutes les images précédentes (voir sa docstring).


def _frames_with_outcome(name: str, outcome: str | None):
    lineup, opponent = _accel_lineup("home", 1), _accel_lineup("away", 101)
    sequence = BUILDERS[name](_accel_goal_event(), lineup, _accel_start_positions(lineup), outcome)
    sequence = enrich_with_background(sequence, opponent)
    frames, t = [], 0.0
    while t <= sequence.duration + 1e-9:
        frames.append(interpolate(sequence, t))
        t += _ACCEL_STEP_S
    return sequence, frames


class TestExtendWithRebound:
    @pytest.mark.parametrize("name", sorted(BUILDERS))
    @pytest.mark.parametrize("outcome", ["poteau", "barre", "arret"])
    def test_existing_frames_are_untouched_and_the_rebound_is_appended_after_the_impact(self, name, outcome):
        sequence, frames = _frames_with_outcome(name, outcome)
        extended = _extend_with_rebound(frames, sequence, outcome, _ACCEL_STEP_S)

        assert extended[: len(frames)] == frames  # images existantes strictement identiques
        extension = extended[len(frames):]
        assert extension, "le clip doit être prolongé"
        assert extension[0].t > sequence.duration  # la première image ajoutée est déjà après l'impact
        times = [f.t for f in extension]
        assert times == sorted(times) and len(set(times)) == len(times)
        assert all(0.0 < b - a <= _ACCEL_STEP_S + 1e-9 for a, b in zip(times, times[1:]))
        assert extension[-1].t - sequence.duration <= REBOUND_MAX_DURATION_S + 1e-9
        assert all(f.players == frames[-1].players for f in extension)  # joueurs figés, comme pendant le vol
        assert all(f.ball.z >= 0.0 and f.ball.owner_id is None for f in extension)
        plan = plan_ball_events(sequence, outcome, 0, None, None)
        if plan.end_tau >= plan.trajectory.duration - 1e-9:
            assert extension[-1].ball.z == 0.0  # le ballon finit au sol (sauf clip coupé 1,0 s après une ligne)

    # B7-c (14/10/2026) : un coup franc d'issue `tacle` / `degagement` est BLOQUE par le mur et donc prolongé (voir
    # `test_extension_free_kick_tackle_and_clearance_are_extended`) ; ces deux cas sortent de la liste « non prolongé ».
    @pytest.mark.parametrize(
        "name,outcome",
        [
            (name, outcome)
            for name in sorted(BUILDERS)
            for outcome in ["but", "hors_cadre", "tacle", "degagement", None]
            if not (name == "coup_franc" and outcome in ("tacle", "degagement"))
        ],
    )
    def test_other_outcomes_are_not_extended(self, name, outcome):
        sequence, frames = _frames_with_outcome(name, outcome)
        assert _extend_with_rebound(frames, sequence, outcome, _ACCEL_STEP_S) is frames

    @pytest.mark.parametrize("outcome", ["tacle", "degagement"])
    def test_extension_free_kick_tackle_and_clearance_are_extended(self, outcome):
        sequence, frames = _frames_with_outcome("coup_franc", outcome)
        extended = _extend_with_rebound(frames, sequence, outcome, _ACCEL_STEP_S)
        assert extended[: len(frames)] == frames  # images existantes strictement identiques
        extension = extended[len(frames):]
        assert extension, "le ballon bloqué par le mur doit être prolongé"
        assert extension[0].t > sequence.duration
        assert all(f.players == frames[-1].players for f in extension)  # joueurs figés, comme pendant un vol
        assert all(f.ball.z >= 0.0 and f.ball.owner_id is None for f in extension)

    def test_the_clip_with_a_rebound_is_longer_than_the_clip_without_it(self):
        sequence, frames = _frames_with_outcome("une_deux", "barre")
        extended = _extend_with_rebound(frames, sequence, "barre", _ACCEL_STEP_S)
        assert extended[-1].t > frames[-1].t + 1.0  # le rebond est visible (plus d'une seconde)


# --- Phase 6, Bloc B4 (08/10/2026) : événements du ballon dans le payload --------------------------------


class TestBallEventsInThePayload:
    """`metadata.events_ball` : champ OPTIONNEL du clip (`render/canvas.html` l'ignore), produit par le moteur."""

    def test_clips_carry_valid_json_ball_events_consistent_with_their_outcome(self):
        import json

        found = 0
        outcomes_seen = set()
        for match in _simulate_n(8):
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=5)
            payloads = json.loads(clips_to_json(clips, timeline))
            for clip, payload in zip(clips, payloads):
                events = payload["metadata"].get("events_ball", [])
                assert events == list(clip.events_ball)
                if clip.issue in ("arret", "but", "hors_cadre", "poteau", "barre", "tacle", "degagement"):
                    assert events, f"{clip.issue} : aucun événement du ballon"
                outcomes_seen.add(clip.issue)
                for event in events:
                    assert event["type"] in BALL_EVENT_TYPES
                    assert 0.0 <= event["t"] <= payload["duration"] + 1e-6
                    assert event["t_minute"] == clip.minute and event["event_ref"]
                    assert 0.0 <= event["x"] <= 1.02 and 0.0 <= event["y"] <= 1.0
                if clip.issue == "but":
                    assert [e["type"] for e in events] == ["but"]
                if clip.issue == "arret":
                    assert events[0]["type"] == "parade"
                found += len(events)
        assert found > 0 and {"but", "arret"} <= outcomes_seen

    def test_the_payload_stays_backward_compatible_without_ball_events(self):
        import json

        timeline = build_timeline(_simulate_n(1)[0])
        clips = [dataclasses.replace(c, events_ball=()) for c in build_clips(timeline, max_occasions=2)]
        for payload in json.loads(clips_to_json(clips, timeline)):
            assert "events_ball" not in payload["metadata"]
