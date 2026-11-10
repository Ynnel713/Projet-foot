"""Contrôle de la chance de tir évaluée contre la résolution physique (ticket v2-realisme/05e).

La décision juge un tir avec `shooting.occasion_quality` : chance de but hors contre x chance de ne pas être contré.
Depuis le 05e, la chance hors contre est calculée avec les lois de la résolution (`shooting.physical_shot_chance`) ;
la chance de contre aussi (`shooting.physical_block_probability`).

Méthode, à refaire après tout ticket qui change la résolution du tir (gardien, cadrage, contre, vitesse du tir) ; la
formule `physical_shot_chance` doit suivre la résolution, sans table de correction :
  1. `uv run python -m scripts.shot_calibration scenes 2000` : grille de 20 positions de tir (tireur et gardien
     neutres, sans défenseur), chance évaluée contre taux de buts de la vraie trajectoire, intervalle de Wilson.
  2. `uv run python -m scripts.shot_calibration relever 120 --debut 2000 --processus 7 --json tirs.json` : tirs de vrais
     matchs (graine de `scripts/measure_v2.run` ; environ 5 min par match et par processus quand 7 tournent ensemble, soit 120 matchs en 1 h 30 environ).
  3. `uv run python -m scripts.shot_calibration verifier tirs.json` : par tranche de chance évaluée, de distance et
     d'angle, chance moyenne contre taux observé ; contre prévu contre contres observés.

Validation des tirs (ticket v2-realisme/05g) : `uv run python -m scripts.shot_calibration rapport tirs.json` (issues par
distance et par angle, cadrage par note, contres selon le cône, arrêts selon la vitesse, sortie des contres et corners).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
from v2engine import shooting
from v2engine.geometry import in_penalty_area

from scripts.measure_v2 import AUDIT_SEED

Z_95 = 1.96
CHANCE_BINS = (0.0, 0.03, 0.06, 0.1, 0.2, 0.35, 0.5, 1.01)  # bornes de l'xG du 06c
DISTANCE_BINS = (0.0, 8.0, 12.0, 16.0, 20.0, 25.0, 30.1)
ANGLE_BINS_DEG = (0.0, 15.0, 25.0, 40.0, 180.1)  # angle sous lequel le tireur voit le but entre les poteaux
NOTE_BINS = (0, 40, 55, 70, 100)  # tranches de note de tir (Finishing dans la surface, Long Shots dehors)
CONE_BINS = (0, 1, 2, 3, 99)  # défenseurs dans le cône de tir au départ
SPEED_BINS_MPS = (0.0, 20.0, 24.0, 27.0, 40.0)  # vitesse du ballon quand il passe au gardien
BLOCK_EXIT_S = 5.0  # délai dans lequel une remise en jeu compte comme sortie directe d'un tir contré
SAVED = ("capté", "repoussé", "claqué")
OUTCOMES = ("but", *SAVED, "à côté", "au-dessus", "dévissé", "contré")


def _one_match(i: int) -> list[dict]:
    """Tirs (hors penaltys) du match `i`, graine de `measure_v2.run`, dans l'ordre de la trace."""
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    seen: list[dict] = []
    original = match.occasion_quality

    def spy(holder, goal, keeper, opponents):  # appelée une fois par tir tracé (`record` de `match._step_ball`)
        low, high, _ = shooting._goal_angle(holder.position, goal)
        seen.append({
            "hors contre": shooting.physical_shot_chance(holder, goal, keeper, opponents),
            "contre prévu": shooting.physical_block_probability(holder, goal, opponents),
            "distance": holder.position.distance_to(goal), "angle": math.degrees(high - low),
            "note": shooting.shooting_note(holder), "surface": in_penalty_area(holder.team, holder.position),
            "dans le cône": len(shooting._blockers(holder, goal, opponents)),
            "pression": shooting.shot_pressure(holder, goal, opponents),
        })
        return original(holder, goal, keeper, opponents)

    match.occasion_quality = spy
    try:
        random.seed(AUDIT_SEED + i)
        home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
        trace = match.simulate_match(home, away)
    finally:
        match.occasion_quality = original
    shots = [s for s in trace.shots if s.origin != "penalty"]
    assert len(shots) == len(seen), (len(shots), len(seen))
    team_of = {p.name: "home" for p in pick_best_formation(home).players}
    team_of.update({p.name: "away" for p in pick_best_formation(away).players})
    corners = sum(r.kind == "corner" for r in trace.restarts)

    def exit_after(shot) -> str:
        """Sortie directe d'un tir contré (ticket 05g, réserve A2 du 05d) : remise en jeu dans les `BLOCK_EXIT_S` après
        le tir, dernier toucheur défenseur ; sinon « en jeu »."""
        for r in trace.restarts:
            if shot.minute <= r.minute <= shot.minute + BLOCK_EXIT_S / 60.0 and team_of.get(r.last_toucher) not in (
                    None, shot.team):
                return r.kind
        return "en jeu"

    return [{**info, "match": i, "évaluée": s.quality, "xg": s.xg, "issue": s.outcome, "origine": s.origin,
             "vitesse au gardien": s.keeper_speed_mps, "écart au gardien": s.keeper_gap_m,
             "temps au gardien": s.keeper_time_s, "sortie du contre": s.block_exit_deg,
             "après le contre": exit_after(s) if s.outcome == "contré" else None, "corners du match": corners}
            for s, info in zip(shots, seen)]


