"""Le défenseur central ne quitte sa ligne que couvert (ticket v2-realisme/10b) : un central dont le rôle (presser,
marquer) l'emmène à plus de 10 m de sa place de référence sans ballon, sans le rapprocher de son but, ne le prend que si
un partenaire tient sa place, si un compensateur y arrive avant l'attaquant le plus proche et l'accepte (Teamwork), ou
si aucun attaquant n'en est à 20 m ou moins ; sinon il garde sa ligne et cède le rôle."""

from __future__ import annotations

import random

import pytest

import v2engine.defense as defense_module
from v2engine.ball_state import BallState
from v2engine.defense import (COMPENSATION, HOLE_AWAY_M, HOLE_DANGER_M, HOLE_FILLED_M, MARQUAGE, PRESSEUR, DefensiveRoles,
                              arrival_time_s, line_exit, own_goal)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps

GOAL = own_goal("home")  # domicile défend x = 0
PLACE = Vec2(10.0, 34.0)  # place de référence du central


def _p(name: str, x: float, y: float = 34.0, poste: str = "DC", team: str = "home", pace: float = 60,
       place: Vec2 | None = None) -> PlayerState:
    """Joueur en (x, y) ; `place` : sa place de référence sans ballon (par défaut, là où il est)."""
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=60, stamina=60, home_target=place or Vec2(x, y))


class _Bloc:
    """Bloc de scène : la place de référence de chacun est sa `home_target`, sans erreur de placement."""

    def reference(self, player: PlayerState, ball: Vec2, situation: str, now_s: float = 0.0) -> Vec2:
        return player.home_target

    def placement_error(self, player: PlayerState, now_s: float) -> Vec2:
        return Vec2(0.0, 0.0)


def _update(players: list[PlayerState], holder: str, bloc: _Bloc | None = None,
            defense: DefensiveRoles | None = None) -> DefensiveRoles:
    random.seed(0)
    holding = next(p for p in players if p.name == holder)
    defense = defense or DefensiveRoles()
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), bloc, 0.0)
    return defense


def _role(defense: DefensiveRoles, name: str) -> tuple[str, str] | None:
    assigned = defense.assignments.get(name)
    return None if assigned is None else (assigned.role, assigned.mate)


def _marking_scene() -> list[PlayerState]:
    """Porteur adverse dans sa moitié (pas de couverture), pressé par le milieu ; l'avant-centre BU1 décroche à 24,5 m du but (dangereux), son
    marquage emmène le central à plus de 10 m de sa place ; BU2, à 18,9 m de la place du central, menace la profondeur."""
    return [_p("H", 56.0, team="away", poste="MC"), _p("MC", 58.0, poste="MC", place=Vec2(52.0, 34.0)),
            _p("DC", 14.0, place=PLACE), _p("BU1", 24.5, team="away", poste="BU"),
            _p("BU2", 20.0, y=50.0, team="away", poste="BU")]


def test_line_exit_geometry() -> None:
    assert HOLE_AWAY_M == 10.0 and HOLE_FILLED_M == 5.0 and HOLE_DANGER_M == 20.0  # constantes reprises du ticket 09
    assert line_exit(Vec2(20.1, 34.0), PLACE, GOAL)  # 10,1 m devant sa place
    assert not line_exit(Vec2(19.9, 34.0), PLACE, GOAL)
    assert line_exit(Vec2(10.0, 44.5), PLACE, GOAL)  # de côté, même profondeur : une sortie
    assert not line_exit(Vec2(3.0, 46.0), PLACE, GOAL)  # plus près de son but : il couvre la profondeur
    assert line_exit(Vec2(105.0 - 21.0, 34.0), Vec2(105.0 - 10.0, 34.0), own_goal("away"))  # extérieur : en miroir


def test_dropping_striker_no_cover_the_centre_back_holds_his_line() -> None:
    players = _marking_scene()
    assert _role(_update(players, "H"), "DC") == (MARQUAGE, "BU1")  # sans bloc : comme avant, il suit
    defense = _update(players, "H", _Bloc())
    assert _role(defense, "DC") is None  # il garde sa ligne
    # seul joueur libre : personne d'autre ne marque, l'attaquant n'est pas marqué
    assert not any(a.role == MARQUAGE for a in defense.assignments.values())


