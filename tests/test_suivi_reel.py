"""Lecteur des données de suivi réelles (ticket v2-realisme/27a), sur des données synthétiques : aucun réseau."""

from __future__ import annotations

import csv
import hashlib
import json

import pytest

from scripts import suivi_reel as sr


def test_to_engine_centre_and_rotation():
    assert sr.to_engine(0.0, 0.0, True, 105.0, 68.0) == (52.5, 34.0)
    # y de l'entrée vers le haut, y du moteur vers le bas
    assert sr.to_engine(10.0, 5.0, True, 105.0, 68.0) == (62.5, 29.0)
    # l'équipe à domicile attaque vers les x négatifs : rotation de 180°, pas un miroir
    assert sr.to_engine(10.0, 5.0, False, 105.0, 68.0) == (42.5, 39.0)
    # mètres réels gardés sur un terrain non standard
    assert sr.to_engine(0.0, 0.0, True, 100.0, 64.0) == (50.0, 32.0)


def test_left_back_stays_on_the_engine_left_in_both_periods():
    # convention du moteur (`v2engine.formation`) : en attaquant vers +x, la gauche de l'équipe est en y petit.
    # SkillCorner : y vers le haut ; latéral gauche à domicile en y > 0 quand elle joue de gauche à droite.
    assert sr.to_engine(-30.0, 25.0, True, 105.0, 68.0)[1] == 9.0
    assert sr.to_engine(30.0, -25.0, False, 105.0, 68.0)[1] == 9.0  # deuxième période, côtés inversés


def test_lfs_pointer():
    text = b"version https://git-lfs.github.com/spec/v1\noid sha256:abc123\nsize 42\n"
    assert sr.lfs_pointer(text) == ("abc123", 42)
    with pytest.raises(ValueError):
        sr.lfs_pointer(b'{"id": 1}')


