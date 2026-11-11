"""Tests du rendement selon la minute (ticket v2-realisme/19d) : tranches de 15 minutes, course, technique et duels par
tranche, comparaison par Stamina, et scène A/B du même joueur à la 15e et à la 85e minute."""

from __future__ import annotations

import math
from types import SimpleNamespace

from scripts import v2_indicators as ind
from scripts import v2_tranches as tr
from tests.scenes import Scene, player, run, seed_scene
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import pass_success_probability


def test_tranches_of_fifteen_minutes_and_added_time() -> None:
    assert tr.tranche(0.0) == "0-15" and tr.tranche(14.99) == "0-15" and tr.tranche(15.0) == "15-30"
    assert tr.tranche(89.9) == "75-90" and tr.tranche(90.0) == "90 et plus" and tr.tranche(97.0) == "90 et plus"


def test_stamina_bands() -> None:
    assert tr.stamina_band(20) == "Stamina 0-40" and tr.stamina_band(55) == "Stamina 55-70"
    assert tr.stamina_band(99) == "Stamina 70 et plus"


def test_running_per_minute_and_sprint_counted_where_it_starts() -> None:
    profile = tr.MinuteProfile()
    for i in range(20):  # 2 s à 8 m/s (au-dessus de 25 km/h) à cheval sur la 15e minute, puis arrêt
        profile.on_player(14.0 + 59.0 / 60.0 + i * 0.1 / 60.0, "A", "MC", 30, 8.0, 0.1)
    profile.on_player(16.0, "A", "MC", 30, 0.0, 0.1)
    profile.end_match([])
    assert profile.run[("0-15", "tous", "sprints")] == 1 and profile.run[("15-30", "tous", "sprints")] == 0
    report = tr.minute_report(profile)
    assert math.isclose(report["15-30 : distance au-dessus de 25 km/h (part)"], 1.0)
    assert math.isclose(report["0-15 : distance par joueur (m/min)"], 8.0 * 60.0)


def test_technique_and_duels_by_tranche() -> None:
    profile = tr.MinuteProfile()
    profile.on_shot(10.0, "capté")
    profile.on_shot(10.5, "à côté")
    profile.on_shot(11.0, "contré")  # hors du cadrage
    profile.count(80.0, "tacles")
    profile.count(80.0, "tacles")
    profile.count(80.0, "tacles gagnés")
    profile.count(80.0, "contrôles ratés")
    profile.end_match([{"t": 600.0, "done": True}, {"t": 610.0, "done": False}, {"t": 4800.0, "done": True}])
    report = tr.minute_report(profile)
    assert report["0-15 : tirs cadrés (part des non contrés)"] == 0.5
    assert report["0-15 : passes réussies (part)"] == 0.5
    assert report["75-90 : tacles gagnés (part)"] == 0.5
    assert report["75-90 : contrôles ratés pour 100 passes"] == 100.0


def _runner(minute_x: float) -> PlayerState:
    return PlayerState(name="A", team="home", poste="MC", position=Vec2(minute_x, 30.0), velocity=Vec2(7.0, 0.0),
                       pace=60, acceleration=60, stamina=30, home_target=Vec2(minute_x, 30.0))


def test_collector_feeds_the_profile_and_compares_stamina() -> None:
    c = ind.Collector()
    ball = SimpleNamespace(position=Vec2(52.5, 34.0), holder=None, receiver=None, restart=None)
    for minute in (5.0, 80.0):
        speed = 7.0 if minute < 15 else 5.0  # le même joueur court moins vite en fin de match
        p = PlayerState(name="A", team="home", poste="MC", position=Vec2(50.0, 30.0), velocity=Vec2(speed, 0.0),
                        pace=60, acceleration=60, stamina=30, home_target=Vec2(50.0, 30.0))
        c.on_tick(minute * 60.0, [p], ball, None)
    c.end_match()
    report = tr.minute_report(c.minutes, postes=("MC",))
    assert math.isclose(report["MC : distance (m/min), 75-90 / 0-15"], 5.0 / 7.0)
    assert math.isclose(report["Stamina 0-40 : distance (m/min), 75-90 / 0-15"], 5.0 / 7.0)
    assert not any(k.startswith("Stamina 70 et plus :") for k in report)  # aucun joueur dans cette tranche


def _two_players(profile: tr.MinuteProfile, minute: float) -> None:
    profile.on_player(minute, "A", "BU", 20, 3.0, 60.0, depth=40.0)  # une minute sans ballon, à 40 m de son but
    profile.on_player(minute, "D", "DC", 90, 2.0, 60.0)  # une minute avec ballon


