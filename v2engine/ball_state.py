"""État du ballon pendant une simulation (Phase 2, docs/PLAN_V2.md) : position/vitesse comme en
Phase 1, plus la possession (quel joueur le contrôle, le cas échéant). Distinct de
`trace.BallSnapshot` (instantané figé destiné au rendu, pas d'état de simulation)."""

from __future__ import annotations

from dataclasses import dataclass, field

from typing import TYPE_CHECKING

from v2engine.geometry import Vec2

if TYPE_CHECKING:
    from v2engine.restart import Restart


@dataclass
class BallState:
    position: Vec2
    velocity: Vec2
    holder: str | None = None  # nom du joueur en contrôle du ballon, None = ballon libre
    # Instant (s de match) avant lequel le porteur garde son choix en cours -- conduite de balle
    # entre deux réévaluations (`decision.DECISION_INTERVAL_S`).
    next_decision_s: float = 0.0
    # Adversaires qui ont lu la passe en cours et le point où ils courent la couper (Anticipation,
    # `anticipation.pass_readers`) ; vidé dès que quelqu'un contrôle le ballon.
    readers: dict[str, Vec2] = field(default_factory=dict)
    last_pass_team: str | None = None  # équipe de la dernière passe, pour repérer une interception
    receiver: str | None = None  # coéquipier visé par la passe en cours, qui vient au-devant du ballon (v2-socle/01)
    receiving: bool = False  # porteur encore dans son temps de réception, avant sa première décision (v2-socle/06)
    # Duels (v2-socle/03) : défenseurs ayant déjà tenté leur tacle dans la confrontation en cours avec
    # `engaged_holder`, et instant jusqu'auquel un défenseur au tacle raté ne peut plus tacler.
    engaged: set[str] = field(default_factory=set)
    engaged_holder: str | None = None
    tackle_ban_until_s: dict[str, float] = field(default_factory=dict)
    # Contrôle raté (ticket v2-collectif/25) : instant jusqu'auquel le joueur qui l'a raté ne peut pas retenter.
    control_ban_until_s: dict[str, float] = field(default_factory=dict)
    released_by: str | None = None  # passeur de la passe en cours : il ne la touche pas en la lâchant (ticket 25)
    # Hors-jeu (ticket v2-collectif/23) : joueurs signalés au départ de la passe en cours. Vidé dès que quelqu'un
    # contrôle le ballon, qu'il meurt ou qu'un coup franc est donné.
    offside_watch: set[str] = field(default_factory=set)
    # Défenseurs qui lèvent la main et attendent le sifflet (Anticipation, directive « play the whistle ») :
    # nom -> instant jusqu'auquel ils relâchent leur effort. Survit à la fin de la passe : il expire tout seul, et
    # le joueur qui récupère le ballon en sort (il joue, lui).
    hesitation: dict[str, float] = field(default_factory=dict)
    # Attaquant fautif écarté de l'action après le coup franc : nom -> instant jusqu'auquel il recule.
    offside_out_until: dict[str, float] = field(default_factory=dict)
    # Plan de passe (ticket v2-collectif/14) : (receveur, suite prévue par le passeur, instant de la passe). Lu par le
    # receveur à sa première décision, puis effacé à toute décision d'un porteur.
    plan: tuple[str, str, float] | None = None
    # Tir qui finira au fond (tirage déjà fait au départ) : équipe du tireur tant que le ballon est en route vers le but.
    # Le but ne compte qu'à l'arrivée du ballon sur la ligne, jamais au départ du tir.
    shot_for: str | None = None
    # Ballon mort (ticket v2-collectif/29) : dernier joueur à l'avoir touché (il décide de la remise en jeu), remise en
    # attente tant que le ballon est mort, mode du ballon et distance qu'il doit encore parcourir en l'air avant de
    # pouvoir être touché (point de chute).
    last_toucher: str | None = None
    restart: Restart | None = None
    mode: str = "sol"
    # Conduite en cours (ticket v2-collectif/33) : (porteur, point visé), tenue jusqu'à sa décision suivante.
    dribble: tuple[str, Vec2] | None = None
    felt: tuple[str, dict[int, float]] | None = None  # erreur du porteur par direction de conduite (ticket 33)
    aerial_left_m: float = 0.0
