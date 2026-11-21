"""Engagement autour du ballon (ticket v2-realisme/28a) : joueurs de champ à moins de 10, 15 et 20 m du ballon,
distance au coéquipier le plus proche, diagnostic par rôle. Mêmes fonctions pour le moteur et le suivi réel ; le banc
observe sans changer le jeu."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import scripts.v2_indicators as ind
from scripts import suivi_distributions as sd
from scripts import suivi_reel as sr
from scripts.measure_v2 import engagement_report
from v2engine.cerveau import APPEL, BALLON_LIBRE, TENIR
from v2engine.defense import PRESSEUR
from v2engine.geometry import Vec2
from tests.scenes import player


def test_players_within_counts_strictly_inside_the_radius():
    ball = Vec2(50.0, 34.0)
    points = [Vec2(50.0, 34.0), Vec2(59.9, 34.0), Vec2(60.0, 34.0), Vec2(50.0, 48.0), Vec2(70.0, 34.0)]
    assert ind.players_within(ball, points, 10.0) == 2  # 10,0 m pile : dehors
    assert ind.players_within(ball, points, 15.0) == 4
    assert ind.players_within(ball, points, 20.0) == 4
    assert ind.players_within(ball, [], 10.0) == 0


def test_mean_nearest_teammate():
    # trois joueurs alignés à 6 m puis 8 m : plus proches 6, 6, 8
    points = [Vec2(0.0, 0.0), Vec2(6.0, 0.0), Vec2(14.0, 0.0)]
    assert ind.mean_nearest_teammate(points) == pytest.approx((6.0 + 6.0 + 8.0) / 3.0)
    assert ind.mean_nearest_teammate([Vec2(0.0, 0.0)]) is None


def test_real_tracking_uses_the_engine_functions():
    for name in ("players_within", "mean_nearest_teammate", "NEAR_BALL_RADII_M"):
        assert getattr(sd, name) is getattr(ind, name)


def _real_frame(ball, players, possession=sr.HOME, source="skillcorner"):
    return sr.Frame(source, "1", 1, 0.0, ball, tuple(players), possession, None, None)


def test_real_near_ball_known_scene_and_ball_out_of_play():
    players = [sr.Player("h1", sr.HOME, 52.0, 34.0, True), sr.Player("h2", sr.HOME, 62.0, 34.0, True),
               sr.Player("hgk", sr.HOME, 5.0, 34.0, True),
               sr.Player("a1", sr.AWAY, 50.0, 40.0, True), sr.Player("a2", sr.AWAY, 80.0, 34.0, True)]
    out = sd.near_ball(_real_frame((50.0, 34.0), players), {"hgk"})
    assert out["joueurs de champ à moins de 10 m du ballon"] == 2  # h1 (2 m), a1 (6 m) ; gardien exclu
    assert out["joueurs de champ à moins de 15 m du ballon"] == 3  # + h2 (12 m)
    assert out["joueurs de champ à moins de 10 m du ballon, équipe avec ballon"] == 1
    assert out["joueurs de champ à moins de 10 m du ballon, équipe sans ballon"] == 1
    assert out["distance au coéquipier le plus proche, équipe avec ballon (m)"] == pytest.approx(10.0)
    # ballon non suivi, ou possession inconnue chez SkillCorner : image écartée ; Metrica n'a pas de possession
    assert sd.near_ball(_real_frame(None, players), {"hgk"}) is None
    assert sd.near_ball(_real_frame((50.0, 34.0), players, possession=None), {"hgk"}) is None
    metrica = sd.near_ball(_real_frame((50.0, 34.0), players, possession=None, source="metrica"), {"hgk"})
    assert metrica["joueurs de champ à moins de 10 m du ballon"] == 2
    assert metrica["joueurs de champ à moins de 10 m du ballon, équipe sans possession"] == pytest.approx(1.0)


def _scene():
    ball = SimpleNamespace(position=Vec2(50.0, 34.0), restart=None, holder="h1")
    players = [player("h1", "home", 51.0, 34.0), player("h2", "home", 58.0, 34.0), player("h3", "home", 75.0, 34.0),
               player("hgk", "home", 50.5, 34.0, poste="GK"),
               player("a1", "away", 53.0, 36.0), player("a2", "away", 62.0, 34.0)]
    roles = {"h1": "porteur", "h2": APPEL, "h3": TENIR, "a1": PRESSEUR, "a2": BALLON_LIBRE}
    targets = {"h1": Vec2(51.0, 34.0), "h2": Vec2(80.0, 34.0), "h3": Vec2(75.0, 34.0), "a1": Vec2(51.0, 34.0),
               "a2": Vec2(50.0, 34.0)}
    return ball, players, roles, targets


def _collector(roles, targets) -> ind.Collector:
    c = ind.Collector(geometry_every_s=1e9)
    c.team = "home"
    for name, role in roles.items():
        c.on_role(name, role)
        c.on_target(name, targets[name])
    return c


def test_engine_engagement_counts_and_diagnostic_by_role():
    ball, players, roles, targets = _scene()
    c = _collector(roles, targets)
    c._engagement(players, ball)
    stats, k = c.stats, c.count
    assert stats["engagement : joueurs de champ à moins de 10 m du ballon"].values == [3]  # h1, h2, a1 (gardien exclu)
    assert stats["engagement : joueurs de champ à moins de 15 m du ballon"].values == [4]  # + a2 (12 m)
    assert stats["engagement : joueurs de champ à moins de 10 m du ballon, équipe avec ballon"].values == [2]
    assert stats["engagement : joueurs de champ à moins de 10 m du ballon, équipe sans ballon"].values == [1]
    assert k["engagement : échantillons"] == 1
    # zones vues de chaque équipe : ballon à x = 50, tiers médian pour les deux
    assert k["engagement : échantillons, équipe avec ballon, tiers médian"] == 1
    assert k["engagement par rôle, équipe sans ballon, tiers médian : presseur"] == 1
    assert stats["engagement par zone : joueurs de champ à moins de 10 m du ballon, équipe sans ballon, "
                 "tiers médian de cette équipe"].values == [1]
    assert k["engagement par rôle : avec ballon : porteur"] == 1
    assert k["engagement par rôle : avec ballon : appel"] == 1
    assert k["engagement par rôle : avec ballon : tenir sa place"] == 0  # h3 à 25 m
    assert k["engagement par rôle : sans ballon : presseur"] == 1
    assert k["engagement par rôle : sans ballon : ballon libre"] == 1
    # l'appelant passe près du ballon mais vise loin ; le presseur et le chasseur y vont
    assert k["engagement par rôle, cible près du ballon : avec ballon : appel"] == 0
    assert k["engagement par rôle, cible près du ballon : sans ballon : presseur"] == 1


def test_dead_ball_is_not_sampled():
    ball, players, roles, targets = _scene()
    c = _collector(roles, targets)
    c._engagement(players, SimpleNamespace(position=ball.position, restart=object(), holder=None))
    assert c.count["engagement : échantillons"] == 0 and not c.stats


def test_engagement_report():
    ball, players, roles, targets = _scene()
    c = _collector(roles, targets)
    c._engagement(players, ball)
    c._engagement(players, ball)
    out: dict = {}
    engagement_report(c, out)
    assert out["engagement : joueurs de champ à moins de 10 m du ballon (quartiles)"]["mediane"] == 3
    rows = out["engagement : diagnostic par rôle à moins de 15 m (équipe : rôle)"]
    assert rows["sans ballon : presseur"] == {"joueurs par échantillon": 1.0, "part de l'engagement": 0.25,
                                              "cible près du ballon (part)": 1.0}
    assert rows["avec ballon : appel"]["cible près du ballon (part)"] == 0.0
    assert out["engagement : joueurs par échantillon à moins de 15 m, par équipe, zone vue de cette équipe, et rôle"][
        "équipe avec ballon, tiers médian"]["porteur"] == 1.0


def test_report_without_samples_gives_empty_rows_not_errors():
    out: dict = {}
    engagement_report(ind.Collector(geometry_every_s=1e9), out)
    assert out["engagement : diagnostic par rôle à moins de 15 m (équipe : rôle)"] == {}


def test_engagement_role_splits_the_presser_role():
    assert ind.engagement_role(PRESSEUR, "presser", "presse le porteur adverse") == "presseur attribué"
    assert ind.engagement_role(PRESSEUR, "couvrir", "quitte le bloc, couvre derrière le presseur") == \
        "presseur : couvre derrière le presseur attribué (11g)"
    assert ind.engagement_role(PRESSEUR, "aller au ballon", "quitte le bloc pour aller au ballon") == \
        "presseur : quitte le bloc vers le ballon"
    assert ind.engagement_role(PRESSEUR, "aller au ballon", "presse le porteur adverse") == \
        "presseur : va au porteur sans attribution"
    assert ind.engagement_role(PRESSEUR) == PRESSEUR  # action inconnue : rôle brut
    assert ind.engagement_role("couverture", "couvrir", "couvre son presseur") == "couverture"


def test_attributed_presser_and_player_leaving_the_bloc_are_two_entries():
    ball = SimpleNamespace(position=Vec2(70.0, 34.0), restart=None, holder="h1")
    players = [player("h1", "home", 70.0, 34.0), player("a1", "away", 72.0, 34.0), player("a2", "away", 74.0, 36.0)]
    c = ind.Collector(geometry_every_s=1e9)
    c.team = "home"
    for name, role in (("h1", "porteur"), ("a1", PRESSEUR), ("a2", PRESSEUR)):
        c.on_role(name, role)
    c.on_target("h1", Vec2(70.0, 34.0))
    c.on_target("a1", Vec2(71.0, 34.0), "presser", "presse le porteur adverse")
    c.on_target("a2", Vec2(70.0, 34.0), "aller au ballon", "quitte le bloc pour aller au ballon")
    c._engagement(players, ball)
    k = c.count
    assert k["engagement par rôle : sans ballon : presseur attribué"] == 1
    assert k["engagement par rôle : sans ballon : presseur : quitte le bloc vers le ballon"] == 1
    # ballon à x = 70 : tiers offensif pour l'équipe qui l'a, tiers médian pour celle qui défend (vue de son but)
    assert k["engagement par rôle, équipe sans ballon, tiers médian : presseur attribué"] == 1
    assert k["engagement : échantillons, équipe avec ballon, tiers offensif"] == 1


def test_real_near_ball_by_zone_of_each_team():
    players = [sr.Player("h1", sr.HOME, 80.0, 34.0, True), sr.Player("a1", sr.AWAY, 82.0, 34.0, True),
               sr.Player("a2", sr.AWAY, 85.0, 30.0, True)]
    out = sd.near_ball(_real_frame((80.0, 34.0), players), set())
    # ballon à x = 80 : tiers offensif de l'équipe à domicile (en possession), tiers défensif de l'équipe extérieure
    assert out["par zone : joueurs de champ à moins de 10 m du ballon, équipe avec ballon, tiers offensif de cette équipe"] == 1
    assert out["par zone : joueurs de champ à moins de 10 m du ballon, équipe sans ballon, tiers défensif de cette équipe"] == 2
