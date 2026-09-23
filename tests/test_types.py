import json

import pytest

from ligue1sim.animation.types import BackgroundTrack, BallState, Keyframe, RosterEntry, Sequence


def _ball(x=0.5, y=0.5, owner_id=None) -> BallState:
    return BallState(x=x, y=y, z=0.0, spin=0.0, owner_id=owner_id)


def _keyframe(t: float, players: dict, tag: str = "", owner_id=None) -> Keyframe:
    return Keyframe(t=t, ball=_ball(owner_id=owner_id), players=players, tag=tag)


def _players(*ids) -> dict:
    return {player_id: (0.1 * i, 0.2 * i) for i, player_id in enumerate(ids)}


def _roster(*ids) -> dict:
    return {
        player_id: RosterEntry(nom=f"Player {player_id}", poste="MC", role=None, numero=i + 1, team_side="scorer")
        for i, player_id in enumerate(ids)
    }


class TestConstruction:
    def test_builds_with_well_formed_keyframes(self):
        sequence = Sequence(
            event_ref="goal:home:1",
            keyframes=[_keyframe(0.0, _players(1, 2)), _keyframe(1.5, _players(1, 2))],
            duration=1.5,
            meta={"club_name": "Home FC"},
            roster=_roster(1, 2),
        )
        assert sequence.duration == 1.5
        assert len(sequence.keyframes) == 2

    def test_empty_keyframes_list_is_a_valid_edge_case(self):
        sequence = Sequence(event_ref="goal:home:1", keyframes=[], duration=0.0, meta={}, roster={})
        assert sequence.keyframes == []


class TestMonotonicity:
    def test_strictly_increasing_timestamps_are_accepted(self):
        Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(1)), _keyframe(0.5, _players(1)), _keyframe(1.0, _players(1))],
            duration=1.0,
            meta={},
            roster=_roster(1),
        )

    def test_repeated_timestamps_are_accepted_non_decreasing_not_strict(self):
        Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(1)), _keyframe(0.5, _players(1)), _keyframe(0.5, _players(1))],
            duration=0.5,
            meta={},
            roster=_roster(1),
        )

    def test_out_of_order_timestamps_are_rejected(self):
        with pytest.raises(ValueError):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(1.0, _players(1)), _keyframe(0.5, _players(1))],
                duration=1.0,
                meta={},
                roster=_roster(1),
            )


class TestPlayerConsistency:
    def test_same_player_set_across_all_keyframes_is_accepted(self):
        Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(1, 2, 3)), _keyframe(1.0, _players(1, 2, 3))],
            duration=1.0,
            meta={},
            roster=_roster(1, 2, 3),
        )

    def test_a_keyframe_with_a_different_player_set_is_rejected(self):
        with pytest.raises(ValueError):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1, 2, 3)), _keyframe(1.0, _players(1, 2))],
                duration=1.0,
                meta={},
                roster=_roster(1, 2, 3),
            )

    def test_a_keyframe_with_an_extra_player_is_rejected(self):
        with pytest.raises(ValueError):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1, 2)), _keyframe(1.0, _players(1, 2, 99))],
                duration=1.0,
                meta={},
                roster=_roster(1, 2, 99),
            )


class TestRosterCompleteness:
    """Sequence.roster doit porter une entrée pour chaque joueur suivi par
    les keyframes -- une Sequence bâtie sans roster complet est un bug de
    génération et ne doit jamais pouvoir exister (voir __post_init__,
    invariant 3), pas seulement planter plus tard au premier appel à
    interpolate()."""

    def test_a_fully_covered_roster_is_accepted(self):
        Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(1, 2))],
            duration=0.0,
            meta={},
            roster=_roster(1, 2),
        )

    def test_forgetting_to_fill_the_roster_fails_at_construction_not_at_frame_sixty(self):
        with pytest.raises(ValueError, match="roster"):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1, 2))],
                duration=0.0,
                meta={},
                roster={},
            )

    def test_a_roster_missing_only_one_of_several_players_still_fails(self):
        with pytest.raises(ValueError, match="roster"):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1, 2, 3))],
                duration=0.0,
                meta={},
                roster=_roster(1, 2),  # 3 manque
            )

    def test_an_empty_sequence_needs_no_roster(self):
        # Aucun joueur suivi -- rien à décrire, roster vide légitime.
        Sequence(event_ref="ref", keyframes=[], duration=0.0, meta={}, roster={})