def collect(n: int, start: int, processes: int) -> list[dict]:
    with ProcessPoolExecutor(max_workers=processes) as pool:
        return [shot for shots in pool.map(_one_match, range(start, start + n)) for shot in shots]


SCENE_DISTANCES_M = (6.0, 11.0, 16.0, 20.0, 25.0)  # du point de tir à la ligne de but
SCENE_OFFSETS_M = (0.0, 5.0, 10.0, 15.0)  # écart latéral au centre du but


def scene_rate(x_from_line: float, offset: float, n: int, seed: int = 0,
               defenders: tuple[tuple[float, float, float, float], ...] = ()) -> tuple[float, float]:
    """Scène contrôlée : tireur et gardien neutres, gardien à `KEEPER_REFERENCE_M` de sa ligne sur l'axe du tir ; `n`
    tirs résolus par la vraie trajectoire (`match._step_ball`). Rend (chance évaluée, taux de buts). `defenders` :
    défenseurs (distance à la ligne, écart à l'axe du but, vitesse en x, vitesse en y), voir `block_scene`."""
    evaluated, rates = _scene(x_from_line, offset, n, seed, defenders)
    return evaluated[0], rates["but"]


def block_scene(x_from_line: float, offset: float, n: int, seed: int,
                defenders: tuple[tuple[float, float, float, float], ...]) -> tuple[float, float]:
    """Même scène avec des défenseurs : (chance de contre évaluée, part de tirs contrés observée)."""
    evaluated, rates = _scene(x_from_line, offset, n, seed, defenders)
    return evaluated[1], rates["contré"]


def on_target_scene(x_from_line: float, offset: float, n: int, seed: int, note: int) -> float:
    """Scène de référence du 05g : part de tirs cadrés (but ou arrêt) d'un tireur de note `note` (Finishing dans la
    surface, Long Shots dehors), sans défenseur, gardien neutre bien placé."""
    _, rates = _scene(x_from_line, offset, n, seed, (), {"Finishing": note, "Long Shots": note})
    return rates["cadré"]


