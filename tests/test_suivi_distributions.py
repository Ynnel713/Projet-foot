"""Distributions de référence du suivi réel (ticket v2-realisme/27b) : scènes synthétiques à valeur connue, mêmes
fonctions que le moteur, aucun réseau."""

from __future__ import annotations

import csv
import json

import pytest

from scripts import suivi_distributions as sd
from scripts import suivi_reel as sr
from scripts import v2_indicators as vi
from v2engine.geometry import Vec2

# 4-4-2 vu de son propre but : défense à 20 m, milieu à 35 m, attaque à 50 m ; largeur 40 m (de y = 14 à 54)
LINES = [(20.0, y) for y in (14.0, 27.0, 41.0, 54.0)] + [(35.0, y) for y in (14.0, 27.0, 41.0, 54.0)] \
    + [(50.0, 30.0), (50.0, 38.0)]


def test_shape_of_a_known_block_home_and_away_on_a_106_m_pitch():
    expected = {"longueur (m)": 30.0, "largeur (m)": 40.0, "hauteur de la ligne défensive (m)": 20.0,
                "écart défense-milieu (m)": 15.0, "écart milieu-attaque (m)": 15.0}
    assert sd.shape(sr.HOME, LINES, 106.0, 68.0) == pytest.approx(expected)
    # la même équipe à l'extérieur, terrain réel de 106 m : rotation de 180°, hauteur toujours comptée depuis son but
    away = [(106.0 - x, 68.0 - y) for x, y in LINES]
    assert sd.shape(sr.AWAY, away, 106.0, 68.0) == pytest.approx(expected)
    # `progress` du moteur suppose 105 m : sans la rotation, la hauteur serait fausse de 1 m
    assert vi.block_height("away", [Vec2(x, y) for x, y in away]) == pytest.approx(19.0)


def test_shared_functions_are_those_of_the_engine_indicators():
    # aucune réécriture parallèle : le script du réel appelle les fonctions de `v2_indicators`
    for name in ("length_width", "line_gaps", "block_height", "nearest_distance", "quartiles", "speed_shares"):
        assert getattr(sd, name) is getattr(vi, name)


def test_nearest_distance():
    assert vi.nearest_distance(Vec2(0.0, 0.0), [Vec2(3.0, 4.0), Vec2(6.0, 8.0)]) == 5.0
    assert vi.nearest_distance(Vec2(0.0, 0.0), []) is None


def test_quartiles():
    assert vi.quartiles([1.0, 2.0, 3.0, 4.0, 5.0]) == {"n": 5, "q1": 2.0, "mediane": 3.0, "q3": 4.0}
    assert vi.quartiles([7.0]) == {"n": 1, "q1": 7.0, "mediane": 7.0, "q3": 7.0}
    assert vi.quartiles([]) == {"n": 0}


def test_speed_shares_thresholds():
    kmh = 1 / 3.6
    assert vi.speed_shares([10 * kmh, 20 * kmh, 26 * kmh, 30 * kmh]) == (0.75, 0.5)
    assert vi.speed_shares([]) is None


def test_poste_family_covers_engine_and_skillcorner_postes():
    assert set(sd.SKILLCORNER_POSTE.values()) <= set(vi.POSTE_FAMILY)
    assert vi.POSTE_FAMILY[sd.SKILLCORNER_POSTE["LM"]] == "milieu"
    assert vi.POSTE_FAMILY[sd.SKILLCORNER_POSTE["RWB"]] == "latéral"
    assert "SUB" not in sd.SKILLCORNER_POSTE


def test_track_speeds_constant_velocity_and_filters():
    fps = 10.0
    track = [(i / fps, 5.0 * i / fps, 0.0, True) for i in range(30)]  # 5 m/s le long de x
    speeds = sd.track_speeds(track, fps)
    assert len(speeds) == 30 - 4 and all(v == pytest.approx(5.0) for v in speeds)
    # une image non détectée retire toutes les fenêtres qui la contiennent (2k + 1 = 5)
    hidden = [t if i != 15 else (t[0], t[1], t[2], False) for i, t in enumerate(track)]
    assert len(sd.track_speeds(hidden, fps)) == 26 - 5
    # une image manquante (trou de temps) : les fenêtres qui l'enjambent sont écartées
    gap = track[:15] + track[16:]
    assert all(v == pytest.approx(5.0) for v in sd.track_speeds(gap, fps))
    assert len(sd.track_speeds(gap, fps)) == 29 - 4 - 4
    # au-dessus de 12 m/s : bruit, écarté
    fast = [(i / fps, 13.0 * i / fps, 0.0, True) for i in range(30)]
    assert sd.track_speeds(fast, fps) == []


def _player(pid, team, x, y, detected=True, role=None):
    return sr.Player(pid, team, x, y, detected, role)


def _frame(players, holder, period=1, possession=sr.HOME, phase="create"):
    return sr.Frame("skillcorner", "1", period, 0.0, None, tuple(players), possession, phase, holder)


