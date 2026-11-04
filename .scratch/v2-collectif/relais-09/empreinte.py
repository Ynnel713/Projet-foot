"""Empreinte de trace : 10 minutes de match, graine d'audit, sha256 du repr de la trace (hors dépôt)."""
import hashlib
import random

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match

clubs = load_clubs(CLUBS_PATH, "Ligue 1")
random.seed(20260923)
trace = match.simulate_match(clubs[0], clubs[1], duration_minutes=10.0)
print(hashlib.sha256(repr(trace).encode("utf-8")).hexdigest()[:16])
