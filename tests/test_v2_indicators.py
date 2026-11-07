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
    # ballon vivant : pas de remise en jeu en attente (ticket v2-collectif/29)
    return SimpleNamespace(position=Vec2(x, y), holder=holder, receiver=receiver, restart=None)


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


def test_close_range_shots_measure_the_keeper_exposure() -> None:
    """Demande du propriétaire (28/10/2026) : la part des tirs pris à moins de 16 m, pour mesurer la vraie
    exposition du gardien derrière un piège haut."""
    c, _home, _away = _collector_with_two_teams()
    near = _p("H9", "home", PITCH_LENGTH_M - 10.0, 34.0)  # 10 m du but adverse
    edge = _p("H8", "home", PITCH_LENGTH_M - 16.0, 34.0)  # pile sur le seuil : compté
    far = _p("H7", "home", PITCH_LENGTH_M - 30.0, 34.0)  # 30 m : pas un tir de près
    for shooter in (near, edge, far):
        c.on_shot(shooter, 1.0)
    away_side = _p("A9", "away", 10.0, 34.0)  # 10 m du but des visiteurs (x = 0)
    c.on_shot(away_side, 2.0)
    assert c.count["tirs"] == 4 and c.count["tirs de près"] == 3


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


def _run_profile(c: ind.Collector, name: str, speeds_kmh: list[tuple[float, int]], poste: str = "MC") -> None:
    """Un joueur seul, en ligne droite : (vitesse en km/h, nombre de ticks de 0,1 s) bout à bout."""
    k = 0
    for kmh, ticks in speeds_kmh:
        for _ in range(ticks):
            c.on_tick(0.1 * k, [_p(name, "home", 50, 34, poste=poste, vx=kmh / 3.6)], _ball(0, 0), None)
            k += 1


def test_high_intensity_distance_and_time_shares_on_a_synthetic_run() -> None:
    # ticket v2-realisme/01d : 10 s à 20 km/h puis 10 s à 10 km/h ; repère R6 en distance, le temps reste suivi
    c = ind.Collector(geometry_every_s=1e9)
    _run_profile(c, "A", [(20.0, 100), (10.0, 100)], poste="DC")
    c.end_match()
    fast, slow = 20.0 / 3.6 * 10.0, 10.0 / 3.6 * 10.0
    assert math.isclose(c.stats["distance au-dessus de 19,8 km/h (part)"].values[0], fast / (fast + slow))  # 2/3
    assert math.isclose(c.stats["temps au-dessus de 19,8 km/h (part)"].values[0], 0.5)
    assert c.stats["temps au-dessus de 25 km/h (part)"].values == [0.0]
    assert math.isclose(c.stats["distance au-dessus de 19,8 km/h par joueur (m) : DC"].values[0], fast)
    assert c.stats["sprints par joueur et par match : DC"].values == [0]
    assert math.isclose(sum(c.km["DC"]), (fast + slow) / 1000.0)


def test_a_sprint_lasts_at_least_one_second_and_one_open_at_the_whistle_counts() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    # 1,5 s à 28,8 km/h (sprint), 0,5 s de marche, 0,5 s à 28,8 km/h (trop court), 1 s de marche, 1 s à 28,8 km/h
    _run_profile(c, "S", [(28.8, 15), (3.6, 5), (28.8, 5), (3.6, 10), (28.8, 10)])
    c.end_match()
    assert c.stats["sprints par joueur et par match"].values == [2]
    assert math.isclose(c.stats["temps au-dessus de 25 km/h (part)"].values[0], 3.0 / 4.5)


def test_runs_are_also_given_per_90_minutes() -> None:
    c, _, away = _collector_with_two_teams()
    holder, ball = _p("H0", "home", 30, 30), _ball(30, 30, "H0")
    c.on_tick(0.0, [holder] + away, ball, None)
    for k in range(10):  # 1 s à 21,6 km/h à 10 m du porteur : un appel
        c.on_tick(0.1 * k, [holder, _p("R", "home", 40, 30, vx=6.0)] + away, ball, None)
    c.on_tick(45 * 60.0, [holder, _p("R", "home", 40, 30)] + away, ball, None)  # match arrêté à 45 min
    c.end_match()
    assert c.stats["appels par joueur et par match : MC"].values.count(1) == 1
    assert 2.0 in c.stats["appels par joueur et par 90 min : MC"].values  # 1 appel en 45 min : 2 par 90 min