def test_a_partner_holds_his_place_the_centre_back_follows() -> None:
    players = _marking_scene() + [_p("MDC", 8.0, y=36.0, poste="MDC", place=Vec2(25.0, 34.0))]  # à 2,8 m de sa place
    defense = _update(players, "H", _Bloc())
    assert _role(defense, "DC") == (MARQUAGE, "BU1")
    assigned = defense.assignments["DC"]
    assert assigned.reference == PLACE and assigned.target.distance_to(PLACE) > HOLE_AWAY_M  # sortie, tracée


@pytest.mark.parametrize("draw, follows", [(0.0, True), (0.999, False)])
def test_a_covering_midfielder_must_arrive_first_and_accept(monkeypatch: pytest.MonkeyPatch, draw: float,
                                                            follows: bool) -> None:
    # le milieu défensif est à 7,3 m de la place du central (pas encore dessus), BU2 à 18,9 m : il y arrive avant lui ;
    # Teamwork : il l'accepte (tirage bas) ou non (tirage haut)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    bu2 = next(p for p in _marking_scene() if p.name == "BU2")
    assert arrival_time_s(mdc, PLACE) + 1.0 < arrival_time_s(bu2, PLACE)  # même avec le plus long délai de réaction
    monkeypatch.setattr(defense_module.DEFENSE, "random", lambda: draw)
    defense = _update(_marking_scene() + [mdc], "H", _Bloc())
    if follows:
        assert _role(defense, "DC") == (MARQUAGE, "BU1")
    else:  # il garde sa ligne, le milieu défensif, libre le plus proche après lui, marque
        assert _role(defense, "DC") is None and _role(defense, "MDC") == (MARQUAGE, "BU1")
    assert defense.cover_draws[("DC", "MDC", "BU1")] is follows  # un tirage par partenaire visé
    if follows:  # sorti couvert : la compensation reprend ce tirage, sans en refaire un
        monkeypatch.setattr(defense_module.DEFENSE, "random", lambda: 1.0)
        assert defense._willing(_p("DC", 14.0, place=PLACE), mdc) is True


def test_a_covering_midfielder_too_slow_does_not_cover(monkeypatch: pytest.MonkeyPatch) -> None:
    # le milieu défensif est trop loin de la place (40 m) : BU2 y arrive avant lui, le central reste
    monkeypatch.setattr(defense_module.DEFENSE, "random", lambda: 0.0)
    defense = _update(_marking_scene() + [_p("MDC", 45.0, y=10.0, poste="MDC", pace=11, place=Vec2(25.0, 34.0))],
                      "H", _Bloc())
    assert _role(defense, "DC") is None


def test_no_attacker_near_his_place_the_centre_back_follows() -> None:
    players = [p for p in _marking_scene() if p.name != "BU2"]  # seul l'attaquant qu'il marque est près de sa place
    assert _role(_update(players, "H", _Bloc()), "DC") == (MARQUAGE, "BU1")


def test_uncovered_centre_back_gives_up_the_press() -> None:
    # porteur à 20 m devant la place du central, hors de toute zone ; le central, rapide, arrive le premier, mais sa
    # place n'est pas couverte et BU2 la menace : le milieu, lent, presse
    dc = _p("DC", 12.0, pace=99, place=PLACE)
    mc = _p("MC", 48.0, poste="MC", pace=11, place=Vec2(45.0, 34.0))
    holder, bu2 = _p("H", 30.0, team="away", poste="BU"), _p("BU2", 20.0, y=50.0, team="away", poste="BU")
    assert arrival_time_s(dc, holder.position) < arrival_time_s(mc, holder.position)
    players = [holder, dc, mc, bu2]
    assert _role(_update(players, "H"), "DC") == (PRESSEUR, "H")  # sans bloc : comme avant
    defense = _update(players, "H", _Bloc())
    # (il prend la couverture, hors du périmètre du ticket : tracée, pas restreinte)
    assert _role(defense, "MC") == (PRESSEUR, "H") and _role(defense, "DC") != (PRESSEUR, "H")
    # seul joueur libre : il presse quand même (quelqu'un presse toujours)
    assert _role(_update([holder, dc, bu2], "H", _Bloc()), "DC") == (PRESSEUR, "H")


