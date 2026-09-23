import json

import pytest

from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.sequence_generator import enrich_with_background
from ligue1sim.animation.serialize import frame_sequence_to_json
from ligue1sim.animation.templates import BUILDERS
from ligue1sim.events import GoalEvent
from ligue1sim.kits import match_kit_colors
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PitchPoint, Zone
from ligue1sim.players import Player

# Brief "canvas vertical slice" (23/09/2026) demande le gabarit
# "frappe_enroulee" -- inexistant dans animation.templates.BUILDERS (12
# gabarits réels, voir leur liste). "decalage_enroulee" est le seul nom
# apparenté ("frappe enroulée" = la conclusion en enroulé du gabarit
# decalage_enroulee, voir templates.py) -- substitution documentée dans le
# retour de tâche, pas un gabarit inventé.
_TEMPLATE_NAME = "decalage_enroulee"

_SCORER_CLUB = "Paris Saint-Germain"
_OPPONENT_CLUB = "AS Monaco"


def _player(poste: str, name: str, player_id: int) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=70.0, club="C", championnat="T", id=player_id)


def _four_three_three(id_offset: int) -> list[Player]:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    return [_player(poste, name, id_offset + i) for i, (poste, name) in enumerate(postes_names)]


def _scorer_lineup() -> Lineup:
    return Lineup(club_name=_SCORER_CLUB, formation="4-3-3", players=_four_three_three(1), rating=70.0)


def _opponent_lineup() -> Lineup:
    return Lineup(club_name=_OPPONENT_CLUB, formation="4-3-3", players=_four_three_three(101), rating=65.0)


def _goal_event() -> GoalEvent:
    return GoalEvent(club_name=_SCORER_CLUB, scorer="bu", assist="mc0", minute=34, zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3))


def _sequence():
    lineup = _scorer_lineup()
    event = _goal_event()
    start_positions = {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
    sequence = BUILDERS[_TEMPLATE_NAME](event, lineup, start_positions)
    return enrich_with_background(sequence, _opponent_lineup())


def _metadata(sequence, *, fps: int = 30) -> dict:
    (scorer_fill, scorer_outline), (opp_fill, opp_outline) = match_kit_colors(_SCORER_CLUB, _OPPONENT_CLUB)
    roster = {
        str(player_id): {"team": entry.team_side, "numero": entry.numero, "active": entry.role is not None}
        for player_id, entry in sequence.roster.items()
    }
    return {
        "duration": sequence.duration,
        "fps_target": fps,
        "template": _TEMPLATE_NAME,
        "teams": {
            "scorer": {"name": _SCORER_CLUB, "color_fill": scorer_fill, "color_outline": scorer_outline},
            "opponent": {"name": _OPPONENT_CLUB, "color_fill": opp_fill, "color_outline": opp_outline},
        },
        "roster": roster,
    }


def _frames(sequence, *, fps: int = 30) -> list:
    step = 1.0 / fps
    frames = []
    t = 0.0
    while t <= sequence.duration + 1e-9:
        frames.append(interpolate(sequence, t))
        t += step
    return frames


class TestFrameSequenceToJsonStructure:
    """Reparse le JSON produit pour `decalage_enroulee` et vérifie la
    structure/les types conformes à docs/canvas_json_schema.md -- pas de
    valeurs exactes (elles changeront au fil des calibrations du moteur)."""

    def test_root_structure_and_types(self):
        sequence = _sequence()
        payload = json.loads(frame_sequence_to_json(_frames(sequence), _metadata(sequence)))

        assert isinstance(payload["duration"], float)
        assert payload["duration"] == sequence.duration
        assert isinstance(payload["fps_target"], int)
        assert isinstance(payload["metadata"], dict)
        assert isinstance(payload["frames"], list)
        assert len(payload["frames"]) > 0

    def test_metadata_structure(self):
        sequence = _sequence()
        payload = json.loads(frame_sequence_to_json(_frames(sequence), _metadata(sequence)))
        meta = payload["metadata"]

        assert meta["template"] == "decalage_enroulee"
        for side in ("scorer", "opponent"):
            team = meta["teams"][side]
            assert isinstance(team["name"], str)
            assert isinstance(team["color_fill"], str) and team["color_fill"].startswith("#")
            assert isinstance(team["color_outline"], str) and team["color_outline"].startswith("#")

    def test_roster_key_not_leaked_into_output_metadata(self):
        # metadata["roster"] est un helper d'ENTRÉE (jointure PlayerId ->
        # team/numero/active), jamais recopié tel quel dans la sortie (voir
        # docstring de frame_sequence_to_json) -- il est répété par joueur
        # dans chaque frame à la place.
        sequence = _sequence()
        payload = json.loads(frame_sequence_to_json(_frames(sequence), _metadata(sequence)))
        assert "roster" not in payload["metadata"]
        assert "roster" not in payload

    def test_frame_structure_and_types(self):
        sequence = _sequence()
        payload = json.loads(frame_sequence_to_json(_frames(sequence), _metadata(sequence)))

        for frame in payload["frames"]:
            assert isinstance(frame["t"], float)
            assert isinstance(frame["players"], list)
            assert len(frame["players"]) == 22  # equipe qui marque + adversaire, enrich_with_background

            ball = frame["ball"]
            for key in ("x", "y", "z", "spin"):
                assert isinstance(ball[key], float), f"ball.{key} n'est pas un float"

    def test_player_entry_structure_and_types(self):
        sequence = _sequence()
        payload = json.loads(frame_sequence_to_json(_frames(sequence), _metadata(sequence)))
        first_frame = payload["frames"][0]

        seen_active = set()
        for player in first_frame["players"]:
            assert isinstance(player["id"], str)
            assert isinstance(player["x"], float)
            assert isinstance(player["y"], float)
            assert player["team"] in ("scorer", "opponent")
            assert isinstance(player["numero"], int)
            assert 1 <= player["numero"] <= 11
            assert isinstance(player["active"], bool)
            seen_active.add(player["active"])

        # decalage_enroulee a 2 rôles actifs (assist/scorer) sur 22 joueurs
        # suivis -- les deux catégories doivent apparaître dans le JSON.
        assert seen_active == {True, False}

    def test_missing_roster_entry_raises(self):
        sequence = _sequence()
        metadata = _metadata(sequence)
        first_player_id = next(iter(sequence.roster))
        del metadata["roster"][str(first_player_id)]
        with pytest.raises(ValueError, match="roster"):
            frame_sequence_to_json(_frames(sequence), metadata)


class TestFrameSequenceToJsonDeterminism:
    def test_two_identical_calls_produce_identical_strings(self):
        sequence = _sequence()
        frames = _frames(sequence)
        metadata = _metadata(sequence)

        first = frame_sequence_to_json(frames, metadata)
        second = frame_sequence_to_json(frames, metadata)
        assert first == second

    def test_two_independently_built_sequences_produce_identical_strings(self):
        # Reconstruit TOUT depuis zéro (nouvelle Sequence, nouveaux frames,
        # nouveau metadata) plutôt que de réutiliser les mêmes objets --
        # preuve plus forte que le simple "même objet donne le même résultat".
        first = frame_sequence_to_json(_frames(_sequence()), _metadata(_sequence()))
        second = frame_sequence_to_json(_frames(_sequence()), _metadata(_sequence()))
        assert first == second