def test_passes_per_match_and_per_minute_of_effective_play() -> None:
    from scripts.measure_v2 import report
    c = ind.Collector()
    c.matches, c.minutes_per_match = 2, 90.0
    # matchs de 100 min (temps additionnel compris), dont 30 min de ballon mort
    c.count.update({"passes": 1800, "temps de ballon mort (s)": 2 * 30 * 60.0, "durée de match (s)": 2 * 100 * 60.0})
    out = report(c)
    assert out["passes par match"] == 900.0
    assert math.isclose(out["passes par minute de jeu effectif"], 1800 / 140)  # 2 × 70 min de jeu effectif
    assert math.isclose(out["temps de jeu effectif (part)"], 0.7)
    assert out["passes par minute"] == 10.0  # par minute de match réglementaire, comme la source (941 / 90)


def test_match_duration_includes_added_time() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    c.on_tick(0.0, [_p("A", "home", 50, 34)], _ball(0, 0), None)
    c.on_tick(95 * 60.0, [_p("A", "home", 50, 34)], _ball(0, 0), None)  # coup de sifflet final à 95 min
    c.end_match()
    assert c.count["durée de match (s)"] == 95 * 60.0


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


def test_retreat_speed_of_the_players_ahead_of_the_ball() -> None:
    """Ticket 10 : 1,5 s après la perte, vitesse vers son but des seuls joueurs qui étaient devant le ballon."""
    c = ind.Collector(geometry_every_s=1e9)
    away = [_p("A0", "away", 80, 30)]
    at_loss = [_p("H0", "home", 10, 30), _p("H1", "home", 20, 30), _p("H2", "home", 75, 30), _p("H4", "home", 65, 30),
               _p("H3", "home", 90, 30)]
    c.on_tick(0.0, at_loss + away, _ball(75, 30, "H2"), None)
    c.on_tick(0.1, at_loss + away, _ball(80, 30, "A0"), None)  # home perd ; H2 à 5 m, H4 à 15 m, H3 devant le ballon
    later = [_p("H0", "home", 10, 30), _p("H1", "home", 20, 30), _p("H2", "home", 78, 30, vx=3.0),
             _p("H4", "home", 65, 30), _p("H3", "home", 88, 30, vx=-4.0)]
    c.on_tick(1.6, later + away, _ball(80, 30, "A0"), None)
    c.end_match()
    assert c.stats["repli : vitesse des joueurs devant le ballon à 1,5 s (m/s)"].values == [4.0]  # H3 seul, il revient


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
                    "passes longues": 360, "passes longues réussies": 180, "tirs": 40, "tirs de près": 21, "buts": 5,
                    "tacles": 70, "choix pass": 3, "choix dribble": 1})
    out = report(c)
    assert out["passes par minute"] == 20.0 and out["passes réussies (part)"] == 0.75
    assert out["tirs par équipe"] == 10.0 and out["buts par match"] == 2.5 and out["tacles par match"] == 35.0
    assert out["passes longues réussies (part)"] == 0.5 and out["choix pass (part)"] == 0.75
    # Une clé mal orthographiée renverrait 0,0 sans bruit (Counters) : on vérifie les deux clés du nouvel indicateur.
    assert out["tirs de près (16 m) par équipe"] == 5.25 and out["part des tirs de près (16 m)"] == 0.525


def test_measure_is_wired_on_a_real_match() -> None:
    from scripts.measure_v2 import report, run
    c = run(1, duration_minutes=3.0)
    out = report(c)
    assert c.count["passes"] > 0 and sum(v for k, v in c.count.items() if k.startswith("choix ")) > 0
    assert 5.0 < out["passes par minute"] < 100.0  # rapporté aux 3 minutes jouées (sur 90, on serait sous 1)
    assert c.stats["longueur avec ballon (m)"].values and c.stats["solutions de passe ouvertes (nombre)"].values
    assert out["pressings d'équipe déclenchés par match"] == c.count["pressings d'équipe déclenchés"] > 0  # réserve A2, ticket 08
    # ticket v2-realisme/02h : chaque appel du banc a un rôle de départ, les places moyennes sont rapportées
    assert sum(v for k, v in c.count.items() if k.startswith("appels du banc, rôle au départ : ")) == c.count["appels"]
    assert any(name.startswith("place moyenne avec ballon") for name in c.stats)
    assert any(name.startswith("part du temps du côté de son poste") for name in c.stats)


