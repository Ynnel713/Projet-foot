"""Tests du banc de mesure V2 (ticket v2-collectif/01) : un test par indicateur de `docs/INDICATEURS_V2.md`,
sur des positions construites à la main."""

from __future__ import annotations

import math
from types import SimpleNamespace

from scripts import v2_indicators as ind
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.movement import PlayerState


def _p(name: str, team: str, x: float, y: float, poste: str = "MC", vx: float = 0.0, vy: float = 0.0) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(vx, vy),
                       pace=60, acceleration=60, stamina=60, home_target=Vec2(x, y))


def _ball(x: float, y: float, holder: str | None = None, receiver: str | None = None):
    return SimpleNamespace(position=Vec2(x, y), holder=holder, receiver=receiver)


# --- Géométrie ----------------------------------------------------------------------------------------------------
def test_length_and_width() -> None:
    assert ind.length_width([Vec2(10, 20), Vec2(40, 30), Vec2(25, 60)]) == (30, 40)


def test_block_follow_slope() -> None:  # ticket v2-collectif/04 : part du déplacement du ballon suivie par le centre
    assert math.isclose(ind.slope([(0, 10), (10, 15), (20, 20)]), 0.5)
    assert ind.slope([(5, 1), (5, 2)]) == 0.0


def test_deep_pass_is_beyond_the_last_outfield_defender() -> None:  # ticket v2-collectif/05
    players = [_p("D", "away", 80, 30), _p("G", "away", 104, 34, poste="GK")]
    assert ind.is_deep_pass("home", Vec2(85, 30), players) and not ind.is_deep_pass("home", Vec2(75, 30), players)
    assert ind.is_deep_pass("away", Vec2(20, 30), [_p("D", "home", 25, 30)])


def test_hull_area_and_stretch_index() -> None:
    square = [Vec2(0, 0), Vec2(10, 0), Vec2(10, 10), Vec2(0, 10), Vec2(5, 5)]  # le point central ne compte pas
    assert math.isclose(ind.hull_area(square), 100.0)
    assert math.isclose(ind.stretch_index([Vec2(0, 0), Vec2(10, 0)]), 5.0)


def test_line_gaps_and_block_height_follow_attack_direction() -> None:
    xs = [20, 22, 21, 23, 35, 36, 34, 50, 51, 49]  # défense ~21,5, milieu 35, attaque 50
    home = [Vec2(x, 30) for x in xs]
    gaps = ind.line_gaps("home", home)
    assert math.isclose(gaps[0], 13.5) and math.isclose(gaps[1], 15.0)
    assert math.isclose(ind.block_height("home", home), 21.5)
    away = [Vec2(PITCH_LENGTH_M - x, 30) for x in xs]  # même bloc, vu par l'équipe qui attaque vers la gauche
    assert ind.line_gaps("away", away) == gaps


def test_zone_is_seen_from_the_team_in_possession() -> None:
    assert ind.zone("home", 90.0) == "tiers offensif" and ind.zone("away", 90.0) == "tiers défensif"


# --- Autour du ballon ---------------------------------------------------------------------------------------------
def test_local_compactness_uses_the_five_nearest_defenders() -> None:
    defenders = [_p(f"D{i}", "away", 50 + d, 34) for i, d in enumerate((1, 2, 3, 4, 5, 40))]
    assert math.isclose(ind.local_compactness(Vec2(50, 34), defenders), 3.0)


def test_local_superiority_within_ten_metres() -> None:
    defenders = [_p("D1", "away", 52, 34), _p("D2", "away", 55, 34), _p("D3", "away", 70, 34)]
    attackers = [_p("A1", "home", 51, 34)]
    assert ind.local_superiority(Vec2(50, 34), defenders, attackers) == 1


