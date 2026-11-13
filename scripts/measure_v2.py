"""Banc de mesure du moteur V2 (ticket v2-collectif/01) : simule N matchs entre clubs de Ligue 1, graines
fixes, et donne tous les indicateurs de `docs/INDICATEURS_V2.md` (classiques et tactiques), découpés par
zone du ballon, score et tranche de 15 minutes.

Usage : uv run python -m scripts.measure_v2 [nombre_de_matchs] [--profil "Work Rate"] [--detail] [--json chemin] [--pas 0.15]
[--sans-plan] [--sans-tenir]

`--profil <Attribut>` : test de profils. L'attribut est forcé à 99 pour une équipe et à 11 pour l'autre,
les rôles s'inversant d'un match à l'autre (neutralise l'avantage du terrain) ; le rapport compare les deux
niveaux. `--detail` : affiche les découpages. Lecture seule : le jeu n'est pas modifié (sauf l'attribut du
profil testé). `--sans-plan` : le passeur ne transmet aucun plan de passe (ticket v2-collectif/14 désactivé, même
moteur sinon), pour comparer à graines égales."""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from collections.abc import Callable
from dataclasses import replace

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.bloc as bloc_module
import v2engine.cerveau as cerveau
import v2engine.defense as defense
import v2engine.match as match
from v2engine.shooting import NEUTRAL_ATTRIBUTES
from ligue1sim.lineup import pick_best_formation

from scripts.v2_indicators import (CARRY_PREFIX, EXIT_STATES, LINE_GAP_LIMITS_M, LINE_JUMP_M, MARKING_GAP_M, PASS_PREFIX,
                                   Collector, shot_decomposition, xg_calibration)
from scripts.v2_tranches import minute_report, player_report

AUDIT_SEED = 20260923
HIGH, LOW = 99, 11
TICK_S = match.TICK_SECONDS  # le pas du produit (ticket v2-collectif/25) : le banc mesure le match regardé


def _hook(collector: Collector, clock: dict[str, float], plans: bool = True,
          defence_perception: bool = True) -> Callable[[], None]:
    """Branche le collecteur sur les fonctions publiques du moteur ; retourne la fonction qui les restaure.
    `defence_perception` faux : la ligne et le marquage lisent les vraies positions, comme avant le ticket 08e (mesure
    A/B du ticket v2-realisme/08f, seul interrupteur du banc qui change le jeu)."""
    real = {name: getattr(match, name) for name in ("pass_velocity", "resolve_tackle", "choose_action", "dribble_lost",
                                                     "lost_carry_outcome", "attempt_control", "_play_restart",
                                                     "lane_closed_during_turn")}
    restarting = {"on": False}  # remise en jeu en cours : sa passe n'entre pas dans la calibration (ticket v2-realisme/18g)

    def pass_velocity(passer, target, *args, **kwargs):
        opponents = args[0] if args else kwargs.get("opponents", ())
        backheel = args[1] if len(args) > 1 else kwargs.get("backheel", False)  # talonnade (ticket v2-realisme/07e)
        one_touch = args[2] if len(args) > 2 else kwargs.get("one_touch", False)  # de première (ticket v2-collectif/31a)
        collector.on_pass(passer, target, opponents, restart=restarting["on"], backheel=backheel, one_touch=one_touch)
        return real["pass_velocity"](passer, target, *args, **kwargs)

    def lane_closed_during_turn(*args, **kwargs):  # passe abandonnée après la rotation (ticket 07e, réserve A1)
        closed = real["lane_closed_during_turn"](*args, **kwargs)
        collector.count["rotation : passes abandonnées, ligne fermée"] += closed
        collector.count["rotation : passes jugées après la rotation"] += 1
        return closed

    def play_restart(*args, **kwargs):
        restarting["on"] = True
        try:
            return real["_play_restart"](*args, **kwargs)
        finally:
            restarting["on"] = False

    def attempt_control(player, *args, **kwargs):  # premier contact d'une passe en vol (ticket v2-realisme/18g)
        controlled = real["attempt_control"](player, *args, **kwargs)
        collector.on_contact(player, controlled)
        return controlled

    def resolve_tackle(*args, **kwargs):
        collector.on_tackle(args[0])  # tacleur (ticket v2-realisme/19d)
        result = real["resolve_tackle"](*args, **kwargs)
        if result.won:
            collector.on_tackle_won(args[1], args[0])  # (tacleur, porteur), tickets v2-realisme/04c et 19d
        return result

    def dribble_lost(holder, opponents, *args, **kwargs):  # ticket v2-realisme/04a : un tirage de perte par intervalle de conduite
        lost = real["dribble_lost"](holder, opponents, *args, **kwargs)
        collector.on_dribble(holder, opponents, lost)
        return lost

    def lost_carry_outcome(*args, **kwargs):  # ticket v2-realisme/04b : où va le ballon perdu en conduite
        outcome = real["lost_carry_outcome"](*args, **kwargs)
        collector.on_lost_carry(outcome[0] is not None)
        return outcome

    def choose_action(*args, **kwargs):
        action = real["choose_action"](*args, **kwargs)
        if not plans:  # sans suite transmise, aucun plan n'est lu ni relancé (ticket 14 désactivé)
            action = replace(action, follow=None)
        collector.on_choice(action.kind, action.follow, action.plan)
        return action

    real_think = match.think

    def think(player, *args, **kwargs):
        intention = real_think(player, *args, **kwargs)
        collector.on_role(player.name, intention.role)
        if player.poste == "GK":
            collector.on_keeper(player, intention, *args[:2])  # ticket v2-realisme/03d ; ballon et joueurs : 03g
        else:
            collector.on_shot_chaser(player, intention, args[0])  # ticket v2-realisme/03k
        return intention

    real_stays = cerveau.stays_behind

    def stays_behind(player):
        stays = real_stays(player)
        collector.on_balance(player, stays)
        return stays

    real_trigger = defense.DefensiveRoles.start_team_press

    def trigger(self, team, players, now_s, *args):  # pressing d'équipe déclenché (réserve A2 du ticket 08), contre-pressing compris
        collector.on_trigger()
        return real_trigger(self, team, players, now_s, *args)

    # ligne et marquage perçus (tickets v2-realisme/08e et 08f) : la ligne est recalculée à côté sur les vraies positions
    # (ombre, état propre : elle ne lit que les formes de départ) ; le marquage compte ses erreurs de place et de choix
    real_bloc_update = bloc_module.Bloc.update
    real_defense_update = defense.DefensiveRoles.update
    real_seen_at = defense.DefensiveRoles.__dict__["_seen_at"]
    real_closest_to = defense.DefensiveRoles.__dict__["_closest_to"]

    def bloc_update(self, players, ball, now_s=0.0, memory=None):
        real_bloc_update(self, players, ball, now_s, memory if defence_perception else None)
        if memory is None or not defence_perception:
            return
        shadow = getattr(self, "_shadow", None)
        if shadow is None:
            shadow = self._shadow = bloc_module.Bloc(self.shapes)
        real_bloc_update(shadow, players, ball, now_s, None)
        holder_team = next((p.team for p in players if p.name == ball.holder), None) if ball.holder else None
        for team, line in self.lines.items():  # la ligne ne sert qu'à l'équipe dont l'adversaire a le ballon
            if holder_team is not None and holder_team != team and team in shadow.lines:
                collector.on_line(team, now_s, line, shadow.lines[team], clock["dt"])

    def defense_update(self, players, ball, bloc, now_s, situations=None, memory=None):
        real_defense_update(self, players, ball, bloc, now_s, situations, memory if defence_perception else None)

    def seen_at(marker, attacker, memory, now_s):
        where, moving = real_seen_at.__func__(marker, attacker, memory, now_s)
        if memory is not None:  # le marquage précède la mise à jour de la mémoire du tick : « vu » = vu au tick précédent
            seen = memory.age_s(marker.name, attacker.name, now_s) <= 1.5 * clock["dt"]
            collector.on_marking(seen, where.distance_to(attacker.position))
        return where, moving

    def closest_to(cls, candidates, attacker, memory, now_s):
        chosen = real_closest_to.__func__(cls, candidates, attacker, memory, now_s)
        if memory is not None:
            collector.on_marker_choice(chosen is real_closest_to.__func__(cls, candidates, attacker, None, now_s))
        return chosen

    bloc_module.Bloc.update = bloc_update
    defense.DefensiveRoles.update = defense_update
    defense.DefensiveRoles._seen_at = staticmethod(seen_at)
    defense.DefensiveRoles._closest_to = classmethod(closest_to)
    match.pass_velocity = pass_velocity
    match.resolve_tackle, match.choose_action, match.dribble_lost = resolve_tackle, choose_action, dribble_lost
    match.lost_carry_outcome = lost_carry_outcome
    match.attempt_control, match._play_restart = attempt_control, play_restart
    match.lane_closed_during_turn = lane_closed_during_turn  # ticket v2-realisme/07e
    cerveau.stays_behind, match.think = stays_behind, think
    defense.DefensiveRoles.start_team_press = trigger
    return lambda: ([setattr(match, name, fn) for name, fn in real.items()] + [setattr(cerveau, "stays_behind", real_stays), setattr(match, "think", real_think)]
                    + [setattr(defense.DefensiveRoles, "start_team_press", real_trigger),
                       setattr(bloc_module.Bloc, "update", real_bloc_update),
                       setattr(defense.DefensiveRoles, "update", real_defense_update),
                       setattr(defense.DefensiveRoles, "_seen_at", real_seen_at),
                       setattr(defense.DefensiveRoles, "_closest_to", real_closest_to)])


