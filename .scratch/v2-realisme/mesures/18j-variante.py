"""Essai hors moteur du ticket 18j : portée du défenseur qui lit la passe (`ball.readers`). Enveloppe de
`match._ball_contacts` : les lecteurs touchent le ballon à `REACH` m au lieu de `CONTROL_RADIUS_M` (rien de commité dans
le moteur). Usage : uv run python .scratch/v2-realisme/mesures/18j-variante.py REACH N DEBUT JSON"""
import sys

sys.path.insert(0, ".")
import v2engine.match as match
from scripts.measure_v2 import main

REACH = float(sys.argv[1])
real_contacts = match._contacts


def _ball_contacts(start, end, dt, players, ball):
    special = {}
    if ball.receiver is not None:
        special[ball.receiver] = match.RECEIVER_REACH_M
    for name in ball.readers:
        special.setdefault(name, REACH)
    if not special:
        return real_contacts(start, end, dt, players, ball.released_by)
    hits = real_contacts(start, end, dt, [p for p in players if p.name not in special], ball.released_by)
    for p in players:
        if p.name in special:
            hits += real_contacts(start, end, dt, [p], ball.released_by, special[p.name])
    hits.sort(key=lambda h: (h[0], h[1]))
    return hits


match._ball_contacts = _ball_contacts
main([sys.argv[2], "--debut", sys.argv[3], "--json", sys.argv[4]])
