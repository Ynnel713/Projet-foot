"""Indicateurs de mesure du moteur V2 (ticket v2-collectif/01). Définitions, unités et sources :
`docs/INDICATEURS_V2.md`. Deux parties :

- fonctions pures sur une image du match (positions à un instant) : géométrie d'équipe, lignes,
  compacité, supériorité locale, défense préventive, couverture du presseur, solutions de passe ;
- `Collector`, nourri tick par tick (`simulate_match(observer=...)`) et par les événements du moteur
  (passes, tirs, tacles, choix du porteur), qui accumule les indicateurs classiques et tactiques,
  découpés par zone du ballon, score et tranche de 15 minutes.

Lecture seule : rien ici ne modifie le jeu."""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from v2engine.cerveau import OPPONENT_GOAL
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, in_penalty_area
from v2engine.movement import PlayerState
from v2engine.offside import offside_line
from v2engine.possession import pass_success_probability
from v2engine.situation import POSSESSION_INSTALLEE, SituationTracker

KMH = 1.0 / 3.6
# Seuils de mesure (docs/INDICATEURS_V2.md, section « Seuils de mesure ») -- ils ne changent pas le jeu.
OPTION_RANGE_M = 40.0
OPTION_PROBABILITY = 0.7  # même seuil que le jeu (`off_ball.OPEN_LANE_PROBABILITY`, ticket 06)
EASY_OPTION_PROBABILITY = 0.8  # solution « facile » (ticket 08, validé le 31/10/2026) : le seuil de 0,5 ne voit pas la pression
PRESS_RADIUS_M = 3.0
COVER_BEHIND_M, COVER_AHEAD_M, COVER_HALF_WIDTH_M = 3.0, 9.0, 4.0
LOCAL_RADIUS_M = 10.0
LOCAL_DEFENDERS = 5
RUN_SPEED_MPS, RUN_MIN_S, RUN_SAME_ZONE_M = 15.0 * KMH, 0.7, 5.0
ON_THE_LINE_M, NEAR_THE_LINE_M = 2.0, 5.0  # appel dans le dos ; jeu sur la ligne à la passe (ticket 16)
TRANSITION_LOSS_S = 5.0
COUNTER_WINDOW_S = 15.0
RETREAT_SPEED_MPS, RETREAT_WINDOW_S = 1.0, 10.0
# Repli (ticket v2-collectif/10) : vitesse vers son but, 1,5 s après la perte, des joueurs qui étaient devant le ballon
CHOICE_AFTER_S = 1.5
RECOVERY_CLASSES = ((5.0, "0-5 s"), (12.0, "5-12 s"), (15.0, "12-15 s"), (math.inf, "plus de 15 s"))
LONG_PASS_M = 32.0
SHOT_CLOSE_RANGE_M = 16.0  # tir « de près » : demande du propriétaire (28/10/2026) pour mesurer l'exposition du gardien
FREE_PASSER_M = 9.0  # porteur libre : défenseur le plus proche à 9 m ou plus (pressé : PRESS_RADIUS_M), ticket 05
SPRINT_MPS, HIGH_INTENSITY_MPS = 25.0 * KMH, 19.8 * KMH
SPRINT_MIN_S = 1.0  # sprint : au-dessus de SPRINT_MPS pendant au moins 1 s (ticket v2-realisme/01d)
MATCH_90_S = 90 * 60.0  # appels ramenés à 90 min, comme la source (CIES n° 88, ticket v2-realisme/01d)
CROWDED_M = 5.0  # regroupement : coéquipier à moins de 5 m, hors duel (ticket 06)
# Combinaisons (ticket v2-collectif/14, validé le 02/11/2026) : passe « sans gain » sous 5 m vers le but ; passe qui
# fait avancer : elle casse une ligne adverse ou gagne au moins 10 m ; retour au passeur dans les 3 s ; une-deux si le
# passeur a avancé d'au moins 5 m entre sa passe et le retour ; triangle : deux coéquipiers à 30 m au plus, trois
# passes toutes au moins à 0,7 et un angle de 20 à 160 degrés au porteur.
NO_GAIN_M = 5.0
PROGRESSIVE_GAIN_M = 10.0
RETURN_WINDOW_S = 3.0
ONE_TWO_MIN_GAIN_M = 5.0
TRIANGLE_RANGE_M = 30.0
TRIANGLE_ANGLES_DEG = (20.0, 160.0)


def forward(team: str) -> float:
    """+1 si l'équipe attaque vers x croissant (domicile), -1 sinon."""
    return 1.0 if team == "home" else -1.0


def progress(team: str, x: float) -> float:
    """Distance (m) depuis le but de `team` : 0 sur sa ligne de but, PITCH_LENGTH_M sur la ligne adverse."""
    return x if team == "home" else PITCH_LENGTH_M - x


def zone(team: str, x: float) -> str:
    third = progress(team, x) / (PITCH_LENGTH_M / 3.0)
    return ("tiers défensif", "tiers médian", "tiers offensif")[min(2, max(0, int(third)))]


def outfield(players: Sequence[PlayerState], team: str) -> list[PlayerState]:
    return [p for p in players if p.team == team and p.poste != "GK"]