def test_crowding_ignores_support_next_to_the_holder() -> None:
    holder, support, a, b = _p("h", "home", 50, 34), _p("s", "home", 53, 34), _p("a", "home", 70, 10), _p("b", "home", 72, 10)
    assert ind.crowded([holder, support, a, b], []) == 1.0
    assert ind.crowded([holder, support, a, b], [], holder="h") == 2 / 3


def test_open_options_threshold_counts_only_easy_passes() -> None:
    holder, mate = _p("H", "home", 50, 34), _p("M", "home", 62, 34)
    marker = _p("X", "away", 63, 34)
    chance = ind.pass_chances(holder, [holder, mate], [marker])[0]
    assert ind.open_options(holder, [holder, mate], [marker], threshold=chance) == 1
    assert ind.open_options(holder, [holder, mate], [marker], threshold=min(1.0, chance + 0.01)) == 0


def test_combination_indicators_read_the_pass_log() -> None:
    # ticket v2-collectif/14 : C2, retour au passeur, une-deux, troisième homme
    c = ind.Collector()
    log = [
        dict(t=0.0, team="home", passer="a", target="b", gain=0.0, start=Vec2(40, 34), end=Vec2(40, 20),
             progressive=False, follow="c", done=True),  # sans gain, suite prévue c
        dict(t=1.0, team="home", passer="b", target="c", gain=12.0, start=Vec2(40, 20), end=Vec2(55, 25),
             progressive=True, follow=None, done=True),  # le troisième homme, et elle fait avancer
        dict(t=2.0, team="home", passer="c", target="d", gain=0.0, start=Vec2(55, 25), end=Vec2(55, 40),
             progressive=False, follow=None, done=True),
        dict(t=3.0, team="home", passer="d", target="c", gain=8.0, start=Vec2(55, 40), end=Vec2(62, 25),
             progressive=False, follow=None, done=True),  # retour vers c, avancé de 7 m : une-deux
    ]
    c.pass_log = log
    c._combinations()
    k = c.count
    assert k["passes sans gain réussies"] == 2 and k["passes sans gain suivies d'une passe qui fait avancer"] == 1
    assert k["troisième homme (suite prévue jouée et réussie)"] == 1
    assert k["retours au passeur en 3 s"] == 1 and k["une-deux"] == 1


def test_triangle_needs_three_open_passes_and_an_angle() -> None:
    holder, a, b = _p("h", "home", 50, 34), _p("a", "home", 60, 28), _p("b", "home", 60, 40)
    assert ind.triangle(holder, [holder, a, b], [])
    aligned = _p("b", "home", 70, 22)  # dans l'axe de a : pas de triangle
    assert not ind.triangle(holder, [holder, a, aligned], [])
    assert ind.breaks_a_line("home", Vec2(30, 34), Vec2(60, 34),
                             [_p(f"o{i}", "away", x, 10 + 6 * i) for i, x in enumerate((45, 46, 47, 75, 76, 90, 91))])


# --- Structure (ticket v2-realisme/02h) ---------------------------------------------------------------------------------
def test_mean_place_by_post_is_seen_from_the_own_goal_and_the_own_side() -> None:
    c = ind.Collector()
    home = [_p("LB", "home", 20, 10, poste="LB"), _p("DC", "home", 20, 34, poste="DC"), _p("MC", "home", 40, 34)]
    away = [_p("RB", "away", 85, 10, poste="RB"), _p("DX", "away", 85, 34, poste="DC"), _p("MX", "away", 65, 34)]
    c.on_tick(0.0, home + away, _ball(50, 34), None)
    c.end_match()
    s = c.stats
    assert s["place moyenne sans ballon : LB : profondeur (m)"].values == [20.0]
    assert s["place moyenne sans ballon : RB : profondeur (m)"].values == [20.0]  # 105 - 85 : vu de son but
    assert s["place moyenne sans ballon : LB : côté (m, négatif = gauche)"].values == [-24.0]
    assert s["place moyenne sans ballon : RB : côté (m, négatif = gauche)"].values == [24.0]  # miroir de l'équipe visiteuse
    assert s["place moyenne sans ballon : DC : côté (m, négatif = gauche)"].values == [0.0, 0.0]
    assert s["part du temps du côté de son poste : LB"].values == [1.0]
    assert s["part du temps du côté de son poste : RB"].values == [1.0]