def test_once_out_covered_he_keeps_the_role_for_the_same_attacker() -> None:
    mdc_on_place = _p("MDC", 8.0, y=36.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = _update(_marking_scene() + [mdc_on_place], "H", _Bloc())
    assert _role(defense, "DC") == (MARQUAGE, "BU1") and defense.exits == {"DC": "BU1"}
    # le milieu défensif s'en va : sorti couvert, le central garde son marquage (pas de clignotement)
    mdc_gone = _p("MDC", 30.0, y=60.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = _update(_marking_scene() + [mdc_gone], "H", _Bloc(), defense)
    assert _role(defense, "DC") == (MARQUAGE, "BU1")
    # sans mémoire (nouvelle équipe de rôles), la même scène le retient
    assert _role(_update(_marking_scene() + [mdc_gone], "H", _Bloc()), "DC") != (MARQUAGE, "BU1")


def test_line_exits_are_traced_and_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20261118)
        # 5 minutes (3 avant le ticket v2-realisme/04e : le ballon devant le porteur décale les phases de jeu, plus
        # aucune sortie de ligne dans les 3 premières minutes de cette graine ; 2 en 5 minutes)
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=5.0))
    records = traces[0].line_exits
    assert records and records == traces[1].line_exits
    assert all(r.exit == bool(r.role) and (r.exit or (not r.covered and not r.threatened)) for r in records)


def _draws(monkeypatch: pytest.MonkeyPatch, values: list[float]) -> list[float]:
    """Tirages du flux DEFENSE pris dans `values`, puis 0 ; renvoie la liste des tirages faits."""
    made: list[float] = []

    def draw() -> float:
        made.append(values[len(made)] if len(made) < len(values) else 0.0)
        return made[-1]
    monkeypatch.setattr(defense_module.DEFENSE, "random", draw)
    return made