# --- Géométrie d'une équipe ---------------------------------------------------------------------------------------
def length_width(points: Sequence[Vec2]) -> tuple[float, float]:
    xs, ys = [p.x for p in points], [p.y for p in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def hull_area(points: Sequence[Vec2]) -> float:
    """Aire (m²) de l'enveloppe convexe (chaîne monotone d'Andrew, puis formule du lacet)."""
    pts = sorted(set((p.x, p.y) for p in points))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return abs(sum(hull[i][0] * hull[i - 1][1] - hull[i - 1][0] * hull[i][1] for i in range(len(hull)))) / 2.0


def stretch_index(points: Sequence[Vec2]) -> float:
    """Distance moyenne (m) des joueurs au centre de l'équipe."""
    cx, cy = statistics.fmean(p.x for p in points), statistics.fmean(p.y for p in points)
    return statistics.fmean(math.hypot(p.x - cx, p.y - cy) for p in points)


def lines(team: str, points: Sequence[Vec2]) -> list[list[float]]:
    """Trois lignes (défense, milieu, attaque) : progressions triées, coupées aux deux plus grands écarts."""
    xs = sorted(progress(team, p.x) for p in points)
    if len(xs) < 3:
        return [xs]
    gaps = sorted(range(1, len(xs)), key=lambda i: xs[i] - xs[i - 1], reverse=True)[:2]
    a, b = sorted(gaps)
    return [xs[:a], xs[a:b], xs[b:]]


def line_gaps(team: str, points: Sequence[Vec2]) -> tuple[float, float] | None:
    """(défense-milieu, milieu-attaque) en m, entre les positions moyennes des lignes."""
    ls = lines(team, points)
    if len(ls) != 3:
        return None
    means = [statistics.fmean(line) for line in ls]
    return means[1] - means[0], means[2] - means[1]


def breaks_a_line(team: str, start: Vec2, end: Vec2, players: Sequence[PlayerState]) -> bool:
    """Passe qui casse une ligne : la position moyenne d'une ligne adverse (`lines`) est entre le passeur et la cible."""
    rivals = [p.position for p in outfield(players, "away" if team == "home" else "home")]
    a, b = progress(team, start.x), progress(team, end.x)
    return any(a < statistics.fmean(line) < b for line in lines(team, rivals) if line)


def triangle(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> bool:
    """Au moins un triangle de passes autour du porteur (définition du ticket v2-collectif/14)."""
    near = [m for m in mates if m is not holder and holder.position.distance_to(m.position) <= TRIANGLE_RANGE_M
            and pass_success_probability(holder, m, opponents) >= OPTION_PROBABILITY]
    low, high = TRIANGLE_ANGLES_DEG
    for i, a in enumerate(near):
        for b in near[i + 1:]:
            u, v = a.position - holder.position, b.position - holder.position
            cos = (u.x * v.x + u.y * v.y) / max(1e-9, u.length() * v.length())
            if low <= math.degrees(math.acos(max(-1.0, min(1.0, cos)))) <= high \
                    and pass_success_probability(a, b, opponents) >= OPTION_PROBABILITY:
                return True
    return False


def is_deep_pass(team: str, target: Vec2, players: Sequence[PlayerState]) -> bool:
    """Passe en profondeur : sa cible est plus près du but adverse que le dernier défenseur de champ adverse."""
    rivals = outfield(players, "away" if team == "home" else "home")
    last = max((progress(team, p.position.x) for p in rivals), default=None)
    return last is not None and progress(team, target.x) > last


def opponent_goal_center(team: str) -> Vec2:
    """Centre du but que `team` attaque (domicile : x = 105), à la même source que le moteur (`cerveau`)."""
    return OPPONENT_GOAL[team]


def slope(pairs: Sequence[tuple[float, float]]) -> float:
    """Pente de la droite des moindres carrés de y en fonction de x (0 si x ne varie pas)."""
    xs, ys = [a for a, _ in pairs], [b for _, b in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    var = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var if var > 0 else 0.0


def block_height(team: str, points: Sequence[Vec2]) -> float:
    """Position moyenne (m) de la ligne défensive depuis son propre but."""
    return statistics.fmean(lines(team, points)[0])


# --- Autour du ballon ---------------------------------------------------------------------------------------------
def local_compactness(ball: Vec2, defenders: Sequence[PlayerState]) -> float:
    """Distance moyenne au ballon (m) des LOCAL_DEFENDERS défenseurs les plus proches."""
    d = sorted(p.position.distance_to(ball) for p in defenders)[:LOCAL_DEFENDERS]
    return statistics.fmean(d) if d else 0.0


def local_superiority(ball: Vec2, defenders: Sequence[PlayerState], attackers: Sequence[PlayerState]) -> int:
    """Défenseurs moins attaquants à moins de LOCAL_RADIUS_M du ballon."""
    near = lambda ps: sum(1 for p in ps if p.position.distance_to(ball) < LOCAL_RADIUS_M)
    return near(defenders) - near(attackers)


def preventive(team: str, ball: Vec2, own: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> tuple[int, int]:
    """(joueurs de `team` derrière le ballon, adversaires dans cette zone) -- défense préventive."""
    line = progress(team, ball.x)
    behind = sum(1 for p in own if progress(team, p.position.x) < line)
    threats = sum(1 for p in opponents if progress(team, p.position.x) < line)
    return behind, threats


def crowded(own: Sequence[PlayerState], opponents: Sequence[PlayerState], holder: str | None = None) -> float | None:
    """Part des joueurs de `own` hors duel (aucun adversaire à moins de PRESS_RADIUS_M) qui ont un coéquipier à
    moins de CROWDED_M -- regroupement (ticket 06). Le porteur `holder` est exclu : se montrer près de lui est du
    soutien, pas du regroupement (critère validé le 31/10/2026). None si tous sont en duel."""
    own = [p for p in own if p.name != holder]
    free = [p for p in own if all(p.position.distance_to(o.position) >= PRESS_RADIUS_M for o in opponents)]
    if not free:
        return None
    return sum(1 for p in free if any(m is not p and p.position.distance_to(m.position) < CROWDED_M for m in own)) / len(free)


def in_cover_zone(holder: Vec2, defended_goal: Vec2, point: Vec2) -> bool:
    """Ellipse de couverture orientée du porteur vers le but défendu : de COVER_BEHIND_M derrière le
    porteur à COVER_AHEAD_M devant lui (côté but), demi-largeur COVER_HALF_WIDTH_M."""
    axis = (defended_goal - holder).normalized()
    rel = point - holder
    along = rel.x * axis.x + rel.y * axis.y
    across = -rel.x * axis.y + rel.y * axis.x
    centre = (COVER_AHEAD_M - COVER_BEHIND_M) / 2.0
    semi = (COVER_AHEAD_M + COVER_BEHIND_M) / 2.0
    return ((along - centre) / semi) ** 2 + (across / COVER_HALF_WIDTH_M) ** 2 <= 1.0


def pressing_cover(holder: PlayerState, defenders: Sequence[PlayerState], defended_goal: Vec2) -> bool | None:
    """None si personne ne presse le porteur ; sinon, un second défenseur est-il dans la zone de couverture ?"""
    pressers = [d for d in defenders if d.position.distance_to(holder.position) < PRESS_RADIUS_M]
    if not pressers:
        return None
    presser = min(pressers, key=lambda d: d.position.distance_to(holder.position))
    return any(d is not presser and in_cover_zone(holder.position, defended_goal, d.position) for d in defenders)


def pass_chances(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> list[float]:
    """Chance de réussite (modèle du moteur) de la passe vers chaque coéquipier à moins de OPTION_RANGE_M."""
    return [pass_success_probability(holder, m, opponents) for m in mates
            if m is not holder and holder.position.distance_to(m.position) <= OPTION_RANGE_M]


def open_options(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState],
                 threshold: float = OPTION_PROBABILITY) -> int:
    """Coéquipiers à moins de OPTION_RANGE_M dont la passe arriverait (modèle du moteur) avec au moins `threshold`."""
    return sum(1 for chance in pass_chances(holder, mates, opponents) if chance >= threshold)


# --- Accumulation -------------------------------------------------------------------------------------------------
@dataclass
class Stat:
    """Valeurs d'un indicateur, avec leur découpage (zone, score, minute)."""
    values: list[float] = field(default_factory=list)
    by: dict[tuple[str, str], list[float]] = field(default_factory=lambda: defaultdict(list))

    def add(self, value: float, **keys: str) -> None:
        self.values.append(value)
        for k, v in keys.items():
            self.by[(k, v)].append(value)


def _score_state(goals: Counter, team: str) -> str:
    other = "away" if team == "home" else "home"
    return "mène" if goals[team] > goals[other] else ("menée" if goals[team] < goals[other] else "égalité")


@dataclass
class _Run:
    start_s: float
    last: Vec2


class Collector:
    """Accumule les indicateurs d'un ou plusieurs matchs. Brancher `on_tick` sur `simulate_match(observer=...)`
    et les `on_*` sur les fonctions du moteur (voir `scripts/measure_v2.py`). Appeler `end_match()` après
    chaque match."""

    def __init__(self, geometry_every_s: float = 1.0) -> None:
        self.every = geometry_every_s
        self.stats: dict[str, Stat] = defaultdict(Stat)
        self.count: Counter = Counter()
        self.km: dict[str, list[float]] = defaultdict(list)
        self.matches = 0
        self._reset_match()

    def _reset_match(self) -> None:
        self.goals: Counter = Counter()
        self.situations = SituationTracker()  # même lecture que le moteur (ticket v2-collectif/03)
        self.dist: Counter = Counter()
        self.hi_by: Counter = Counter()  # course au-dessus de 19,8 km/h par joueur (m)
        self.levels: dict[str, str] = {}  # joueur -> niveau du profil testé ("haut"/"bas"), voir measure_v2
        self.poste: dict[str, str] = {}
        self.sprint = self.hi = self.total = 0.0
        self.hi_time = self.sprint_time = self.time = 0.0
        self.sprint_run: Counter = Counter()  # durée de la course en cours au-dessus de SPRINT_MPS, par joueur (s)
        self.sprints: Counter = Counter()  # sprints d'au moins SPRINT_MIN_S, par joueur (ticket v2-realisme/01d)
        self.hi_first = self.hi_last = 0.0
        self.holder: str | None = None
        self.holder_since = 0.0
        self.team: str | None = None  # équipe en possession (dernier porteur)
        self.team_since = 0.0
        self.team_passes = 0
        self.last_sample = -math.inf
        self.pending_pass: tuple[str, str, float, bool] | None = None  # (équipe, receveur visé, longueur, en profondeur)
        self.players: list[PlayerState] = []  # joueurs au dernier tick (lecture des passes en profondeur)
        self.recoveries: list[tuple[float, str, str, Vec2, bool]] = []  # (instant, équipe, zone, lieu, close)
        self.relost: list[tuple[str, bool]] = []  # par récupération : (zone, reperdu en moins de 5 s)
        self.retreat_done: list[dict] = []
        self.length_out: dict[str, list[float]] = defaultdict(list)  # longueur sans ballon, par équipe
        self.loss_open: dict[str, float] = {}  # équipe qui a perdu -> instant de la perte
        self.retreat: list[dict] = []
        self.runs: dict[str, _Run] = {}
        self.run_log: list[tuple[str, float, float, Vec2]] = []  # (joueur, début, fin, position finale)
        self.deep_runs: Counter = Counter()  # appels finis à ON_THE_LINE_M ou moins de la ligne, par joueur (16)
        self.follow: dict[str, list[tuple[float, float]]] = defaultdict(list)  # axe -> (ballon, centre d'équipe)
        self.profile_gaps: dict[str, list[float]] = defaultdict(list)  # niveau -> distances défense-milieu
        self.press_open: tuple[str, float] | None = None  # pressing en cours (ticket 08) : (équipe qui presse, début)
        self.now = 0.0  # instant du dernier tick
        self.planned: str | None = None  # suite prévue par la dernière décision (plan de passe, ticket 14)
        # passes du match (ticket 14) : instant, équipe, passeur, cible, gain (m), avance, suite prévue, réussie
        self.pass_log: list[dict] = []

    # --- événements du moteur ---
    def on_pass(self, passer: PlayerState, target: PlayerState) -> None:
        length = passer.position.distance_to(target.position)
        self.count["passes"] += 1
        self.count["passes longues"] += length > LONG_PASS_M
        deep = is_deep_pass(passer.team, target.position, self.players)
        self.count["passes en profondeur"] += deep
        self.pending_pass = (passer.team, target.name, length, deep)
        self._line_at_pass(passer)
        self.team_passes += 1
        goal = opponent_goal_center(passer.team)
        gain = passer.position.distance_to(goal) - target.position.distance_to(goal)
        self.pass_log.append({"t": self.now, "team": passer.team, "passer": passer.name, "target": target.name,
                              "gain": gain, "start": passer.position, "end": target.position,
                              "progressive": gain >= PROGRESSIVE_GAIN_M
                              or breaks_a_line(passer.team, passer.position, target.position, self.players),
                              "follow": self.planned, "done": False})

    def _line_at_pass(self, passer: PlayerState) -> None:
        """Jeu sur la ligne (ticket 16) : distance de l'attaquant le plus avancé à la ligne du hors-jeu, à la passe."""
        line = offside_line(passer.team, passer.position, [p for p in self.players if p.team != passer.team])
        mates = [progress(passer.team, p.position.x) for p in self.players
                 if p.team == passer.team and p.poste != "GK" and p.name != passer.name]
        if line is None or not mates:
            return
        gap = line - max(mates)
        self.stats["attaquant le plus avancé à la passe : distance à la ligne (m)"].add(gap)
        self.stats["attaquant le plus avancé à la passe : 2 m ou moins de la ligne (part)"].add(1.0 if gap <= ON_THE_LINE_M else 0.0)
        self.stats["attaquant le plus avancé à la passe : 5 m ou moins de la ligne (part)"].add(1.0 if gap <= NEAR_THE_LINE_M else 0.0)

    def on_shot(self, shooter: PlayerState, now_s: float) -> None:
        self.count["tirs"] += 1
        distance = shooter.position.distance_to(opponent_goal_center(shooter.team))
        self.count["tirs de près"] += distance <= SHOT_CLOSE_RANGE_M
        last = self.recoveries[-1] if self.recoveries else None
        if last is not None and last[1] == shooter.team and now_s - last[0] <= COUNTER_WINDOW_S:
            camp = "camp adverse" if progress(shooter.team, last[3].x) > PITCH_LENGTH_M / 2.0 else "propre camp"
            self.count["tirs de contre, récupération " + camp] += 1

    def on_trigger(self) -> None:
        self.count["pressings d'équipe déclenchés"] += 1

    def on_tackle(self) -> None:
        self.count["tacles"] += 1

    def on_choice(self, kind: str, follow: str | None = None, plan: str | None = None) -> None:
        self.count["choix " + kind] += 1
        self.planned = follow
        if plan is not None:  # sort du plan reçu (ticket 14)
            self.count["plans reçus"] += 1
            self.count["plan " + plan] += 1
        holder = next((p for p in self.players if p.name == self.holder), None)
        if holder is not None:  # triangles autour du porteur, à chaque décision (ticket 14)
            mates = [p for p in self.players if p.team == holder.team]
            rivals = [p for p in self.players if p.team != holder.team]
            self.stats["décisions avec au moins un triangle (part)"].add(1.0 if triangle(holder, mates, rivals) else 0.0)

    def on_balance(self, player: PlayerState, stays: bool) -> None:
        """Défenseur d'équilibre dont l'appel le mènerait devant le ballon : y va-t-il quand même ? (ticket 06)"""
        key = "équilibre : appels devant le ballon maintenus (part)"
        level = self.levels.get(player.name)
        self.stats[f"profil {level} : {key}" if level else key].add(0.0 if stays else 1.0)

    def on_offside(self, event) -> None:
        """Hors-jeu sifflé (ticket v2-collectif/23) ; `event` : `v2engine.trace.OffsideEvent`."""
        self.count["hors-jeu"] += 1
        self.count["hors-jeu " + event.team] += 1

    def on_restart(self, event) -> None:
        """Remise en jeu jouée (ticket v2-collectif/29) ; `event` : `v2engine.trace.RestartEvent`."""
        self.count["remises : " + event.kind] += 1
        self.count["remises jouées long : " + event.kind] += event.long
        self.count["temps de ballon mort (s)"] += event.dead_s
        if event.kind == "coup franc" and _final_third(event.team, event.x):
            self.count["coups francs du dernier tiers"] += 1
            self.count["coups francs du dernier tiers frappés"] += event.shot

    def on_shot_event(self, event) -> None:
        """Tir tracé avec son issue et son origine (ticket v2-collectif/28b) ; `event` : `v2engine.trace.ShotEvent`."""
        self.count["tirs tracés"] += 1
        self.count["tirs : " + event.outcome] += 1
        self.count["tirs, origine : " + event.origin] += 1
        self.count["qualité des occasions (somme)"] += event.quality
        if event.outcome == "but" and in_penalty_area(event.team, Vec2(event.x, event.y)):
            self.count["buts dans la surface"] += 1

    def on_foul(self, event) -> None:
        """Faute (ticket v2-collectif/30) ; `event` : `v2engine.trace.FoulEvent`."""
        self.count["fautes"] += 1
        self.count["fautes : " + event.outcome] += 1
        self.count["fautes : gravité " + event.severity] += 1
        level = self.levels.get(event.player)
        if level:
            self.count[f"profil {level} : fautes"] += 1

    # --- tick ---
    def on_tick(self, now_s: float, players: list[PlayerState], ball, scoring_team: str | None, dt: float = 0.1) -> None:
        minute = now_s / 60.0
        self.now = now_s
        by_name = {p.name: p for p in players}
        self.players = players
        self._speeds(players, minute, dt)
        if scoring_team is not None:  # but : la possession se clôt, l'engagement n'est pas une perte de balle
            self.goals[scoring_team] += 1
            self.count["buts"] += 1
            self._close_possession(now_s)
        current = self.situations.update(now_s, ball, players, scoring_team)
        for team, situation in current.items():
            self.count["temps en " + situation] += dt
        self._possession(now_s, ball, by_name)
        if self.team is not None:
            self._runs(now_s, players, ball)
        self._retreat(now_s, players, ball)
        self._pressing(now_s, players, ball, by_name, dt)
        if now_s - self.last_sample >= self.every - 1e-9:
            self.last_sample = now_s
            self._geometry(now_s, players, ball, by_name)

    def _speeds(self, players, minute, dt):
        for p in players:
            self.poste[p.name] = p.poste
            if p.poste == "GK":
                continue
            v = p.velocity.length()
            self.dist[p.name] += v * dt
            self.total += v * dt
            self.time += dt
            if v > SPRINT_MPS:
                self.sprint += v * dt
                self.sprint_time += dt
                self.sprint_run[p.name] += dt
            else:
                self._close_sprint(p.name)
            if v > HIGH_INTENSITY_MPS:
                self.hi += v * dt
                self.hi_by[p.name] += v * dt
                self.hi_time += dt
                if minute < 15.0:
                    self.hi_first += v * dt
                elif minute >= 75.0:
                    self.hi_last += v * dt

    def _close_sprint(self, name: str) -> None:
        if self.sprint_run.pop(name, 0.0) >= SPRINT_MIN_S - 1e-9:
            self.sprints[name] += 1

    def _close_possession(self, now_s):
        if self.holder is not None:
            self.stats["temps par possession de joueur (s)"].add(now_s - self.holder_since)
        if self.team is not None:
            self.stats["possession d'équipe (s)"].add(now_s - self.team_since)
            self.stats["passes par possession"].add(self.team_passes)
            self._close_recovery(now_s, relost=False)
        self.holder = self.team = self.pending_pass = None
        self.loss_open.clear()
        self.retreat_done.extend(self.retreat)
        self.retreat = []

    def _close_recovery(self, now_s, relost: bool):
        """Clôt la dernière récupération de l'équipe en possession : reperdue en moins de 5 s ou non."""
        if self.recoveries and self.recoveries[-1][1] == self.team and not self.recoveries[-1][4]:
            t, team, rz, where, _ = self.recoveries[-1]
            self.recoveries[-1] = (t, team, rz, where, True)
            self.relost.append((rz, relost and now_s - t < TRANSITION_LOSS_S))

    def _possession(self, now_s, ball, by_name):
        holder = ball.holder
        if holder == self.holder:
            return
        if self.holder is not None:
            self.stats["temps par possession de joueur (s)"].add(now_s - self.holder_since)
        self.holder, self.holder_since = holder, now_s
        if holder is None:
            return
        team = by_name[holder].team
        if self.pending_pass is not None:
            pass_team, target, length, deep = self.pending_pass
            self.count["passes en profondeur réussies"] += team == pass_team and deep
            self.count["passes réussies"] += team == pass_team
            self.count["passes longues réussies"] += team == pass_team and length > LONG_PASS_M
            self.count["passes chez l'adversaire"] += team != pass_team
            self.count["receveur visé"] += holder == target
            if holder == target and self.pass_log:
                self.pass_log[-1]["done"] = True
            self.pending_pass = None
        if team == self.team:
            return
        if self.team is not None:  # changement d'équipe en possession : perte pour self.team
            self.stats["possession d'équipe (s)"].add(now_s - self.team_since)
            self.stats["passes par possession"].add(self.team_passes)
            lost = self.team
            z = zone(team, by_name[holder].position.x)
            self._close_recovery(now_s, relost=True)
            self.recoveries.append((now_s, team, z, by_name[holder].position, False))
            if team in self.loss_open:  # l'équipe qui récupère avait perdu le ballon : temps de récupération
                waited = now_s - self.loss_open.pop(team)
                label = next(name for limit, name in RECOVERY_CLASSES if waited < limit)
                self.count["récupération " + label] += 1
                self.count["récupérations"] += 1
            self.loss_open[lost] = now_s
            self.retreat.append({"team": lost, "start": now_s, "latency": None, "speeds": [], "lengths": [],
                                 "behind": None, "length0": None, "choice": None})
            self.count["pertes de balle"] += 1
        self.team, self.team_since, self.team_passes = team, now_s, 0

    def _runs(self, now_s, players, ball):
        for p in players:
            if p.name == ball.holder and p.name in self.runs:  # appel conclu par la réception : il compte
                run = self.runs.pop(p.name)
                if now_s - run.start_s >= RUN_MIN_S:
                    self.run_log.append((p.name, run.start_s, now_s, p.position))
                    self._deep_run(p.name, p.team, p.position, players, ball)
                continue
            if p.team != self.team or p.poste == "GK" or p.name == ball.holder:
                self.runs.pop(p.name, None)  # ponytail: appel interrompu par une perte de balle, non compté
                continue
            if p.velocity.length() > RUN_SPEED_MPS:
                run = self.runs.setdefault(p.name, _Run(now_s, p.position))
                run.last = p.position
            elif p.name in self.runs:
                run = self.runs.pop(p.name)
                if now_s - run.start_s >= RUN_MIN_S and self._creates_option(p, players, ball):
                    self.run_log.append((p.name, run.start_s, now_s, run.last))
                    self._deep_run(p.name, p.team, run.last, players, ball)

    def _deep_run(self, name: str, team: str, end: Vec2, players, ball) -> None:
        line = offside_line(team, ball.position, [p for p in players if p.team != team])
        if line is not None and progress(team, end.x) >= line - ON_THE_LINE_M:
            self.deep_runs[name] += 1

    def _creates_option(self, runner: PlayerState, players, ball) -> bool:
        """Un appel compte s'il crée une option de passe : receveur visé d'une passe en cours, ou solution
        ouverte pour le porteur à la fin de la course (même seuil que `open_options`)."""
        if ball.holder is None:
            return runner.name == ball.receiver
        holder = next((p for p in players if p.name == ball.holder), None)
        if holder is None or holder.team != runner.team:
            return False
        opponents = [p for p in players if p.team != runner.team]
        return (holder.position.distance_to(runner.position) <= OPTION_RANGE_M
                and pass_success_probability(holder, runner, opponents) >= OPTION_PROBABILITY)

    def _retreat(self, now_s, players, ball=None):
        """Repli après une perte, suivi RETREAT_WINDOW_S : latence, vitesse de recul, longueur d'équipe."""
        still = []
        for r in self.retreat:
            elapsed = now_s - r["start"]
            if elapsed > RETREAT_WINDOW_S or self.team == r["team"]:  # fenêtre finie ou ballon récupéré
                self.retreat_done.append(r)
                continue
            own = outfield(players, r["team"])
            back = -forward(r["team"]) * statistics.fmean(p.velocity.x for p in own)  # centre vers son but
            if r["latency"] is None and back > RETREAT_SPEED_MPS:
                r["latency"] = elapsed
            r["speeds"].append(back)
            length = length_width([p.position for p in own])[0]
            if r["length0"] is None:
                r["length0"] = length
            r["lengths"].append((elapsed, length))
            if r["choice"] is None and ball is not None:  # joueurs devant le ballon à la perte (ticket 10)
                r["choice"] = {p.name for p in own if forward(r["team"]) * (p.position.x - ball.position.x) > 0.0}
            elif r["choice"] and elapsed >= CHOICE_AFTER_S:
                self._retreat_speeds(r, own)
                r["choice"] = set()
            if r["behind"] is None and elapsed >= 1.0 and ball is not None:  # 1 s après la perte (au tick près)
                r["behind"], _ = preventive(r["team"], ball.position, own, ())
                self.stats["4 joueurs ou plus derrière le ballon 1 s après la perte (part)"].add(
                    1.0 if r["behind"] >= 4 else 0.0)
            still.append(r)
        self.retreat = still

    def _retreat_speeds(self, r, own):
        """Ticket 10 : 1,5 s après la perte, vitesse vers son but des joueurs qui étaient devant le ballon (profils
        Work Rate)."""
        for p in own:
            if p.name in r["choice"]:
                back = -forward(r["team"]) * p.velocity.x
                self.stats["repli : vitesse des joueurs devant le ballon à 1,5 s (m/s)"].add(back)
                level = self.levels.get(p.name)
                if level:
                    self.stats[f"profil {level} : vitesse de repli à 1,5 s (m/s)"].add(back)

    def _pressing(self, now_s, players, ball, by_name, dt):
        """Ticket 08 : pressings (un défenseur passe à moins de PRESS_RADIUS_M du porteur) suivis d'une récupération
        de l'équipe qui presse dans les 5 s ; profils : temps passé à presser et distance presseur-porteur."""
        holder = by_name.get(ball.holder) if ball.holder else None
        if self.press_open is not None and self.team == self.press_open[0]:
            self.count["pressings suivis d'une récupération en 5 s"] += now_s - self.press_open[1] <= 5.0
            self.press_open = None
        if self.press_open is not None and now_s - self.press_open[1] > 5.0:
            self.press_open = None
        if holder is None:
            return
        rivals = [p for p in players if p.team != holder.team and p.poste != "GK"]
        presser = min(rivals, key=lambda p: p.position.distance_to(holder.position), default=None)
        if presser is None or presser.position.distance_to(holder.position) >= PRESS_RADIUS_M:
            return
        if self.press_open is None:
            self.press_open = (presser.team, now_s)
            self.count["pressings"] += 1
        level = self.levels.get(presser.name)
        if level:
            self.count[f"profil {level} : temps de pressing (s)"] += dt
            self.stats[f"profil {level} : distance presseur-porteur (m)"].add(presser.position.distance_to(holder.position))

    def _geometry(self, now_s, players, ball, by_name):
        minute = now_s / 60.0
        sl = f"{int(minute // 15) * 15}-{int(minute // 15) * 15 + 15} min"
        for team in ("home", "away"):
            own = outfield(players, team)
            pts = [p.position for p in own]
            if len(pts) < 3:
                continue
            phase = "avec ballon" if team == self.team else "sans ballon"
            seen = zone(self.team, ball.position.x) if self.team else "sans possession"  # vue de l'équipe en possession
            keys = {"zone": seen, "score": _score_state(self.goals, team), "minute": sl,
                    "situation": self.situations.current[team]}
            length, width = length_width(pts)
            self.stats[f"longueur {phase} (m)"].add(length, **keys)
            if phase == "sans ballon":
                self.length_out[team].append(length)
            self.stats[f"largeur {phase} (m)"].add(width, **keys)
            self.stats[f"surface {phase} (m²)"].add(hull_area(pts), **keys)
            self.stats[f"stretch index {phase} (m)"].add(stretch_index(pts), **keys)
            gaps = line_gaps(team, pts)
            if gaps:
                self.stats[f"distance défense-milieu {phase} (m)"].add(gaps[0], **keys)
                self.stats[f"distance milieu-attaque {phase} (m)"].add(gaps[1], **keys)
            height = block_height(team, pts)
            self.stats[f"hauteur du bloc {phase} (m)"].add(height, **keys)
            holder = by_name.get(ball.holder) if ball.holder else None
            if phase == "sans ballon":  # ticket 05 : ligne et ballon, pression sur le porteur
                self.stats["écart ligne-ballon sans ballon (m)"].add(progress(team, ball.position.x) - height, **keys)
                if holder is not None and holder.team != team:
                    gap = min(p.position.distance_to(holder.position) for p in own)
                    if gap < PRESS_RADIUS_M or gap >= FREE_PASSER_M:
                        state = "pressé" if gap < PRESS_RADIUS_M else "libre"
                        self.stats[f"hauteur du bloc sans ballon, porteur {state} (m)"].add(height, **keys)
                        self.stats[f"écart ligne-ballon sans ballon, porteur {state} (m)"].add(
                            progress(team, ball.position.x) - height, **keys)  # à position du ballon comparable
            self.follow["longueur"].append((ball.position.x, statistics.fmean(p.x for p in pts)))
            self.follow["largeur"].append((ball.position.y, statistics.fmean(p.y for p in pts)))
            packed = crowded(own, outfield(players, "away" if team == "home" else "home"), self.holder)
            if packed is not None:
                self.stats[f"regroupement {phase} : coéquipiers à moins de 5 m hors duel (part)"].add(packed, **keys)
            level = self.levels.get(own[0].name)
            if level:  # profils : compacité de l'équipe haute contre l'équipe basse
                self.stats[f"profil {level} : stretch index (m)"].add(stretch_index(pts))
                self.stats[f"profil {level} : longueur (m)"].add(length)
                if phase == "sans ballon":
                    self.stats[f"profil {level} : hauteur du bloc sans ballon (m)"].add(height)
                if gaps:
                    self.profile_gaps[level].append(gaps[0])
        if self.team is None:
            return
        att, dfd = self.team, ("away" if self.team == "home" else "home")
        keys = {"zone": zone(att, ball.position.x), "score": _score_state(self.goals, att), "minute": sl,
                "situation": self.situations.current[dfd]}  # vue de l'équipe qui défend : ces indicateurs la décrivent
        defenders, attackers = outfield(players, dfd), outfield(players, att)
        self.stats["compacité autour du ballon (m)"].add(local_compactness(ball.position, defenders), **keys)
        self.stats["supériorité locale des défenseurs (nombre)"].add(local_superiority(ball.position, defenders, attackers), **keys)
        behind, threats = preventive(att, ball.position, attackers, outfield(players, dfd))
        self.stats["défense préventive : joueurs derrière le ballon"].add(behind, **keys)
        self.stats["défense préventive : adversaires dans cette zone"].add(threats, **keys)
        level = self.levels.get(attackers[0].name) if attackers else None
        if self.situations.current[att] == POSSESSION_INSTALLEE:  # équilibre derrière le ballon (ticket 06)
            self.stats["possession installée : au moins 1 joueur derrière le ballon (part)"].add(1.0 if behind >= 1 else 0.0, **keys)
            if level:
                self.stats[f"profil {level} : possession installée, 2 joueurs ou plus derrière le ballon (part)"].add(
                    1.0 if behind >= 2 else 0.0)
        holder = by_name.get(ball.holder) if ball.holder else None
        if holder is not None:
            goal = Vec2(0.0 if dfd == "home" else PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)
            cover = pressing_cover(holder, defenders, goal)
            if cover is not None:
                self.stats["couverture du presseur (part)"].add(1.0 if cover else 0.0, **keys)
            mates = [p for p in players if p.team == holder.team]
            all_opponents = [p for p in players if p.team == dfd]  # gardien compris, comme dans le moteur
            chances = pass_chances(holder, mates, all_opponents)
            options = sum(1 for c in chances if c >= OPTION_PROBABILITY)
            easy = sum(1 for c in chances if c >= EASY_OPTION_PROBABILITY)
            self.stats["solutions de passe ouvertes (nombre)"].add(options, **keys)
            self.stats["solutions de passe faciles (nombre)"].add(easy, **keys)
            if chances:
                self.stats["réussite moyenne des passes disponibles (part)"].add(sum(chances) / len(chances), **keys)
            if level:
                self.stats[f"profil {level} : solutions de passe ouvertes (nombre)"].add(options)
                space = [min(m.position.distance_to(o.position) for o in all_opponents)
                         for m in mates if m is not holder and m.poste != "GK"]
                if space and all_opponents:  # critère reporté du ticket cerveau 03 (ticket 16)
                    self.stats[f"profil {level} : espace des coéquipiers du porteur (m)"].add(statistics.fmean(space))
            defending = self.levels.get(defenders[0].name) if defenders else None
            if defending:  # ticket 08 : solutions laissées au porteur par l'équipe haute ou basse
                self.stats[f"profil {defending} : solutions laissées au porteur adverse (nombre)"].add(options)
                self.stats[f"profil {defending} : solutions faciles laissées au porteur adverse (nombre)"].add(easy)

    def end_match(self) -> None:
        self.matches += 1
        for name, d in self.dist.items():
            if self.poste.get(name) != "GK":
                self.km[self.poste[name]].append(d / 1000.0)
                self.km["tous"].append(d / 1000.0)
        if self.total > 0:
            self.stats["distance au-dessus de 25 km/h (part)"].add(self.sprint / self.total)
            self.stats["temps au-dessus de 19,8 km/h (part)"].add(self.hi_time / self.time)
            # ticket v2-realisme/01d : la source mesure la distance (repère R6), le temps reste suivi
            self.stats["distance au-dessus de 19,8 km/h (part)"].add(self.hi / self.total)
            self.stats["temps au-dessus de 25 km/h (part)"].add(self.sprint_time / self.time)
        for name in list(self.sprint_run):  # sprint encore en cours au coup de sifflet final
            self._close_sprint(name)
        if self.hi_first > 0:
            self.stats["baisse de la course intense en fin de match (part)"].add(1.0 - self.hi_last / self.hi_first)
        for r in self.retreat_done + self.retreat:
            if r["latency"] is not None:
                self.stats["repli : latence (s)"].add(r["latency"])
            if r["speeds"]:
                self.stats["repli : vitesse de recul (m/s)"].add(statistics.fmean(r["speeds"]))
            if self.length_out[r["team"]] and r["length0"] is not None:
                # bloc reformé : longueur revenue sous sa médiane sans ballon du match (calcul a posteriori),
                # seulement si le bloc était plus long que cette médiane au moment de la perte
                ref = statistics.median(self.length_out[r["team"]])
                t = None if r["length0"] <= ref else next((e for e, length in r["lengths"] if length <= ref), None)
                if t is not None:
                    self.stats["repli : temps pour reformer le bloc (s)"].add(t)
        self._close_recovery(math.inf, relost=False)  # dernière récupération du match
        for z, lost in self.relost:
            self.stats["pertes en transition (part des récupérations)"].add(1.0 if lost else 0.0, zone=z)
        per_player = Counter(name for name, *_ in self.run_log)
        for name, poste in self.poste.items():  # tous les joueurs de champ, y compris ceux sans appel
            if poste != "GK":
                self.stats[f"appels par joueur et par match : {poste}"].add(per_player.get(name, 0))
                # ticket v2-realisme/01d : par poste, à côté des km (repères R4 à R6)
                self.stats[f"distance au-dessus de 19,8 km/h par joueur (m) : {poste}"].add(self.hi_by[name])
                self.stats[f"sprints par joueur et par match : {poste}"].add(self.sprints[name])
                self.stats["sprints par joueur et par match"].add(self.sprints[name])
                if self.now > 0:
                    per_90 = per_player.get(name, 0) * MATCH_90_S / self.now
                    self.stats[f"appels par joueur et par 90 min : {poste}"].add(per_90)
                    self.stats["appels par joueur et par 90 min"].add(per_90)
        redundant = 0
        for a, s1, e1, p1 in self.run_log:
            if any(b != a and s2 < e1 and s1 < e2 and p1.distance_to(p2) < RUN_SAME_ZONE_M
                   for b, s2, e2, p2 in self.run_log):
                redundant += 1
        if self.run_log:
            self.stats["appels redondants (part)"].add(redundant / len(self.run_log))
        for name, level in self.levels.items():  # profils : même mesure, attribut haut contre bas
            if self.poste.get(name) not in (None, "GK"):
                self.stats[f"profil {level} : course intense par joueur (m)"].add(self.hi_by[name])
                self.stats[f"profil {level} : appels par joueur"].add(per_player.get(name, 0))
                self.stats[f"profil {level} : appels dans le dos par joueur"].add(self.deep_runs[name])
                self.stats[f"profil {level} : km par joueur"].add(self.dist[name] / 1000.0)
        for axis, pairs in self.follow.items():  # pente : part du déplacement du ballon suivie par le centre d'équipe
            if len(pairs) > 2:
                self.stats[f"suivi du ballon par le bloc, {axis} (pente)"].add(slope(pairs))
        for level, gaps in self.profile_gaps.items():
            if len(gaps) > 1:
                self.stats[f"profil {level} : écart-type distance défense-milieu (m)"].add(statistics.pstdev(gaps))
        self.count["appels"] += len(self.run_log)
        self.count["durée de match (s)"] += self.now  # temps additionnel compris (ticket v2-realisme/01d)
        self.count["appels dans le dos"] += sum(self.deep_runs.values())
        self._combinations()
        self._reset_match()

    def _combinations(self) -> None:
        """Enchaînements de passes du match (ticket v2-collectif/14)."""
        k = self.count
        for p, q in zip(self.pass_log, self.pass_log[1:] + [None]):
            if not p["done"]:
                continue
            k["passes réussies (journal)"] += 1
            nxt = q if q is not None and q["passer"] == p["target"] and q["team"] == p["team"] else None
            if p["gain"] < NO_GAIN_M:  # C2 du ticket 13
                k["passes sans gain réussies"] += 1
                k["passes sans gain suivies d'une passe qui fait avancer"] += nxt is not None and nxt["progressive"]
            if nxt is None:
                continue
            if nxt["target"] == p["passer"] and nxt["t"] - p["t"] <= RETURN_WINDOW_S:
                k["retours au passeur en 3 s"] += 1
                one_two = progress(p["team"], nxt["end"].x) - progress(p["team"], p["start"].x) >= ONE_TWO_MIN_GAIN_M
                k["une-deux"] += one_two
            if p["follow"] is not None and nxt["target"] == p["follow"] and nxt["done"]:
                k["troisième homme (suite prévue jouée et réussie)"] += 1


def _final_third(team: str, x: float) -> bool:
    """Le point `x` est-il dans le dernier tiers que `team` attaque (domicile attaque vers x = 105) ?"""
    return x >= 70.0 if team == "home" else x <= 35.0
