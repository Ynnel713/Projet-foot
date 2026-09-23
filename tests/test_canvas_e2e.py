"""Test d'intégration bout-en-bout (brief "canvas player", 23/09/2026,
Tâche 6) : simule un match via le pipeline existant -> `Timeline` ->
`Clip`s -> JSON canvas, sur la seule chaîne Python (aucune dépendance
navigateur, voir Tâche 6.2 -- le rendu visuel est couvert par les captures
de `docs/previews/canvas/`, pas par ce test).

Seed fixe (recherche déterministe et bornée, même principe que
`scripts/render_player_preview.py::find_timeline`) pour retomber sur un
match où TOUS les buts réels sont résolubles par `home_lineup`/`away_lineup`
(voir la limite documentée dans `engine/narrative_player.py`) -- sans ça, le
score final recalculé à partir des clips pourrait légitimement ne pas
atteindre le score réel (un but marqué par un remplaçant omis), ce qui
rendrait l'invariant de score non vérifiable de façon fiable ici."""

import json
import random

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from narrative import build_timeline, match_result_from
from narrative_player import build_clips, clips_to_json

_SEED_BASE = 100
_MAX_SEED_ATTEMPTS = 200
_MAX_OCCASIONS = 4


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


def _find_usable_match():
    """Cherche un match (seed fixe, tentatives bornees) ou (a) TOUS les buts
    reels sont resolubles par home_lineup/away_lineup, ET (b) ces buts
    tombent tous parmi les `_MAX_OCCASIONS` premiers evenements
    chronologiques -- les DEUX conditions a la fois necessaires pour que "le
    score final recalcule a partir des [_MAX_OCCASIONS premiers] clips
    egale le score du match" (Tache 6.1) soit un invariant honnetement
    verifiable ici : `max_occasions` limite structurellement `build_clips`
    aux premiers evenements chronologiques (voir narrative_player.py), donc
    un but tardif hors de cette fenetre rendrait l'egalite mathematiquement
    impossible, pas un bug a masquer."""
    for attempt in range(_MAX_SEED_ATTEMPTS):
        seed = _SEED_BASE + attempt
        random.seed(seed)
        np.random.seed(seed)

        home = Club(name="Home FC", players=_squad("home", 72.0))
        away = Club(name="Away FC", players=_squad("away", 68.0))
        context = LeagueContext.from_clubs([home, away])
        home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)

        home_goals, away_goals, events = simulate_match(home, away, context)
        if events is None:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        result = match_result_from(match, events, home_lineup, away_lineup, date=str(seed))
        timeline = build_timeline(result)

        starter_names = {p.name for p in timeline.home_lineup.players} | {p.name for p in timeline.away_lineup.players}
        all_resolvable = all(
            g.scorer in starter_names and (g.assist is None or g.assist in starter_names) for g in result.goals
        )
        if not all_resolvable:
            continue

        goals_within_window = {(g.minute, g.scorer) for g in result.goals} <= {
            (e.minute, e.main_player) for e in timeline.events[:_MAX_OCCASIONS]
        }
        if goals_within_window:
            return timeline
    raise AssertionError(f"aucun match utilisable trouve en {_MAX_SEED_ATTEMPTS} tentatives depuis {_SEED_BASE}")


class TestMatchToCanvasEndToEnd:
    def test_match_to_canvas_end_to_end(self):
        timeline = _find_usable_match()
        clips = build_clips(timeline, max_occasions=_MAX_OCCASIONS)
        assert clips, "aucun clip construit -- le match choisi devrait pourtant en fournir au moins un"

        payload = clips_to_json(clips, timeline)
        data = json.loads(payload)

        # Conformite au schema canvas (docs/canvas_json_schema.md) -- un
        # objet par clip, meme forme qu'un JSON de gabarit isole.
        assert isinstance(data, list)
        assert len(data) == len(clips)
        for clip_json in data:
            assert isinstance(clip_json["duration"], float) and clip_json["duration"] > 0
            assert isinstance(clip_json["fps_target"], int) and clip_json["fps_target"] > 0
            meta = clip_json["metadata"]
            assert isinstance(meta["template"], str)
            assert set(meta["teams"]) == {"scorer", "opponent"}
            for side in ("scorer", "opponent"):
                assert {"name", "color_fill", "color_outline"} <= set(meta["teams"][side])
            assert isinstance(meta["minute"], int)
            assert meta["home_team"] == timeline.home_team
            assert meta["away_team"] == timeline.away_team
            assert isinstance(meta["score_before"], list) and len(meta["score_before"]) == 2
            assert isinstance(meta["score_after"], list) and len(meta["score_after"]) == 2
            # interval_events (Tache 1, consolidation du 23/09/2026) : plus
            # forcement vide -- verifie la FORME de chaque element plutot
            # que son absence.
            assert isinstance(meta["interval_events"], list)
            for item in meta["interval_events"]:
                assert set(item) == {"minute", "type", "equipe", "joueur", "detail"}
                assert item["type"] in ("carton", "remplacement")

            frames = clip_json["frames"]
            assert frames, "clip serialise sans frames (malforme)"
            for frame in frames:
                assert isinstance(frame["t"], float)
                assert frame["players"], "frame sans aucun joueur (malformee)"
                for player in frame["players"]:
                    assert {"id", "x", "y", "team", "numero", "active"} <= set(player)
                ball = frame["ball"]
                assert {"x", "y", "z", "spin"} <= set(ball)

        # Ordre chronologique (Tache 6.1).
        minutes = [c["metadata"]["minute"] for c in data]
        assert minutes == sorted(minutes)

        # Score final recalcule a partir des clips == score du match (Tache
        # 6.1) -- verifiable ici puisque _find_fully_resolvable_match
        # garantit qu'aucun but n'a ete omis par build_clips.
        assert clips[-1].score_after == (timeline.home_goals, timeline.away_goals)