def test_preventive_defence_counts_players_and_threats_behind_the_ball() -> None:
    own = [_p("H1", "home", 30, 34), _p("H2", "home", 40, 34), _p("H3", "home", 70, 34)]
    opponents = [_p("A1", "away", 45, 34), _p("A2", "away", 80, 34)]
    assert ind.preventive("home", Vec2(60, 34), own, opponents) == (2, 1)


def test_pressing_cover_needs_a_second_defender_in_the_ellipse() -> None:
    holder = _p("H", "home", 60, 34)
    goal = Vec2(PITCH_LENGTH_M, 34)  # l'extérieur défend le but de droite
    presser = _p("P", "away", 62, 34)
    assert ind.pressing_cover(holder, [presser, _p("C", "away", 66, 35)], goal) is True
    assert ind.pressing_cover(holder, [presser, _p("C", "away", 55, 34)], goal) is False  # derrière le porteur
    assert ind.pressing_cover(holder, [_p("C", "away", 66, 35)], goal) is None  # personne ne presse


def test_open_options_counts_reachable_teammates() -> None:
    holder = _p("H", "home", 50, 34)
    free, far, blocked = _p("F", "home", 50, 24), _p("L", "home", 95, 34), _p("B", "home", 80, 34)
    lane = [_p(n, "away", x, 34) for n, x in (("X", 60), ("Y", 65), ("Z", 70), ("W", 80.5), ("V", 51))]
    assert ind.open_options(holder, [holder, free, far, blocked], lane) == 1  # trop loin et couloir fermé exclus


# --- Collecteur (événements) --------------------------------------------------------------------------------------
def _collector_with_two_teams():
    c = ind.Collector(geometry_every_s=1e9)  # géométrie hors sujet ici
    home = [_p(f"H{i}", "home", 30 + i, 30) for i in range(3)]
    away = [_p(f"A{i}", "away", 60 + i, 30) for i in range(3)]
    return c, home, away


def test_pass_outcome_and_intended_receiver() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    c.on_tick(0.0, players, _ball(30, 30, "H0"), None)
    c.on_pass(home[0], home[1])
    c.on_tick(0.1, players, _ball(31, 30, None), None)
    c.on_tick(0.2, players, _ball(31, 30, "H2"), None)  # reçue par un coéquipier, pas le visé
    assert c.count["passes"] == 1 and c.count["passes réussies"] == 1 and c.count["receveur visé"] == 0


def test_recovery_classes_transition_losses_and_possession_times() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    c.on_tick(0.0, players, _ball(30, 30, "H0"), None)
    c.on_tick(10.0, players, _ball(60, 30, "A0"), None)  # home perd
    c.on_tick(13.0, players, _ball(30, 30, "H0"), None)  # home récupère en 3 s
    c.on_tick(15.0, players, _ball(60, 30, "A0"), None)  # reperdu 2 s après : perte en transition
    assert c.count["récupération 0-5 s"] == 2  # home en 3 s, puis away en 2 s
    assert c.relost[-1][1] is True
    assert c.stats["possession d'équipe (s)"].values[:2] == [10.0, 3.0]


def test_counter_shot_within_fifteen_seconds_of_a_recovery() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    c.on_tick(0.0, players, _ball(60, 30, "A0"), None)
    c.on_tick(5.0, players, _ball(30, 30, "H0"), None)  # home récupère dans son camp (x = 30)
    c.on_shot(home[0], 12.0)
    c.on_shot(home[0], 30.0)  # trop tard : pas un contre
    assert c.count["tirs de contre, récupération propre camp"] == 1 and c.count["tirs"] == 2


def test_retreat_latency_after_a_loss() -> None:
    c, home, away = _collector_with_two_teams()
    c.on_tick(0.0, home + away, _ball(30, 30, "H0"), None)
    c.on_tick(1.0, home + away, _ball(60, 30, "A0"), None)  # home perd
    backing = [_p(p.name, "home", p.position.x, 30, vx=-2.0) for p in home]  # recule à 2 m/s vers son but
    c.on_tick(1.5, backing + away, _ball(60, 30, "A0"), None)
    c.end_match()
    assert c.stats["repli : latence (s)"].values == [0.5]


