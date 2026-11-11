"""Rendement selon la minute (ticket v2-realisme/19d) : indicateurs du banc V2 découpés en tranches de 15 minutes de
temps de jeu écoulé, pour tous les joueurs de champ, par poste, par tranche de Stamina et par joueur. État des lieux de
ce que la fatigue change aujourd'hui, avant 12d, 12e et les tickets 20. Définitions : `docs/INDICATEURS_V2.md`,
section 23.

`MinuteProfile` est nourri par `v2_indicators.Collector` (course et position à chaque tick, passes, tacles, tirs,
buts, contrôles ratés du journal) ; chaque événement est attribué à son auteur, donc à ses groupes (poste, Stamina,
joueur). `minute_report` et `player_report` en tirent les chiffres publiés. Lecture seule : rien ici ne modifie le
jeu."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

TRANCHE_MIN = 15.0
TRANCHES = ("0-15", "15-30", "30-45", "45-60", "60-75", "75-90", "90 et plus")  # la dernière : temps additionnel
FIRST, LAST = TRANCHES[0], TRANCHES[5]  # première et dernière tranche réglementaire, comparées
STAMINA_BINS = (0, 40, 55, 70)  # bornes basses des tranches de Stamina (mêmes que Dribbling au 04c)
SPRINT_MPS, HIGH_INTENSITY_MPS = 25.0 / 3.6, 19.8 / 3.6  # mêmes seuils que le banc 01d
SPRINT_MIN_S = 1.0
ON_TARGET = ("but", "capté", "repoussé", "claqué")  # tir cadré jugé par le gardien (`v2_indicators.SAVE_OUTCOMES`)
BLOCKED = "contré"
ALL = "tous"
PLAYER_PREFIX = "joueur "
NINETY_S = 90.0 * 60.0
# Joueur retenu dans la synthèse par joueur : au moins 5 minutes jouées dans chacune des deux tranches comparées.
PLAYER_MIN_S = 5.0 * 60.0


def tranche(minute: float) -> str:
    """Tranche de 15 minutes de temps de jeu écoulé ; au-delà de 90 minutes, « 90 et plus »."""
    return TRANCHES[min(len(TRANCHES) - 1, int(max(0.0, minute) // TRANCHE_MIN))]


def stamina_band(stamina: float) -> str:
    lows = [b for b in STAMINA_BINS if stamina >= b]
    low = lows[-1] if lows else STAMINA_BINS[0]
    i = STAMINA_BINS.index(low)
    return f"Stamina {low}-{STAMINA_BINS[i + 1]}" if i + 1 < len(STAMINA_BINS) else f"Stamina {low} et plus"


def _ratio(a: float, b: float) -> float | None:
    return a / b if b else None


class MinuteProfile:
    """Sommes par tranche, sur tous les matchs. Course : `run[(tranche, groupe, mesure)]` ; événements :
    `events[(tranche, groupe, indicateur)]`. Le groupe est « tous », le poste, la tranche de Stamina ou « joueur <nom> » ;
    un événement sans auteur connu ne compte que dans « tous ». Les sprints sont comptés dans la tranche où ils
    commencent. `info` : poste et Stamina de chaque joueur vu."""

    def __init__(self) -> None:
        self.run: Counter = Counter()  # mesures : temps, distance, intense, sprint, sprints, sans ballon, profondeur
        self.events: Counter = Counter()
        self.info: dict[str, tuple[str, float]] = {}
        self.sprint_open: dict[str, tuple[float, str, tuple[str, ...]]] = {}  # joueur -> (durée, tranche, groupes)

    def groups(self, name: str | None) -> tuple[str, ...]:
        if name is None or name not in self.info:
            return (ALL,)
        poste, stamina = self.info[name]
        return ALL, poste, stamina_band(stamina), PLAYER_PREFIX + name

    def on_player(self, minute: float, name: str, poste: str, stamina: float, speed: float, dt: float,
                  depth: float | None = None) -> None:
        """Un joueur de champ à ce tick. `depth` : sa distance à son propre but (m) quand son équipe n'a pas le ballon,
        `None` sinon."""
        self.info[name] = (poste, stamina)
        sl, groups = tranche(minute), self.groups(name)
        for g in groups:
            self.run[(sl, g, "temps")] += dt
            self.run[(sl, g, "distance")] += speed * dt
            if speed > HIGH_INTENSITY_MPS:
                self.run[(sl, g, "intense")] += speed * dt
            if speed > SPRINT_MPS:
                self.run[(sl, g, "sprint")] += speed * dt
            if depth is not None:
                self.run[(sl, g, "sans ballon")] += dt
                self.run[(sl, g, "profondeur")] += depth * dt
        if speed > SPRINT_MPS:
            held, start, gs = self.sprint_open.get(name, (0.0, sl, groups))
            self.sprint_open[name] = (held + dt, start, gs)
        else:
            self._close_sprint(name)

    def _close_sprint(self, name: str) -> None:
        held, start, groups = self.sprint_open.pop(name, (0.0, "", ()))
        if held >= SPRINT_MIN_S - 1e-9:
            for g in groups:
                self.run[(start, g, "sprints")] += 1

    def count(self, minute: float, key: str, amount: float = 1.0, actor: str | None = None) -> None:
        sl = tranche(minute)
        for g in self.groups(actor):
            self.events[(sl, g, key)] += amount

    def on_shot(self, minute: float, outcome: str, actor: str | None = None) -> None:
        self.count(minute, "tirs", actor=actor)
        if outcome != BLOCKED:
            self.count(minute, "tirs non contrés", actor=actor)
            self.count(minute, "tirs cadrés", outcome in ON_TARGET, actor=actor)

    def on_goal(self, minute: float, scoring_team: str, on_pitch: list[tuple[str, str]]) -> None:
        """But : un but par match dans « tous » ; pour chaque joueur de champ présent (`(nom, équipe)`), but marqué ou
        encaissé par son équipe pendant qu'il est sur le terrain."""
        sl = tranche(minute)
        self.events[(sl, ALL, "buts")] += 1
        for name, team in on_pitch:
            key = "buts marqués" if team == scoring_team else "buts encaissés"
            for g in self.groups(name):
                self.events[(sl, g, key)] += 1

    def end_match(self, passes: list[dict]) -> None:
        """Fin de match : sprints encore ouverts, passes du journal du banc (`t` en s, `done` : reçue par le visé)."""
        for name in list(self.sprint_open):
            self._close_sprint(name)
        for p in passes:
            minute = p["t"] / 60.0
            self.count(minute, "passes", actor=p.get("passer"))
            self.count(minute, "passes réussies", p["done"], actor=p.get("passer"))
            self.count(minute, "passes visées", actor=p.get("target"))
        self.events[(FIRST, ALL, "matchs")] += 1

    def merge(self, run: dict, events: dict, info: dict) -> None:
        """Fusion d'un autre profil (série parallèle, `scripts/bench_series.py`)."""
        self.run.update(run)
        self.events.update(events)
        self.info.update(info)