def _new_shots(collector: Collector, live: dict, now_s: float, players) -> None:
    """Tirs du pas qui vient de finir, lus dans la trace (ticket v2-realisme/05h, réserve A3 du 05a) : le tir et son
    contexte (but, gardien adverse, adversaires) au moment de la frappe ; les joueurs n'ont pas bougé depuis. Mêmes tirs
    que l'ancien comptage par `attempt_shot` : ni les tirs contrés, ni les penaltys."""
    shots = live["trace"].shots
    for event in shots[live["shots"]:]:
        if event.origin == "penalty":
            continue
        shooter = next(p for p in players if p.name == event.player)
        opponents = [p for p in players if p.team != shooter.team]
        keeper = next((p for p in opponents if p.poste == "GK"), None)
        collector.on_shot_notes(event.minute, shooter, keeper, opponents)  # ticket v2-realisme/06b, contrés compris
        if event.outcome == "contré":
            continue
        collector.on_shot(shooter, now_s)
        collector.on_shot_context(shooter, match.OPPONENT_GOAL[shooter.team], keeper, opponents)
    live["shots"] = len(shots)


def _force_attribute(attribute: str, high_team: str, team_of: dict[str, str]) -> Callable[[], None]:
    """Force `attribute` à 99 pour `high_team` et à 11 pour l'autre, dans tous les modules du moteur. `team_of`
    (nom -> équipe) sert aux joueurs encore sans équipe : Pace, Acceleration et Stamina sont lus à la
    construction des joueurs, sur les fiches de la base."""
    patched = []
    for name, module in list(sys.modules.items()):
        if name.startswith("v2engine") and hasattr(module, "player_attribute"):
            real = module.player_attribute

            def forced(player, attr, _real=real):
                team = getattr(player, "team", None) or team_of.get(getattr(player, "name", None))
                # copie neutre de l'xG neutre (ticket v2-realisme/06b) : jamais forcée (réserve A1 de l'expert)
                if attr == attribute and team in ("home", "away") and getattr(player, "attributes", None) is not NEUTRAL_ATTRIBUTES:
                    return HIGH if team == high_team else LOW
                return _real(player, attr)
            module.player_attribute = forced
            patched.append((module, real))
    return lambda: [setattr(m, "player_attribute", r) for m, r in patched]


