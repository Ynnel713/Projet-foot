"""Ticket v2-realisme/04f, mesure en lecture seule (moteur avec le profil de touche du 04f, sans interception) : en
conduite, ballon éloigné du pied du porteur (plus de `CONTROL_RADIUS_M`), adversaires que le ballon frôle à moins de
`CONTROL_RADIUS_M` pendant le pas (`match._contacts`, mouvement relatif), hors adversaires écartés (tacle raté,
déséquilibre, hors-jeu) ; « hors duel » : adversaire à au moins `TACKLE_RADIUS_M` du porteur. Un épisode par porteur et par touche (période `TOUCH_PERIOD_S`). Comparé, par tranche de gêne
(bornes du 04c), aux tirages de perte de conduite du 04a (`dribble_lost`) : intervalles, pertes tirées.
Usage : uv run python .scratch/v2-realisme/mesures/04f-diag-script.py N DEBUT > sortie.json"""
import json
import random
import sys
from collections import Counter

sys.path.insert(0, ".")
import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.possession import pressure

AUDIT_SEED = 20260923
BINS = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9)
count = Counter()
state = {"prev": None, "seen": set()}
real_lost = match.dribble_lost


def band(g):
    lo = [b for b in BINS if g >= b][-1]
    return f"gêne {lo}"


def dribble_lost(holder, opponents, duration_s=match.DECISION_INTERVAL_S):
    lost = real_lost(holder, opponents, duration_s)
    if duration_s == match.DECISION_INTERVAL_S:
        b = band(pressure(holder, opponents))
        count[f"{b} : intervalles"] += 1
        count[f"{b} : pertes tirées"] += lost
    return lost


match.dribble_lost = dribble_lost


def observer(now_s, players, ball, scoring):
    holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
    if holder is None or ball.dribble is None or ball.receiving:
        state["prev"] = None
        return
    prev = state["prev"]
    state["prev"] = (holder.name, ball.position)
    if prev is None or prev[0] != holder.name:
        return
    count["ticks de conduite"] += 1
    lead = ball.position.distance_to(holder.position)
    if lead <= match.CONTROL_RADIUS_M + 1e-6:
        return
    count["ticks ballon loin du pied"] += 1
    rivals = [p for p in players if p.team != holder.team
              and ball.tackle_ban_until_s.get(p.name, 0.0) <= now_s and ball.unsettled_until_s.get(p.name, 0.0) <= now_s
              and ball.offside_out_until.get(p.name, 0.0) <= now_s]
    hits = match._contacts(prev[1], ball.position, match.TICK_SECONDS, rivals)
    if not hits:
        return
    touch = (holder.name, int((now_s - ball.carry_start_s) / match.TOUCH_PERIOD_S), round(ball.carry_start_s, 1))
    for _, _, rival in hits:  # distance porteur - adversaire au contact, chaque contact (sans dédoublonnage)
        count[f"contacts, adversaire à {min(int(rival.position.distance_to(holder.position) * 2) / 2, 3.0)} m du porteur"] += 1
    if touch in state["seen"]:
        return
    state["seen"].add(touch)
    b = band(pressure(holder, [p for p in players if p.team != holder.team]))
    count[f"{b} : touches interceptables"] += 1
    count["touches interceptables"] += 1
    count["interceptables, gardien"] += hits[0][2].poste == "GK"
    far = [h for h in hits if h[2].position.distance_to(holder.position) >= match.TACKLE_RADIUS_M]
    if far:
        count[f"{b} : touches interceptables hors duel"] += 1
        count["touches interceptables hors duel"] += 1
        count[f"hors duel, avance {min(int(lead * 2) / 2, 2.0)} m"] += 1
        count[f"hors duel, Dribbling {min(int(holder.attributes.get('Dribbling', 50) / 20) * 20, 80)}"] += 1
    count[f"interceptables, avance {min(int(lead * 2) / 2, 2.0)} m"] += 1


n, start = int(sys.argv[1]), int(sys.argv[2])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
for k in range(start, start + n):
    random.seed(AUDIT_SEED + k)
    match.simulate_match(clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)], observer=observer)
    state["prev"], state["seen"] = None, set()
count["matchs"] = n
json.dump(count, sys.stdout, ensure_ascii=False)