def test_a_wing_post_on_the_wrong_side_and_the_transition_filter() -> None:
    c = ind.Collector()
    home = [_p("LB", "home", 20, 10, poste="LB"), _p("DC", "home", 20, 34, poste="DC"), _p("MC", "home", 40, 34)]
    away = [_p("AX", "away", 85, 20), _p("DX", "away", 85, 34, poste="DC"), _p("MX", "away", 65, 34)]
    c.on_tick(0.0, home + away, _ball(50, 34), None)  # du bon côté, hors transition
    c.situations.current["home"] = ind.TRANSITION_OFFENSIVE
    crossed = [_p("LB", "home", 20, 50, poste="LB")] + home[1:]  # passé à droite, en transition
    c._place("home", crossed, "sans ballon")
    c.end_match()
    assert c.stats["part du temps du côté de son poste : LB"].values == [0.5]
    assert c.stats["part du temps du côté de son poste, hors transition : LB"].values == [1.0]


def test_simultaneous_callers_are_counted_per_team_in_possession() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    home = [_p(f"H{i}", "home", 30 + i, 30) for i in range(4)]
    away = [_p(f"A{i}", "away", 60 + i, 30) for i in range(3)]
    for t, callers in enumerate((2, 3, 1)):
        c.on_role("H0", "porteur")
        for i in range(1, 4):
            c.on_role(f"H{i}", ind.APPEL if i <= callers else ind.TENIR)
        c.on_tick(0.1 * t, home + away, _ball(30, 30, "H0"), None)
    assert max(c.max_callers.values()) == 3  # le porteur n'est jamais compté
    c.on_role("A0", ind.APPEL)  # l'équipe qui défend n'a pas la possession : ses rôles ne comptent pas
    c.on_tick(0.5, home + away, _ball(30, 30, "H0"), None)
    assert max(c.max_callers.values()) == 3
    c.end_match()
    assert [s.values for n, s in c.stats.items() if n.startswith("appelants simultanés d'une équipe")] == [[3]]


def test_instants_above_the_engine_cap_are_counted(monkeypatch) -> None:
    from v2engine import situation as sit
    every = (sit.POSSESSION_INSTALLEE, sit.DEFENSE_PLACEE, sit.TRANSITION_OFFENSIVE, sit.TRANSITION_DEFENSIVE,
             sit.DERNIER_TIERS)
    monkeypatch.setattr(ind.cerveau, "CALLER_CAP", {s: 2 for s in every})
    c = ind.Collector(geometry_every_s=1e9)
    home = [_p(f"H{i}", "home", 30 + i, 30) for i in range(4)]
    away = [_p(f"A{i}", "away", 60 + i, 30) for i in range(3)]
    for t, callers in enumerate((2, 3, 3, 1)):
        for i in range(1, 4):
            c.on_role(f"H{i}", ind.APPEL if i <= callers else ind.TENIR)
        c.on_tick(0.1 * t, home + away, _ball(30, 30, "H0"), None)
    over = sum(v for k, v in c.count.items() if k.startswith("appelants simultanés au-dessus du plafond"))
    instants = sum(v for k, v in c.count.items() if k.startswith("appelants simultanés, instants"))
    assert (over, instants) == (2, 4)


def test_call_episodes_are_counted_per_90_minutes_by_post() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    players = [_p("X", "home", 30, 30), _p("H0", "home", 31, 30)]
    c.on_tick(0.0, players, _ball(31, 30, "H0"), None)
    for role in (ind.APPEL, ind.APPEL, ind.TENIR, ind.APPEL):  # deux épisodes APPEL, séparés par TENIR
        c.on_role("X", role)
    c.on_tick(45 * 60.0, players, _ball(31, 30, "H0"), None)
    c.end_match()
    assert 4.0 in c.stats["épisodes APPEL par joueur et par 90 min : MC"].values  # 2 épisodes en 45 min


