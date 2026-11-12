"""Format de trace de match (D-V04, docs/TRD_V2.md) : position de chaque joueur et du ballon à
chaque instant échantillonné, calculée une fois côté serveur (voir `match.py`) puis destinée à
être rejouée par un rendu -- même principe calcul-puis-rejeu que la V1, mais contenu physique et
continu au lieu de narratif. Le rendu lui-même n'est pas construit en Phase 1 (voir
docs/PLAN_V2.md) : ce module ne fait que produire et porter les données."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.added_time import display_minute
from v2engine.cerveau import Intention
from v2engine.geometry import Vec2


@dataclass(frozen=True)
class PlayerSnapshot:
    name: str
    team: str  # "home" / "away"
    poste: str
    position: Vec2
    intention: Intention | None = None  # ce que le joueur cherche à faire à cet instant (ADR 0001)
    role: str = ""  # rôle du joueur (mezzala, pivot, latéral...), ticket v2-realisme/02c ; sans effet sur le jeu
    energy: float = 1.0  # part de sa réserve d'énergie restante (ticket v2-realisme/12e)
    facing: Vec2 = Vec2(1.0, 0.0)  # cap du corps, vecteur unitaire (ticket v2-realisme/07a)


@dataclass(frozen=True)
class BallSnapshot:
    position: Vec2
    holder: str | None = None  # porteur du ballon à cet instant (None = ballon en l'air ou libre), pour afficher son nom
    mode: str = "sol"  # "sol" ou "aérien" (ticket v2-collectif/29), pour le rendu
    dead: bool = False  # ballon mort, en attente d'une remise en jeu (ticket v2-collectif/29)


@dataclass(frozen=True)
class Tick:
    minute: float  # minute de match simulée
    players: tuple[PlayerSnapshot, ...]
    ball: BallSnapshot


@dataclass(frozen=True)
class DecisionRecord:
    """Une décision du porteur (journal des décisions, ADR 0001)."""
    minute: float
    player: str
    team: str
    action: str  # "shot" | "pass" | "dribble"
    target: str | None  # coéquipier visé, pour une passe
    considered: int  # options envisagées
    best: bool  # meilleure option prise
    best_kind: str | None = None  # meilleur choix factuel (ticket v2-collectif/33)
    gap: float = 0.0  # valeur réelle perdue par rapport au meilleur choix factuel, en part de celui-ci


@dataclass(frozen=True)
class SituationRecord:
    """Changement de situation de jeu d'une équipe (ticket v2-collectif/03)."""
    minute: float
    team: str
    situation: str


@dataclass(frozen=True)
class GoalEvent:
    minute: float
    team: str  # "home" / "away"
    # Ticket v2-realisme/19b : buteur = dernier joueur à avoir touché le ballon ; but contre son camp si son équipe n'est
    # pas celle qui marque (impossible avant le ticket 05i : un ballon dévié ne fait pas but).
    scorer: str | None = None
    last_toucher: str | None = None
    own_goal: bool = False


@dataclass(frozen=True)
class OffsideEvent:
    """Hors-jeu sifflé (ticket v2-collectif/23) : `team` est l'équipe qui le commet (celle de l'attaquant
    signalé), `player` le joueur signalé, `x`/`y` l'endroit où le ballon a été touché (le coup franc est donné
    là, simplifié)."""
    minute: float
    team: str  # "home" / "away"
    player: str
    x: float
    y: float


@dataclass(frozen=True)
class RestartEvent:
    """Remise en jeu jouée (ticket v2-collectif/29) : `minute` de la sortie (ou du but), `kind` touche, sortie de but,
    corner ou engagement, `team` l'équipe qui remet en jeu, `x`/`y` le point de remise, `last_toucher` le dernier
    joueur à avoir touché le ballon, `dead_s` la durée du ballon mort, `long` jouée au-delà de `LONG_RESTART_M`
    (`restart.py`), `target` le receveur visé."""
    minute: float
    kind: str
    team: str
    x: float
    y: float
    last_toucher: str | None
    dead_s: float
    long: bool
    target: str | None = None
    shot: bool = False  # coup franc frappé au but (ticket v2-collectif/30)