def group_metrics(profile: MinuteProfile, sl: str, g: str) -> dict[str, float | None]:
    """Indicateurs d'un groupe dans une tranche. Course par joueur et par minute ; technique en parts ; tirs et buts
    pour 90 minutes jouées (temps cumulé des joueurs du groupe) ; position moyenne sans ballon depuis son but."""
    r, e = profile.run, profile.events
    t = r[(sl, g, "temps")]
    if not t:
        return {}
    minutes = t / 60.0
    per90 = NINETY_S / t
    return {
        "distance (m/min)": r[(sl, g, "distance")] / minutes,
        "au-dessus de 19,8 km/h (m/min)": r[(sl, g, "intense")] / minutes,
        "au-dessus de 25 km/h (m/min)": r[(sl, g, "sprint")] / minutes,
        "sprints par 15 min": r[(sl, g, "sprints")] * TRANCHE_MIN / minutes,
        "passes réussies (part)": _ratio(e[(sl, g, "passes réussies")], e[(sl, g, "passes")]),
        "contrôles ratés pour 100 passes visées": (
            None if not e[(sl, g, "passes visées")] else 100.0 * e[(sl, g, "contrôles ratés")] / e[(sl, g, "passes visées")]),
        "tirs cadrés (part des non contrés)": _ratio(e[(sl, g, "tirs cadrés")], e[(sl, g, "tirs non contrés")]),
        "tacles gagnés (part)": _ratio(e[(sl, g, "tacles gagnés")], e[(sl, g, "tacles")]),
        "position sans ballon (m depuis son but)": _ratio(r[(sl, g, "profondeur")], r[(sl, g, "sans ballon")]),
        "tirs pour 90 min": e[(sl, g, "tirs")] * per90,
        "buts personnels pour 90 min": e[(sl, g, "buts personnels")] * per90,
        "buts marqués par l'équipe pour 90 min": e[(sl, g, "buts marqués")] * per90,
        "buts encaissés par l'équipe pour 90 min": e[(sl, g, "buts encaissés")] * per90,
    }


# Indicateurs comparés par un rapport (dernière / première tranche) ; les autres le sont par une différence.
RATIO_METRICS = ("distance (m/min)", "au-dessus de 19,8 km/h (m/min)", "au-dessus de 25 km/h (m/min)",
                 "sprints par 15 min")


def _compare(first: dict, last: dict) -> dict[str, float]:
    out = {}
    for k, a in first.items():
        b = last.get(k)
        if a is None or b is None:
            continue
        if k in RATIO_METRICS:
            if a:
                out[f"{k}, {LAST} / {FIRST}"] = b / a
        else:
            out[f"{k}, {LAST} - {FIRST}"] = b - a
    return out


