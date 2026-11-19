"""Ticket 10d, diagnostic après l'échec de la mesure (zone 14 inchangée) : à chaque passe reçue en zone 14, où est
l'écran de l'équipe qui défend, et pourquoi ? Relevés : situation de l'équipe qui défend, rôle défensif tenu par l'écran
au tick précédent (presseur, marquage, couverture, compensation, aucun), poids de l'écran (côté du ballon), distance de
l'écran à l'axe, à sa place de référence, au receveur, et s'il est entre le receveur et son but. Échantillon de fond :
même relevé à chaque tick où l'équipe défend sans ballon.
Usage : uv run python .scratch/v2-realisme/mesures/10d-diagnostic.py DEBUT FIN SORTIE.json"""
import json, os, sys
from collections import Counter
sys.path.insert(0, ".")
import v2engine.match as match
from v2engine.defense import DefensiveRoles
from v2engine.bloc import screen_weight
from v2engine.situation import DEFENSE_PLACEE
from v2engine.geometry import Vec2, PITCH_LENGTH_M
from scripts.measure_v2 import run
from scripts.v2_indicators import in_zone_14, RECEIVED_PASSES

start, end, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
snap = {}
real_update = DefensiveRoles.update
def update(self, players, ball, bloc, now_s, situations=None, memory=None):
    snap.update(players=players, ball=ball, bloc=bloc, now=now_s, situations=dict(situations or {}),
                roles={n: a.role for n, a in self.assignments.items()})  # rôles du tick précédent
    return real_update(self, players, ball, bloc, now_s, situations, memory)
DefensiveRoles.update = update

def screen_state(team_def, point):
    bloc, players = snap["bloc"], snap["players"]
    name = bloc.screens.get(team_def)
    s = next((p for p in players if p.name == name), None)
    if s is None:
        return {"ecran": False}
    ref = bloc.reference(s, point, DEFENSE_PLACEE, snap["now"])
    return {"ecran": True, "situation": snap["situations"].get(team_def, "?"), "role": snap["roles"].get(name, "aucun"),
            "poids": round(screen_weight(point), 2), "axe_m": round(abs(s.position.y - 34.0), 1),
            "place_m": round(s.position.distance_to(ref), 1), "ref_axe_m": round(abs(ref.y - 34.0), 1)}

rows = json.load(open(out)) if os.path.exists(out) else {"zone14": [], "fond": Counter()}
rows["fond"] = Counter(rows["fond"])
real_rec = match.ReceptionEvent
def reception(**kw):
    ev = real_rec(**kw)
    if snap and ev.origin in RECEIVED_PASSES and in_zone_14(ev.team, ev.x, ev.y):
        team_def = "away" if ev.team == "home" else "home"
        st = screen_state(team_def, Vec2(ev.x, ev.y))
        if st["ecran"]:
            s = next(p for p in snap["players"] if p.name == snap["bloc"].screens[team_def])
            goal_x = 0.0 if team_def == "home" else PITCH_LENGTH_M
            st["receveur_m"] = round(s.position.distance_to(Vec2(ev.x, ev.y)), 1)
            st["entre"] = abs(s.position.x - goal_x) < abs(ev.x - goal_x)
            st["origin"] = ev.origin
        rows["zone14"].append(st)
    return ev
match.ReceptionEvent = reception

real_def = DefensiveRoles.update
def sampled(self, players, ball, bloc, now_s, situations=None, memory=None):
    real_def(self, players, ball, bloc, now_s, situations, memory)
    holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
    if holder is not None and bloc is not None:
        team_def = "away" if holder.team == "home" else "home"
        name = bloc.screens.get(team_def)
        if name:
            sit = (situations or {}).get(team_def, "?")
            role = self.assignments.get(name).role if name in self.assignments else "aucun"
            rows["fond"][f"{sit}|{role}|{'actif' if screen_weight(holder.position) > 0 else 'axe'}"] += 1
DefensiveRoles.update = sampled

for k in range(start, end):
    run(1, start=k)
    print(k, len(rows["zone14"]), flush=True)
    json.dump(rows, open(out, "w"))
