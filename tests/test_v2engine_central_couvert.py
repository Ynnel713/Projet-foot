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
from v2engine.movement import PlayerState

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
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=3.0))
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