def test_events_are_attributed_to_the_player_his_poste_and_his_stamina() -> None:
    """Réserve du contrôle qualité (19d) : chaque indicateur par joueur et par poste, pas seulement la course."""
    profile = tr.MinuteProfile()
    for minute in (5.0, 80.0):
        _two_players(profile, minute)
    profile.on_shot(5.0, "capté", actor="A")
    profile.on_shot(80.0, "à côté", actor="A")
    profile.count(80.0, "tacles", actor="D")
    profile.count(80.0, "tacles gagnés", actor="D")
    profile.count(80.0, "contrôles ratés", actor="A")
    profile.count(80.0, "buts personnels", actor="A")
    profile.on_goal(80.0, "home", [("A", "home"), ("D", "away")])
    profile.end_match([{"t": 300.0, "passer": "D", "target": "A", "done": True},
                       {"t": 4800.0, "passer": "D", "target": "A", "done": False}])
    report = tr.minute_report(profile, postes=("BU", "DC"))
    assert report["BU : 0-15 : tirs cadrés (part des non contrés)"] == 1.0
    assert report["BU : 75-90 : tirs cadrés (part des non contrés)"] == 0.0
    assert report["BU : tirs cadrés (part des non contrés), 75-90 - 0-15"] == -1.0
    assert report["DC : 75-90 : tacles gagnés (part)"] == 1.0 and report["BU : 75-90 : tacles gagnés (part)"] is None
    assert report["DC : 0-15 : passes réussies (part)"] == 1.0 and report["DC : 75-90 : passes réussies (part)"] == 0.0
    assert report["BU : 75-90 : contrôles ratés pour 100 passes visées"] == 100.0
    assert report["Stamina 0-40 : 75-90 : position sans ballon (m depuis son but)"] == 40.0
    assert report["DC : 75-90 : position sans ballon (m depuis son but)"] is None  # jamais sans ballon
    # buts : marqué par l'équipe de A, encaissé par celle de D, pour 90 minutes jouées (1 minute jouée ici)
    assert report["BU : 75-90 : buts marqués par l'équipe pour 90 min"] == 90.0
    assert report["BU : 75-90 : buts encaissés par l'équipe pour 90 min"] == 0.0
    assert report["DC : 75-90 : buts encaissés par l'équipe pour 90 min"] == 90.0
    assert report["BU : 75-90 : buts personnels pour 90 min"] == 90.0
    assert report["75-90 : buts par match"] == 1.0  # un seul but compté pour tous


def test_player_report_and_its_summary() -> None:
    profile = tr.MinuteProfile()
    for minute, speed in ((1.0, 6.0), (6.0, 6.0), (76.0, 3.0), (81.0, 3.0)):  # 2 × 5 min par tranche comparée
        profile.on_player(minute, "A", "BU", 20, speed, 300.0)
    profile.on_player(1.0, "B", "DC", 60, 5.0, 60.0)  # 1 minute seulement : hors synthèse
    profile.on_player(76.0, "B", "DC", 60, 5.0, 60.0)
    profile.end_match([])
    out = tr.player_report(profile)
    assert out["joueurs"]["A"]["poste"] == "BU" and out["joueurs"]["A"]["Stamina"] == 20
    assert math.isclose(out["joueurs"]["A"]["comparaison"]["distance (m/min), 75-90 / 0-15"], 0.5)
    assert "comparaison" not in out["joueurs"]["B"] and "0-15" in out["joueurs"]["B"]["tranches"]
    summary = out["synthèse"]["distance (m/min), 75-90 / 0-15"]
    assert summary["joueurs"] == 1 and math.isclose(summary["médiane"], 0.5)


def test_collector_attributes_tackles_shots_goals_and_depth() -> None:
    c = ind.Collector()
    ball = SimpleNamespace(position=Vec2(52.5, 34.0), holder=None, receiver=None, restart=None)
    a = PlayerState(name="A", team="home", poste="BU", position=Vec2(30.0, 30.0), velocity=Vec2(0.0, 0.0),
                    pace=60, acceleration=60, stamina=30, home_target=Vec2(30.0, 30.0))
    d = PlayerState(name="D", team="away", poste="DC", position=Vec2(80.0, 30.0), velocity=Vec2(0.0, 0.0),
                    pace=60, acceleration=60, stamina=80, home_target=Vec2(80.0, 30.0))
    c.on_tick(60.0, [a, d], ball, None)
    c.team = "away"  # l'équipe de D a le ballon : A est sans ballon, à 30 m de son but
    c.on_tick(60.1, [a, d], ball, None)
    c.on_tackle(a)
    c.on_tackle_won(d, a)
    c.on_tick(60.2, [a, d], ball, "home")
    c.end_match()
    e = c.minutes.events
    assert e[("0-15", "joueur A", "tacles")] == 1 and e[("0-15", "BU", "tacles gagnés")] == 1
    assert e[("0-15", "DC", "buts encaissés")] == 1 and e[("0-15", "joueur A", "buts marqués")] == 1
    r = c.minutes.run
    assert math.isclose(r[("0-15", "joueur A", "profondeur")] / r[("0-15", "joueur A", "sans ballon")], 30.0)


def _scene(minute: float, stamina: int) -> Scene:
    players = [player("A", x=30.0, y=34.0, Stamina=stamina, Pace=70, Acceleration=70),
               player("B", x=45.0, y=20.0), player("G", "away", x=104.0, y=34.0, poste="GK")]
    return Scene.full(players, holder="A", start_s=minute * 60.0)


def _distance(minute: float, stamina: int) -> tuple[float, float]:
    scene = _scene(minute, stamina)
    seed_scene(19)
    start = scene.get("A").position
    run(scene, 4.0)
    fresh = _scene(minute, stamina)  # passe lue sur la scène de départ : seule la minute diffère entre A et B
    chance = pass_success_probability(fresh.get("A"), fresh.get("B"), [fresh.get("G")])
    return scene.get("A").position.distance_to(start), chance


def test_same_player_at_15_and_85_minutes_runs_less_but_passes_the_same() -> None:
    """Scène A/B (19d) : même joueur, même graine, même scène, seule la minute change. Aujourd'hui la fatigue ne réduit
    que la vitesse maximale : la course baisse à la 85e pour un Stamina bas, la probabilité de passe est identique."""
    run_15, pass_15 = _distance(15.0, 20)
    run_85, pass_85 = _distance(85.0, 20)
    assert run_85 < run_15
    assert pass_85 == pass_15
    assert _distance(85.0, 99)[0] > run_85  # un Stamina élevé perd moins à la 85e
