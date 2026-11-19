"""Diagnostic des passes et des interceptions, comparé au réel (ticket v2-realisme/28). Lecture seule : le moteur n'est
pas modifié, les crochets ne consomment aucun tirage (l'état du flux `PASSE` est copié, jamais avancé).

Pour chaque match (graines du banc, `scripts/measure_v2.run`) :
1. passes réussies (le premier joueur qui prend le ballon après la passe est de l'équipe du passeur ; ballon mort ou
   pris par l'adversaire : ratée), dans le jeu (hors remises en jeu), au sol et en l'air ;
2. pertes de balle par équipe (journal `PERTE`, par cause) et passes sorties du terrain ;
3. passes frôlées : un adversaire de champ à moins de 1 m, ou de 1 à 2 m, du ballon pendant la passe (distance entre le
   segment parcouru par le ballon pendant un pas et la position du joueur à la fin du pas), sans qu'il soit le premier
   à le prendre ; lecteur de la passe ou non (`ball.readers`) ; « en situation de jouer le ballon » s'il atteint, depuis
   sa position au départ de la passe, le point le plus proche de la trajectoire avant le ballon (`arrival_time_s`) ;
4. passes ratées au tirage (`possession.pass_aim`) que le receveur visé prend quand même, puis que son équipe garde
   3 s (`KEEP_S`) ;
5. écart moteur / écran sur les passes frôlées : distance minimale du ballon au joueur telle qu'affichée (piste du
   ballon et joueurs à 2 images par seconde, courbe de Catmull-Rom centripète de `ui/src/utils/v2Spline.js`, recopiée
   ici) contre la distance du moteur ; écart significatif au-delà de `DISPLAY_GAP_M`.

Constantes validées par le propriétaire le 19/11/2026 (ticket 28).

Usage :
  uv run python -m scripts.diag_passes_v2 50 --processus 4 --json diag28.json
  uv run python -m scripts.diag_passes_v2 --relire diag28.json   (rapport refait depuis la série, sans rejouer)

Défenseur frôlé (comptes et quantiles) : par passe, l'adversaire le plus proche du ballon. Règles candidates du 29b :
tous les adversaires non lecteurs de la passe (réserve A1 de l'expert au 29a).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
import v2engine.possession as possession
from v2engine.condition import effective_rating
from v2engine.defense import arrival_time_s
from v2engine.flux import PASSE
from v2engine.geometry import Vec2
from v2engine.restart import AERIEN
from v2engine.trace import PERTE

from scripts.measure_v2 import AUDIT_SEED, TICK_S

NEAR_M = (1.0, 2.0)  # tranches des passes frôlées
WATCH_M = 3.0  # adversaires suivis pour l'écran : au-delà, l'affichage ne peut pas les ramener sous 2 m
KEEP_S = 3.0  # fenêtre « l'équipe garde le ballon » (même fenêtre que le porteur bousculé, 11i)
DISPLAY_GAP_M = 0.5  # écart d'affichage significatif
# extrémités de la passe (départ, arrivée) : en deçà, l'adversaire presse le passeur ou marque le receveur (mesure
# ajoutée en cours de ticket, à faire valider par le propriétaire)
ENDS_M = 2.0
# Ticket 29a (tranches et seuils candidats validés par le propriétaire le 19/11/2026) : tranches de distance du
# défenseur frôlé (sous `CONTROL_RADIUS_M`, 0,41 m, il aurait dû toucher : contrôle interdit ou déséquilibre), règles
# candidates du 29b comptées sans être appliquées
BANDS_M = ((0.0, 0.41), (0.41, 0.6), (0.6, 0.8), (0.8, 1.0))
REACH_CANDIDATES_M = (0.8, 1.0)
REACTION_CANDIDATES_S = (0.2, 0.25, 0.3)
FACING_MAX_DEG = 90.0
RECORD_EVERY = 5  # cadence des images envoyées à l'écran (`api/routers/v2._RECORD_EVERY`)
SUBSTEPS = 5  # échantillons par pas du moteur pour les distances continues
Z_95 = 1.96


# --- Courbe de l'écran (copie de ui/src/utils/v2Spline.js) ------------------------------------------------------------
_ALPHA, _EPS = 0.5, 1e-6


def _knot(p, q):
    return max(_EPS, math.hypot(q[0] - p[0], q[1] - p[1]) ** _ALPHA)


def catmull_rom(p0, p1, p2, p3, f):
    if p0 is None:
        p0 = p1
    if p3 is None:
        p3 = p2
    if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) < _EPS:
        return p1
    t0 = 0.0
    t1 = t0 + _knot(p0, p1)
    t2 = t1 + _knot(p1, p2)
    t3 = t2 + _knot(p2, p3)
    t = t1 + (t2 - t1) * f

    def lerp(a, b, ta, tb):
        w = 0.0 if tb - ta < _EPS else (t - ta) / (tb - ta)
        return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)

    a1, a2, a3 = lerp(p0, p1, t0, t1), lerp(p1, p2, t1, t2), lerp(p2, p3, t2, t3)
    return lerp(lerp(a1, a2, t0, t2), lerp(a2, a3, t1, t3), t1, t2)


def _crosses(m1, m2, half):
    return half is not None and m1 < half <= m2


def _ball_cut(u, v, half):
    return u.holder != v.holder or u.dead != v.dead or (u.dead and v.dead) or _crosses(u.minute, v.minute, half)


def display_ball(track, i, f, half):
    """`ballFromTrack` entre les points `i` et `i + 1` de la piste, à la fraction `f`."""
    p1 = track[i]
    p2 = track[min(len(track) - 1, i + 1)]
    xy = lambda p: (p.position.x, p.position.y)  # noqa: E731
    if p2 is p1:
        return xy(p1)
    if _ball_cut(p1, p2, half):
        if p1.dead or p2.dead or _crosses(p1.minute, p2.minute, half):
            return xy(p1)
        return (p1.position.x + (p2.position.x - p1.position.x) * f, p1.position.y + (p2.position.y - p1.position.y) * f)
    p0 = xy(track[i - 1]) if i > 0 and not _ball_cut(track[i - 1], p1, half) else None
    p3 = xy(track[i + 2]) if i + 2 < len(track) and not _ball_cut(p2, track[i + 2], half) else None
    return catmull_rom(p0, xy(p1), xy(p2), p3, f)


def display_player(frames, k, name, half):
    """`playersBetween` pour un joueur, à l'instant du pas `k` du moteur (fraction de pas comprise : `k` réel)."""
    j = min(int(k // RECORD_EVERY), len(frames) - 1)
    f = (k - j * RECORD_EVERY) / RECORD_EVERY
    last = len(frames) - 1
    a, b = frames[j], frames[min(last, j + 1)]
    cut = lambda u, v: u.ball.dead != v.ball.dead or _crosses(u.minute, v.minute, half)  # noqa: E731
    pos = lambda fr: next((p.position.x, p.position.y) for p in fr.players if p.name == name)  # noqa: E731
    pa, pb = pos(a), pos(b)
    if b is a or cut(a, b):
        return (pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f)
    prev = pos(frames[j - 1]) if j > 0 and not cut(frames[j - 1], a) else None
    nxt = pos(frames[j + 2]) if j + 2 <= last and not cut(b, frames[j + 2]) else None
    return catmull_rom(prev, pa, pb, nxt, f)


# --- Géométrie -------------------------------------------------------------------------------------------------------
def _relative_closest(a: Vec2, b: Vec2, player, dt: float) -> tuple[float, float]:
    """Distance minimale du ballon (de `a` à `b` pendant le pas) au joueur, en mouvement relatif comme
    `match._contacts` : position de début de pas estimée par sa vitesse. Rend la distance et la fraction du pas."""
    r0 = a - (player.position - player.velocity * dt)
    r1 = b - player.position
    seg = r1 - r0
    length2 = seg.x * seg.x + seg.y * seg.y
    u = 0.0 if length2 < 1e-12 else min(1.0, max(0.0, -(r0.x * seg.x + r0.y * seg.y) / length2))
    return (r0 + seg * u).length(), u


def _segment_closest(a: Vec2, b: Vec2, p: Vec2) -> tuple[float, float]:
    """Distance de `p` au segment [a, b] et fraction du point le plus proche."""
    ab = b - a
    length2 = ab.x * ab.x + ab.y * ab.y
    u = 0.0 if length2 < 1e-12 else max(0.0, min(1.0, ((p.x - a.x) * ab.x + (p.y - a.y) * ab.y) / length2))
    closest = a + ab * u
    return closest.distance_to(p), u


# --- Un match --------------------------------------------------------------------------------------------------------
def play(k: int, minutes: float = 90.0, keep_trace: bool = False) -> dict:
    """Joue le match `k` du banc et rend ses comptes et ses cas suspects (`keep_trace` : la trace aussi, pour les tests)."""
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    count: Counter = Counter()
    pending: list = []  # passes lancées, en attente de leur premier pas
    state = {"pass": None, "restart": False, "k": -1, "prev_ball": None}
    passes: list[dict] = []
    keep_checks: list[dict] = []  # passes ratées récupérées : l'équipe garde-t-elle 3 s ?
    holders: list[tuple[int, str | None, str | None]] = []  # (pas, porteur, équipe)

    real_aim, real_velocity, real_restart = possession.pass_aim, match.pass_velocity, match._play_restart

    def pass_aim(passer, target, opponents=(), backheel=False, one_touch=False, lofted=False):
        probe = random.Random()
        probe.setstate(PASSE.getstate())  # même premier tirage que `pass_aim`, sans avancer le flux du match
        missed = probe.random() >= possession.pass_accuracy_probability(passer, target, opponents, backheel, one_touch,
                                                                         lofted)
        pending.append({"missed": missed})
        return real_aim(passer, target, opponents, backheel, one_touch, lofted)

    def pass_velocity(passer, target, opponents=(), *args, **kwargs):
        velocity = real_velocity(passer, target, opponents, *args, **kwargs)
        info = pending.pop() if pending else {"missed": False}
        info.update(passer=passer.name, team=passer.team, target=target.name, restart=state["restart"],
                    start=[replace(o) for o in opponents if o.poste != "GK"], opened=None)
        state["new"] = info
        return velocity

    def play_restart(*args, **kwargs):
        state["restart"] = True
        try:
            return real_restart(*args, **kwargs)
        finally:
            state["restart"] = False

    def close(current, outcome_team, outcome_name, k_end, end_pos):
        current["end"] = k_end
        current["end_pos"] = end_pos
        current["won"] = outcome_team == current["team"]
        current["taker"] = outcome_name
        current["taker_team"] = outcome_team
        passes.append(current)

    def observer(now_s, players, ball, scoring_team):
        state["k"] += 1
        k_now = state["k"]
        by_name = {p.name: p for p in players}
        holder = by_name.get(ball.holder) if ball.holder else None
        holders.append((k_now, ball.holder, holder.team if holder else None))
        current = state["pass"]
        prev_ball = state["prev_ball"]
        new = state.pop("new", None)
        if current is not None:
            ended = None
            relayer = by_name.get(ball.released_by) if ball.released_by else None
            if holder is not None:
                ended = (holder.team, holder.name)
            elif new is not None and new["passer"] != current["passer"]:  # remise de première : le passeur l'a eue
                ended = (new["team"], new["passer"])
            elif ball.shot_in_flight and relayer is not None and relayer.name != current["passer"]:  # tir de première
                ended = (relayer.team, relayer.name)
            elif ball.restart is not None or scoring_team is not None or new is not None or ball.shot_in_flight:
                ended = (None, None)
            if ball.last_toucher and ball.last_toucher != current["passer"]:
                current["touched"].add(ball.last_toucher)
            if current["opened"] is not None and prev_ball is not None:
                start_s = current["opened"]
                for p in players:
                    if p.team == current["team"] or p.poste == "GK":
                        continue
                    # distance du moteur (`match._contacts`) : mouvement relatif, position de début de pas
                    # estimée par la vitesse (ticket 29a) ; la distance au point de fin de pas reste celle de l'écran
                    d, u = _relative_closest(prev_ball, ball.position, p, TICK_S)
                    if d < current["near"].get(p.name, (math.inf,))[0]:
                        reach_t = (k_now - 1 + u) * TICK_S - start_s
                        closest = prev_ball + (ball.position - prev_ball) * u
                        to_ball = closest - p.position
                        angle = (math.degrees(math.acos(max(-1.0, min(1.0, (p.facing.x * to_ball.x + p.facing.y
                                                                           * to_ball.y) / to_ball.length()))))
                                 if to_ball.length() > 1e-9 else 0.0)
                        current["near"][p.name] = (d, k_now - 1 + u, reach_t, closest, ball.mode == AERIEN,
                                                   p.name in ball.readers, p.velocity.length(), angle,
                                                   effective_rating(p, "Anticipation"))
                    world = _segment_closest(prev_ball, ball.position, p.position)[0]  # celle de l'écran (ticket 28)
                    if world < current["world"].get(p.name, (math.inf, False))[0]:
                        current["world"][p.name] = (world, ball.mode == AERIEN)
            if ended is not None:
                close(current, ended[0], ended[1], k_now, ball.position)
                state["pass"] = current = None
        if new is not None:
            new["opened"] = k_now * TICK_S
            new["k0"] = k_now
            new["near"] = {}
            new["world"] = {}
            new["touched"] = set()
            new["origin"] = prev_ball if prev_ball is not None else ball.position
            new["lofted"] = ball.mode == AERIEN
            state["pass"] = new
        state["prev_ball"] = ball.position

    possession.pass_aim, match.pass_velocity, match._play_restart = pass_aim, pass_velocity, play_restart
    try:
        trace = match.simulate_match(home, away, duration_minutes=minutes, tick_seconds=TICK_S, record_every=RECORD_EVERY,
                                     observer=observer)
    finally:
        possession.pass_aim, match.pass_velocity, match._play_restart = real_aim, real_velocity, real_restart
    if state["pass"] is not None:
        close(state["pass"], None, None, state["k"], state["prev_ball"])
    if len(trace.ball_track) != state["k"] + 1 or len(trace.ticks) != state["k"] // RECORD_EVERY + 1:
        raise RuntimeError(f"piste ({len(trace.ball_track)}), images ({len(trace.ticks)}) et pas ({state['k'] + 1}) "
                           "décalés")

    half = trace.second_half_start_minute
    frames, track = trace.ticks, trace.ball_track
    by_step = {k: team for k, _, team in holders}
    suspects = []
    cases = []  # passes au sol frôlées à moins de 1 m par un non-lecteur (ticket 29a)
    for ps in passes:
        kind = "remises" if ps["restart"] else "jeu"
        air = "en l'air" if ps["lofted"] else "au sol"
        count[f"passes ({kind})"] += 1
        count[f"passes ({kind}, {air})"] += 1
        count[f"passes réussies ({kind})"] += ps["won"]
        count[f"passes réussies ({kind}, {air})"] += ps["won"]
        if ps["taker_team"] is None:
            count[f"passes sans preneur, ballon mort ou tir ({kind})"] += 1
        elif not ps["won"]:
            count[f"passes prises par l'adversaire ({kind})"] += 1
        if ps["restart"]:
            continue
        # passes ratées au tirage
        if ps["missed"]:
            count["passes ratées au tirage"] += 1
            count["ratées : receveur visé prend le ballon"] += ps["taker"] == ps["target"]
            count["ratées : son équipe prend le ballon"] += ps["won"]
            if ps["won"]:
                horizon = ps["end"] + round(KEEP_S / TICK_S)
                lost = any(by_step.get(s) not in (None, ps["team"]) for s in range(ps["end"], horizon + 1))
                count["ratées : son équipe garde 3 s"] += not lost
        else:
            count["passes précises au tirage"] += 1
            count["précises : son équipe prend le ballon"] += ps["won"]
        # passes frôlées : l'adversaire le plus proche qui n'a pas pris le ballon
        near = [(name, v) for name, v in ps["near"].items() if name != ps["taker"] and name not in ps["touched"]]
        count["passes touchées par un adversaire qui ne la prend pas"] += any(
            n in ps["touched"] for n in ps["near"] if n != ps["taker"])
        if not near:
            continue
        # règles candidates du 29b sur tous les défenseurs non lecteurs frôlés de la passe (réserve A1 de l'expert
        # au 29a) : une passe compte touchable dès qu'un d'eux remplit la règle, par partie de la passe
        for reach in REACH_CANDIDATES_M:
            for react in REACTION_CANDIDATES_S:
                for facing in (False, True):
                    parts = {_part(ps, v[3]) for _, v in near
                             if not v[4] and not v[5] and v[0] < reach and v[2] >= react
                             and (not facing or v[7] < FACING_MAX_DEG)}
                    tag = _rule_tag(reach, react, facing)
                    count[f"{tag} : passes"] += bool(parts)
                    for part in parts:
                        count[f"{tag} : {part}"] += 1
        name, (d, k_at, reach_t, closest, aerial, reader, speed, angle, anticipation) = min(
            near, key=lambda item: item[1][0])
        band = "< 1 m" if d < NEAR_M[0] else "1 à 2 m" if d < NEAR_M[1] else None
        if band is not None:
            where = "en l'air" if aerial else "au sol"
            # où sur la passe : presseur du passeur (départ), marqueur du receveur (arrivée) ou sur le trajet
            part = _part(ps, closest)
            count[f"frôlées {band}, {where}, {part}"] += 1
            snapshot = next(o for o in ps["start"] if o.name == name)
            in_time = arrival_time_s(snapshot, closest) <= reach_t
            count[f"frôlées {band}"] += 1
            count[f"frôlées {band}, {where}"] += 1
            if not aerial:
                count[f"frôlées {band}, au sol, lecteur"] += reader
                count[f"frôlées {band}, au sol, en situation de jouer le ballon"] += in_time
                count[f"frôlées {band}, au sol, passe réussie quand même"] += ps["won"]
                if band == "< 1 m" and not reader:  # défenseur frôlé non lecteur (ticket 29a)
                    cases.append({"partie": part, "d": round(d, 3), "t": round(reach_t, 3), "v": round(speed, 2),
                                  "angle": round(angle, 1), "anticipation": anticipation})
                if part == "trajet":
                    count[f"frôlées {band}, au sol, trajet, lecteur"] += reader
                    count[f"frôlées {band}, au sol, trajet, en situation de jouer le ballon"] += in_time
                    count[f"frôlées {band}, au sol, trajet, passe réussie quand même"] += ps["won"]
        # écart d'affichage : tout adversaire suivi à moins de WATCH_M, sur la durée de la passe
        for name2, (d2, aerial2) in ps["world"].items():
            if name2 == ps["taker"] or name2 in ps["touched"] or d2 >= WATCH_M:
                continue
            shown = math.inf
            for step in range(ps["k0"], ps["end"]):
                for s in range(SUBSTEPS):
                    f = s / SUBSTEPS
                    bx, by = display_ball(track, step, f, half)
                    px, py = display_player(frames, step + f, name2, half)
                    shown = min(shown, math.hypot(bx - px, by - py))
            suspects.append({"moteur": d2, "écran": shown, "sol": not aerial2})
    for event in trace.events:
        if event.kind == PERTE:
            count["pertes (journal)"] += 1
            count[f"pertes (journal) : {event.detail}"] += 1
    shown_close = [s for s in suspects if s["sol"]]
    count["écran : cas suivis (au sol, < 3 m au moteur)"] += len(shown_close)
    for s in shown_close:
        engine_band = "< 1 m" if s["moteur"] < 1.0 else "1 à 2 m" if s["moteur"] < 2.0 else "2 à 3 m"
        count[f"écran : moteur {engine_band}"] += 1
        count[f"écran : moteur {engine_band}, écart > {DISPLAY_GAP_M} m"] += abs(s["écran"] - s["moteur"]) > DISPLAY_GAP_M
        count[f"écran : moteur {engine_band}, affiché < 1 m"] += s["écran"] < 1.0
    result = {"k": k, "count": dict(count), "home": trace.home, "away": trace.away,
              "ecarts": [round(s["écran"] - s["moteur"], 3) for s in shown_close if s["moteur"] < 2.0],
              "frolees": cases}
    if keep_trace:
        result["trace"] = trace
    return result


def _summary(values):
    n = len(values)
    mean = statistics.fmean(values)
    half = Z_95 * (statistics.stdev(values) if n > 1 else 0.0) / math.sqrt(n)
    return mean, half


def _part(ps: dict, closest: Vec2) -> str:
    """Où sur la passe : presseur du passeur (départ), marqueur du receveur (arrivée) ou sur le trajet."""
    if closest.distance_to(ps["origin"]) < ENDS_M:
        return "départ"
    return "arrivée" if closest.distance_to(ps["end_pos"]) < ENDS_M else "trajet"


def _rule_tag(reach: float, react: float, facing: bool) -> str:
    orientation = f"cap < {FACING_MAX_DEG:.0f}°" if facing else "toute orientation"
    return f"règle {reach:.1f} m, {react:.2f} s, {orientation}"


def _quantiles(values, qs=(0.1, 0.25, 0.5, 0.75, 0.9)):
    values = sorted(values)
    return [values[min(len(values) - 1, int(q * len(values)))] for q in qs] if values else []


def _frolees_report(results: list[dict]) -> list[str]:
    """Ticket 29a : défenseurs non lecteurs frôlés à moins de 1 m par une passe au sol (distance du moteur), par
    partie de la passe et par tranche ; règles candidates du 29b comptées sans être appliquées."""
    n = len(results)
    cases = [c for r in results for c in r.get("frolees", [])]
    lines = [f"Défenseurs non lecteurs frôlés à moins de 1 m, passes au sol ({len(cases)} cas, {n} matchs) :"]
    for part in ("départ", "trajet", "arrivée"):
        sub = [c for c in cases if c["partie"] == part]
        if not sub:
            continue
        lines.append(f"  {part} : {len(sub) / n:.2f} par match")
        for low, high in ((0.0, 1.0),) + BANDS_M:  # toutes distances, puis par tranche (critère 3 du 29a)
            band = [c for c in sub if low <= c["d"] < high]
            lines.append(f"    {low:.2f}-{high:.2f} m : {len(band) / n:6.2f} par match")
            for key, label in (("t", "temps depuis le départ (s)"), ("v", "vitesse (m/s)"),
                               ("angle", "angle cap / ballon (°)"), ("anticipation", "Anticipation")):
                q = _quantiles([c[key] for c in band])
                if q:
                    lines.append(f"      {label:28s} 10/25/50/75/90 % : " + " / ".join(f"{v:.2f}" for v in q))
    lines.append("Règles candidates du 29b, tous les défenseurs non lecteurs de la passe (passes touchables par match ;"
                 " une passe compte dans chaque partie où un défenseur remplit la règle) :")
    for reach in REACH_CANDIDATES_M:
        for react in REACTION_CANDIDATES_S:
            for facing in (False, True):
                tag = _rule_tag(reach, react, facing)
                cells = []
                for part in ("passes", "départ", "trajet", "arrivée"):
                    mean, half = _summary([r["count"].get(f"{tag} : {part}", 0) for r in results])
                    cells.append(f"{part} {mean:6.2f} ± {half:.2f}")
                lines.append(f"  {tag:40s} " + " | ".join(cells))
    return lines


def report(results: list[dict]) -> str:
    keys = sorted({key for r in results for key in r["count"]})
    lines = [f"{len(results)} matchs (graines du banc {results[0]['k']} à {results[-1]['k']}), par match (les deux équipes) :"]
    for key in keys:
        mean, half = _summary([r["count"].get(key, 0) for r in results])
        lines.append(f"  {key:60s} {mean:9.2f}  ± {half:.2f}")

    def rate(num, den):
        values = [r["count"].get(num, 0) / r["count"][den] for r in results if r["count"].get(den)]
        mean, half = _summary(values)
        return f"{100 * mean:5.1f} % ± {100 * half:.1f}"

    lines.append("Taux (moyenne des taux match par match, IC 95 %) :")
    for num, den in (("passes réussies (jeu)", "passes (jeu)"),
                     ("passes réussies (jeu, au sol)", "passes (jeu, au sol)"),
                     ("passes réussies (jeu, en l'air)", "passes (jeu, en l'air)"),
                     ("passes réussies (remises)", "passes (remises)"),
                     ("passes ratées au tirage", "passes (jeu)"),
                     ("ratées : receveur visé prend le ballon", "passes ratées au tirage"),
                     ("ratées : son équipe prend le ballon", "passes ratées au tirage"),
                     ("ratées : son équipe garde 3 s", "passes ratées au tirage"),
                     ("précises : son équipe prend le ballon", "passes précises au tirage"),
                     ("frôlées < 1 m", "passes (jeu)"),
                     ("frôlées 1 à 2 m", "passes (jeu)"),
                     ("frôlées < 1 m, au sol, trajet", "passes (jeu)"),
                     ("frôlées 1 à 2 m, au sol, trajet", "passes (jeu)"),
                     ("frôlées < 1 m, au sol, trajet, passe réussie quand même", "frôlées < 1 m, au sol, trajet")):
        if any(r["count"].get(den) for r in results):
            lines.append(f"  {num} / {den} : {rate(num, den)}")
    lines.extend(_frolees_report(results))
    gaps = [g for r in results for g in r["ecarts"]]
    if gaps:
        gaps.sort()
        q = lambda p: gaps[min(len(gaps) - 1, int(p * len(gaps)))]  # noqa: E731
        lines.append(f"Écart écran - moteur, passes au sol frôlées à moins de 2 m ({len(gaps)} cas) : "
                     f"médiane {q(0.5):+.2f} m, 5 % {q(0.05):+.2f} m, 95 % {q(0.95):+.2f} m, "
                     f"au-delà de {DISPLAY_GAP_M} m : {100 * sum(abs(g) > DISPLAY_GAP_M for g in gaps) / len(gaps):.1f} %")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("matchs", type=int, nargs="?", default=0)
    parser.add_argument("--debut", type=int, default=0)
    parser.add_argument("--processus", type=int, default=1)
    parser.add_argument("--json")
    parser.add_argument("--relire", help="refaire le rapport depuis la sortie --json d'une série, sans rejouer")
    args = parser.parse_args(argv)
    if args.relire:
        with open(args.relire, encoding="utf-8") as handle:
            print(report(json.load(handle)))
        return 0
    seeds = list(range(args.debut, args.debut + args.matchs))
    if args.processus > 1:
        with ProcessPoolExecutor(args.processus) as pool:
            results = list(pool.map(play, seeds))
    else:
        results = [play(k) for k in seeds]
    text = report(results)
    print(text)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
