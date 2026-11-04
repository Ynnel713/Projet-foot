"""Diagnostic hors dépôt, ticket v2-collectif/09 : trous laissés dans la ligne défensive après une perte de balle.

Après chaque perte (le porteur change d'équipe), pendant WINDOW_S, pour chaque défenseur (groupe DEFENDER) de
l'équipe qui vient de perdre le ballon : sa place dans le bloc sans ballon (`Bloc.reference`, défense placée) est
un « trou » si le défenseur en est à plus de OWNER_AWAY_M et qu'aucun coéquipier de champ n'est à moins de
FILLED_M de cette place. Trou « exploité » : un adversaire à moins de FILLED_M de la place pendant qu'elle est
vide. Tir adverse dans les 15 s après la perte : occasion de contre.

Usage : PYTHONPATH=<copie du moteur> uv run python diag_trous.py [n_matchs]"""

from __future__ import annotations

import random
import sys
from collections import defaultdict

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import DEFENDER, position_group
from ligue1sim.season import CLUBS_PATH

import v2engine.bloc as bloc_mod
import v2engine.match as match
from v2engine.situation import DEFENSE_PLACEE

AUDIT_SEED = 20260923
WINDOW_S = 10.0
OWNER_AWAY_M = 10.0
FILLED_M = 5.0
SHOT_WINDOW_S = 15.0
FREE_M = 3.0  # attaquant libre : aucun défenseur à moins de 3 m


def run(n: int) -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    captured = {}
    real_update = bloc_mod.Bloc.update

    def update(self, players, ball, now_s=0.0):
        captured["bloc"] = self
        return real_update(self, players, ball, now_s)
    bloc_mod.Bloc.update = update
    real_shot = match.attempt_shot
    state = {"now": 0.0}
    shots = []

    def attempt_shot(shooter, *a, **k):
        shots.append((state["now"], shooter.team))
        return real_shot(shooter, *a, **k)
    match.attempt_shot = attempt_shot

    totals = defaultdict(float)
    for k in range(n):
        random.seed(AUDIT_SEED + k)
        home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
        defenders = {p.name for c in (home, away) for p in pick_best_formation(c).players
                     if position_group(p.poste) == DEFENDER}
        last_team = [None]
        losses = []  # [équipe qui perd, instant, trous vus, trous exploités, tirs adverses]
        shots.clear()

        def observer(now_s, players, ball, scored):
            state["now"] = now_s
            holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
            if holder is not None:
                if last_team[0] is not None and holder.team != last_team[0]:
                    losses.append({"team": last_team[0], "t": now_s, "holes": set(), "exploited": set(),
                                   "hole_ticks": 0, "owners_away": 0})
                last_team[0] = holder.team
            bloc = captured.get("bloc")
            if bloc is None:
                return
            for loss in losses:
                if not 0.0 <= now_s - loss["t"] <= WINDOW_S:
                    continue
                team = loss["team"]
                mates = [p for p in players if p.team == team and p.poste != "GK"]
                foes = [p for p in players if p.team != team and p.poste != "GK"]
                for d in mates:
                    if d.name not in defenders:
                        continue
                    place = bloc.reference(d, ball.position, DEFENSE_PLACEE, now_s)
                    if d.position.distance_to(place) <= OWNER_AWAY_M:
                        continue
                    if now_s == loss["t"]:
                        loss["owners_away"] += 1
                    if any(m.position.distance_to(place) < FILLED_M for m in mates if m is not d):
                        continue
                    own = 0.0 if team == "home" else 105.0
                    # trou qui compte : dans sa moitié, entre le ballon et son but
                    if abs(place.x - own) > 52.5 or abs(place.x - own) >= abs(ball.position.x - own):
                        continue
                    loss["holes"].add(d.name)
                    loss["hole_ticks"] += 1
                    if any(f.position.distance_to(place) < FILLED_M
                           and min(m.position.distance_to(f.position) for m in mates) > FREE_M for f in foes):
                        loss["exploited"].add(d.name)

        match.simulate_match(home, away, observer=observer)
        for loss in losses:
            other_shot = any(team != loss["team"] and 0.0 <= t - loss["t"] <= SHOT_WINDOW_S for t, team in shots)
            totals["pertes"] += 1
            totals["defenseur_loin_a_la_perte"] += loss["owners_away"] > 0
            totals["pertes_avec_trou"] += bool(loss["holes"])
            totals["pertes_trou_exploite"] += bool(loss["exploited"])
            totals["secondes_de_trou"] += loss["hole_ticks"] * match.TICK_SECONDS
            totals["tir_15s"] += other_shot
            totals["tir_15s_si_trou_exploite"] += other_shot and bool(loss["exploited"])
            totals["tir_15s_sans_trou"] += other_shot and not loss["holes"]
            totals["pertes_sans_trou"] += not loss["holes"]
        print(f"match {k + 1}/{n} : {len(losses)} pertes", file=sys.stderr)

    p = totals["pertes"]
    print(f"{n} matchs, {p / n:.0f} pertes par match")
    print(f"défenseur à plus de {OWNER_AWAY_M:.0f} m de sa place à la perte : {totals['defenseur_loin_a_la_perte'] / p:.1%}")
    print(f"pertes avec un trou dans la ligne (10 s) : {totals['pertes_avec_trou'] / p:.1%}")
    print(f"pertes avec un trou exploité : {totals['pertes_trou_exploite'] / p:.1%}")
    print(f"durée de trou par perte (défenseur-secondes) : {totals['secondes_de_trou'] / p:.2f} s")
    print(f"tir adverse en 15 s : {totals['tir_15s'] / p:.2%} des pertes, {totals['tir_15s'] / n:.1f} par match")
    ex = totals["pertes_trou_exploite"]
    if ex:
        print(f"  après un trou exploité : {totals['tir_15s_si_trou_exploite'] / ex:.2%}")
    if totals["pertes_sans_trou"]:
        print(f"  sans trou : {totals['tir_15s_sans_trou'] / totals['pertes_sans_trou']:.2%}")
    nx = p - ex
    print(f"  sans trou exploité : {(totals['tir_15s'] - totals['tir_15s_si_trou_exploite']) / nx:.2%}")


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