def minute_report(profile: MinuteProfile, block_height: dict[str, float] | None = None,
                  postes: tuple[str, ...] = ()) -> dict[str, float | None]:
    """Chiffres publiés (section 23). D'abord, par tranche, tous les joueurs de champ (clés historiques : course, parts,
    sprints, technique, duels, hauteur du bloc d'équipe, tirs et buts par match). Puis, pour chaque poste et chaque
    tranche de Stamina, tous les indicateurs de `group_metrics` à chaque tranche et la comparaison 0-15 / 75-90."""
    r, e = profile.run, profile.events
    matches = max(1.0, e[(FIRST, ALL, "matchs")])
    out: dict[str, float | None] = {}
    for sl in TRANCHES:
        t = r[(sl, ALL, "temps")]
        if not t and not any(key[0] == sl for key in e):
            continue  # tranche non jouée (pas de temps additionnel, par exemple)
        if t:
            minutes = t / 60.0
            out[f"{sl} : distance par joueur (m/min)"] = r[(sl, ALL, "distance")] / minutes
            out[f"{sl} : distance au-dessus de 19,8 km/h (part)"] = _ratio(r[(sl, ALL, "intense")],
                                                                          r[(sl, ALL, "distance")])
            out[f"{sl} : distance au-dessus de 25 km/h (part)"] = _ratio(r[(sl, ALL, "sprint")], r[(sl, ALL, "distance")])
            out[f"{sl} : sprints par joueur et par 15 min"] = r[(sl, ALL, "sprints")] * TRANCHE_MIN / minutes
            out[f"{sl} : position sans ballon (m depuis son but)"] = _ratio(r[(sl, ALL, "profondeur")],
                                                                           r[(sl, ALL, "sans ballon")])
        out[f"{sl} : passes réussies (part)"] = _ratio(e[(sl, ALL, "passes réussies")], e[(sl, ALL, "passes")])
        out[f"{sl} : contrôles ratés pour 100 passes"] = (
            None if not e[(sl, ALL, "passes")] else 100.0 * e[(sl, ALL, "contrôles ratés")] / e[(sl, ALL, "passes")])
        out[f"{sl} : tirs cadrés (part des non contrés)"] = _ratio(e[(sl, ALL, "tirs cadrés")],
                                                                  e[(sl, ALL, "tirs non contrés")])
        out[f"{sl} : tacles gagnés (part)"] = _ratio(e[(sl, ALL, "tacles gagnés")], e[(sl, ALL, "tacles")])
        out[f"{sl} : tirs par match"] = e[(sl, ALL, "tirs")] / matches
        out[f"{sl} : buts par match"] = e[(sl, ALL, "buts")] / matches
        if block_height and sl in block_height:
            out[f"{sl} : hauteur du bloc sans ballon (m)"] = block_height[sl]
    for g in list(postes) + [stamina_band(b) for b in STAMINA_BINS]:
        if not r[(FIRST, g, "temps")] or not r[(LAST, g, "temps")]:
            continue
        for sl in TRANCHES:
            for k, v in group_metrics(profile, sl, g).items():
                out[f"{g} : {sl} : {k}"] = v
        for k, v in _compare(group_metrics(profile, FIRST, g), group_metrics(profile, LAST, g)).items():
            out[f"{g} : {k}"] = v
    return out


def _quantiles(values: list[float]) -> dict[str, float]:
    values = sorted(values)
    if len(values) < 2:
        return {"médiane": values[0]} if values else {}
    deciles = statistics.quantiles(values, n=10, method="inclusive")
    return {"1er décile": deciles[0], "médiane": statistics.median(values), "9e décile": deciles[-1]}


def player_report(profile: MinuteProfile) -> dict:
    """Par joueur : poste, Stamina et indicateurs de chaque tranche jouée (« joueurs »), puis la synthèse des joueurs
    qui ont joué au moins `PLAYER_MIN_S` dans les tranches 0-15 et 75-90 : déciles de la comparaison de chaque
    indicateur (« synthèse »)."""
    players, spread = {}, defaultdict(list)
    for name in sorted(profile.info):
        g = PLAYER_PREFIX + name
        poste, stamina = profile.info[name]
        tranches = {sl: m for sl in TRANCHES if (m := group_metrics(profile, sl, g))}
        players[name] = {"poste": poste, "Stamina": stamina, "tranches": tranches}
        r = profile.run
        if r[(FIRST, g, "temps")] >= PLAYER_MIN_S and r[(LAST, g, "temps")] >= PLAYER_MIN_S:
            compared = _compare(tranches[FIRST], tranches[LAST])
            players[name]["comparaison"] = compared
            for k, v in compared.items():
                spread[k].append(v)
    summary = {k: {"joueurs": len(v), **_quantiles(v)} for k, v in sorted(spread.items())}
    return {"joueurs": players, "synthèse": summary}


def block_height_by_tranche(stat) -> dict[str, float]:
    """Hauteur moyenne du bloc par tranche, lue dans le découpage « minute » du banc (`Stat.by`, clés `0-15 min`...)."""
    acc: dict[str, list[float]] = defaultdict(list)
    for (kind, label), values in stat.by.items():
        if kind == "minute":
            acc[tranche(float(label.split("-")[0]))].extend(values)
    return {sl: sum(v) / len(v) for sl, v in acc.items() if v}
