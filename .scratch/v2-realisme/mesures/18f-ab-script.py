"""Scènes A/B du ticket 18f : sens des attributs Passing, Composure, Dribbling, Vision, Decisions, avant (couloir de 2 m
sans cône) et après (cône 45° + portée de jambe). 400 scènes tirées : porteur pressé (adversaire à 1 à 2,5 m), trois
coéquipiers à 8-25 m, quatre adversaires de plus au hasard. Lecture seule du moteur ; rien n'est écrit dans le dépôt."""
import math, random, statistics as st

import v2engine.possession as P
from v2engine import decision, flux
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

NEW = P._lane_opponents


def old(start, end, opponents):
    path = end - start
    length = path.length()
    if length < 1e-9:
        return 0
    d = path * (1.0 / length)
    n = 0
    for o in opponents:
        r = o.position - start
        a = r.x * d.x + r.y * d.y
        if 0.0 < a < length and o.position.distance_to(start + d * a) <= P._LANE_WIDTH_M:
            n += 1
    return n


def pl(name, team, pos, **att):
    return PlayerState(name=name, team=team, poste="MC", position=pos, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=pos, attributes=att or None)


def scenes(n=400):
    rng = random.Random(20261112)
    out = []
    for _ in range(n):
        h = Vec2(rng.uniform(35, 70), rng.uniform(15, 53))
        a = rng.uniform(0, 2 * math.pi); d = rng.uniform(1.0, 2.5)
        opp = [Vec2(h.x + d * math.cos(a), h.y + d * math.sin(a))]
        mates = []
        for _ in range(3):
            b = rng.uniform(0, 2 * math.pi); r = rng.uniform(8, 25)
            mates.append(Vec2(h.x + r * math.cos(b), h.y + r * math.sin(b)))
        for _ in range(4):
            opp.append(Vec2(h.x + rng.uniform(-20, 20), h.y + rng.uniform(-15, 15)))
        out.append((h, mates, opp))
    return out


def build(scene, **att):
    h, mates, opp = scene
    holder = pl("H", "home", h, **att)
    return holder, [pl(f"M{i}", "home", m) for i, m in enumerate(mates)], [pl(f"O{i}", "away", o) for i, o in enumerate(opp)]


def best_pass(scene, **att):
    holder, mates, opp = build(scene, **att)
    return max(P.pass_success_probability(holder, m, opp) for m in mates)


def pass_share(scene_list, **att):
    """Part des décisions de passe (choose_action, graine fixe), porteur à `att`."""
    flux.reseed(1) if hasattr(flux, "reseed") else None
    rng_state = random.getstate(); random.seed(7)
    for s in (flux.DECISION, flux.PERCEPTION, flux.DUEL):
        s.seed(7)
    k = 0
    for scene in scene_list:
        holder, mates, opp = build(scene, **att)
        goal = Vec2(105.0, 34.0)
        a = decision.choose_action(holder, [holder] + mates + opp, goal, None)
        k += a.kind == "pass"
    random.setstate(rng_state)
    return k / len(scene_list)


S = scenes()
for label, rule in (("avant", old), ("après", NEW)):
    P._lane_opponents = rule
    print(f"== {label}")
    for att in ("Passing", "Composure"):
        hi = st.fmean(best_pass(s, **{att: 99}) for s in S); lo = st.fmean(best_pass(s, **{att: 11}) for s in S)
        print(f"  meilleure passe, {att} 99 / 11 : {hi:.3f} / {lo:.3f}  (écart {hi - lo:+.3f})")
    for att in ("Passing", "Dribbling", "Vision", "Decisions"):
        hi = pass_share(S, **{att: 99}); lo = pass_share(S, **{att: 11})
        print(f"  part de passes choisies, {att} 99 / 11 : {hi:.3f} / {lo:.3f}  (écart {hi - lo:+.3f})")
P._lane_opponents = NEW
