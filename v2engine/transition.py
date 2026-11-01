"""Transition défense-attaque (ticket v2-collectif/11) : à la récupération, le porteur choisit entre contre-attaque et
conservation (`decision.choose_transition`, Decisions). Le choix vaut pour son équipe tant qu'elle est en transition
offensive (`situation.TRANSITION_WINDOW_S`) : il s'arrête au dernier tiers ou à la perte du ballon. Pas de choix sur un
ballon rendu au gardien ni sur le coup franc d'un hors-jeu : ce ne sont pas des récupérations dans le jeu.
- en contre-attaque, le porteur cherche la progression (`decision.evaluate_options`) et ses coéquipiers devant le
  ballon font un appel dans la profondeur dès qu'ils ont perçu la récupération (`cerveau.decide`, délai de réaction
  d'Anticipation) ;
- en conservation, le porteur sort d'abord de la zone de pression par une passe sûre."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.ball_state import BallState
from v2engine.decision import choose_transition
from v2engine.movement import PlayerState
from v2engine.situation import TRANSITION_OFFENSIVE, SituationTracker


@dataclass
class TransitionPlay:
    """Choix de transition de chaque équipe, mis à jour une fois par tick après `SituationTracker.update`."""
    mode: dict[str, str] = field(default_factory=dict)  # équipe -> contre-attaque ou conservation
    launched: set[str] = field(default_factory=set)  # joueurs déjà lancés dans la profondeur pour cette contre-attaque
    _decided_at_s: float | None = None  # instant du changement de possession déjà traité

    def update(self, situations: SituationTracker, ball: BallState, players: list[PlayerState], now_s: float = 0.0) -> None:
        for team in [t for t in self.mode if situations.current[t] != TRANSITION_OFFENSIVE]:
            del self.mode[team]
        if not situations.transition or situations.changed_at_s == self._decided_at_s or ball.holder is None:
            return
        holder = next((p for p in players if p.name == ball.holder), None)
        if holder is None or holder.team != situations.possession:
            return
        self._decided_at_s = situations.changed_at_s
        self.launched = set()
        self.mode = {}
        free_kick = any(until > now_s for until in ball.offside_out_until.values())  # coup franc de hors-jeu
        # récupération dans le dernier tiers : la finition prime, pas de choix de transition
        if situations.current[holder.team] == TRANSITION_OFFENSIVE and holder.poste != "GK" and not free_kick:
            self.mode[holder.team] = choose_transition(holder, players)
