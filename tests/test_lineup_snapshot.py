"""Compo persistée dans le Match (brief Étape B, 07/10/2026) : le `Lineup`
de la simulation est figé, survit à un aller-retour JSON champ à champ, et
n'est jamais recalculé par `pick_best_formation` côté lecture."""

import dataclasses
import random

import numpy as np
import pytest

from ligue1sim import lineup as lineup_module
from ligue1sim import simulation
from ligue1sim.clubs import Club
from ligue1sim.lineup_snapshot import (
    SCHEMA_VERSION,
    LineupNotPersistedError,
    persisted_lineups,
    require_persisted_lineups,
)
from ligue1sim.match_persistence import match_from_dict, match_from_json, match_to_dict, match_to_json
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match


def _player(poste: str, note: float, name: str, club: str, idx: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=20 + idx % 15, poste=poste, note=note, club=club,
        championnat="TEST", poste_secondaire=("MC",) if poste == "MOC" else (), categorie="buteur_axial" if poste == "BU" else None,
        id=1000 + idx if idx % 3 else None,  # mélange id connu / repli sur le nom
        attributes={"Finishing": 60 + idx, "Pace": np.int64(70)} if idx % 2 else None,  # numpy : doit être sérialisé
        preferred_moves="Tente des tirs de loin" if idx % 4 == 0 else None, valeur_marchande=12.5, pied="G", weak_foot=3.0,
    )


def _club(name: str) -> Club:
    spec = [("GK", 2), ("DC", 4), ("LB", 2), ("RB", 2), ("MDC", 2), ("MC", 4), ("MOC", 2), ("AG", 2), ("AD", 2), ("BU", 3)]
    players, i = [], 0
    for poste, n in spec:
        for k in range(n):
            players.append(_player(poste, 60.0 + (i * 7) % 25 + 0.25, f"{name}_{poste}{k}", name, i + (0 if name.startswith("Home") else 600)))  # ids uniques entre clubs (600 % 12 == 0 : même mélange id/None)
            i += 1
    return Club(name=name, players=players)


@pytest.fixture
def played(monkeypatch):
    """Simule un vrai match via `simulate_match` et capture, côté simulation,
    les `Lineup` retournés par `pick_best_formation` (référence indépendante
    du snapshot persisté)."""
    home, away = _club("Home FC"), _club("Away FC")
    used: list = []
    real = simulation.pick_best_formation

    def spy(club, unavailable=frozenset()):
        lineup = real(club, unavailable)
        used.append(lineup)
        return lineup

    monkeypatch.setattr(simulation, "pick_best_formation", spy)
    random.seed(11)
    np.random.seed(11)
    hg, ag, events = simulate_match(home, away, LeagueContext.from_clubs([home, away]))
    match = Match("Home FC", "Away FC", hg, ag, events)
    monkeypatch.undo()
    return home, away, match, used[0], used[1]


def test_snapshot_is_taken_at_simulation_and_equals_the_lineup_used(played):
    _, _, match, home_used, away_used = played
    home_snap, away_snap = match.events.home_lineup_snapshot, match.events.away_lineup_snapshot
    assert home_snap.schema_version == away_snap.schema_version == SCHEMA_VERSION
    assert home_snap.lineup == home_used
    assert away_snap.lineup == away_used
    assert len(home_snap.starters) == len(away_snap.starters) == 11
    assert [s.name for s in home_snap.starters] == [p.name for p in home_used.players]
    entered = {s.player_name for s in match.events.home_lineup if not s.started}
    assert {p.name for p in home_snap.entered_substitutes} == entered


def test_roundtrip_json_rebuilds_identical_lineup_even_if_squad_changed_since(played, monkeypatch):
    home, away, match, home_used, away_used = played
    text = match_to_json(match)

    # L'effectif change entre-temps : on vide le club et on bouleverse les notes.
    home.players.clear()
    away.players[:] = [dataclasses.replace(p, note=1.0) for p in away.players]

    # Et toute tentative de recalcul est interdite côté lecture.
    def forbidden(*_a, **_k):
        raise AssertionError("pick_best_formation appelé à la relecture")

    monkeypatch.setattr(lineup_module, "pick_best_formation", forbidden)
    monkeypatch.setattr(simulation, "pick_best_formation", forbidden)

    reloaded = match_from_json(text)
    home_l, away_l = require_persisted_lineups(reloaded)

    for rebuilt, original in ((home_l, home_used), (away_l, away_used)):
        for f in dataclasses.fields(original):  # champ à champ, message explicite
            assert getattr(rebuilt, f.name) == getattr(original, f.name), f.name
        assert rebuilt == original
        assert [dataclasses.asdict(p) for p in rebuilt.players] == [dataclasses.asdict(p) for p in original.players]
    assert reloaded.events == match.events  # tout MatchEvents survit, pas seulement la compo


