"""Contrôle du 02c (même méthode qu'au 02a1) : réceptions « centre » relues sur la piste du ballon, graines 0 à 2 de
`scripts.measure_v2` (ou celles passées en argument) ; pour chacune, vérifie de façon indépendante (chute libre recalculée ici, sans `hauteur.py`) que
le ballon n'a pas touché le sol entre son lancement et le pas du contact. Usage, depuis la racine du dépôt :
PYTHONHASHSEED=0 uv run python .scratch/v2-hauteur-ballon/mesures/02c-controle-centres.py"""
import math
import random
import sys

from ligue1sim.clubs import load_clubs
from scripts.measure_v2 import AUDIT_SEED, CLUBS_PATH
from v2engine import match

G = 9.81
state = {"launch": None, "touched": False, "z_min": None}
rows = []
original = match._step_ball


def ground_in(z, vz, dt):
    """Instant d'impact (s) dans le pas, chute libre ; None sans impact."""
    if z <= 0.0 and vz <= 0.0:
        return None
    t = (vz + math.sqrt(vz * vz + 2.0 * G * max(0.0, z))) / G
    return t if t <= dt else None


def step(ball, dt, players, now_s=0.0, *args, **kwargs):
    z0, vz0, holder0 = ball.z, ball.vz, ball.holder
    receptions = args[6] if len(args) > 6 else kwargs.get("receptions")
    n0 = len(receptions) if receptions is not None else 0
    out = original(ball, dt, players, now_s, *args, **kwargs)
    if holder0 is None and z0 == 0.0 and vz0 > 0.0:  # ballon lancé au pas précédent
        state.update(launch=(now_s, vz0), touched=False)
    hit = ground_in(z0, vz0, dt) if holder0 is None else None
    if receptions is not None and len(receptions) > n0:
        ev = receptions[-1]
        if ev.origin == "centre":
            rows.append((now_s, state["launch"], state["touched"], z0, vz0, hit, ev.player, ev.intended))
    if hit is not None:
        state["touched"] = True
    return out


match._step_ball = step
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
total = 0
for k in (map(int, sys.argv[1:]) if sys.argv[1:] else range(3)):
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    before = len(rows)
    trace = match.simulate_match(home, away)
    centres = sum(1 for r in trace.receptions if r.origin == "centre")
    print(f"graine {k} : {centres} réceptions « centre » dans la trace, {len(rows) - before} relues")
for r in rows:
    now, launch, touched, z0, vz0, hit, who, intended = r
    since = now - launch[0] if launch else float("nan")
    flight = 2.0 * launch[1] / G if launch else float("nan")
    print(f"t={now:7.1f}s  {since:4.1f}s après la frappe (vol prévu {flight:4.2f}s)  z={z0:5.2f}m vz={vz0:+6.2f}  "
          f"sol touché avant : {touched}  impact dans le pas : {'%.3f' % hit if hit is not None else '-'}  "
          f"{who} {'visé' if intended else 'non visé'}")
ok = sum(1 for r in rows if not r[2])
print(f"\n{ok} sur {len(rows)} reçues avant le premier contact au sol (avant le pas du contact) ; "
      f"{len(rows)} « centre » au total")
