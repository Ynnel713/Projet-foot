"""Situation de jeu (ticket v2-collectif/03) : à chaque instant, chaque équipe reconnaît le type de problème tactique
qu'elle affronte. C'est une perception collective : elle oriente les rôles (tickets suivants), elle ne joue pas à leur
place. Chaque joueur ne prend conscience d'un changement qu'après son délai de réaction (Anticipation,
`anticipation.reaction_delay_s`).

Seuils validés par le propriétaire le 26/10/2026 (ordres de grandeur, ajustables) :
- transition : 8 s après un changement de possession (contre-pression jugée sur 5-6 s, StatsBomb/CMU ; classes de
  récupération 0-5, 5-12, 12-15 s), ajustable de 5 à 12 s ;
- dernier tiers : ballon à plus de 70 m de son propre but, en possession."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.anticipation import MAX_REACTION_S, reaction_delay_s
from v2engine.ball_state import BallState
from v2engine.geometry import PITCH_LENGTH_M
from v2engine.movement import PlayerState

TRANSITION_WINDOW_S = 8.0
FINAL_THIRD_M = 70.0

POSSESSION_INSTALLEE, DEFENSE_PLACEE = "possession installée", "défense placée"
TRANSITION_OFFENSIVE, TRANSITION_DEFENSIVE, DERNIER_TIERS = "transition offensive", "transition défensive", "dernier tiers"


def _other(team: str) -> str:
    return "away" if team == "home" else "home"


def _progress(team: str, x: float) -> float:
    return x if team == "home" else PITCH_LENGTH_M - x


@dataclass
class SituationTracker:
    """Situation de chaque équipe, mise à jour une fois par tick (`update`), et situation perçue par un joueur
    (`perceived`). L'équipe en possession est celle du dernier porteur, y compris pendant une passe en vol."""
    possession: str | None = None
    changed_at_s: float = 0.0  # instant du dernier changement de possession
    transition: bool = False  # le dernier changement est une perte ou une récupération (pas un engagement)
    current: dict[str, str] = field(default_factory=lambda: {"home": DEFENSE_PLACEE, "away": DEFENSE_PLACEE})
    previous: dict[str, str] = field(default_factory=lambda: {"home": DEFENSE_PLACEE, "away": DEFENSE_PLACEE})
    since_s: dict[str, float] = field(default_factory=lambda: {"home": 0.0, "away": 0.0})
    kick_off: bool = False  # un but vient d'être marqué : la prochaine prise de balle est l'engagement
    delays_s: dict[str, float] = field(default_factory=dict)  # délai de réaction par joueur, calculé une fois

    def update(self, now_s: float, ball: BallState, players: list[PlayerState], scored: str | None = None) -> dict[str, str]:
        if scored is not None:  # but : l'autre équipe engage, ce n'est pas une transition
            self.possession, self.changed_at_s, self.transition, self.kick_off = _other(scored), now_s, False, True
        elif ball.restart is not None:  # remise en jeu (ticket v2-collectif/29) : ni perte ni récupération
            self.kick_off = False
            if ball.restart.team != self.possession:
                self.possession, self.changed_at_s, self.transition = ball.restart.team, now_s, False
        elif ball.holder is not None:
            team = next((p.team for p in players if p.name == ball.holder), None)
            if team is not None and self.kick_off:
                # première prise de balle après un but (l'engagement n'est pas modélisé : n'importe quelle équipe
                # peut toucher le ballon la première) : c'est l'engagement, pas une perte ni une récupération
                self.kick_off = False
                if team != self.possession:
                    self.possession, self.changed_at_s, self.transition = team, now_s, False
            elif team is not None and team != self.possession:
                self.transition = self.possession is not None
                self.possession, self.changed_at_s = team, now_s
        for team in ("home", "away"):
            situation = self._situation(team, now_s, ball)
            if situation != self.current[team]:
                self.previous[team], self.current[team], self.since_s[team] = self.current[team], situation, now_s
        return dict(self.current)

    def _situation(self, team: str, now_s: float, ball: BallState) -> str:
        if self.possession is None:
            return DEFENSE_PLACEE
        in_transition = self.transition and now_s - self.changed_at_s < TRANSITION_WINDOW_S
        if team == self.possession:
            if _progress(team, ball.position.x) > FINAL_THIRD_M:
                return DERNIER_TIERS  # prime sur la transition offensive : c'est d'abord un problème de finition
            return TRANSITION_OFFENSIVE if in_transition else POSSESSION_INSTALLEE
        return TRANSITION_DEFENSIVE if in_transition else DEFENSE_PLACEE

    def perceived(self, player: PlayerState, now_s: float) -> str:
        """Situation de son équipe telle que le joueur la perçoit : la précédente tant que son délai de réaction
        n'est pas écoulé. ponytail : un seul changement en mémoire ; deux changements plus rapprochés que le délai
        font percevoir directement l'avant-dernier état, à affiner si les tickets suivants le demandent."""
        team = player.team
        elapsed = now_s - self.since_s[team]
        if elapsed < MAX_REACTION_S and elapsed < self._delay(player):  # au-delà de 1 s, tout le monde a vu
            return self.previous[team]
        return self.current[team]

    def _delay(self, player: PlayerState) -> float:
        if player.name not in self.delays_s:
            self.delays_s[player.name] = reaction_delay_s(player)
        return self.delays_s[player.name]
