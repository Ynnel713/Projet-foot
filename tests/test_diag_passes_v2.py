"""Diagnostic des passes (ticket v2-realisme/28) : la courbe recopiée de l'écran donne les mêmes points que
`ui/src/utils/v2Spline.js`, et les crochets du diagnostic ne changent pas le match (lecture seule)."""

import hashlib
import random

import pytest

import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from scripts.diag_passes_v2 import RECORD_EVERY, catmull_rom, play
from scripts.measure_v2 import AUDIT_SEED, TICK_S

# Valeurs calculées par `catmullRom` de v2Spline.js (node, 19/11/2026)
_JS = {0.25: (0.852965422, -0.165174251), 0.5: (1.988837851, -0.017295434), 0.8: (3.334847102, 0.496786461)}


@pytest.mark.parametrize("f", sorted(_JS))
def test_courbe_identique_a_l_ecran(f):
    x, y = catmull_rom((-1.0, 3.0), (0.0, 0.0), (4.0, 1.0), (5.0, 7.0), f)
    assert x == pytest.approx(_JS[f][0], abs=1e-8) and y == pytest.approx(_JS[f][1], abs=1e-8)


def test_voisin_absent_comme_l_ecran():
    x, y = catmull_rom(None, (0.0, 0.0), (4.0, 1.0), (9.0, -2.0), 0.4)
    assert (x, y) == (pytest.approx(1.015033439, abs=1e-8), pytest.approx(0.410475253, abs=1e-8))


def _fingerprint(trace) -> str:
    h = hashlib.sha256()
    for p in trace.ball_track:
        h.update(f"{p.minute:.6f}{p.position.x:.6f}{p.position.y:.6f}{p.holder}".encode())
    h.update(f"{trace.home_goals}-{trace.away_goals}-{len(trace.events)}".encode())
    return h.hexdigest()


def test_le_diagnostic_ne_change_pas_le_match():
    minutes = 6.0
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED)
    plain = match.simulate_match(clubs[0], clubs[1], duration_minutes=minutes, tick_seconds=TICK_S,
                                 record_every=RECORD_EVERY)
    probed = play(0, minutes=minutes, keep_trace=True)
    assert _fingerprint(probed["trace"]) == _fingerprint(plain)
    count = probed["count"]
    assert count["passes (jeu)"] > 0
    assert count["passes réussies (jeu)"] <= count["passes (jeu)"]


def test_distance_du_defenseur_comme_le_moteur():
    """Ticket 29a : la distance du défenseur frôlé est celle que juge `match._contacts` (mouvement relatif)."""
    from scripts.diag_passes_v2 import _relative_closest
    from v2engine.geometry import Vec2
    from v2engine.movement import PlayerState

    defender = PlayerState(name="d", team="away", poste="DC", position=Vec2(10.0, 0.7), velocity=Vec2(3.0, 0.0),
                           pace=60, acceleration=60, stamina=60, home_target=Vec2(10.0, 0.7))
    start, end = Vec2(8.0, 0.0), Vec2(11.0, 0.0)
    hits = match._contacts(start, end, TICK_S, [defender], None, radius=5.0)
    distance, _ = _relative_closest(start, end, defender, TICK_S)
    assert distance == pytest.approx(hits[0][1], abs=1e-9)