class TestBackground:
    """Point 1 du bilan simulation physique (23/09/2026) : `Sequence.background`
    porte les joueurs "décor" (drift, pas de keyframes) -- couvert par les
    mêmes exigences que les keyframes : roster complet (invariant 4) et
    jamais le même joueur des deux côtés (invariant 3)."""

    def test_background_defaults_to_empty_when_omitted(self):
        sequence = Sequence(
            event_ref="ref", keyframes=[_keyframe(0.0, _players(1))], duration=0.0, meta={}, roster=_roster(1)
        )
        assert sequence.background == {}

    def test_a_fully_covered_background_is_accepted(self):
        Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(1))],
            duration=1.0,
            meta={},
            roster=_roster(1, 2),
            background={2: BackgroundTrack(start=(0.5, 0.5), drift=(0.02, 0.0))},
        )

    def test_a_background_player_missing_from_roster_fails_at_construction(self):
        with pytest.raises(ValueError, match="roster"):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1))],
                duration=1.0,
                meta={},
                roster=_roster(1),  # 2 manque
                background={2: BackgroundTrack(start=(0.5, 0.5), drift=(0.02, 0.0))},
            )

    def test_a_player_tracked_by_both_keyframes_and_background_is_rejected(self):
        # Un seul mode de suivi par joueur -- sinon quelle est sa "vraie"
        # position ? (voir invariant 3, Sequence.__post_init__)
        with pytest.raises(ValueError, match="background"):
            Sequence(
                event_ref="ref",
                keyframes=[_keyframe(0.0, _players(1))],
                duration=1.0,
                meta={},
                roster=_roster(1),
                background={1: BackgroundTrack(start=(0.5, 0.5), drift=(0.02, 0.0))},
            )


class TestPlayerIdsMatchTheSquad:
    """"Cohérence des ids joueurs avec la compo" : les ids utilisés dans une
    Sequence construite à partir d'un effectif réel doivent tous
    correspondre à un joueur effectivement sur le terrain -- pas une
    contrainte imposée par Sequence elle-même (qui ne connaît pas la compo),
    mais une propriété que toute construction réaliste doit respecter."""

    def _squad_ids(self) -> set[int]:
        # Effectif synthétique façon tests/test_events_zone.py, avec des ids
        # explicites (Player.id est None par défaut dans ce helper partagé,
        # ici on en a besoin de vrais pour vérifier la cohérence).
        return set(range(1, 12))  # 11 titulaires, ids 1 à 11

    def test_sequence_built_from_a_real_squad_only_references_players_on_the_pitch(self):
        squad_ids = self._squad_ids()
        sequence = Sequence(
            event_ref="goal:home:7",
            keyframes=[
                _keyframe(0.0, _players(*squad_ids), owner_id=3),
                _keyframe(2.0, _players(*squad_ids), owner_id=7),
            ],
            duration=2.0,
            meta={},
            roster=_roster(*squad_ids),
        )
        used_ids = {player_id for kf in sequence.keyframes for player_id in kf.players}
        assert used_ids <= squad_ids
        assert all(kf.ball.owner_id in squad_ids for kf in sequence.keyframes)

    def test_a_player_id_absent_from_the_squad_is_a_construction_mistake_not_caught_by_sequence_itself(self):
        # Sequence ne connaît pas la compo : rien ne l'empêche d'accepter un
        # id inventé (ni de lui trouver un nom/poste plausible dans roster)
        # -- c'est à l'appelant (le futur build_sequence) de garantir la
        # cohérence, documenté ici pour que ça reste explicite. Ce que
        # Sequence exige, c'est seulement que roster COUVRE les ids utilisés
        # (voir TestRosterCompleteness), pas qu'ils soient réels.
        squad_ids = self._squad_ids()
        bogus_id = max(squad_ids) + 1000
        sequence = Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, _players(bogus_id))],
            duration=0.0,
            meta={},
            roster=_roster(bogus_id),
        )
        used_ids = {player_id for kf in sequence.keyframes for player_id in kf.players}
        assert not used_ids <= squad_ids