def test_switches_are_counted_inside_a_possession_only() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    players = [_p("X", "home", 30, 30), _p("H0", "home", 31, 30), _p("A0", "away", 60, 30)]
    c.on_tick(0.0, players, _ball(31, 30, "H0"), None)  # possession de home depuis 0 s
    c.on_role("X", ind.TENIR)
    c.on_tick(1.0, players, _ball(31, 30, "H0"), None)
    c.on_role("X", ind.APPEL)  # passage après 1 s : alternance courte
    c.on_tick(4.0, players, _ball(31, 30, "H0"), None)
    c.on_role("X", ind.TENIR)  # passage après 3 s
    c.on_role("X", "soutien")  # un autre rôle interrompt la suite : pas de passage
    c.on_role("X", ind.APPEL)
    assert c.count["passages APPEL / TENIR dans une possession"] == 2
    assert c.count["passages APPEL / TENIR dans une possession, état de moins de 1,5 s"] == 1
    # seul l'appel qui s'arrête (APPEL -> TENIR) est un clignotement ; TENIR -> APPEL est le délai d'Off the Ball
    assert c.count["appels arrêtés dans une possession"] == 1
    assert c.count["appels arrêtés dans une possession, en moins de 1,5 s"] == 0  # cet appel a duré 3 s
    c.on_tick(4.5, players, _ball(31, 30, "H0"), None)
    c.on_role("X", ind.TENIR)  # l'appel relancé s'arrête après 0,5 s : clignotement
    assert c.count["appels arrêtés dans une possession"] == 2
    assert c.count["appels arrêtés dans une possession, en moins de 1,5 s"] == 1
    c.on_role("X", ind.APPEL)
    c.on_tick(5.0, players, _ball(60, 30, "A0"), None)  # home perd le ballon
    c.on_tick(6.0, players, _ball(31, 30, "H0"), None)  # et le reprend : nouvelle possession
    c.on_role("X", ind.TENIR)  # APPEL -> TENIR à cheval sur deux possessions : non compté ici
    assert c.count["passages APPEL / TENIR dans une possession"] == 4
    assert c.possession_switches["X"] == 4 and c.role_switches["X"] == 6  # l'ancien compteur compte tout


def test_bench_runs_keep_the_role_the_player_had_at_the_start_of_the_run() -> None:
    c, _, away = _collector_with_two_teams()
    holder, ball = _p("H0", "home", 30, 30), _ball(30, 30, "H0")
    c.on_tick(0.0, [holder] + away, ball, None)
    c.on_role("R", ind.TENIR)  # il tient sa place et rejoint sa position à pleine vitesse
    for k in range(10):
        if k == 5:
            c.on_role("R", ind.APPEL)  # le rôle change en cours de course : le départ fait foi
        c.on_tick(0.1 * k, [holder, _p("R", "home", 40, 30, vx=6.0)] + away, ball, None)
    c.on_tick(1.0, [holder, _p("R", "home", 40, 30)] + away, ball, None)
    assert len(c.run_log) == 1 and c.count["appels du banc, rôle au départ : " + ind.TENIR] == 1
    assert c.count["appels du banc, rôle au départ : " + ind.APPEL] == 0


def test_the_called_player_is_a_pass_option_only_when_he_is_not_covered() -> None:
    def share(marker_x: float) -> float:
        c = ind.Collector()
        home = [_p("H0", "home", 30, 30), _p("R", "home", 42, 30), _p("M", "home", 35, 45)]
        away = [_p("A0", "away", marker_x, 30), _p("A1", "away", 70, 10), _p("A2", "away", 72, 50)]
        c.on_role("R", ind.APPEL)
        c.on_tick(0.0, home + away, _ball(30, 30, "H0"), None)
        return c.stats["appelant retenu : passe ouverte pour le porteur (part)"].values[0]
    assert share(80.0) == 1.0  # personne près de la ligne de passe
    assert share(41.5) == 0.0  # un adversaire collé au receveur : chance de passe de 0,61, sous le seuil de 0,7


def test_report_gives_the_structure_indicators() -> None:
    from scripts.measure_v2 import report
    c = ind.Collector()
    c.matches = 2
    c.count.update({"passages APPEL / TENIR dans une possession": 10,
                    "passages APPEL / TENIR dans une possession, état de moins de 1,5 s": 3, "appels": 20,
                    "appels du banc, rôle au départ : " + ind.TENIR: 15, "appels du banc, rôle au départ : " + ind.APPEL: 5,
                    "appels arrêtés dans une possession": 4, "appels arrêtés dans une possession, en moins de 1,5 s": 1,
                    "appelants simultanés au-dessus du plafond, instants : dernier tiers": 3,
                    "appelants simultanés, somme : dernier tiers": 12, "appelants simultanés, instants : dernier tiers": 6})
    c.stats["appelants simultanés d'une équipe, maximum du match : dernier tiers"].values.extend([2, 3])
    out = report(c)
    assert out["passages APPEL / TENIR dans une possession par match"] == 5.0
    assert out["passages APPEL / TENIR dans une possession : état de moins de 1,5 s (part)"] == 0.3
    assert out["appels arrêtés dans une possession, en moins de 1,5 s (part des APPEL qui se terminent par TENIR)"] == 0.25
    assert out["appelants simultanés au-dessus du plafond du moteur, part des instants : dernier tiers"] == 0.5
    assert out["appels du banc, rôle au départ : tenir sa place (part)"] == 0.75
    assert out["appelants simultanés d'une équipe en possession, moyenne : dernier tiers"] == 2.0
    assert out["appelants simultanés d'une équipe, maximum de la série : dernier tiers"] == 3


