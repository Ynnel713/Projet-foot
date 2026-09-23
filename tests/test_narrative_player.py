"""Tests d'`engine/narrative_player.py` (brief "canvas player", 23/09/2026,
Tâche 3) -- `build_clips`. Mêmes helpers de simulation que
`tests/test_narrative.py` (dupliqués, pas importés depuis un autre fichier
de test -- même motif déjà établi dans ce projet, voir la docstring
d'`apps/streamlit_preview.py` sur l'indépendance volontaire des fichiers)."""

from ligue1sim.clubs import Club
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from narrative import BUT, build_timeline, match_result_from
from narrative_player import build_clips

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


class TestBuildClipsScoreSequence:
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
    def test_build_clips_interval_events_currently_always_empty(self):
        # Tache 3.5 -- limite documentee (voir Clip/build_clips dans
        # narrative_player.py et narrative_timeline_schema.md) : Timeline ne
        # porte pas MatchEvents.cards/.substitutions (hors du perimetre des
        # deux extensions autorisees le 23/09/2026), donc interval_events
        # reste TOUJOURS () pour cette iteration -- verifie explicitement ce
        # comportement connu plutot que de le laisser non teste.
        [match] = _simulate_n(1)
        timeline = build_timeline(match)
        clips = build_clips(timeline, max_occasions=None)
        assert clips
        assert all(c.interval_events == () for c in clips)


class TestBuildClipsFramesNeverEmpty:
    def test_no_clip_has_empty_frames(self):
        results = _simulate_n(_N_MATCHES)
        for match in results:
            timeline = build_timeline(match)
            clips = build_clips(timeline, max_occasions=4)
            for clip in clips:
                assert clip.frames, f"{timeline.match_id} : clip {clip.minute}/{clip.gabarit} sans frames"
                assert clip.duration_s > 0