def _runs_logged(duration_s: float, speed: float, end_x: float = 40.0) -> int:
    c, _, away = _collector_with_two_teams()
    holder, ball = _p("H0", "home", 30, 30), _ball(30, 30, "H0")
    c.on_tick(0.0, [holder] + away, ball, None)
    ticks = round(duration_s / 0.1)
    for k in range(ticks):
        c.on_tick(0.1 * k, [holder, _p("R", "home", end_x, 30, vx=speed)] + away, ball, None)
    c.on_tick(0.1 * ticks, [holder, _p("R", "home", end_x, 30)] + away, ball, None)
    return len(c.run_log)


def test_a_run_needs_duration_speed_and_a_pass_option() -> None:
    assert _runs_logged(1.0, 6.0) == 1  # 1 s à 21,6 km/h, à 10 m du porteur : un appel
    assert _runs_logged(0.5, 6.0) == 0  # trop court
    assert _runs_logged(1.0, 3.0) == 0  # trop lent (10,8 km/h)
    assert _runs_logged(1.0, 6.0, end_x=90.0) == 0  # à 60 m : aucune option de passe créée


def test_a_run_ending_with_the_reception_counts() -> None:
    c, _, away = _collector_with_two_teams()
    holder = _p("H0", "home", 30, 30)
    for k in range(10):
        c.on_tick(0.1 * k, [holder, _p("R", "home", 40, 30, vx=6.0)] + away, _ball(30, 30, "H0"), None)
    c.on_tick(1.0, [holder, _p("R", "home", 40, 30, vx=6.0)] + away, _ball(40, 30, "R"), None)  # il reçoit
    assert len(c.run_log) == 1


def test_simultaneous_runs_to_the_same_zone_are_redundant() -> None:
    c, _, away = _collector_with_two_teams()
    holder, ball = _p("H0", "home", 30, 30), _ball(30, 30, "H0")
    for k in range(10):  # 1 s à 21,6 km/h, côte à côte
        c.on_tick(0.1 * k, [holder, _p("R1", "home", 40, 30, vx=6.0), _p("R2", "home", 42, 31, vx=6.0)] + away, ball, None)
    c.on_tick(1.0, [holder, _p("R1", "home", 40, 30), _p("R2", "home", 42, 31)] + away, ball, None)
    assert len(c.run_log) == 2
    c.end_match()
    assert c.stats["appels redondants (part)"].values == [1.0]
    assert c.stats["appels par joueur et par match : MC"].values.count(0) == 4  # les joueurs sans appel comptent


def test_distance_sprint_share_and_late_decline() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    sprinter = _p("S", "home", 50, 34, vx=8.0)  # 28,8 km/h
    walker = _p("W", "home", 50, 34, vx=1.0)
    ball = _ball(0, 0)
    for k in range(10):
        c.on_tick(0.1 * k, [sprinter, walker], ball, None)  # minute 0 : course intense du sprinteur
    c.on_tick(80 * 60.0, [walker, _p("S", "home", 50, 34)], ball, None)  # fin de match : plus de course intense
    c.end_match()
    assert math.isclose(c.stats["distance au-dessus de 25 km/h (part)"].values[0], 8.0 / 9.1, rel_tol=1e-6)
    assert c.stats["baisse de la course intense en fin de match (part)"].values == [1.0]
    assert math.isclose(sum(c.km["tous"]), 9.1 / 1000.0)  # 8 m de sprint + 1,1 m de marche