def test_a_refusal_holds_while_the_holder_is_the_same(monkeypatch: pytest.MonkeyPatch) -> None:
    # réserve A1 de l'expert : tick 1, le milieu défensif refuse (tirages hauts) ; tick 2, les tirages suivants
    # accepteraient : le refus doit tenir, sans nouveau tirage, tant que le porteur ne change pas
    made = _draws(monkeypatch, [0.999] * 3)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = _update(_marking_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") is None and _role(defense, "MDC") == (MARQUAGE, "BU1")
    drawn = len(made)
    defense = _update(_marking_scene() + [mdc], "H", _Bloc(), defense)
    assert _role(defense, "DC") is None and _role(defense, "MDC") == (MARQUAGE, "BU1")
    assert len(made) == drawn  # aucun nouveau tirage
    # nouveau porteur : nouveaux tirages (ici des accords), le central suit
    scene = [p for p in _marking_scene() if p.name != "H"] + [mdc, _p("H2", 57.0, y=40.0, team="away", poste="MC")]
    defense = _update(scene, "H2", _Bloc(), defense)
    assert _role(defense, "DC") == (MARQUAGE, "BU1") and len(made) > drawn


def test_the_compensation_reuses_the_draw_that_let_him_out(monkeypatch: pytest.MonkeyPatch) -> None:
    # réserve A1 de l'expert : sortie accordée (tirages bas) ; le central est ensuite à 12 m de sa place, BU2 menace :
    # le milieu défensif compense, même si tout tirage suivant serait un refus
    _draws(monkeypatch, [0.0] * 3)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = _update(_marking_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") == (MARQUAGE, "BU1")
    monkeypatch.setattr(defense_module.DEFENSE, "random", lambda: 0.999)
    out = [_p("DC", 22.0, place=PLACE) if p.name == "DC" else p for p in _marking_scene()] + [mdc]
    defense = _update(out, "H", _Bloc(), defense)
    assert _role(defense, "DC") == (MARQUAGE, "BU1") and _role(defense, "MDC") == (COMPENSATION, "DC")


def test_the_draw_that_let_him_out_survives_a_change_of_holder(monkeypatch: pytest.MonkeyPatch) -> None:
    # A1 de l'expert, passage 2 : décrochage servi. Sortie accordée avec le porteur H ; la passe arrive à BU1 (nouveau
    # porteur, tirages des couvreurs effacés), le central l'a suivi à 12 m de sa place, BU2 menace : le milieu défensif
    # compense sur l'accord qui a autorisé la sortie, même si tout tirage suivant serait un refus
    _draws(monkeypatch, [0.0] * 3)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = _update(_marking_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") == (MARQUAGE, "BU1") and defense.exit_cover == {"DC": ("MDC", "BU1")}
    monkeypatch.setattr(defense_module.DEFENSE, "random", lambda: 0.999)
    # BU1 porteur dans la moitié défendue : la couverture revient à l'autre central, au plus près du point de couverture
    dc2 = _p("DC2", 16.0, y=30.0, place=Vec2(16.0, 30.0))
    served = [_p("DC", 22.0, place=PLACE) if p.name == "DC" else p for p in _marking_scene()] + [mdc, dc2]
    defense = _update(served, "BU1", _Bloc(), defense)
    assert _role(defense, "DC") == (PRESSEUR, "BU1")  # il presse le décrocheur servi, exempté pour lui
    assert _role(defense, "MDC") == (COMPENSATION, "DC")


@pytest.mark.parametrize("hole", [False, True])
def test_an_open_hole_imposes_its_draw_on_the_cover(monkeypatch: pytest.MonkeyPatch, hole: bool) -> None:
    # A1 de l'expert, passage 2 : un trou encore ouvert (tirage `willing` présent) impose son tirage à la couverture,
    # dans les deux sens, quel que soit le tirage `_covers` qui serait fait
    _draws(monkeypatch, [0.999 if hole else 0.0] * 3)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    defense = DefensiveRoles()
    defense.willing[("DC", "MDC")] = hole
    defense = _update(_marking_scene() + [mdc], "H", _Bloc(), defense)
    assert (_role(defense, "DC") == (MARQUAGE, "BU1")) is hole
    assert ("DC", "MDC", "BU1") not in defense.cover_draws  # aucun tirage de couverture


# --- ticket v2-realisme/10b2 : la couverture suit la même règle ; le couvreur retenu est réservé ---

def _cover_scene() -> list[PlayerState]:
    """Porteur adverse dans la moitié défendue, à 20 m devant la place du central (point de couverture à 14 m de cette
    place : une sortie), pressé par le milieu ; le central arrive le premier sur le point de couverture ; BU2, à 18,9 m
    de sa place, la menace."""
    return [_p("H", 30.0, team="away", poste="MC"), _p("MC", 32.0, poste="MC", place=Vec2(32.0, 34.0)),
            _p("DC", 22.0, place=PLACE), _p("BU2", 20.0, y=50.0, team="away", poste="BU")]


def test_uncovered_centre_back_leaves_the_cover_to_another() -> None:
    # le milieu défensif, trop loin pour combler la place avant BU2, prend la couverture ; le central garde sa ligne
    mdc = _p("MDC", 30.0, y=40.0, poste="MDC", place=Vec2(30.0, 40.0))
    defense = _update(_cover_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "MC") == (PRESSEUR, "H")
    assert _role(defense, "MDC") == ("couverture", "H") and _role(defense, "DC") is None


def test_nobody_else_free_nobody_covers() -> None:
    defense = _update(_cover_scene(), "H", _Bloc())
    assert _role(defense, "MC") == (PRESSEUR, "H") and _role(defense, "DC") is None
    assert not any(a.role == "couverture" for a in defense.assignments.values())


def test_a_partner_on_his_place_the_centre_back_covers() -> None:
    # le milieu défensif tient la place du central (à 5 m ou moins) : le central couvre, sortie retenue pour H
    mdc = _p("MDC", 13.0, y=36.0, poste="MDC", place=Vec2(13.0, 36.0))
    defense = _update(_cover_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") == ("couverture", "H") and defense.exits == {"DC": "H"}


def test_the_coverer_of_an_exit_is_reserved(monkeypatch: pytest.MonkeyPatch) -> None:
    # réserve A2 de l'expert au 10b : le central sort marquer BU1 sur l'accord du milieu défensif ; BU3, dangereux et
    # plus près du milieu que de tout autre, n'est pas marqué par lui : le milieu reste libre pour combler la place
    _draws(monkeypatch, [0.0] * 5)
    mdc = _p("MDC", 12.0, y=27.0, poste="MDC", place=Vec2(25.0, 34.0))
    bu3 = _p("BU3", 22.0, y=22.5, team="away", poste="BU")  # à 24,8 m du but, après BU1 (24,5 m) dans l'ordre
    defense = _update(_marking_scene() + [mdc, bu3], "H", _Bloc())
    assert _role(defense, "DC") == (MARQUAGE, "BU1") and defense.reserved == {"MDC"}
    assert _role(defense, "MDC") is None  # sans la réserve : marquage de BU3


def test_the_covering_centre_back_is_rechecked_every_tick() -> None:
    # 10b2, décision du propriétaire : pas d'exemption « sorti couvert » pour la couverture. Le central couvre tant que
    # le milieu défensif tient sa place ; le milieu remonte (trop loin pour la combler avant BU2) : la couverture lui
    # revient au tick suivant (avec l'exemption, le central la garderait)
    mdc = _p("MDC", 13.0, y=36.0, poste="MDC", place=Vec2(13.0, 36.0))
    defense = _update(_cover_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") == ("couverture", "H") and defense.exits == {"DC": "H"}
    mdc = _p("MDC", 30.0, y=40.0, poste="MDC", place=Vec2(30.0, 40.0))
    defense = _update(_cover_scene() + [mdc], "H", _Bloc(), defense)
    assert _role(defense, "MDC") == ("couverture", "H") and _role(defense, "DC") is None


def _delay_for(monkeypatch: pytest.MonkeyPatch, late_s: float) -> None:
    """Délai de réaction du milieu défensif tel qu'il arrive sur la place du central `late_s` après BU2 (négatif : avant)."""
    bu2, mdc = _p("BU2", 20.0, y=50.0, team="away", poste="BU"), _p("MDC", 30.0, y=40.0, poste="MDC")
    gap = arrival_time_s(bu2, PLACE) - arrival_time_s(mdc, PLACE)
    real = defense_module.reaction_delay_s
    monkeypatch.setattr(defense_module, "reaction_delay_s",
                        lambda p, *a, **k: gap + late_s if p.name == "MDC" else real(p, *a, **k))


@pytest.mark.parametrize(("late_s", "keeps"), [(0.1, True), (0.5, False)])
def test_the_covering_centre_back_keeps_the_holder_margin(monkeypatch: pytest.MonkeyPatch, late_s: float,
                                                          keeps: bool) -> None:
    # réserve A1 de l'expert au 10b2 : le central qui couvre déjà garde le rôle tant que son couvreur arrive au plus
    # `HOLD_MARGIN_S` (0,3 s) après l'attaquant, comme le titulaire d'une compensation ; au-delà, il le perd
    _draws(monkeypatch, [0.0] * 10)
    mdc = _p("MDC", 30.0, y=40.0, poste="MDC", place=Vec2(30.0, 40.0))
    _delay_for(monkeypatch, -0.1)  # tick 1 : le milieu arrive à temps, le central couvre
    defense = _update(_cover_scene() + [mdc], "H", _Bloc())
    assert _role(defense, "DC") == ("couverture", "H")
    _delay_for(monkeypatch, late_s)
    defense = _update(_cover_scene() + [mdc], "H", _Bloc(), defense)
    assert (_role(defense, "DC") == ("couverture", "H")) is keeps


def test_the_coverer_of_an_ongoing_exit_does_not_cover(monkeypatch: pytest.MonkeyPatch) -> None:
    # réserve A2 de l'expert au 10b2 : le central marque BU1 en sortie gardée sur l'accord du milieu défensif ; la
    # couverture, choisie avant le marquage, ne revient pas au milieu, réservé dès le début du tick
    _draws(monkeypatch, [0.0] * 10)
    mdc = _p("MDC", 30.0, y=40.0, poste="MDC", place=Vec2(30.0, 40.0))
    defense = DefensiveRoles()
    defense.exits = {"DC": "BU1"}
    defense.exit_cover = {"DC": ("MDC", "BU1")}
    defense = _update(_cover_scene() + [mdc], "H", _Bloc(), defense)
    assert "MDC" in defense.reserved and _role(defense, "MDC") != ("couverture", "H")


def _cover_at(x_holder: float) -> list[PlayerState]:
    """Scène de couverture, porteur en `x_holder` (point de couverture 6 m derrière lui), pressé par le milieu."""
    return [_p("H", x_holder, team="away", poste="MC"), _p("MC", x_holder + 2.0, poste="MC", place=Vec2(32.0, 34.0)),
            _p("DC", 22.0, place=PLACE), _p("BU2", 20.0, y=50.0, team="away", poste="BU")]


@pytest.mark.parametrize(("spot_m", "keeps"), [(9.9, True), (11.0, False)])
def test_the_covering_centre_back_loses_the_cover_at_the_exit_threshold(spot_m: float, keeps: bool) -> None:
    # réserve A1 de l'expert au 10b2 : le central qui couvre (point à 7 m de sa place) garde le rôle jusqu'à
    # `HOLE_AWAY_M` ; au-delà, place non tenue et menacée, personne d'autre de libre : personne ne couvre
    defense = _update(_cover_at(PLACE.x + 7.0 + 6.0), "H", _Bloc())
    assert _role(defense, "DC") == ("couverture", "H")
    defense = _update(_cover_at(PLACE.x + spot_m + 6.0), "H", _Bloc(), defense)
    assert (_role(defense, "DC") == ("couverture", "H")) is keeps


@pytest.mark.parametrize(("spot_m", "takes"), [(7.0, True), (9.0, False)])
def test_a_new_centre_back_takes_the_cover_only_inside_the_band(spot_m: float, takes: bool) -> None:
    # hystérésis : un central qui ne couvrait pas ne prend sans couverture qu'un point à moins de `HOLE_AWAY_M` moins
    # la distance qu'il parcourt en `HOLD_MARGIN_S` (2,6 m à Pace 60, soit 7,4 m) ; entre 7,4 et 10 m, il ne le prend
    # pas, le titulaire le garde (test précédent) : le rôle ne va et vient plus au seuil
    band = defense_module.HOLD_MARGIN_S * max_speed_mps(60)
    assert 7.0 < HOLE_AWAY_M - band < 9.0
    defense = _update(_cover_at(PLACE.x + spot_m + 6.0), "H", _Bloc())
    assert (_role(defense, "DC") == ("couverture", "H")) is takes


def test_a_centre_back_who_lost_the_cover_is_no_longer_its_holder() -> None:
    # réserve A1 de l'expert au 10b2 : le central perd la couverture à 11 m, personne ne couvre ; le point revient à
    # 9 m (au-delà de 7,4 m) : il ne la reprend pas sans couverture (hystérésis : il n'en est plus titulaire)
    defense = _update(_cover_at(PLACE.x + 7.0 + 6.0), "H", _Bloc())
    assert _role(defense, "DC") == ("couverture", "H")
    defense = _update(_cover_at(PLACE.x + 11.0 + 6.0), "H", _Bloc(), defense)
    assert _role(defense, "DC") is None
    defense = _update(_cover_at(PLACE.x + 9.0 + 6.0), "H", _Bloc(), defense)
    assert _role(defense, "DC") is None


@pytest.mark.parametrize(("behind_m", "leaves"), [(1.0, True), (4.0, False)])
def test_the_band_also_applies_behind_the_place(behind_m: float, leaves: bool) -> None:
    # hystérésis du 10b2 sur le second seuil de `line_exit` : un point à 12 m de la place, à 1 m en deçà vers le but
    # (pas une sortie pour `line_exit`), reste une sortie pour un central qui ne couvrait pas (bande de 2,6 m à Pace
    # 60) ; à 4 m en deçà, non. Place menacée par BU2, personne pour la combler
    target = Vec2(PLACE.x - behind_m, PLACE.y + (12.0 ** 2 - behind_m ** 2) ** 0.5)
    assert not line_exit(target, PLACE, GOAL)
    dc, bu2 = _p("DC", 22.0, place=PLACE), _p("BU2", 20.0, y=50.0, team="away", poste="BU")
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(0.0, 0.0), holder="H")
    assert DefensiveRoles()._leaves_uncovered(dc, target, "H", [dc, bu2], [dc], {"DC": PLACE}, GOAL, ball, 0.0,
                                              recheck=True) is leaves