def _scene(x_from_line, offset, n, seed, defenders, attributes=None):
    from collections import Counter

    from v2engine.ball_state import BallState
    from v2engine.decision import Action
    from v2engine.flux import seed_streams
    from v2engine.geometry import PITCH_LENGTH_M, Vec2
    from v2engine.movement import PlayerState

    def make(name, team, poste, at, velocity=Vec2(0.0, 0.0), attrs=None):
        return PlayerState(name=name, team=team, poste=poste, position=at, velocity=velocity, pace=60,
                           acceleration=60, stamina=60, home_target=at, attributes=attrs)

    goal = Vec2(PITCH_LENGTH_M, match.GOAL_CENTER_Y)
    at = Vec2(PITCH_LENGTH_M - x_from_line, match.GOAL_CENTER_Y + offset)
    keeper_at = goal + (at - goal).normalized() * shooting.KEEPER_REFERENCE_M

    def players():
        rivals = [make(f"D{i}", "away", "DC", Vec2(PITCH_LENGTH_M - d, match.GOAL_CENTER_Y + y), Vec2(vx, vy))
                  for i, (d, y, vx, vy) in enumerate(defenders)]
        return make("Buteur", "home", "BU", at, attrs=attributes), make("Gardien", "away", "GK", keeper_at), rivals

    saved = match.should_attempt_tackle, match.choose_action
    match.should_attempt_tackle = lambda *a: False
    match.choose_action = lambda *a: Action("shot", 1.0)
    random.seed(seed)
    seed_streams(seed)
    outcomes = Counter()
    dt = match.TICK_SECONDS
    try:
        for _ in range(n):
            shooter, keeper, rivals = players()
            ball = BallState(position=at, velocity=Vec2(0.0, 0.0), holder="Buteur")
            shots: list = []
            scored = None
            for tick in range(60):
                for r in rivals:  # les défenseurs gardent leur vitesse pendant le vol
                    r.position = r.position + r.velocity * dt
                scored = match._step_ball(ball, dt, [shooter, keeper, *rivals], tick * dt, shots=shots)
                if scored is not None or (shots and ball.shot_flight is None):
                    break
            outcomes["but" if scored == "home" else shots[0].outcome] += 1
        shooter, keeper, rivals = players()
        evaluated = (shooting.physical_shot_chance(shooter, goal, keeper, [keeper, *rivals]) if not rivals else
                     shooting.occasion_quality(shooter, goal, keeper, [keeper, *rivals]),
                     shooting.physical_block_probability(shooter, goal, [keeper, *rivals]))
    finally:
        match.should_attempt_tackle, match.choose_action = saved
    rates = {k: outcomes[k] / n for k in ("but", "contré")}
    rates["cadré"] = sum(outcomes[k] for k in ("but", *SAVED)) / n
    return evaluated, rates


def scene_grid(n: int) -> list[dict]:
    out = []
    for d in SCENE_DISTANCES_M:
        for off in SCENE_OFFSETS_M:
            evaluated, rate = scene_rate(d, off, n)
            low, high = wilson(round(rate * n), n)
            out.append({"distance": d, "écart": off, "évaluée": evaluated, "observé": rate, "ic95": (low, high)})
    return out