def _skillcorner_fixture(root):
    folder = root / "skillcorner" / "7"
    folder.mkdir(parents=True)
    (root / "skillcorner" / "matches.json").write_text(json.dumps([{"id": 7}]), encoding="utf-8")
    meta = {"home_team": {"id": 1}, "away_team": {"id": 2}, "pitch_length": 105, "pitch_width": 68,
            "home_team_side": ["left_to_right", "right_to_left"],
            "players": [{"id": 10, "team_id": 1, "player_role": {"acronym": "GK"}},
                        {"id": 20, "team_id": 2, "player_role": {"acronym": "CF"}}]}
    (folder / "7_match.json").write_text(json.dumps(meta), encoding="utf-8")
    with (folder / "7_phases_of_play.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame_start", "frame_end", "team_in_possession_id", "team_in_possession_phase_type"])
        writer.writerow([1, 2, 1, "build_up"])
        writer.writerow([5, 6, 2, "finish"])

    def frame(no, period, stamp, group, gk_x, holder=None):
        return {"frame": no, "timestamp": stamp, "period": period,
                "ball_data": {"x": 1.0, "y": 2.0, "z": 0.1, "is_detected": True},
                "possession": {"player_id": holder, "group": group},
                "player_data": [{"x": gk_x, "y": 3.0, "player_id": 10, "is_detected": True},
                                {"x": 5.0, "y": -4.0, "player_id": 20, "is_detected": False}]}

    rows = [{"frame": 0, "timestamp": None, "period": None, "ball_data": {"x": None}, "possession": {}, "player_data": []},
            frame(1, 1, "00:00:00.10", "home team", -40.0),
            frame(3, 1, "00:00:00.30", None, -40.0),
            frame(5, 2, "00:45:00.00", "away team", 40.0, holder=20)]
    (folder / "7_tracking_extrapolated.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_read_skillcorner(tmp_path):
    _skillcorner_fixture(tmp_path)
    frames = list(sr.read_skillcorner("7", tmp_path))
    assert [f.period for f in frames] == [1, 1, 2]  # l'image sans période est ignorée
    first, gap, second = frames
    gk = first.players[0]
    assert (gk.team, gk.role, gk.detected) == (sr.HOME, "GK", True)
    assert (gk.x, gk.y) == (12.5, 31.0)
    assert first.ball == (53.5, 32.0)
    assert (first.possession, first.phase) == (sr.HOME, "build_up")
    assert (gap.possession, gap.phase) == (None, None)  # entre deux phases
    # deuxième période : l'équipe à domicile défend à droite dans la source, rotation -> toujours près de x = 0
    assert (second.players[0].x, second.players[0].y) == (12.5, 37.0)
    assert (second.possession, second.phase) == (sr.AWAY, "finish")
    assert (first.holder, second.holder) == (None, "20")  # porteur lu (ticket v2-realisme/27b)
    assert second.players[1].detected is False and second.players[1].team == sr.AWAY
    assert first.time_s == 0.0 and second.time_s == 0.0  # temps depuis le début de la période, comme Metrica
    assert sr.skillcorner_match("7", tmp_path).standard


def _metrica_file(path, team, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["", "", "", team, "", team, "", "", ""])
        writer.writerow(["", "", "", "1", "", "2", "", "", ""])
        writer.writerow(["Period", "Frame", "Time [s]", "Player1", "", "Player2", "", "Ball", ""])
        writer.writerows(rows)


def test_read_metrica(tmp_path):
    home, away = (tmp_path / "metrica" / name for name in sr._metrica_names(1))
    # période 1 : l'équipe à domicile est à gauche (x < 0,5) ; période 2 : à droite ; ballon au centre
    _metrica_file(home, "Home", [[1, 1, 0.04, 0.1, 0.5, 0.3, 0.25, 0.5, 0.5],
                                 [2, 2, 2700.0, 0.9, 0.5, 0.7, 0.75, 0.5, 0.5]])
    _metrica_file(away, "Away", [[1, 1, 0.04, 0.8, 0.5, "NaN", "NaN", 0.5, 0.5],
                                 [2, 2, 2700.0, 0.2, 0.5, 0.4, 0.5, 0.5, 0.5]])
    first, second = list(sr.read_metrica(1, tmp_path))
    by_id = {p.id: p for p in first.players}
    assert by_id["home-Player1"].x == pytest.approx(10.5) and by_id["home-Player1"].y == pytest.approx(34.0)
    assert by_id["home-Player2"].y == pytest.approx(17.0)  # Metrica et moteur : y vers le bas, aucun miroir
    assert "away-Player2" not in by_id  # position absente (NaN)
    assert first.ball == pytest.approx((52.5, 34.0))
    by_id = {p.id: p for p in second.players}
    assert by_id["home-Player1"].x == pytest.approx(10.5)  # rotation en deuxième période
    assert by_id["home-Player2"].y == pytest.approx(17.0)
    assert second.time_s == 0.0 and second.period == 2


def test_metrica_raw_y_is_kept(tmp_path):
    home, away = (tmp_path / "metrica" / name for name in sr._metrica_names(2))
    _metrica_file(home, "Home", [[1, 1, 0.04, 0.1, 0.1, 0.3, 0.5, 0.5, 0.5]])
    _metrica_file(away, "Away", [[1, 1, 0.04, 0.8, 0.5, 0.7, 0.5, 0.5, 0.5]])
    (frame,) = list(sr.read_metrica(2, tmp_path))
    assert {p.id: p for p in frame.players}["home-Player1"].y == pytest.approx(6.8)


def test_reading_is_deterministic(tmp_path):
    _skillcorner_fixture(tmp_path)
    assert list(sr.read_skillcorner("7", tmp_path)) == list(sr.read_skillcorner("7", tmp_path))


def test_summary(tmp_path):
    _skillcorner_fixture(tmp_path)
    result = sr.summary(sr.read_skillcorner("7", tmp_path))
    assert result["images"] == 3
    assert result["part_22_joueurs"] == 0.0 and result["part_20_detectes"] == 0.0
    assert result["part_ballon"] == 1.0 and result["part_phase"] == pytest.approx(0.6667)


def test_download_checks_sha256_and_is_idempotent(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"suivi")
    good = hashlib.sha256(b"suivi").hexdigest()
    target = tmp_path / "out" / "copie.bin"
    assert sr._download(source.as_uri(), target, good) == good
    source.write_bytes(b"autre contenu")  # déjà présent et juste : pas de nouveau téléchargement
    assert sr._download(source.as_uri(), target, good) == good and target.read_bytes() == b"suivi"
    with pytest.raises(ValueError):
        sr._download(source.as_uri(), tmp_path / "out" / "refus.bin", good)
    assert not (tmp_path / "out" / "refus.bin").exists()
    assert not (tmp_path / "out" / "refus.bin.part").exists()