def test_roundtrip_is_stable_and_scores_untouched(played):
    _, _, match, *_ = played
    assert match_to_dict(match_from_dict(match_to_dict(match))) == match_to_dict(match)
    reloaded = match_from_json(match_to_json(match))
    assert (reloaded.home_goals, reloaded.away_goals) == (match.home_goals, match.away_goals)
    assert reloaded.events.goals == match.events.goals


def test_legacy_match_without_snapshot_degrades_without_crash_or_recompute(played, monkeypatch):
    _, _, match, *_ = played
    data = match_to_dict(match)
    del data["events"]["home_lineup_snapshot"], data["events"]["away_lineup_snapshot"]  # document ancien

    def forbidden(*_a, **_k):
        raise AssertionError("recalcul silencieux interdit")

    monkeypatch.setattr(lineup_module, "pick_best_formation", forbidden)
    monkeypatch.setattr(simulation, "pick_best_formation", forbidden)

    legacy = match_from_dict(data)
    assert legacy.events.goals == match.events.goals  # le reste du match est intact
    assert persisted_lineups(legacy) is None
    with pytest.raises(LineupNotPersistedError):
        require_persisted_lineups(legacy)


def test_match_without_events_degrades():
    match = Match("A", "B", 1, 0)
    assert persisted_lineups(match) is None
    assert match_from_json(match_to_json(match)).events is None
    with pytest.raises(LineupNotPersistedError):
        require_persisted_lineups(match)


def test_snapshot_is_isolated_from_later_mutation_of_the_lineup(played):
    _, _, match, home_used, _ = played
    snap = match.events.home_lineup_snapshot.lineup
    assert snap.players is not home_used.players and snap.bands is not home_used.bands


def test_reloaded_lineup_feeds_the_animation_consumers_identically(played):
    """Ce que `enrich_with_background` lit d'une compo adverse : positions
    (`_opponent_positions`) et numéros -- identiques entre la compo de la
    simulation et celle rechargée du JSON."""
    from ligue1sim.animation.sequence_generator import _opponent_positions
    from ligue1sim.animation.templates import numeros_by_player_id

    _, _, match, home_used, away_used = played
    home_l, away_l = require_persisted_lineups(match_from_json(match_to_json(match)))
    for rebuilt, original in ((home_l, home_used), (away_l, away_used)):
        assert _opponent_positions(rebuilt) == _opponent_positions(original)
        assert numeros_by_player_id(rebuilt) == numeros_by_player_id(original)


# --- Tâche 2 (Étape B bis) : qui est sur le terrain à la minute m ---------


def test_substitution_events_are_persisted_with_the_match(played):
    _, _, match, *_ = played
    assert match.events.substitutions, "le moteur produit toujours des remplacements avec ce banc"
    reloaded = match_from_json(match_to_json(match))
    assert reloaded.events.substitutions == match.events.substitutions  # (club_name, player_off, player_on, minute, zone)
    assert reloaded.events.cards == match.events.cards


def test_players_on_pitch_follows_substitutions_and_survives_reload(played):
    from ligue1sim.lineup_snapshot import players_on_pitch

    _, _, match, home_used, away_used = played
    reloaded = match_from_json(match_to_json(match))
    for used in (home_used, away_used):
        club = used.club_name
        assert [p.name for p in players_on_pitch(reloaded, club, 0)] == [p.name for p in used.players]
        for sub in (s for s in reloaded.events.substitutions if s.club_name == club):
            before = {p.name for p in players_on_pitch(reloaded, club, sub.minute - 1)}
            after = {p.name for p in players_on_pitch(reloaded, club, sub.minute)}
            assert sub.player_on not in before
            assert sub.player_on in after and sub.player_off not in after
        for minute in (0, 30, 60, 90):
            assert (
                players_on_pitch(reloaded, club, minute) == players_on_pitch(match, club, minute)
            )  # identique avant/après rechargement
        final = [p.name for p in players_on_pitch(reloaded, club, 90)]
        assert len(final) == len(set(final))  # jamais deux fois le même joueur
        entrants = {s.player_on for s in reloaded.events.substitutions}
        sent_off = {c.player for c in reloaded.events.cards if c.club_name == club and c.card_type != "yellow"}
        assert not (sent_off - entrants) & set(final)  # un expulsé reste hors du terrain


def test_players_on_pitch_refuses_legacy_match_and_unknown_club(played):
    from ligue1sim.lineup_snapshot import players_on_pitch

    _, _, match, *_ = played
    with pytest.raises(ValueError):
        players_on_pitch(match, "Autre FC", 10)
    with pytest.raises(LineupNotPersistedError):
        players_on_pitch(Match("A", "B", 1, 0), "A", 10)


# --- Tâche 3 : déterminisme de enrich_with_background ----------------------