def wilson(goals: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = goals / n
    centre, half = p + Z_95 ** 2 / (2 * n), Z_95 * math.sqrt(p * (1 - p) / n + Z_95 ** 2 / (4 * n * n))
    return (centre - half) / (1 + Z_95 ** 2 / n), (centre + half) / (1 + Z_95 ** 2 / n)


def table(shots: list[dict], key: str, bins: tuple[float, ...], chance: str = "évaluée") -> list[dict]:
    """Par tranche de `key` : effectif, chance moyenne, taux de buts observé et son intervalle à 95 %, calibrée si
    l'intervalle contient la chance moyenne."""
    out = []
    for lo, hi in zip(bins, bins[1:]):
        band = [s for s in shots if lo <= s[key] < hi]
        if not band:
            continue
        goals = sum(s["issue"] == "but" for s in band)
        mean = sum(s[chance] for s in band) / len(band)
        low, high = wilson(goals, len(band))
        out.append({"tranche": f"[{lo:g} ; {hi:g}[", "tirs": len(band), "chance": mean, "buts": goals / len(band),
                    "ic95": (low, high), "calibrée": low <= mean <= high})
    return out


def _band(value: float, bins: tuple) -> str | None:
    for lo, hi in zip(bins, bins[1:]):
        if lo <= value < hi:
            return f"[{lo:g} ; {hi:g}["
    return None


def _shares(group: list[dict]) -> dict:
    """Effectif et part de chaque issue."""
    return {"tirs": len(group), **{o: sum(s["issue"] == o for s in group) / len(group) for o in OUTCOMES}}


def validation_report(shots: list[dict]) -> dict:
    """Validation des tirs (ticket v2-realisme/05g) : issues par distance et par angle, cadrage par note de tir, contres
    selon les défenseurs dans le cône, arrêts selon la vitesse au gardien, sortie des contres et corners (réserve A2 du
    05d), chance hors contre et contre prévu par distance (réserve A1 du 05e). Aucun réglage."""
    matches = len({s["match"] for s in shots})
    out: dict = {"matchs": matches, "tirs par match": len(shots) / matches,
                 "buts par match": sum(s["issue"] == "but" for s in shots) / matches}
    for name, key, bins in (("issues par distance (m)", "distance", DISTANCE_BINS),
                            ("issues par angle (°)", "angle", ANGLE_BINS_DEG)):
        out[name] = {band: _shares([s for s in shots if _band(s[key], bins) == band])
                     for band in dict.fromkeys(_band(s[key], bins) for s in shots) if band is not None}
        out[name] = dict(sorted(out[name].items(), key=lambda kv: float(kv[0][1:].split(" ;")[0])))
    flown = [s for s in shots if s["issue"] not in ("contré", "dévissé")]
    for kind, surface in (("Finishing (surface)", True), ("Long Shots (dehors)", False)):
        rows = {}
        for lo, hi in zip(NOTE_BINS, NOTE_BINS[1:]):
            group = [s for s in flown if s["surface"] == surface and lo <= s["note"] < hi]
            if group:
                on = sum(s["issue"] == "but" or s["issue"] in SAVED for s in group)
                rows[f"[{lo} ; {hi}["] = {"tirs non contrés": len(group), "cadrés": on / len(group),
                                          "ic95": wilson(on, len(group))}
        out[f"cadrage par note, {kind}"] = rows
    rows = {}
    for lo, hi in zip(CONE_BINS, CONE_BINS[1:]):
        group = [s for s in shots if lo <= s["dans le cône"] < hi]
        if group:
            blocked = sum(s["issue"] == "contré" for s in group)
            rows[f"{lo}" if hi == lo + 1 else f"{lo} et plus"] = {
                "tirs": len(group), "contrés": blocked / len(group), "ic95": wilson(blocked, len(group))}
    out["contres par défenseurs dans le cône"] = rows
    judged = [s for s in shots if s["vitesse au gardien"] is not None and (s["issue"] == "but" or s["issue"] in SAVED)]
    rows = {}
    for lo, hi in zip(SPEED_BINS_MPS, SPEED_BINS_MPS[1:]):
        group = [s for s in judged if lo <= s["vitesse au gardien"] < hi]
        if group:
            saved = sum(s["issue"] in SAVED for s in group)
            rows[f"[{lo:g} ; {hi:g}[ m/s"] = {"tirs cadrés jugés": len(group), "arrêtés": saved / len(group),
                                               "ic95": wilson(saved, len(group))}
    out["arrêts par vitesse au gardien"] = rows
    blocked = [s for s in shots if s["issue"] == "contré"]
    corners = {s["match"]: s["corners du match"] for s in shots}
    out["contres : suite directe (part)"] = {k: sum(s["après le contre"] == k for s in blocked) / max(1, len(blocked))
                                             for k in ("corner", "touche", "sortie de but", "en jeu")}
    out["corners par match"] = sum(corners.values()) / matches
    out["corners par match : après un contre"] = sum(s["après le contre"] == "corner" for s in blocked) / matches
    out["corners par match : après un tir claqué"] = sum(s["issue"] == "claqué" for s in shots) / matches
    rows = {}
    for lo, hi in zip(DISTANCE_BINS, DISTANCE_BINS[1:]):
        group = [s for s in shots if lo <= s["distance"] < hi]
        unblocked = [s for s in group if s["issue"] != "contré"]
        judged_here = [s for s in unblocked if s["écart au gardien"] is not None]
        if group and unblocked:
            rows[f"[{lo:g} ; {hi:g}["] = {
                "contre prévu": sum(s["contre prévu"] for s in group) / len(group),
                "contrés": sum(s["issue"] == "contré" for s in group) / len(group),
                "chance hors contre": sum(s["hors contre"] for s in unblocked) / len(unblocked),
                "buts des non contrés": sum(s["issue"] == "but" for s in unblocked) / len(unblocked),
                "écart au gardien moyen (m)": (sum(s["écart au gardien"] for s in judged_here) / len(judged_here)
                                               if judged_here else None),
            }
    out["chance et contre par distance (réserve A1 du 05e)"] = rows
    return out


def report(shots: list[dict]) -> dict:
    total = len(shots)
    return {
        "tirs": total, "matchs": len({s["match"] for s in shots}),
        "buts": sum(s["issue"] == "but" for s in shots) / total, "chance évaluée moyenne": sum(s["évaluée"] for s in shots) / total,
        "par chance évaluée": table(shots, "évaluée", CHANCE_BINS),
        "par distance (m)": table(shots, "distance", DISTANCE_BINS),
        "par angle (°)": table(shots, "angle", ANGLE_BINS_DEG),
        "contre, par chance de contre prévue": [
            {**row, "contrés": row.pop("buts")} for row in table(
                [{**s, "issue": "but" if s["issue"] == "contré" else "-"} for s in shots], "contre prévu",
                (0.0, 0.05, 0.15, 0.3, 0.5, 1.01), chance="contre prévu")],
    }


def _print(rep: dict) -> None:
    print(f"{rep['tirs']} tirs sur {rep['matchs']} matchs ; buts {rep['buts']:.3f}, chance évaluée {rep['chance évaluée moyenne']:.3f}")
    for name, rows in rep.items():
        if isinstance(rows, list):
            print(name)
            for r in rows:
                observed = r.get("buts", r.get("contrés"))
                print(f"  {r['tranche']:>14} {r['tirs']:6d} tirs  chance {r['chance']:.3f}  observé {observed:.3f} "
                      f"[{r['ic95'][0]:.3f} ; {r['ic95'][1]:.3f}]  {'calibrée' if r['calibrée'] else 'ÉCART'}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("relever")
    r.add_argument("matchs", type=int)
    r.add_argument("--debut", type=int, default=2000)
    r.add_argument("--processus", type=int, default=7)
    r.add_argument("--json", required=True)
    sub.add_parser("verifier").add_argument("fichier")
    sub.add_parser("rapport").add_argument("fichier")
    sub.add_parser("scenes").add_argument("tirs", type=int)
    args = parser.parse_args(argv)
    if args.cmd == "scenes":
        for r in scene_grid(args.tirs):
            ok = r["ic95"][0] <= r["évaluée"] <= r["ic95"][1]
            print(f"  {r['distance']:4.0f} m, écart {r['écart']:4.0f} m  chance {r['évaluée']:.3f}  observé "
                  f"{r['observé']:.3f} [{r['ic95'][0]:.3f} ; {r['ic95'][1]:.3f}]  {'calibrée' if ok else 'ÉCART'}")
        return
    if args.cmd == "relever":
        started = time.perf_counter()
        shots = collect(args.matchs, args.debut, args.processus)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(shots, f, ensure_ascii=False)
        print(f"{len(shots)} tirs, {(time.perf_counter() - started) / 60:.1f} min", file=sys.stderr)
        return
    with open(args.fichier, encoding="utf-8") as f:
        shots = json.load(f)
    if args.cmd == "rapport":
        print(json.dumps(validation_report(shots), ensure_ascii=False, indent=1))
        return
    _print(report(shots))


if __name__ == "__main__":
    main()