@dataclass(frozen=True)
class ShotEvent:
    """Tir (ticket v2-collectif/28b) : `team` et `player` le tireur, `x`/`y` le lieu du tir, `quality` la qualité de
    l'occasion (ticket 28a, chance de but s'il n'est pas contré, contre compris), `outcome` l'issue tirée au départ (but,
    à côté, contré, capté, repoussé, claqué ; un tir « à côté » peut encore être dévié en route), `origin` comment le
    tireur a eu le ballon (passe au sol, passe en retrait, passe en profondeur, centre, dribble, rebond, récupération,
    coup franc, penalty). Le rendu rejoue l'issue enregistrée."""
    minute: float
    team: str
    player: str
    x: float
    y: float
    quality: float
    outcome: str
    origin: str
    # Tir en vol (ticket v2-realisme/05b) : temps de vol (s) et écart au gardien (m) quand le ballon passe au plus près de
    # lui ; `None` si le gardien n'a pas eu à juger le tir (hors cadre, tir tiré au départ).
    keeper_time_s: float | None = None
    keeper_gap_m: float | None = None
    keeper_speed_mps: float | None = None  # vitesse du ballon quand il passe au gardien (réserve A4 du 05h)
    # Contre physique (ticket v2-realisme/05c) : point de contact du tir contré.
    block_x: float | None = None
    block_y: float | None = None
    block_exit_deg: float | None = None  # angle de sortie du ballon contré avec la direction du tir (0 : il continue ; ticket 05d)
    # xG (ticket v2-realisme/06a) : neutre (tireur et gardien moyens, `shooting.neutral_xg`) ; après frappe, pour un tir non
    # contré (`shooting.post_shot_xg`, 0 hors du cadre) ; `None` si non défini (tir contré, penalty).
    xg: float | None = None
    post_shot_xg: float | None = None


@dataclass(frozen=True)
class ChanceEvent:
    """Grosse occasion (ticket v2-collectif/28c) : séquence dangereuse de `team` dont le pic de danger atteint le seuil
    (`occasion.BIG_CHANCE_DANGER`), avec ou sans tir. `start`, `peak_minute`, `end` : début, pic et fin de la séquence
    (minutes) ; `player`, `x`/`y` : l'attaquant de la meilleure occasion au pic et sa position ; `danger` : le pic
    (qualité de l'occasion x chance que le ballon lui parvienne) ; `outcome` : « tir : <issue du tir> », tacle,
    interception, gardien, dégagement, ballon non repris, danger retombé, « ballon mort : <remise> » ou fin de période ;
    `origin` : comment la situation est née, même vocabulaire que le tir (`ShotEvent.origin`)."""
    start: float
    peak_minute: float
    end: float
    team: str
    player: str
    x: float
    y: float
    danger: float
    outcome: str
    origin: str
    shot: bool


@dataclass(frozen=True)
class FoulEvent:
    """Faute (ticket v2-collectif/30) : `team` et `player` le fautif, `victim` le joueur fauté, `x`/`y` le lieu,
    `severity` la gravité (`duel.foul_severity`), `outcome` ce qu'en a fait l'arbitre : coup franc, penalty ou
    avantage (laissé jouer et acquis)."""
    minute: float
    team: str
    player: str
    victim: str
    x: float
    y: float
    severity: str
    outcome: str


# Journal des événements (ticket v2-realisme/19b) : types d'événements.
PASSE, CONTROLE_RATE, PERTE, TOUCHE_LONGUE = "passe", "contrôle raté", "perte", "touche longue"
TIR, CONTRE, ARRET, BUT = "tir", "contre", "arrêt", "but"
REMISE, FAUTE, HORS_JEU = "remise", "faute", "hors-jeu"


@dataclass(frozen=True)
class TraceEvent:
    """Événement du journal (ticket v2-realisme/19b), dans l'ordre où le moteur le produit. `cause` : identifiant de
    l'événement du ballon qui le précède (vide pour un engagement, qui ouvre une chaîne). `detail` : précision selon le
    type (type de remise, issue d'un arrêt, façon de perdre le ballon) ; `other` : l'autre joueur (receveur visé, joueur
    qui récupère le ballon, joueur fauté)."""
    id: int
    minute: float
    kind: str
    team: str | None
    player: str | None
    cause: int | None
    detail: str | None = None
    other: str | None = None