def run(n_matches: int, profile: str | None = None, duration_minutes: float = 90.0, tick_s: float = TICK_S,
        plans: bool = True, start: int = 0, defence_perception: bool = True) -> Collector:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    collector = Collector()
    collector.minutes_per_match = duration_minutes
    clock = {"now": 0.0, "dt": tick_s}
    started = time.perf_counter()
    restore = _hook(collector, clock, plans, defence_perception)
    try:
        for i in range(start, start + n_matches):  # `start` : découper un banc en lots parallèles
            # profils : chaque affiche est jouée deux fois, même graine, rôles haut/bas inversés
            k = i // 2 if profile else i
            random.seed(AUDIT_SEED + k)
            clock["now"] = 0.0
            home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
            high_team = "home" if i % 2 == 0 else "away"
            team_of = {p.name: "home" for p in pick_best_formation(home).players}
            team_of.update({p.name: "away" for p in pick_best_formation(away).players})
            unforce = _force_attribute(profile, high_team, team_of) if profile else (lambda: None)

            live = {"trace": None, "shots": 0}

            def observer(now_s, players, ball, scoring_team):
                clock["now"] = now_s
                if profile and not collector.levels:
                    collector.levels = {p.name: ("haut" if p.team == high_team else "bas") for p in players}
                _new_shots(collector, live, now_s, players)
                if live["trace"] is not None:  # temps joué des tranches (ticket v2-realisme/19f)
                    collector.minutes.second_half_start = live["trace"].second_half_start_minute
                collector.on_tick(now_s, players, ball, scoring_team, tick_s)
            try:
                trace = match.simulate_match(home, away, duration_minutes=duration_minutes, tick_seconds=tick_s,
                                             observer=observer, on_start=lambda t: live.update(trace=t))
                for event in trace.offsides:  # hors-jeu sifflés (ticket v2-collectif/23)
                    collector.on_offside(event)
                for event in trace.restarts:  # remises en jeu (ticket v2-collectif/29)
                    collector.on_restart(event)
                for event in trace.fouls:  # fautes (ticket v2-collectif/30)
                    collector.on_foul(event)
                for event in trace.shots:  # tirs et leur issue (ticket v2-collectif/28b)
                    collector.on_shot_event(event)
                for event in trace.chances:  # grosses occasions (ticket v2-collectif/28c)
                    collector.on_chance(event)
                collector.on_events(trace.events)  # contrôles ratés par tranche (ticket v2-realisme/19d)
                collector.on_decisions(trace.decisions)  # rotation avant la passe ou le tir (ticket v2-realisme/07e)
                collector.on_receptions(trace.receptions)  # mémoire du receveur (ticket v2-realisme/08b)
                collector.on_scans(trace.scans, trace.receptions)  # scans (ticket v2-realisme/08c)
            finally:
                unforce()
            collector.end_match()
    finally:
        restore()
    collector.seconds_per_match = (time.perf_counter() - started) / max(1, n_matches)
    return collector


def _exit_states(k, n: int) -> dict[str, float]:
    """Ballons avec sortie par état du ballon (ticket v2-realisme/03j) : nombre par match, puis part de chaque issue à 3 s."""
    out = {}
    for state in EXIT_STATES:
        key = "gardien : ballons avec sortie, état : " + state
        out[key + " (par match)"] = k[key] / n
        for label, held in (("au gardien", "gardien"), ("à un coéquipier", "coéquipier"), ("à l'adversaire", "adversaire"),
                            ("encore libre", "libre"), ("sortie de but", "arrêt : sortie de but"), ("corner", "arrêt : corner"),
                            ("engagement", "arrêt : engagement")):
            # part non définie (None) quand aucun ballon dans cet état : elle ne pèse pas comme un zéro dans la moyenne par match
            out[f"{key}, ballon à 3 s, {label} (part)"] = k[f"{key}, ballon à 3 s : {held}"] / k[key] if k[key] else None
        cross = f"gardien : ballons avec sortie hors tir du 03i, état : {state}"
        out[cross + " (par match)"] = k[cross] / n
        out[cross + ", corner (par match)"] = k[cross + ", corner"] / n
    return out


def _share(k, held: str) -> float:
    """Part des ballons avec sortie (ticket v2-realisme/03i) dont l'état à 3 s est `held`."""
    return k["gardien : ballons avec sortie, ballon à 3 s : " + held] / max(1, k["gardien : ballons avec sortie"])


