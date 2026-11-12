"""Calibration hors ligne du ticket v2-collectif/35b : sur les vrais tirs du moteur, calcule pour une grille
(sigma, hauteur de visee) la part attendue de tirs cadres, a cote, au-dessus. Usage : python 35b-calib.py debut n sortie.json"""
import json, random, sys, itertools
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
import v2engine.match as match
import v2engine.shooting as sh

start, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
SIGMAS = [0.08, 0.10, 0.11, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24]
AIMS = [0.6, 0.8, 1.0, 1.22]
acc = {f"{s}|{a}": [0.0, 0.0, 0.0, 0.0, 0.0] for s in SIGMAS for a in AIMS}  # cadre non marque, a cote, au-dessus, devisse, n
real = match.classify_unscored

def wrapped(shooter, goal, keeper, opponents):
    chance = sh.shot_probability(shooter, goal, keeper, opponents)
    s0, a0 = sh.SHOT_ERROR_SIGMA_RAD, sh.SHOT_AIM_HEIGHT_M
    for s, a in itertools.product(SIGMAS, AIMS):
        sh.SHOT_ERROR_SIGMA_RAD, sh.SHOT_AIM_HEIGHT_M = s, a
        w, h = sh.on_target_axes(shooter, goal, opponents)
        on = max(w * h, chance)
        p_cad = (on - chance) / (1 - chance)
        ratio = sh.shot_error_sigma(shooter, goal, opponents) / s
        p_shank = sh.SHANK_SHARE * ratio ** 2
        over = (1 - h) / max(1e-9, (1 - w) + (1 - h))
        rest = (1 - p_cad) * (1 - p_shank)
        r = acc[f"{s}|{a}"]
        r[0] += p_cad; r[1] += rest * (1 - over); r[2] += rest * over; r[3] += (1 - p_cad) * p_shank; r[4] += 1
    sh.SHOT_ERROR_SIGMA_RAD, sh.SHOT_AIM_HEIGHT_M = s0, a0
    return real(shooter, goal, keeper, opponents)

match.classify_unscored = wrapped
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
shots = goals = 0
for i in range(start, start + n):
    random.seed(20260923 + i)
    t = match.simulate_match(clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)], duration_minutes=90.0,
                             tick_seconds=match.TICK_SECONDS)
    shots += len(t.shots); goals += sum(1 for e in t.shots if e.outcome == "but")
json.dump({"shots": shots, "goals": goals, "acc": acc}, open(out, "w"))
