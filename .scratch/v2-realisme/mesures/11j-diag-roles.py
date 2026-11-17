"""Diagnostic hors moteur (ticket v2-realisme/11j, refait d'après celui du 11g) : contacts francs entre coéquipiers sur
30 min de jeu (graine d'audit 20260923), par paire de rôles, et part de ceux dont les deux cibles sont à moins de 1 m
(cibles d'intention, et cibles réellement données à l'évitement quand le moteur les écarte).

Usage (depuis la racine du dépôt) : PYTHONHASHSEED=0 PYTHONPATH=.:src .venv/bin/python .scratch/v2-realisme/mesures/11j-diag-roles.py"""

from __future__ import annotations

import collections
import random

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
from v2engine.duel import CONTACT_MIN_CLOSING_MPS

AUDIT_SEED = 20260923
intentions_seen: dict = {}
placed_seen: dict = {}
pairs: collections.Counter = collections.Counter()
gaps: collections.Counter = collections.Counter()  # écart entre les deux cibles, par tranche
own: collections.Counter = collections.Counter()  # au moins un des deux à moins de 2 m de sa propre cible
moving: collections.Counter = collections.Counter()  # au moins une cible mobile (pressing, soutien)
near_raw = near_placed = total = 0
real_step, real_share = match._step_player, match.contact_share


def step_player(player, *args, **kwargs):
    moved = real_step(player, *args, **kwargs)
    intentions = args[5] if len(args) > 5 else kwargs.get("intentions")
    if intentions is not None:
        intentions_seen.clear()
        intentions_seen.update(intentions)
    placed = kwargs.get("placed")
    if placed is not None:
        placed_seen.clear()
        placed_seen.update(placed)
    return moved


def contact_share(a, b, *args, **kwargs):
    global near_raw, near_placed, total
    share = real_share(a, b, *args, **kwargs)
    if a.team != b.team:
        return share
    delta = b.position - a.position
    if delta.length() <= 0.0:
        return share
    n = delta.normalized()
    rel = a.velocity - b.velocity
    if rel.x * n.x + rel.y * n.y <= CONTACT_MIN_CLOSING_MPS:
        return share
    ia, ib = intentions_seen.get(a.name), intentions_seen.get(b.name)
    if ia is None or ib is None:
        return share
    total += 1
    pairs[tuple(sorted((ia.role, ib.role)))] += 1
    gap = ia.target.distance_to(ib.target)
    near_raw += gap < 1.0
    gaps[next(f"< {b} m" for b in (1, 2, 3, 5, 10, 1000) if gap < b)] += 1
    own["oui"] += min(a.position.distance_to(ia.target), b.position.distance_to(ib.target)) < 2.0
    moving["oui"] += ia.target_velocity.length() > 0.0 or ib.target_velocity.length() > 0.0
    ta, tb = placed_seen.get(a.name, ia.target), placed_seen.get(b.name, ib.target)
    near_placed += ta.distance_to(tb) < 1.0
    return share


match._step_player, match.contact_share = step_player, contact_share
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
random.seed(AUDIT_SEED)
match.simulate_match(clubs[0], clubs[1], duration_minutes=30.0)
print("total", total)
for pair, count in pairs.most_common():
    print(count, pair)
print("cibles d'intention à moins de 1 m", near_raw)
print("cibles données à l'évitement à moins de 1 m", near_placed)
print("écart des cibles d'intention :", dict(sorted(gaps.items(), key=lambda kv: float(kv[0].split()[1]))))
print("l'un des deux à moins de 2 m de sa cible", own["oui"])
print("au moins une cible mobile", moving["oui"])
