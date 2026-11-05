"""Flux aléatoires par sous-système (ticket v2-realisme/01a, D-V13) : graines dérivées par sha256 d'une clé stable,
indépendance des flux entre eux et vis-à-vis du module `random`, reproductibilité d'un match à graine fixée."""

from __future__ import annotations

import hashlib
import random

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.flux import DECISION, PERCEPTION, seed_streams, stream_seed
from v2engine.match import simulate_match


def test_stream_seeds_come_from_sha256_of_a_stable_key() -> None:
    # valeurs figées : une dérivation par `hash()` (salée par processus) ou un changement de clé les casserait
    assert stream_seed(20260923, "perception") == 805051646593221841
    assert stream_seed(20260923, "decision") == 1562525141020014378
    expected = int.from_bytes(hashlib.sha256(b"20260923|perception").digest()[:8], "big")
    assert stream_seed(20260923, "perception") == expected


def test_an_extra_perception_draw_does_not_shift_the_decision_stream() -> None:
    seed_streams(7)
    reference = [DECISION.random() for _ in range(20)]
    seed_streams(7)
    PERCEPTION.random()  # tirage ajouté dans un autre sous-système
    PERCEPTION.gauss(0.0, 1.0)
    assert [DECISION.random() for _ in range(20)] == reference


def test_streams_and_the_random_module_do_not_shift_each_other() -> None:
    random.seed(3)
    seed_streams(7)
    global_ref, stream_ref = [random.random() for _ in range(10)], [PERCEPTION.random() for _ in range(10)]
    random.seed(3)
    seed_streams(7)
    DECISION.random()  # tirage de flux ajouté : le module `random` (tirages pas encore migrés, 01b) ne bouge pas
    assert [random.random() for _ in range(10)] == global_ref
    random.random()  # tirage du module ajouté : les flux ne bougent pas
    assert [PERCEPTION.random() for _ in range(10)] == stream_ref


def _trace_print(seed: int) -> str:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(seed)
    trace = simulate_match(clubs[4], clubs[5], duration_minutes=1.0, record_every=5)
    state = [(t.minute, [(p.name, p.position) for p in t.players], t.ball.position, t.ball.holder) for t in trace.ticks]
    return hashlib.sha256(repr((state, trace.decisions)).encode()).hexdigest()


def test_match_trace_is_reproducible_at_fixed_seed_and_changes_with_the_seed() -> None:
    first = _trace_print(20260923)
    assert _trace_print(20260923) == first
    assert _trace_print(20260924) != first
