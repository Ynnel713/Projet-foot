"""Vérifications V1 et V2 demandées par l'expert (ticket v2-collectif/09), hors dépôt. Réutilise `_scene`, `_update`
et `step` de tests/test_v2engine_compensations.py (importé en lecture, sans bytecode).

V1 : après l'arrivée de l'ailier (à 1,5 m de la place), le compensateur garde-t-il son rôle tant que le latéral
(immobile) n'est pas revenu ? Déplacements : ailier vers la place ; joueur domicile avec rôle vers la cible de son
rôle ; sans rôle vers sa place de bloc (`bloc.reference`, comme REPLACEMENT) ; latéral immobile.
V2 : passe en vol vers l'ailier puis ailier porteur : la compensation de la place du latéral tient-elle ?

Usage (racine du dépôt) : PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 uv run python <ce fichier> v1|v2"""

from __future__ import annotations

import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "tests"))
import test_v2engine_compensations as t  # noqa: E402
from v2engine.ball_state import BallState  # noqa: E402
from v2engine.defense import COMPENSATION, PRESSEUR, DefensiveRoles  # noqa: E402
from v2engine.geometry import Vec2  # noqa: E402
from v2engine.situation import DEFENSE_PLACEE  # noqa: E402

DT = 0.1


def _move(players, defense, bloc, holder_pos, now_s, winger_target=None, static_unassigned=False):
    moved = []
    for p in players:
        a = defense.assignments.get(p.name)
        if p.name == "W" and winger_target is not None:
            p = t.step(p, DT, winger_target, 0.0)
        elif p.team == "home" and p.name != "RB":
            if a is not None:
                p = t.step(p, DT, a.target, 0.0)
            elif not static_unassigned:
                p = t.step(p, DT, bloc.reference(p, holder_pos, DEFENSE_PLACEE, now_s), 0.0)
        moved.append(p)
    return moved


def _comp_rb(defense):
    return next((n for n, a in defense.assignments.items() if a.role == COMPENSATION and a.mate == "RB"), None)


def v1(n=1000):
    kept = {0.5: 0, 1.0: 0, 2.0: 0}
    near = {0.5: 0, 1.0: 0, 2.0: 0}
    arrived = lost = 0
    lost_dist, lost_offset = [], []
    for seed in range(n):
        random.seed(seed)
        players, bloc, place, _ = t._scene()
        holder_pos = next(p for p in players if p.name == "H").position
        defense, t_arr, last_comp, lost_at = DefensiveRoles(), None, None, None
        for i in range(int(8.0 / DT)):
            now = i * DT
            defense = t._update(players, bloc, defense=defense, now_s=now)
            comp = _comp_rb(defense)
            if last_comp is not None and comp is None and lost_at is None and t_arr is not None:
                lost_at = now
                c = next(p for p in players if p.name == last_comp)
                lost_dist.append(c.position.distance_to(place))
                lost_offset.append(round(now - t_arr, 1))
            if comp is not None:
                last_comp = comp
            if t_arr is not None:
                for k in kept:
                    if abs(now - (t_arr + k)) < DT / 2:
                        kept[k] += comp is not None
                        home = [p for p in players if p.team == "home" and p.name != "RB"]
                        near[k] += min(p.position.distance_to(place) for p in home) < 5.0
                if now >= t_arr + 2.0 - DT / 2:
                    break
            players = _move(players, defense, bloc, holder_pos, now, winger_target=place)
            w = next(p for p in players if p.name == "W")
            if t_arr is None and w.position.distance_to(place) <= 1.5:
                t_arr = now + DT
        if t_arr is not None:
            arrived += 1
            lost += lost_at is not None
    print(f"V1 : {n} tirages, ailier arrivé dans {arrived}")
    for k in kept:
        print(f"  +{k} s : rôle COMPENSATION (RB) encore attribué {kept[k] / arrived:.1%} ; "
              f"joueur domicile à moins de 5 m de la place {near[k] / arrived:.1%}")
    print(f"  rôle perdu après l'arrivée (latéral toujours absent) : {lost / arrived:.1%}")
    if lost_dist:
        print(f"  distance du compensateur à la place au retrait : médiane {statistics.median(lost_dist):.2f} m, "
              f"min {min(lost_dist):.2f}, max {max(lost_dist):.2f}")
        print(f"  instant du retrait après l'arrivée (s) : {sorted(set(lost_offset))[:10]} ... médiane "
              f"{statistics.median(lost_offset):.1f}")