_ENRICH_SCRIPT = """
import hashlib, json, sys
from ligue1sim.animation.sequence_generator import MatchState, deterministic_rng, enrich_with_background, generate_sequence
from ligue1sim.animation.spatial import PitchLayoutState
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.lineup_snapshot import require_persisted_lineups
from ligue1sim.match_persistence import match_from_json
from ligue1sim.pitch_geometry import Zone
from ligue1sim.pitch_layout import place_starting_xi

match = match_from_json(open(sys.argv[1], encoding="utf-8").read())
scorer_lineup, opponent_lineup = require_persisted_lineups(match)
field = [p for p in scorer_lineup.players if p.group != "GK"]
event = GoalEvent(club_name=scorer_lineup.club_name, scorer=field[-1].name, assist=field[-2].name, minute=41,
                  zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3))
stats = [PlayerMatchStat(player_name=p.name, club_name=scorer_lineup.club_name, poste=p.poste, started=True,
                         band=scorer_lineup.bands.get(p.name)) for p in scorer_lineup.players]
state = PitchLayoutState(placed_players=tuple(place_starting_xi(stats, attacking_up=False)), attacking_up=False)
digests = []
for _ in range(2):  # deux appels successifs dans le même process
    seq = generate_sequence(event, scorer_lineup, state, MatchState(goal_diff_before=0, minute=41, competition_type="league"),
                            deterministic_rng("m", 0), match_id="m", event_index=0)
    digests.append(hashlib.sha256(json.dumps(enrich_with_background(seq, opponent_lineup).to_json(), sort_keys=True).encode()).hexdigest())
print(digests[0], digests[1])
"""


def _run_enrich(path, hashseed: str) -> tuple[str, str]:
    import os
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-c", _ENRICH_SCRIPT, str(path)], capture_output=True, text=True, check=True,
        env={**os.environ, "PYTHONHASHSEED": hashseed},
    ).stdout.split()
    return out[0], out[1]


def test_enrich_with_background_is_deterministic_on_a_reloaded_lineup(played, tmp_path):
    """Deux appels sur la même compo rechargée -> séquences strictement égales
    (positions x/y et drifts compris), dans le process courant."""
    from ligue1sim.animation.sequence_generator import MatchState, deterministic_rng, enrich_with_background, generate_sequence
    from ligue1sim.animation.spatial import PitchLayoutState
    from ligue1sim.events import GoalEvent, PlayerMatchStat
    from ligue1sim.pitch_geometry import Zone
    from ligue1sim.pitch_layout import place_starting_xi

    _, _, match, *_ = played
    scorer, opponent = require_persisted_lineups(match_from_json(match_to_json(match)))
    field = [p for p in scorer.players if p.group != "GK"]
    event = GoalEvent(club_name=scorer.club_name, scorer=field[-1].name, assist=field[-2].name, minute=41,
                      zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3))
    stats = [PlayerMatchStat(player_name=p.name, club_name=scorer.club_name, poste=p.poste, started=True,
                             band=scorer.bands.get(p.name)) for p in scorer.players]
    state = PitchLayoutState(placed_players=tuple(place_starting_xi(stats, attacking_up=False)), attacking_up=False)

    def once():
        seq = generate_sequence(event, scorer, state, MatchState(goal_diff_before=0, minute=41, competition_type="league"),
                                deterministic_rng("m", 0), match_id="m", event_index=0)
        return enrich_with_background(seq, opponent)

    first, second = once(), once()
    assert first == second
    assert first.to_json() == second.to_json()
    assert len(first.roster) == 22


@pytest.mark.parametrize("hashseed", ["0", "1", "42", "2026"])
def test_enrich_with_background_is_stable_across_processes(played, tmp_path, hashseed):
    """Même séquence quel que soit PYTHONHASHSEED (ordre d'itération des
    `set`/dict de str) : détecte toute dépendance à l'ordre de hachage."""
    _, _, match, *_ = played
    path = tmp_path / "match.json"
    path.write_text(match_to_json(match), encoding="utf-8")
    reference = _run_enrich(path, "0")
    assert reference[0] == reference[1]
    assert _run_enrich(path, hashseed) == reference


def test_engine_substitutes_an_already_sent_off_player_and_the_helper_does_not_hide_it(played):
    """Incohérence du moteur (seed 11) : un joueur expulsé puis « remplacé »
    plus tard. Documenté, pas masqué : l'helper suit les événements persistés,
    l'entrant joue à partir de la minute du remplacement."""
    from ligue1sim.lineup_snapshot import players_on_pitch

    _, _, match, *_ = played
    red = {(c.club_name, c.player): c.minute for c in match.events.cards if c.card_type != "yellow"}
    anomalies = [
        s for s in match.events.substitutions if (s.club_name, s.player_off) in red and red[(s.club_name, s.player_off)] < s.minute
    ]
    assert anomalies, "ce seed doit produire le cas (sinon le test ne prouve plus rien)"
    for s in anomalies:
        names = {p.name for p in players_on_pitch(match, s.club_name, s.minute)}
        assert s.player_off not in names and s.player_on in names
