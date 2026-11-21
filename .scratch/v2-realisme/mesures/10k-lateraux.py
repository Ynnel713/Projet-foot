"""Sonde du ticket v2-realisme/10k, lecture seule : où sont les latéraux (LB/RB) de l'équipe sans ballon quand l'adversaire
porte le ballon dans l'axe du tiers médian, quel rôle ils tiennent, va-et-vient des suiveurs du pressing d'équipe.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/10k-lateraux.py N [pas] [sortie.json]
(avant : PYTHONPATH vers un worktree de l'état a8cecf5)."""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.bloc as bloc_module
import v2engine.defense as defense_module
import v2engine.match as match
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

AUDIT_SEED = 20260923
AXIS = PITCH_WIDTH_M / 2.0
CENTRAL_Y_M = 10.0          # porteur à moins de 10 m de l'axe
MID_X = (PITCH_LENGTH_M / 3.0, 2.0 * PITCH_LENGTH_M / 3.0)  # tiers médian
WIDE_Y_M = 12.0             # adversaire « côté » : à plus de 12 m de l'axe, du côté du latéral
FREE_M = 10.0               # libre : aucun défenseur à moins de 10 m
FB = ("LB", "RB")


def run(k: int, tick_s: float) -> dict:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    stats = defaultdict(list)
    roles = Counter()
    real = defense_module.DefensiveRoles.update
    follow_state = {}

    def update(self, players, ball, bloc, now_s, situations=None, memory=None):
        real(self, players, ball, bloc, now_s, situations, memory)
        current = {a.mate: n for n, a in self.assignments.items() if a.role == "marquage"
                   and any(self.trigger_until.get(t, 0.0) > now_s for t in ("home", "away"))}
        for rec, marker in current.items():
            old = follow_state.get(rec)
            if old is not None and old[0] != marker:
                roles["suivi/changements"] += 1
                if old[1] == marker and now_s - old[2] <= 1.0:
                    roles["suivi/va_et_vient"] += 1
                follow_state[rec] = (marker, old[0], now_s)
            elif old is None:
                follow_state[rec] = (marker, None, -9.0)
        for rec in [r for r in follow_state if r not in current]:
            del follow_state[rec]
        if ball.holder is None or bloc is None or not situations:
            return
        by = {p.name: p for p in players}
        h = by.get(ball.holder)
        if h is None or h.poste == "GK":
            return
        if abs(h.position.y - AXIS) > CENTRAL_Y_M or not (MID_X[0] <= h.position.x <= MID_X[1]):
            return
        team = "away" if h.team == "home" else "home"
        situation = situations.get(team)
        if situation not in bloc_module._WITHOUT_BALL:
            return
        defenders = [p for p in players if p.team == team and p.poste != "GK"]
        for p in defenders:
            if p.poste not in FB:
                continue
            side = 1.0 if p.home_target.y > AXIS else -1.0
            lat = (p.position.y - AXIS) * side          # >0 : de son côté ; distance à l'axe
            ref = (bloc.reference(p, ball.position, situation, now_s).y - AXIS) * side
            a = self.assignments.get(p.name)
            role = a.role if a is not None else "bloc"
            roles[role] += 1
            stats["lat_" + role].append(lat)
            stats["lat"].append(lat)
            stats["ref"].append(ref)
            stats["ecart_ref"].append(ref - lat)        # >0 : plus axial que sa place de bloc
            if a is not None and a.mate in by:
                stats["mate_lat_" + role].append((by[a.mate].position.y - AXIS) * side)
            if role == "marquage" and a.mate in by:
                m = by[a.mate]
                goal = defense_module.own_goal(team)
                path = "suivi" if self.trigger_until.get(team, 0.0) > now_s else "danger25"
                roles["marquage/" + path] += 1
                if abs(m.position.y - AXIS) < CENTRAL_Y_M:
                    roles["marquage/" + path + "/receveur_central"] += 1
                roles["marque/" + m.poste] += 1
                dc_free = [d for d in defenders if d.poste == "DC" and d.name not in self.assignments]
                roles["marquage/dc_libre" if dc_free else "marquage/dc_tous_occupes"] += 1
            wingers = [o for o in players if o.team == h.team and o.poste != "GK"
                       and (o.position.y - AXIS) * side >= WIDE_Y_M]
            free = [o for o in wingers if min(d.position.distance_to(o.position) for d in defenders) > FREE_M]
            stats["ailier_cote"].append(1.0 if wingers else 0.0)
            if wingers:
                w = max(wingers, key=lambda o: (o.position.y - AXIS) * side)
                stats["ailier_axe"].append((w.position.y - AXIS) * side)
                stats["ecart_lat_ailier"].append(p.position.distance_to(w.position))
                stats["ecart_lat_ailier_y"].append((w.position.y - p.position.y) * side)
            stats["ailier_libre"].append(1.0 if free else 0.0)
            stats["libre_" + role].append(1.0 if free else 0.0)
        for p in defenders:
            if p.poste == "DC":
                stats["dc_lat"].append(abs(p.position.y - AXIS))

    defense_module.DefensiveRoles.update = update
    try:
        trace = match.simulate_match(home, away, tick_seconds=tick_s)
    finally:
        defense_module.DefensiveRoles.update = real
    kinds = Counter(e.kind for e in trace.events)
    glob = {"buts": trace.home_goals + trace.away_goals, "tirs": len(trace.shots), "fautes": len(trace.fouls),
            "hors-jeu": len(trace.offsides), "passes": kinds.get("passe", 0), "pertes": kinds.get("perte", 0),
            "evenements": len(trace.events)}
    glob.update({"evt:" + k: c for k, c in kinds.items()})
    return {"stats": dict(stats), "roles": dict(roles), "glob": glob,
            "empreinte": [trace.home_goals, trace.away_goals, len(trace.events), len(trace.shots)]}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tick_s = float(sys.argv[2]) if len(sys.argv) > 2 else match.TICK_SECONDS
    stats, roles, glob, prints = defaultdict(list), Counter(), Counter(), []
    with ProcessPoolExecutor() as ex:
        for res in ex.map(run, range(n), [tick_s] * n):
            for key, vals in res["stats"].items():
                stats[key].extend(vals)
            roles.update(res["roles"])
            glob.update(res["glob"])
            prints.append(res["empreinte"])
    def mean(v):
        return sum(v) / len(v) if v else float("nan")
    def pct(v, q):
        s = sorted(v); return s[int(q * (len(s) - 1))] if s else float("nan")
    total = sum(c for r, c in roles.items() if "/" not in r)
    print(f"{n} matchs, pas {tick_s} s, {total} ticks-latéral (porteur adverse dans l'axe, tiers médian)")
    print(f"distance du latéral à l'axe : moyenne {mean(stats['lat']):.1f} m, p10 {pct(stats['lat'], .1):.1f}, "
          f"médiane {pct(stats['lat'], .5):.1f}, p90 {pct(stats['lat'], .9):.1f}")
    print(f"place de bloc (référence) : moyenne {mean(stats['ref']):.1f} m ; écart réf - réel moyen "
          f"{mean(stats['ecart_ref']):.1f} m")
    print(f"part du temps à moins de 8 m de l'axe : {mean([1.0 if x < 8 else 0.0 for x in stats['lat']]):.0%}")
    print(f"centraux : distance à l'axe moyenne {mean(stats['dc_lat']):.1f} m")
    print(f"adversaire large de son côté : {mean(stats['ailier_cote']):.0%} ; libre (>10 m de tout défenseur) : "
          f"{mean(stats['ailier_libre']):.0%}")
    print(f"ailier le plus large : {mean(stats['ailier_axe']):.1f} m de l'axe ; écart latéral-ailier "
          f"{mean(stats['ecart_lat_ailier']):.1f} m (en largeur {mean(stats['ecart_lat_ailier_y']):.1f} m, "
          f"p90 {pct(stats['ecart_lat_ailier_y'], .9):.1f})")
    for role, c in sorted(roles.items()):
        if "/" in role:
            print(f"  {role:28s} {c}")
    for role, c in roles.most_common():
        if "/" in role:
            continue
        print(f"  {role:13s} {c / total:5.0%}  axe moyen {mean(stats['lat_' + role]):5.1f} m  "
              f"cible/marqué à {mean(stats.get('mate_lat_' + role, [])):5.1f} m de l'axe  "
              f"ailier libre {mean(stats['libre_' + role]):.0%}")
    print("par match :", {k: round(v / n, 2) for k, v in sorted(glob.items())})
    print("empreintes :", prints)
    with open(sys.argv[3] if len(sys.argv) > 3 else "/dev/null", "w") as f:
        json.dump({"roles": roles, "n": n, "glob": glob, "empreintes": prints,
                   "moyennes": {k: (sum(v) / len(v) if v else None) for k, v in stats.items()},
                   "sous8": sum(1 for x in stats["lat"] if x < 8) / max(1, len(stats["lat"]))}, f, indent=1)


if __name__ == "__main__":
    main()