def test_keeper_distance_to_his_own_goal_is_seen_for_both_teams() -> None:
    # ticket v2-realisme/03a : le gardien domicile défend x = 0, le gardien visiteur x = 105 (centre du but à y = 34)
    c = ind.Collector(geometry_every_s=1e9)
    for k, (home_x, away_x) in enumerate(((5.0, 100.0), (15.0, 90.0))):
        players = [_p("GH", "home", home_x, 34, poste="GK"), _p("GA", "away", away_x, 34, poste="GK")]
        c.on_tick(0.1 * k, players, _ball(50, 34), None)
    c.end_match()
    assert sorted(c.stats["distance maximale du gardien à son but (m)"].values) == [15.0, 15.0]
    assert sorted(c.stats["distance moyenne du gardien à son but (m)"].values) == [10.0, 10.0]


def test_shot_context_gives_the_shot_chance_and_the_keeper_gap_to_the_bisector() -> None:
    # ticket v2-realisme/03b : le gardien adverse est sur la bissectrice (y = 34 pour un tir dans l'axe) ou à côté
    def gap(keeper_y: float) -> tuple[float, float]:
        c = ind.Collector(geometry_every_s=1e9)
        shooter = _p("S", "home", 90.0, 34.0)
        keeper = _p("K", "away", 100.0, keeper_y, poste="GK")
        c.on_shot_context(shooter, Vec2(PITCH_LENGTH_M, 34.0), keeper, [keeper])
        return (c.stats["gardien au tir : écart à la bissectrice (m)"].values[0],
                c.stats["gardien au tir : écart à la bissectrice sous le seuil (part)"].values[0])
    on_axis, within_axis = gap(34.0)
    assert math.isclose(on_axis, 0.0, abs_tol=1e-6) and within_axis == 1.0
    off, within = gap(38.0)
    assert math.isclose(off, 4.0, abs_tol=1e-6) and within == 0.0
    c = ind.Collector(geometry_every_s=1e9)
    shooter = _p("S", "home", 90.0, 34.0)
    c.on_shot_context(shooter, Vec2(PITCH_LENGTH_M, 34.0), None, [])  # sans gardien : la chance seule
    assert 0.0 < c.stats["chance du tir (shot_probability)"].values[0] < 1.0
    assert "gardien au tir : écart à la bissectrice (m)" not in c.stats


def test_keeper_rush_episodes_successes_distance_and_loose_balls_left() -> None:
    from v2engine.cerveau import Intention
    c = ind.Collector(geometry_every_s=1e9)
    keeper = _p("K", "home", 5.0, 34.0, poste="GK")

    def step(reason: str, target: Vec2) -> None:
        c.on_keeper(keeper, Intention("gardien", "aller au ballon", target, reason=reason))

    step("placement : il se place sur la bissectrice ballon-poteaux", Vec2(3.0, 34.0))
    step("sortie : ballon libre (il arrive en 2.0 s, l'adversaire en 3.5 s)", Vec2(28.0, 34.0))  # hors de sa surface
    step("sortie : ballon libre (il arrive en 1.5 s, l'adversaire en 3.5 s)", Vec2(26.0, 34.0))  # même épisode
    step("relance : il a le ballon", Vec2(25.0, 34.0))  # sortie réussie
    step("sortie : ballon libre (...)", Vec2(10.0, 34.0))  # nouvel épisode, dans sa surface
    step("placement : l'adversaire arrive avant lui (1.0 s contre 2.0 s), il garde sa place", Vec2(3.0, 34.0))  # raté
    step("placement : le ballon est trop loin de son but, il garde sa place", Vec2(3.0, 34.0))  # même ballon laissé
    assert c.count["gardien : sorties"] == 2 and c.count["gardien : sorties réussies"] == 1
    assert c.count["gardien : sorties hors de sa surface"] == 1 and c.count["gardien : ballons libres laissés"] == 1
    assert c.stats["gardien : sortie, point visé à son but (m)"].values == [28.0, 10.0]