def v2(n=200):
    flight_ticks = flight_comp = flight_presser_was_comp = 0
    hold_ticks = hold_comp = hold_presser_was_comp = 0
    hold_both = hold_far = 0
    flight_both = 0
    pressers = {"vol": {}, "porteur": {}}
    for seed in range(n):
        random.seed(seed)
        players, bloc, place, _ = t._scene(Teamwork=99)
        holder = next(p for p in players if p.name == "H")
        defense, now, comp0 = DefensiveRoles(), 0.0, None
        for _ in range(30):  # phase 1 : H porteur jusqu'à la compensation du milieu défensif
            defense = t._update(players, bloc, defense=defense, now_s=now)
            comp0 = _comp_rb(defense)
            if comp0 is not None:
                break
            players = _move(players, defense, bloc, holder.position, now, static_unassigned=True)
            now += DT
        if comp0 is None:
            continue
        w = next(p for p in players if p.name == "W")
        direction = w.position - holder.position
        velocity = direction * (18.0 / direction.length())
        ball_pos = holder.position
        for _ in range(60):  # phase 2 : passe en vol vers W
            now += DT
            ball = BallState(position=ball_pos, velocity=velocity, receiver="W", last_pass_team="away")
            defense.update(players, ball, bloc, now)
            flight_ticks += 1
            flight_comp += _comp_rb(defense) is not None
            p_name = next((n_ for n_, a in defense.assignments.items() if a.role == PRESSEUR), None)
            pressers["vol"][p_name] = pressers["vol"].get(p_name, 0) + 1
            flight_presser_was_comp += p_name == comp0
            roles_w = {a.role for a in defense.assignments.values() if a.mate == "W"}
            flight_both += {PRESSEUR, "couverture"} <= roles_w
            players = _move(players, defense, bloc, holder.position, now, static_unassigned=True)
            ball_pos = ball_pos + velocity * DT
            velocity = velocity * (0.6 ** DT)
            if ball_pos.distance_to(next(p for p in players if p.name == "W").position) < 1.0:
                break
        for _ in range(10):  # phase 3 : W porteur 1 s, vers la place
            now += DT
            w = next(p for p in players if p.name == "W")
            defense.update(players, BallState(position=w.position, velocity=Vec2(0.0, 0.0), holder="W"), bloc, now)
            hold_ticks += 1
            hold_comp += _comp_rb(defense) is not None
            p_name = next((n_ for n_, a in defense.assignments.items() if a.role == PRESSEUR), None)
            pressers["porteur"][p_name] = pressers["porteur"].get(p_name, 0) + 1
            hold_presser_was_comp += p_name == comp0
            roles_w = {a.role for a in defense.assignments.values() if a.mate == "W"}
            hold_both += {PRESSEUR, "couverture"} <= roles_w
            rb = next(p for p in players if p.name == "RB")
            hold_far += w.position.distance_to(bloc.reference(rb, w.position, DEFENSE_PLACEE, now)) > 20.0
            players = _move(players, defense, bloc, w.position, now, winger_target=place, static_unassigned=True)
    print(f"V2 : {n} tirages (Teamwork 99 au milieu défensif)")
    print(f"  vol : {flight_ticks} ticks ; COMPENSATION (RB) {flight_comp / flight_ticks:.1%} ; "
          f"presseur = ancien compensateur {flight_presser_was_comp / flight_ticks:.1%} ; presseurs {pressers['vol']}")
    print(f"  porteur : {hold_ticks} ticks ; COMPENSATION (RB) {hold_comp / hold_ticks:.1%} ; "
          f"presseur = ancien compensateur {hold_presser_was_comp / hold_ticks:.1%} ; presseurs {pressers['porteur']}")
    print(f"  W pressé ET couvert : vol {flight_both / flight_ticks:.1%}, porteur {hold_both / hold_ticks:.1%} ; "
          f"W à plus de 20 m de la place (bloc) du latéral, porteur : {hold_far / hold_ticks:.1%}")


if __name__ == "__main__":
    {"v1": v1, "v2": v2}[sys.argv[1]]()