def test_around_holder_support_presser_and_reception():
    players = [_player("h1", sr.HOME, 50.0, 30.0), _player("h2", sr.HOME, 60.0, 30.0),
               _player("a1", sr.AWAY, 52.0, 30.0), _player("gk", sr.AWAY, 51.0, 30.0)]
    acc, last = sd.Accumulator(), {}
    sd._around_holder(acc, _frame(players, "h2"), {"gk"}, last)  # premier porteur : pas de réception
    sd._around_holder(acc, _frame(players, "h1"), {"gk"}, last)  # passe h2 -> h1 : réception
    sd._around_holder(acc, _frame(players, "h1"), {"gk"}, last)  # toujours h1 : pas de nouvelle réception
    values = acc.values
    # le gardien compte pour le receveur (1 m), pas comme presseur (adversaire de champ : 2 m)
    assert values["skillcorner | réception | distance au plus proche adversaire (m)"] == [1.0]
    assert values["skillcorner | porteur | toutes | distance presseur-porteur (m)"] == [8.0, 2.0, 2.0]
    assert values["skillcorner | porteur | toutes | presseur à moins de 3 m (part)"] == [0.0, 1.0, 1.0]
    assert values["skillcorner | porteur | toutes | soutien le plus proche (m)"] == [10.0] * 3
    assert len(values["skillcorner | porteur | phase create | soutien le plus proche (m)"]) == 3


def test_reception_needs_same_team_same_period_and_a_detected_receiver():
    players = [_player("h1", sr.HOME, 50.0, 30.0), _player("h2", sr.HOME, 60.0, 30.0, detected=False),
               _player("a1", sr.AWAY, 52.0, 30.0)]
    label = "skillcorner | réception | distance au plus proche adversaire (m)"
    acc, last = sd.Accumulator(), {}
    sd._around_holder(acc, _frame(players, "a1"), set(), last)
    sd._around_holder(acc, _frame(players, "h1"), set(), last)  # interception : pas une réception
    sd._around_holder(acc, _frame(players, "h2"), set(), last)  # receveur hors caméra : non mesuré
    sd._around_holder(acc, _frame(players, "h1", period=2), set(), last)  # nouvelle période : pas de porteur précédent
    assert label not in acc.values


def test_shapes_variants_and_phases():
    home = [_player(f"h{i}", sr.HOME, x, y) for i, (x, y) in enumerate(LINES)]
    away = [_player(f"a{i}", sr.AWAY, 105.0 - x, 68.0 - y, detected=i > 0) for i, (x, y) in enumerate(LINES)]
    keepers = [_player("gk", sr.HOME, 2.0, 34.0)]
    match = sr.Match("skillcorner", "1", 105.0, 68.0)
    acc = sd.Accumulator()
    sd._shapes(acc, _frame(home + away + keepers, None, phase="build_up"), match, {"gk"})
    v = acc.values
    assert v["skillcorner | forme | équipe détectée | avec ballon | largeur (m)"] == [40.0]
    assert v["skillcorner | forme | toutes positions | avec ballon, phase build_up | hauteur de la ligne défensive (m)"] == [20.0]
    assert v["skillcorner | forme | toutes positions | sans ballon | longueur (m)"] == [pytest.approx(30.0)]
    assert "skillcorner | forme | équipe détectée | sans ballon | longueur (m)" not in v  # un joueur hors caméra
    # 9 joueurs de champ : forme non mesurée
    acc = sd.Accumulator()
    sd._shapes(acc, _frame(home[1:], None), match, set())
    assert not acc.values


def _metrica_fixture(root, frames=60):
    """Deux équipes de 11 joueurs ; le gardien de chaque équipe près de son but. Format brut Metrica (x, y dans [0, 1])."""
    folder = root / "metrica" / "Sample_Game_1"
    folder.mkdir(parents=True)
    for side, sign in (("Home", 1), ("Away", -1)):
        names = [f"Player{i}" for i in range(11)]
        with (folder / f"Sample_Game_1_RawTrackingData_{side}_Team.csv").open("w", newline="") as stream:
            w = csv.writer(stream)
            w.writerow(["", "", "", side] + [""] * 23)
            w.writerow(["", "", ""] + [n for n in names for _ in (0, 1)] + ["", ""])
            w.writerow(["Period", "Frame", "Time [s]"] + [n for n in names for _ in (0, 1)] + ["Ball", ""])
            for f in range(frames):
                row = [1, f + 1, f / 25.0]
                for i in range(11):  # domicile dans sa moitié gauche, extérieur dans la droite ; Player0 = gardien
                    depth = 0.05 if i == 0 else 0.2 + 0.02 * i
                    row += [0.5 - sign * (0.5 - depth) + 0.001 * f, 0.1 + 0.07 * i]
                row += [0.5, 0.5]
                w.writerow(row)
    return root


def test_metrica_goalkeepers_and_determinism(tmp_path):
    root = _metrica_fixture(tmp_path)
    assert sd._metrica_goalkeepers(1, root) == {"home-Player0", "away-Player0"}
    first, second = sd.report(sd.measure_match("metrica", "1", root)), sd.report(sd.measure_match("metrica", "1", root))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    speed = first["distributions"]["metrica | vitesse | joueurs de champ | vitesse (m/s)"]
    assert speed["mediane"] == pytest.approx(0.001 * 105.0 * 25.0)  # 0,001 de la longueur par image à 25 images/s
    assert speed["part > 19,8 km/h"] == 0.0
    assert first["volumes"] == {"metrica | images": 60, "metrica | matchs": 1}