def test_geometry_is_split_by_zone_score_and_minute() -> None:
    c = ind.Collector(geometry_every_s=1.0)
    home = [_p(f"H{i}", "home", 30 + 5 * i, 20 + 5 * i) for i in range(10)]
    away = [_p(f"A{i}", "away", 60 + 3 * i, 20 + 4 * i) for i in range(10)]
    c.on_tick(0.0, home + away, _ball(80, 34, "H0"), None)
    stat = c.stats["longueur avec ballon (m)"]
    assert stat.values == [45.0]
    assert stat.by[("zone", "tiers offensif")] == [45.0] and stat.by[("score", "égalité")] == [45.0]
    assert stat.by[("minute", "0-15 min")] == [45.0]


def test_passes_to_the_opponent_and_long_passes() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    long_target = _p("H9", "home", 70, 30)
    c.on_tick(0.0, players, _ball(30, 30, "H0"), None)
    c.on_pass(home[0], long_target)  # 40 m : passe longue
    c.on_tick(0.1, players, _ball(40, 30, None), None)
    c.on_tick(0.2, players, _ball(60, 30, "A0"), None)  # interceptée
    assert c.count["passes longues"] == 1 and c.count["passes chez l'adversaire"] == 1
    assert c.count["passes longues réussies"] == 0


def test_player_possession_time() -> None:
    c, home, away = _collector_with_two_teams()
    c.on_tick(0.0, home + away, _ball(30, 30, "H0"), None)
    c.on_tick(2.5, home + away, _ball(30, 30, None), None)
    assert c.stats["temps par possession de joueur (s)"].values == [2.5]


def test_a_goal_closes_the_possession_and_the_kick_off_is_not_a_loss() -> None:
    c, home, away = _collector_with_two_teams()
    c.on_tick(0.0, home + away, _ball(30, 30, "H0"), None)
    c.on_tick(5.0, home + away, _ball(52.5, 34, None), "home")  # but de home, engagement au centre
    c.on_tick(6.0, home + away, _ball(52.5, 34, "A0"), None)  # away engage
    assert c.count["buts"] == 1 and c.count["pertes de balle"] == 0 and c.count["récupérations"] == 0
    assert c.stats["possession d'équipe (s)"].values == [5.0]


def test_transition_loss_share_counts_every_recovery() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    c.on_tick(0.0, players, _ball(60, 30, "A0"), None)
    c.on_tick(10.0, players, _ball(30, 30, "H0"), None)  # home récupère
    c.on_tick(12.0, players, _ball(60, 30, "A0"), None)  # reperdu en 2 s
    c.on_tick(30.0, players, _ball(30, 30, "H0"), None)  # home récupère, garde le ballon jusqu'à la fin
    c.end_match()
    assert sorted(c.stats["pertes en transition (part des récupérations)"].values) == [0.0, 0.0, 1.0]


def test_retreat_speed_block_reform_and_players_behind_the_ball() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    home = [_p(f"H{i}", "home", x, 30) for i, x in enumerate((20, 40, 60, 70, 75))]
    away = [_p("A0", "away", 80, 30)]
    c.length_out["home"] = [20.0]  # médiane sans ballon de référence
    c.on_tick(0.0, home + away, _ball(70, 30, "H3"), None)
    c.on_tick(1.0, home + away, _ball(80, 30, "A0"), None)  # home perd, bloc long de 55 m
    back = [_p(f"H{i}", "home", x, 30, vx=-3.0) for i, x in enumerate((20, 40, 60, 70, 75))]
    c.on_tick(1.5, back + away, _ball(80, 30, "A0"), None)
    c.on_tick(2.0, back + away, _ball(80, 30, "A0"), None)  # 1 s après la perte : 5 joueurs derrière le ballon
    short = [_p(f"H{i}", "home", x, 30, vx=-3.0) for i, x in enumerate((20, 25, 30, 35, 38))]
    c.on_tick(3.0, short + away, _ball(80, 30, "A0"), None)  # bloc revenu à 18 m
    c.length_out["home"].append(20.0)
    c.end_match()
    assert c.stats["repli : vitesse de recul (m/s)"].values[0] > 1.0
    assert c.stats["repli : temps pour reformer le bloc (s)"].values == [2.0]
    assert c.stats["4 joueurs ou plus derrière le ballon 1 s après la perte (part)"].values == [1.0]