class EventLog:
    """Écrit le journal : chaque événement prend pour cause le dernier événement du ballon, puis le devient."""

    def __init__(self, events: list[TraceEvent]) -> None:
        self.events = events
        self.last: int | None = events[-1].id if events else None

    def add(self, minute: float, kind: str, team: str | None, player: str | None, detail: str | None = None,
            other: str | None = None, start: bool = False) -> TraceEvent:
        event = TraceEvent(len(self.events), minute, kind, team, player, None if start else self.last, detail, other)
        self.events.append(event)
        self.last = event.id
        return event

    def last_event(self) -> TraceEvent | None:
        return None if self.last is None else self.events[self.last]


def chain(events: list[TraceEvent], event_id: int) -> list[TraceEvent]:
    """Chaîne de causes de l'événement `event_id`, de son origine (un engagement) à lui."""
    out = []
    current: int | None = event_id
    while current is not None:
        out.append(events[current])
        current = events[current].cause
    return out[::-1]


@dataclass
class MatchTrace:
    home: str
    away: str
    tick_seconds: float  # intervalle de temps de match entre deux ticks enregistrés
    ticks: list[Tick] = field(default_factory=list)
    # Score : émerge entièrement du moteur (Phase 4, docs/PLAN_V2.md) -- jamais décidé à
    # l'avance, contrairement à la V1. `goals` horodate chaque but (minute, équipe) pour que le
    # rendu puisse révéler le score au fil du visionnage (US-29), pas avant.
    home_goals: int = 0
    away_goals: int = 0
    goals: list[GoalEvent] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    situations: list[SituationRecord] = field(default_factory=list)
    offsides: list[OffsideEvent] = field(default_factory=list)  # hors-jeu sifflés (ticket v2-collectif/23)
    restarts: list[RestartEvent] = field(default_factory=list)  # remises en jeu (ticket v2-collectif/29)
    fouls: list[FoulEvent] = field(default_factory=list)  # fautes (ticket v2-collectif/30)
    shots: list[ShotEvent] = field(default_factory=list)  # tirs et leur issue (ticket v2-collectif/28b)
    chances: list[ChanceEvent] = field(default_factory=list)  # grosses occasions, avec ou sans tir (ticket 28c)
    reaction_delays_s: dict[str, float] = field(default_factory=dict)  # par joueur (Anticipation, ticket v2-collectif/03)
    # Minute du coup d'envoi de la 2e période (ticket v2-coach-et-gestion-de-match/07) ; None tant qu'elle n'est pas
    # jouée. Le moteur garde son sens de jeu : c'est l'écran qui retourne la scène à partir de cette minute.
    second_half_start_minute: float | None = None
    # Minutes de temps additionnel annoncées à la fin de chaque période (ticket v2-coach-et-gestion-de-match/03).
    added_minutes: list[int] = field(default_factory=list)
    events: list[TraceEvent] = field(default_factory=list)  # journal ordonné, avec les causes (ticket v2-realisme/19b)

    def display_minute(self, minute: float) -> str:
        """Minute affichée (`12'`, `45+2'`, `90+4'`) d'un instant de la trace, pour le rendu et la narration."""
        return display_minute(minute, self.second_half_start_minute)

    def record(self, minute: float, players: list[PlayerSnapshot], ball: BallSnapshot) -> None:
        self.ticks.append(Tick(minute=minute, players=tuple(players), ball=ball))

    def record_goal(self, team: str, minute: float, scorer: str | None = None, own_goal: bool = False) -> None:
        if team == "home":
            self.home_goals += 1
        elif team == "away":
            self.away_goals += 1
        else:
            raise ValueError(f"équipe inconnue : {team!r} (attendu 'home' ou 'away')")
        self.goals.append(GoalEvent(minute=minute, team=team, scorer=scorer, last_toucher=scorer, own_goal=own_goal))