def report(c: Collector, detail: bool = False) -> dict:
    n = max(1, c.matches)
    k = c.count
    passes = max(1, k["passes"])
    minutes = getattr(c, "minutes_per_match", 90.0) * n
    # durée réelle, temps additionnel compris : passes et ballon mort sont comptés sur tout le match (ticket
    # v2-realisme/01d) ; à défaut (collecteur construit à la main), la durée réglementaire
    played = k["durée de match (s)"] / 60.0 or minutes
    out: dict[str, object] = {
        "matchs": c.matches,
        "passes par minute": k["passes"] / minutes,
        # ticket v2-realisme/01d (repère R7) : la source compte les passes par match ; 15-17 vaut par minute de jeu effectif
        "passes par match": k["passes"] / n,
        "passes par minute de jeu effectif": k["passes"] / max(1e-9, played - k["temps de ballon mort (s)"] / 60.0),
        "passes réussies (part)": k["passes réussies"] / passes,
        "passes chez l'adversaire (part)": k["passes chez l'adversaire"] / passes,
        "receveur visé (part)": k["receveur visé"] / passes,
        "passes longues (part)": k["passes longues"] / passes,
        "passes longues réussies (part)": k["passes longues réussies"] / max(1, k["passes longues"]),
        "passes en profondeur (part)": k["passes en profondeur"] / passes,
        "passes en profondeur réussies (part)": k["passes en profondeur réussies"] / max(1, k["passes en profondeur"]),
        "tirs par équipe": k["tirs"] / (2 * n),
        "tirs de près (16 m) par équipe": k["tirs de près"] / (2 * n),
        "part des tirs de près (16 m)": k["tirs de près"] / max(1, k["tirs"]),
        "buts par match": k["buts"] / n,
        "hors-jeu par match": k["hors-jeu"] / n,
        "hors-jeu par équipe": k["hors-jeu"] / (2 * n),
        # ballon mort (ticket v2-collectif/29)
        "touches par match": k["remises : touche"] / n,
        "sorties de but par match": k["remises : sortie de but"] / n,
        "corners par match": k["remises : corner"] / n,
        "engagements par match": k["remises : engagement"] / n,
        "touches jouées long (part)": k["remises jouées long : touche"] / max(1, k["remises : touche"]),
        "sorties de but jouées long (part)": k["remises jouées long : sortie de but"] / max(1, k["remises : sortie de but"]),
        "corners joués long (part)": k["remises jouées long : corner"] / max(1, k["remises : corner"]),
        "temps de jeu effectif (part)": 1.0 - k["temps de ballon mort (s)"] / (60.0 * played),
        "tacles par match": k["tacles"] / n,
        # issues du tir (ticket v2-collectif/28b) : sur les tirs tracés, contrés et penaltys compris
        "tirs tracés par équipe": k["tirs tracés"] / (2 * n),
        "tirs cadrés (part)": sum(k["tirs : " + o] for o in ("but", "capté", "repoussé", "claqué")) / max(1, k["tirs tracés"]),
        "tirs contrés (part)": k["tirs : contré"] / max(1, k["tirs tracés"]),
        "tirs à côté (part)": k["tirs : à côté"] / max(1, k["tirs tracés"]),
        "tirs au-dessus (part)": k["tirs : au-dessus"] / max(1, k["tirs tracés"]),  # ticket v2-collectif/35b
        "tirs dévissés (part)": k["tirs : dévissé"] / max(1, k["tirs tracés"]),
        "conversion des tirs (part)": k["tirs : but"] / max(1, k["tirs tracés"]),
        "buts dans la surface (part)": k["buts dans la surface"] / max(1, k["tirs : but"]),
        "qualité moyenne de l'occasion": k["qualité des occasions (somme)"] / max(1, k["tirs tracés"]),
        "arrêts par match": sum(k["tirs : " + o] for o in ("capté", "repoussé", "claqué")) / n,
        "arrêts captés (part)": k["tirs : capté"] / max(1, sum(k["tirs : " + o] for o in ("capté", "repoussé", "claqué"))),
        "arrêts repoussés (part)": k["tirs : repoussé"] / max(1, sum(k["tirs : " + o] for o in ("capté", "repoussé", "claqué"))),
        "arrêts claqués (part)": k["tirs : claqué"] / max(1, sum(k["tirs : " + o] for o in ("capté", "repoussé", "claqué"))),
        # grosses occasions, avec ou sans tir (ticket v2-collectif/28c)
        "grosses occasions par match": k["grosses occasions"] / n,
        "grosses occasions sans tir (part)": k["grosses occasions sans tir"] / max(1, k["grosses occasions"]),
        "grosses occasions : danger moyen au pic": k["grosses occasions : danger au pic (somme)"] / max(1, k["grosses occasions"]),
        # fautes (ticket v2-collectif/30)
        "fautes par match": k["fautes"] / n,
        "avantages acquis (part des fautes)": k["fautes : avantage"] / max(1, k["fautes"]),
        "coups francs par match": k["fautes : coup franc"] / n,
        "penaltys par match": k["fautes : penalty"] / n,
        "fautes inconsidérées (part)": k["fautes : gravité inconsidérée"] / max(1, k["fautes"]),
        "fautes avec excès d'engagement (part)": k["fautes : gravité excès d'engagement"] / max(1, k["fautes"]),
        "coups francs du dernier tiers frappés au but (part)":
            k["coups francs du dernier tiers frappés"] / max(1, k["coups francs du dernier tiers"]),
        "profil haut : fautes par match": k["profil haut : fautes"] / n,
        "profil bas : fautes par match": k["profil bas : fautes"] / n,
        "pressings d'équipe déclenchés par match": k["pressings d'équipe déclenchés"] / n,
        "pertes de balle par match": k["pertes de balle"] / n,
        "pertes en transition par match": None,
        "tirs de contre par match (récupération dans son camp)": k["tirs de contre, récupération propre camp"] / n,
        "tirs de contre par match (récupération dans le camp adverse)": k["tirs de contre, récupération camp adverse"] / n,
        "gardien : sorties par match": k["gardien : sorties"] / n,  # ticket v2-realisme/03d
        "gardien : sorties réussies (part)": k["gardien : sorties réussies"] / max(1, k["gardien : sorties"]),
        "gardien : sorties hors de sa surface (part)": k["gardien : sorties hors de sa surface"] / max(1, k["gardien : sorties"]),
        "gardien : ballons libres à sa portée laissés par match": k["gardien : ballons libres laissés"] / n,
        "gardien : face-à-face par match": k["gardien : face-à-face"] / n,  # ticket v2-realisme/03e
        # ticket v2-realisme/04a : un tirage de perte par intervalle de conduite, selon la gêne du porteur
        "conduite : intervalles par match": k["conduite : intervalles"] / n,
        "conduite : pertes par match": k["conduite : pertes"] / n,
        "conduite : perte par intervalle (part)": k["conduite : pertes"] / max(1, k["conduite : intervalles"]),
        "conduite sans adversaire proche (gêne < 0,1) : intervalles par match": k["conduite libre : intervalles"] / n,
        "conduite sans adversaire proche (gêne < 0,1) : perte par intervalle (part)": k["conduite libre : pertes"] / max(1, k["conduite libre : intervalles"]),
        "conduite serrée (gêne >= 0,5) : intervalles par match": k["conduite serrée : intervalles"] / n,
        "conduite serrée (gêne >= 0,5) : perte par intervalle (part)": k["conduite serrée : pertes"] / max(1, k["conduite serrée : intervalles"]),
        # ticket v2-realisme/04b : issue du ballon perdu en conduite (dépossession au contact, ou touche trop longue)
        "conduite : pertes par dépossession par match": k["conduite : dépossessions"] / n,
        "conduite : pertes par touche trop longue par match": k["conduite : touches trop longues"] / n,
        "conduite : part des pertes par dépossession": k["conduite : dépossessions"] / max(1, k["conduite : pertes"]),
        # ticket v2-realisme/03k : tirs en vol retirés de la sortie du gardien ; joueurs de champ qui courent encore derrière
        "gardien : placements sur tir en vol par match (deux gardiens)": k["gardien : placements sur tir en vol"] / n,
        "tir à côté en vol : joueurs de champ en course vers le ballon par match": k["tir à côté en vol : joueurs de champ en course vers le ballon"] / n,
        "tir qui entre en vol : joueurs de champ en course vers le ballon par match": k["tir qui entre en vol : joueurs de champ en course vers le ballon"] / n,
        # ticket v2-realisme/03g
        "gardien : sorties disputées par match": k["gardien : sorties disputées"] / n,
        "gardien : sorties très disputées par match": k["gardien : sorties très disputées"] / n,
        "gardien : sorties disputées gagnées (part)": k["gardien : sorties disputées gagnées"] / max(1, k["gardien : sorties disputées"]),
        "gardien : courses gagnantes masquées, coéquipier plus rapide, par match": k["gardien : course gagnante masquée, coéquipier"] / n,
        "gardien : courses gagnantes masquées, coéquipier battu, par match": k["gardien : course gagnante masquée, battu"] / n,
        # ticket v2-realisme/03i : par ballon libre (premier épisode de sortie), pas par épisode d'état
        "gardien : ballons avec sortie par match": k["gardien : ballons avec sortie"] / n,
        "gardien : ballons avec sortie, ballon à 3 s, au gardien (part)": _share(k, "gardien"),
        "gardien : ballons avec sortie, ballon à 3 s, à un coéquipier (part)": _share(k, "coéquipier"),
        "gardien : ballons avec sortie, ballon à 3 s, à l'adversaire (part)": _share(k, "adversaire"),
        "gardien : ballons avec sortie, ballon à 3 s, encore libre (part)": _share(k, "libre"),
        "gardien : ballons avec sortie, ballon à 3 s, sortie de but (part)": _share(k, "arrêt : sortie de but"),
        "gardien : ballons avec sortie, ballon à 3 s, corner (part)": _share(k, "arrêt : corner"),
        "gardien : ballons avec sortie, ballon à 3 s, but encaissé ou marqué (engagement) (part)": _share(k, "arrêt : engagement"),
        "gardien : ballons avec sortie, ballon à 3 s, autre arrêt de jeu (part)": _share(k, "arrêt : autre"),
        "gardien : ballons avec sortie, ballon issu d'un tir adverse des 5 s précédentes (part)":
            k["gardien : ballons avec sortie, tir adverse dans les 5 s avant"] / max(1, k["gardien : ballons avec sortie"]),
        "gardien : ballons avec sortie, tir adverse dans les 5 s (part)":
            k["gardien : ballons avec sortie, tir adverse dans les 5 s"] / max(1, k["gardien : ballons avec sortie"]),
        "gardien : ballons avec sortie hors tir par match": k["gardien : ballons avec sortie hors tir"] / n,
        # ticket v2-realisme/03j : par état du ballon à la sortie, nombre par match et issue à 3 s (part de l'état)
        "gardien : ballons avec sortie, non résolus en fin de match, par match":
            k["gardien : ballons avec sortie, non résolus en fin de match"] / n,  # réserve A2 du 03i
        **_exit_states(k, n),
        **{f"gardien : ballons avec sortie hors tir, ballon à 3 s, {label} (part)":
           k["gardien : ballons avec sortie hors tir, ballon à 3 s : " + held] / max(1, k["gardien : ballons avec sortie hors tir"])
           for label, held in (("au gardien", "gardien"), ("à un coéquipier", "coéquipier"), ("à l'adversaire", "adversaire"),
                               ("encore libre", "libre"), ("sortie de but", "arrêt : sortie de but"),
                               ("corner", "arrêt : corner"), ("engagement", "arrêt : engagement"))},
        "gardien : ballons avec course gagnante masquée, coéquipier plus rapide, par match":
            k["gardien : ballons avec course gagnante masquée, coéquipier"] / n,
        "gardien : ballons avec course gagnante masquée, coéquipier battu, par match":
            k["gardien : ballons avec course gagnante masquée, battu"] / n,
        "face-à-face : tirs par match": k["face-à-face : tirs"] / n,
        "appels par match": k["appels"] / n,
        "appels dans le dos par match": k["appels dans le dos"] / n,  # ticket v2-collectif/16
        "pressings par match": k["pressings"] / n,
        "pressings suivis d'une récupération en 5 s (part)": k["pressings suivis d'une récupération en 5 s"] / max(1, k["pressings"]),
        "profil haut : temps de pressing par match (s)": k["profil haut : temps de pressing (s)"] / n,
        "profil bas : temps de pressing par match (s)": k["profil bas : temps de pressing (s)"] / n,
        "temps de calcul par match (s)": getattr(c, "seconds_per_match", None),
        # combinaisons (ticket v2-collectif/14)
        "passes sans gain suivies d'une passe qui fait avancer (part, C2)":
            k["passes sans gain suivies d'une passe qui fait avancer"] / max(1, k["passes sans gain réussies"]),
        "retours au passeur en 3 s (part des passes réussies)":
            k["retours au passeur en 3 s"] / max(1, k["passes réussies (journal)"]),
        "retours au passeur en 3 s hors une-deux (part)":
            (k["retours au passeur en 3 s"] - k["une-deux"]) / max(1, k["passes réussies (journal)"]),
        "une-deux par équipe et par match": k["une-deux"] / (2 * n),
        "troisième homme par équipe et par match": k["troisième homme (suite prévue jouée et réussie)"] / (2 * n),
        "plans reçus par match": k["plans reçus"] / n,
        "plans tenus (part)": k["plan tenu"] / max(1, k["plans reçus"]),
        "plans abandonnés, ligne fermée (part)": k["plan abandonné"] / max(1, k["plans reçus"]),
        "plans abandonnés, cible non vue ou hors-jeu (part)": k["plan non vu"] / max(1, k["plans reçus"]),
        "plans refusés, Teamwork (part)": k["plan refusé"] / max(1, k["plans reçus"]),
    }
    # calibration de la conduite (ticket v2-realisme/04c) : risque évalué contre perte observée, par tranche
    for tranche in sorted({key[len(CARRY_PREFIX):].rsplit(" : ", 1)[0] for key in k if key.startswith(CARRY_PREFIX)}):
        base, n_int = f"{CARRY_PREFIX}{tranche} : ", k[f"{CARRY_PREFIX}{tranche} : intervalles"]
        evaluated, drawn = k[base + "risque évalué (somme)"] / n_int, k[base + "pertes"] / n_int
        total = (k[base + "pertes"] + k[base + "pertes par tacle"]) / n_int
        out[f"{base}intervalles par match"] = n_int / n
        out[f"{base}risque évalué (part)"] = evaluated
        out[f"{base}perte tirée (part)"] = drawn
        out[f"{base}écart évalué / tirée (points)"] = 100.0 * (drawn - evaluated)
        out[f"{base}perte avec tacle gagné (part)"] = total
        out[f"{base}écart évalué / avec tacle (points)"] = 100.0 * (total - evaluated)
    # calibration de la passe (ticket v2-realisme/18g) : chance évaluée contre passe non perdue, par tranche
    for group in sorted({key[len(PASS_PREFIX):].rsplit(" : ", 1)[0] for key in k if key.startswith(PASS_PREFIX)}):
        base, n_pass = f"{PASS_PREFIX}{group} : ", k[f"{PASS_PREFIX}{group} : passes"]
        evaluated, kept = k[base + "chance évaluée (somme)"] / n_pass, k[base + "non perdues"] / n_pass
        out[f"{base}passes par match"] = n_pass / n
        out[f"{base}chance évaluée (part)"] = evaluated
        out[f"{base}non perdue (part)"] = kept
        out[f"{base}écart évaluée / non perdue (points)"] = 100.0 * (evaluated - kept)
        out[f"{base}reçue par le receveur visé (part)"] = k[base + "reçues par le receveur visé"] / n_pass
    # structure (ticket v2-realisme/02h)
    out["passages APPEL / TENIR dans une possession par match"] = k["passages APPEL / TENIR dans une possession"] / n
    out["passages APPEL / TENIR dans une possession : état de moins de 1,5 s (part)"] = (
        k["passages APPEL / TENIR dans une possession, état de moins de 1,5 s"]
        / max(1, k["passages APPEL / TENIR dans une possession"]))
    out["appels arrêtés dans une possession, en moins de 1,5 s (part des APPEL qui se terminent par TENIR)"] = (
        k["appels arrêtés dans une possession, en moins de 1,5 s"] / max(1, k["appels arrêtés dans une possession"]))
    for key, v in sorted(k.items()):  # rôle des joueurs que le banc compte comme appelants (réserve A1 du 02g)
        if key.startswith("appels du banc, rôle au départ : "):
            out[f"{key} (part)"] = v / max(1, k["appels"])
        elif key.startswith("appelants simultanés, somme : "):
            situation = key.removeprefix("appelants simultanés, somme : ")
            out[f"appelants simultanés d'une équipe en possession, moyenne : {situation}"] = (
                v / max(1, k["appelants simultanés, instants : " + situation]))
            out[f"appelants simultanés au-dessus du plafond du moteur, part des instants : {situation}"] = (
                k["appelants simultanés au-dessus du plafond, instants : " + situation]
                / max(1, k["appelants simultanés, instants : " + situation]))
    for name, stat in sorted(c.stats.items()):
        if name.startswith("appelants simultanés d'une équipe, maximum du match : ") and stat.values:
            out[name.replace("maximum du match", "maximum de la série")] = max(stat.values)
    choices = sum(v for key, v in k.items() if key.startswith("choix "))
    for key, v in sorted(k.items()):
        if key.startswith("choix "):
            out[f"{key} (part)"] = v / max(1, choices)
    for key, v in sorted(k.items()):  # taux d'arrêt des tirs cadrés par distance et par vitesse (ticket v2-realisme/05h)
        if key.startswith("tirs cadrés jugés, "):
            out["taux d'arrêt, " + key.removeprefix("tirs cadrés jugés, ")] = k[key.replace("jugés", "arrêtés")] / v
            out[key + " (effectif)"] = v  # réserve A2 de l'expert, 05h : effectif de chaque tranche
    # rotation avant la passe ou le tir, talonnades (ticket v2-realisme/07e)
    for kind in ("passes", "tirs"):
        decided, turned = k[f"rotation : {kind} décidés"], k[f"rotation : {kind} décidés avec rotation"]
        out[f"rotation : {kind} décidés avec rotation (part)"] = turned / max(1, decided)
        out[f"rotation : {kind}, durée moyenne quand il y en a une (s)"] = k[f"rotation : {kind}, durée (somme, s)"] / max(1, turned)
    out["rotation : ballons perdus en se retournant par match"] = k["rotation : ballons perdus en se retournant"] / n
    out["rotation : passes abandonnées, ligne fermée, par match"] = k["rotation : passes abandonnées, ligne fermée"] / n
    out["rotation : passes abandonnées, ligne fermée (part des passes jugées après la rotation)"] = (
        k["rotation : passes abandonnées, ligne fermée"] / max(1, k["rotation : passes jugées après la rotation"]))
    decided = max(1, k["vision : décisions"])  # champ de vision du porteur (ticket v2-realisme/08a)
    out["vision : adversaires non vus par le porteur à la décision (moyenne)"] = k["vision : adversaires non vus (somme)"] / decided
    out["vision : adversaires non vus à 5 m au plus (moyenne)"] = k["vision : adversaires non vus à 5 m (somme)"] / decided
    out["vision : décisions avec un adversaire non vu à 5 m au plus (part)"] = (
        k["vision : décisions avec un adversaire non vu à 5 m"] / decided)
    # ticket v2-realisme/08f : part des adversaires proches (5 m au plus) non vus, et pertes au contact sur adversaire non vu
    out["vision : adversaires à 5 m au plus par décision (moyenne)"] = k["vision : adversaires à 5 m (somme)"] / decided
    out["vision : adversaires à 5 m au plus non vus à la décision (part des adversaires proches)"] = (
        k["vision : adversaires non vus à 5 m (somme)"] / max(1, k["vision : adversaires à 5 m (somme)"]))
    out["pertes de balle au contact par match (tacle, conduite, rotation)"] = k["pertes au contact"] / n
    out["pertes au contact sur adversaire non vu (part des pertes au contact)"] = (
        k["pertes au contact sur adversaire non vu"] / max(1, k["pertes au contact"]))
    for way in ("tacle", "conduite", "rotation"):
        out[f"pertes au contact : {way}, par match"] = k[f"pertes au contact : {way}"] / n
        out[f"pertes au contact : {way}, sur adversaire non vu (part)"] = (
            k[f"pertes au contact sur adversaire non vu : {way}"] / max(1, k[f"pertes au contact : {way}"]))
    # mémoire de perception du porteur et du receveur sur les adversaires non vus (ticket v2-realisme/08b)
    held = max(1, k["mémoire : décisions avec un adversaire non vu"])
    out["mémoire : âge de la dernière vue des adversaires non vus, porteur (s)"] = k["mémoire : âge de la dernière vue (somme, s)"] / held
    out["mémoire : erreur de position perçue des adversaires non vus, porteur (m)"] = k["mémoire : erreur moyenne (somme, m)"] / held
    out["mémoire : fantômes perçus par décision (adversaires perçus avec plus de 4 s de retard et 10 m d'erreur)"] = (
        k["mémoire : fantômes (somme)"] / max(1, k["vision : décisions"]))
    out["mémoire : décisions avec un fantôme (part)"] = (
        k["mémoire : décisions avec un fantôme (plus de 4 s, plus de 10 m)"] / max(1, k["vision : décisions"]))
    out["mémoire : erreur maximale, porteur (m)"] = c.peak["mémoire : erreur maximale du porteur (m)"]
    received = max(1, k["mémoire : réceptions avec un adversaire non vu"])
    out["mémoire : réceptions avec un adversaire non vu (part)"] = (
        k["mémoire : réceptions avec un adversaire non vu"] / max(1, k["mémoire : réceptions"]))
    out["mémoire : âge de la dernière vue des adversaires non vus, receveur (s)"] = k["mémoire : âge à la réception (somme, s)"] / received
    out["mémoire : erreur de position perçue des adversaires non vus, receveur (m)"] = k["mémoire : erreur à la réception (somme, m)"] / received
    out["mémoire : erreur maximale, receveur (m)"] = c.peak["mémoire : erreur maximale du receveur (m)"]
    # scans (ticket v2-realisme/08c)
    out["scans par match"] = k["scans"] / n
    match_minutes = getattr(c, "minutes_per_match", 90.0)  # absent hors de `run` (tests du rapport)
    out["scans par minute et par joueur"] = k["scans"] / max(1e-9, n * match_minutes * 22)
    on_pitch_s = sum(v for key, v in k.items() if key.startswith("temps sur le terrain (s) : "))
    out["scans par minute et par joueur (temps réellement sur le terrain, temps additionnel compris)"] = (
        k["scans"] / max(1e-9, on_pitch_s / 60.0))  # le total ci-dessus suppose 90 min nominales (08c) ; même base que les postes
    for poste in sorted(key.split(" : ")[1] for key in k if key.startswith("temps sur le terrain (s) : ")):
        out[f"scans par minute et par joueur : {poste}"] = k[f"scans : {poste}"] / max(1e-9, k[f"temps sur le terrain (s) : {poste}"] / 60.0)
    out["scans en défense (part des scans ; l'équipe sans le ballon ne suit plus le ballon le temps du scan)"] = (
        k["scans : en défense"] / max(1, k["scans"]))
    out["scans du porteur (part des scans)"] = k["scans : du porteur"] / max(1, k["scans"])
    out["scans dans les 10 s avant la réception (moyenne par réception)"] = (
        k["scans : avant la réception (somme, 10 s)"] / max(1, k["scans : réceptions"]))
    for level in ("haut", "bas"):  # profil testé (--profil Vision, Dribbling, Technique, Pace)
        out[f"profil {level} : scans par minute et par joueur"] = k[f"profil {level} : scans"] / max(1e-9, n * match_minutes * 11)
        out[f"profil {level} : scans dans les 10 s avant la réception (moyenne)"] = (
            k[f"profil {level} : scans avant la réception (somme, 10 s)"] / max(1, k[f"profil {level} : réceptions"]))
    # ligne et marquage perçus (tickets v2-realisme/08e et 08f, réserve A1 du 08e) : effet exact de la perception tick par tick
    ticks = max(1, k["ligne : ticks adversaire porteur"])
    out["ligne perçue : ticks avec l'adversaire porteur par match"] = k["ligne : ticks adversaire porteur"] / n
    out["ligne perçue : écart absolu à la ligne sur vraies positions (moyenne, m)"] = k["ligne : écart absolu (somme, m)"] / ticks
    out["ligne perçue : écart signé, perçue - réelle (moyenne, m ; positif = ligne plus haute)"] = (
        k["ligne : écart perçue - réelle (somme, m)"] / ticks)
    for limit in LINE_GAP_LIMITS_M:
        out[f"ligne perçue : ticks avec un écart de plus de {limit:g} m (part)"] = (
            k[f"ligne : ticks avec un écart de plus de {limit:g} m"] / ticks)
    gaps = c.stats["ligne : écart absolu dû à la perception (m)"].values
    out["ligne perçue : écart absolu, 95e centile (m)"] = statistics.quantiles(gaps, n=20)[-1] if len(gaps) >= 2 else 0.0
    out["ligne perçue : écart maximal (m)"] = c.peak["ligne : écart maximal (m)"]
    for tag in ("perçue", "réelle"):
        steps = max(1, k[f"ligne {tag} : variations (nombre)"])
        out[f"ligne {tag} : variation moyenne d'un tick à l'autre (m)"] = k[f"ligne {tag} : variation absolue (somme, m)"] / steps
        out[f"ligne {tag} : variation efficace d'un tick à l'autre (m)"] = (k[f"ligne {tag} : variation au carré (somme, m²)"] / steps) ** 0.5
        out[f"ligne {tag} : sauts de plus de {LINE_JUMP_M:g} m par match"] = k[f"ligne {tag} : sauts de plus de {LINE_JUMP_M:g} m"] / n
        out[f"ligne {tag} : changements de sens par match"] = k[f"ligne {tag} : changements de sens"] / n
    marked = max(1, k["marquage : marqueur-ticks"])
    out["marquage : marqueur-ticks par match"] = k["marquage : marqueur-ticks"] / n
    out["marquage : attaquant non vu par son marqueur (part des marqueur-ticks)"] = k["marquage : attaquant non vu"] / marked
    out["marquage : erreur de place de l'attaquant (moyenne, m)"] = k["marquage : erreur de place (somme, m)"] / marked
    out["marquage : erreur de place quand l'attaquant n'est pas vu (moyenne, m)"] = (
        k["marquage : erreur de place, attaquant non vu (somme, m)"] / max(1, k["marquage : attaquant non vu"]))
    out[f"marquage : erreur de plus de {MARKING_GAP_M:g} m (part des marqueur-ticks)"] = (
        k[f"marquage : erreur de plus de {MARKING_GAP_M:g} m"] / marked)
    out["marquage : erreur maximale (m)"] = c.peak["marquage : erreur maximale (m)"]
    out["marquage : marqueur différent de celui des vraies positions (part des choix)"] = (
        k["marquage : marqueur différent de celui des vraies positions"] / max(1, k["marquage : choix du marqueur"]))
    # temps de possession individuelle par type de réception (ticket v2-realisme/07d)
    for key in sorted(k):
        if key.startswith("possession par réception : ") and key.endswith(" : réceptions"):
            group = key.removeprefix("possession par réception : ").removesuffix(" : réceptions")
            out[f"temps par possession de joueur, réception {group} (s)"] = (
                k[f"possession par réception : {group} : durée (somme, s)"] / max(1, k[key]))
            out[f"réceptions {group} (part des contrôles appariés)"] = k[key] / max(
                1, sum(k[f"possession par réception : {kind} : réceptions"] for kind in ("de face", "de profil", "dos au jeu")))

    # contrôle à l'aveugle (ticket v2-realisme/07d) ; appariement de l'indicateur par type (réserve A4)
    out["contrôles à l'aveugle (part des contrôles non orientés)"] = (
        k["contrôle à l'aveugle : non orientés"] / max(1, k["contrôle : non orientés"]))
    out["temps par possession par réception : contrôles appariés (part)"] = (
        k["possession par réception : contrôles appariés"] / max(1, k["possession par réception : contrôles"]))
    # contrôle orienté (ticket v2-collectif/31b)
    out["contrôles orientés (part des contrôles)"] = k["contrôle orienté : orientés"] / max(1, k["contrôle orienté : réceptions"])
    # ballon dur (ticket v2-collectif/31c)
    out["contrôles de ballon dur, plus de 12 m/s (part des contrôles)"] = (
        k["contrôle orienté : réceptions de ballon dur"] / max(1, k["contrôle orienté : réceptions"]))
    out["contrôles orientés, ballon dur (part)"] = (
        k["contrôle orienté : ballons durs orientés"] / max(1, k["contrôle orienté : réceptions de ballon dur"]))
    # jeu à une touche (ticket v2-collectif/31a)
    out["passes de première (part des passes décidées)"] = k["une touche : passes décidées"] / max(1, k["rotation : passes décidés"])
    out["passes de première par match"] = k["une touche : passes décidées"] / n
    out["passes de première : non perdues (part)"] = k["une touche : non perdues"] / max(1, k["une touche : passes jouées"])
    out["passes de première : chance évaluée (part)"] = k["une touche : chance évaluée (somme)"] / max(1, k["une touche : passes jouées"])
    out["talonnades par match"] = k["talonnades"] / n
    out["talonnades : non perdues (part)"] = k["talonnades : non perdues"] / max(1, k["talonnades"])
    out["talonnades : reçues par le receveur visé (part)"] = k["talonnades : reçues par le receveur visé"] / max(1, k["talonnades"])
    out["talonnades : chance évaluée (part)"] = k["talonnades : chance évaluée (somme)"] / max(1, k["talonnades"])
    # xG (ticket v2-realisme/06a) : par match, à comparer aux buts ; xG neutre sur les tirs hors penalty, xG après frappe
    # sur les tirs non contrés
    out["xG neutre par match"] = k["xG neutre (somme)"] / n
    out["xG après frappe par match"] = k["xG après frappe (somme)"] / n
    out["xG neutre moyen par tir"] = k["xG neutre (somme)"] / max(1, k["xG neutre (tirs)"])
    out["xG après frappe moyen par tir non contré"] = k["xG après frappe (somme)"] / max(1, k["xG après frappe (tirs)"])
    out.update(shot_decomposition(k, n))
    out.update(xg_calibration(k, n))  # ticket v2-realisme/06c
    for key, v in sorted(k.items()):  # direction de sortie des tirs contrés (ticket v2-realisme/05d)
        if key.startswith("tirs contrés, sortie "):
            out[key + " (part)"] = v / max(1, k["tirs : contré"])
    for key, v in sorted(k.items()):  # origine des tirs (ticket v2-collectif/28b)
        if key.startswith("tirs, origine : "):
            out[f"{key} (part)"] = v / max(1, k["tirs tracés"])
    for key, v in sorted(k.items()):  # issue et origine des grosses occasions (ticket v2-collectif/28c)
        if key.startswith(("grosses occasions, issue : ", "grosses occasions, origine : ")):
            out[f"{key} (part)"] = v / max(1, k["grosses occasions"])
    in_situation = sum(v for key, v in k.items() if key.startswith("temps en "))
    for key, v in sorted(k.items()):
        if key.startswith("temps en "):
            out[f"part du {key} (deux équipes)"] = v / max(1e-9, in_situation)
    recoveries = max(1, k["récupérations"])
    for key, v in sorted(k.items()):
        if key.startswith("récupération "):
            out[f"{key} (part)"] = v / recoveries
    relost = c.stats.get("pertes en transition (part des récupérations)")
    out["pertes en transition par match"] = sum(relost.values) / n if relost else 0.0
    out["km par joueur de champ, par poste"] = {p: round(statistics.fmean(v), 2) for p, v in sorted(c.km.items())}
    for name, stat in sorted(c.stats.items()):
        out[name] = statistics.fmean(stat.values) if stat.values else None
        if detail and stat.by:
            out[name + " — découpage"] = {f"{a}={b}": round(statistics.fmean(v), 2) for (a, b), v in sorted(stat.by.items())}
    # ticket v2-realisme/19d : rendement par tranche de 15 minutes, par poste et par Stamina
    postes = tuple(sorted(p for p in c.km if p != "tous"))
    out["rendement par tranche de 15 min"] = {
        key: (round(v, 4) if isinstance(v, float) else v) for key, v in minute_report(c.minutes, postes).items()}
    out["rendement par joueur (tranches de 15 min)"] = player_report(c.minutes)  # dictionnaire imbriqué : hors « par match"
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=20, help="avec --profil : nombre pair (affiche jouée deux fois)")
    parser.add_argument("--profil", default=None)
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--json", default=None)
    parser.add_argument("--pas", type=float, default=TICK_S, help="pas de calcul (s), par défaut celui du produit")
    parser.add_argument("--sans-plan", action="store_true", help="ticket v2-collectif/14 désactivé")
    parser.add_argument("--debut", type=int, default=0, help="indice du premier match (lots parallèles)")
    parser.add_argument("--sans-perception-defense", action="store_true",
                        help="ticket v2-realisme/08e désactivé : ligne et marquage lisent les vraies positions (A/B du 08f)")
    parser.add_argument("--sans-tenir", action="store_true", help="tickets v2-realisme/02f et 02g désactivés : tous les coéquipiers du porteur appellent")
    args = parser.parse_args(argv)
    if args.sans_tenir:
        cerveau.CALLER_CAP = {}
    result = report(run(args.matches, args.profil, tick_s=args.pas, plans=not args.sans_plan, start=args.debut,
                       defence_perception=not args.sans_perception_defense),
                    args.detail)
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{key} :")
            for sub, v in value.items():
                print(f"    {sub} : {v}")
        else:
            print(f"{key} : {round(value, 3) if isinstance(value, float) else value}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