# --- Commande de mesure -------------------------------------------------------------------------------------------
def test_profile_forces_physical_attributes_read_on_database_players() -> None:
    import v2engine.match as match
    from scripts.measure_v2 import _force_attribute
    fiche = SimpleNamespace(name="Joueur", attributes={"Pace": 50})  # fiche de la base : pas d'équipe
    restore = _force_attribute("Pace", "home", {"Joueur": "home"})
    try:
        assert match.player_attribute(fiche, "Pace") == 99
        assert match.player_attribute(_p("X", "away", 0, 0), "Pace") == 11
    finally:
        restore()
    assert match.player_attribute(fiche, "Pace") == 50


def test_hooks_are_restored_and_the_observer_changes_nothing() -> None:
    import random

    import v2engine.match as match
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from scripts.measure_v2 import run
    real = (match.pass_velocity, match.attempt_shot, match.resolve_tackle, match.choose_action)
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    plain = match.simulate_match(clubs[0], clubs[1], duration_minutes=2.0)
    first = run(1, duration_minutes=2.0)
    second = run(1, duration_minutes=2.0)
    assert (match.pass_velocity, match.attempt_shot, match.resolve_tackle, match.choose_action) == real
    assert first.count == second.count  # déterminisme : même graine, mêmes chiffres
    random.seed(20260923)
    observed = match.simulate_match(clubs[0], clubs[1], duration_minutes=2.0, observer=lambda *a: None)
    assert [t.players for t in observed.ticks] == [t.players for t in plain.ticks]


def test_tackles_choices_and_passes_per_possession() -> None:
    c, home, away = _collector_with_two_teams()
    players = home + away
    c.on_tick(0.0, players, _ball(30, 30, "H0"), None)
    for kind in ("pass", "pass", "dribble"):
        c.on_choice(kind)
    c.on_pass(home[0], home[1])
    c.on_tick(0.5, players, _ball(31, 30, "H1"), None)
    c.on_pass(home[1], home[2])
    c.on_tick(1.0, players, _ball(32, 30, "H2"), None)
    c.on_tackle()
    c.on_tick(2.0, players, _ball(60, 30, "A0"), None)  # tacle gagné : fin de la possession de home
    assert c.count["tacles"] == 1 and c.count["choix pass"] == 2 and c.count["choix dribble"] == 1
    assert c.stats["passes par possession"].values == [2]


def test_report_turns_counts_into_rates() -> None:
    from scripts.measure_v2 import report
    c = ind.Collector()
    c.matches, c.minutes_per_match = 2, 90.0
    c.count.update({"passes": 3600, "passes réussies": 2700, "passes chez l'adversaire": 900, "receveur visé": 1800,
                    "passes longues": 360, "passes longues réussies": 180, "tirs": 40, "buts": 5, "tacles": 70,
                    "choix pass": 3, "choix dribble": 1})
    out = report(c)
    assert out["passes par minute"] == 20.0 and out["passes réussies (part)"] == 0.75
    assert out["tirs par équipe"] == 10.0 and out["buts par match"] == 2.5 and out["tacles par match"] == 35.0
    assert out["passes longues réussies (part)"] == 0.5 and out["choix pass (part)"] == 0.75


def test_measure_is_wired_on_a_real_match() -> None:
    from scripts.measure_v2 import report, run
    c = run(1, duration_minutes=3.0)
    out = report(c)
    assert c.count["passes"] > 0 and sum(v for k, v in c.count.items() if k.startswith("choix ")) > 0
    assert 5.0 < out["passes par minute"] < 100.0  # rapporté aux 3 minutes jouées (sur 90, on serait sous 1)
    assert c.stats["longueur avec ballon (m)"].values and c.stats["solutions de passe ouvertes (nombre)"].values