class TestToJson:
    def _sample_sequence(self) -> Sequence:
        return Sequence(
            event_ref="goal:home:23:34",
            keyframes=[
                _keyframe(0.0, {1: (0.4, 0.5), 2: (0.6, 0.5)}, tag="recuperation", owner_id=1),
                _keyframe(1.2, {1: (0.7, 0.5), 2: (0.8, 0.5)}, tag="tir", owner_id=None),
            ],
            duration=1.2,
            meta={"club_name": "Home FC"},
            roster={
                1: RosterEntry(nom="Buteur", poste="BU", role="scorer", numero=9, team_side="scorer"),
                2: RosterEntry(nom="Passeur", poste="MOC", role="assist", numero=10, team_side="scorer"),
            },
        )

    def test_round_trips_through_real_json_encoding_unchanged(self):
        sequence = self._sample_sequence()
        payload = sequence.to_json()
        reencoded = json.loads(json.dumps(payload))
        assert reencoded == payload

    def test_is_deterministic_across_calls(self):
        sequence = self._sample_sequence()
        assert sequence.to_json() == sequence.to_json()

    def test_top_level_shape_matches_the_documented_contract(self):
        payload = self._sample_sequence().to_json()
        assert set(payload) == {"event_ref", "duration", "meta", "roster", "background", "keyframes"}
        assert payload["event_ref"] == "goal:home:23:34"
        assert payload["duration"] == 1.2
        assert payload["meta"] == {"club_name": "Home FC"}
        assert len(payload["keyframes"]) == 2

    def test_roster_shape_matches_the_documented_contract(self):
        payload = self._sample_sequence().to_json()
        assert payload["roster"] == {
            "1": {"nom": "Buteur", "poste": "BU", "role": "scorer", "numero": 9, "team_side": "scorer"},
            "2": {"nom": "Passeur", "poste": "MOC", "role": "assist", "numero": 10, "team_side": "scorer"},
        }

    def test_background_is_empty_when_the_sequence_has_no_background_players(self):
        payload = self._sample_sequence().to_json()
        assert payload["background"] == {}

    def test_background_shape_matches_the_documented_contract(self):
        sequence = Sequence(
            event_ref="ref",
            keyframes=[_keyframe(0.0, {1: (0.4, 0.5)})],
            duration=1.0,
            meta={},
            roster={
                1: RosterEntry(nom="Buteur", poste="BU", role="scorer", numero=9, team_side="scorer"),
                2: RosterEntry(nom="Decor", poste="DC", role=None, numero=4, team_side="opponent"),
            },
            background={2: BackgroundTrack(start=(0.2, 0.3), drift=(0.04, -0.01))},
        )
        payload = sequence.to_json()
        assert payload["background"] == {"2": {"start": [0.2, 0.3], "drift": [0.04, -0.01]}}
        for value in payload["background"]["2"].values():
            assert isinstance(value, list)

    def test_keyframe_shape_matches_the_documented_contract(self):
        payload = self._sample_sequence().to_json()
        kf = payload["keyframes"][0]
        assert set(kf) == {"t", "tag", "ball", "players"}
        assert kf["t"] == 0.0
        assert kf["tag"] == "recuperation"
        assert set(kf["ball"]) == {"x", "y", "z", "spin", "owner_id"}
        assert kf["ball"]["owner_id"] == "1"  # PlayerId int converti en chaîne
        assert kf["players"] == {"1": [0.4, 0.5], "2": [0.6, 0.5]}

    def test_none_owner_id_stays_none_not_the_string_none(self):
        payload = self._sample_sequence().to_json()
        assert payload["keyframes"][1]["ball"]["owner_id"] is None

    def test_player_position_is_a_list_not_a_tuple(self):
        payload = self._sample_sequence().to_json()
        position = payload["keyframes"][0]["players"]["1"]
        assert position == [0.4, 0.5]
        assert isinstance(position, list)
