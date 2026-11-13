"""Mémoire de perception (ticket v2-realisme/08b) : chaque joueur garde, pour chacun des autres, la dernière position et
la dernière vitesse VUES (dans son cône, `vision.seen_by`, 08a) avec l'instant ; la position qu'il en perçoit est
extrapolée de cette observation. Calculée et tracée, sans effet sur le jeu dans ce ticket (décisions sur le monde perçu :
08d ; rotations de tête qui rafraîchissent la mémoire : scan, 08c).

Constantes validées par le propriétaire (13/11/2026, « ok constantes ») :
- Extrapolation : dernière position vue + part × dernière vitesse vue × âge. La part est celle de l'Anticipation déjà
  branchée au ticket v2-collectif/33 (`decision.anticipation_share` : 99 -> 100 %, 55 -> 65 %, 11 -> 30 %) : même effet
  (prolonger l'élan des adversaires), aucune courbe nouvelle (R1).
- `EXTRAPOLATION_HORIZON_S` : l'extrapolation s'arrête à 2 s ; au-delà, le joueur reste figé au point extrapolé. Le
  déplacement extrapolé est donc borné (au plus l'horizon × sa vitesse d'alors) ; l'erreur contre la position réelle, elle,
  continue de croître tant qu'il n'est pas revu (correction de l'énoncé validé, constatée à la mesure).
- Aucun bruit ajouté : l'erreur croissante est celle du jeu (l'adversaire change de direction, de vitesse). Elle croît
  vite puis plafonne avec l'horizon (non linéaire).
- Initialisation : au coup d'envoi (et à la reprise de la 2e période), chacun connaît la position réelle de tous ; un
  joueur absent de la mémoire (arrivé après) est connu à sa première apparition.
- Mise à jour à chaque tick, pour les 22 joueurs.
Chiffres réels (durée de la mémoire visuelle d'un footballeur pour des positions mobiles) : non trouvés ; ce sont des choix
de modèle, à recaler au 08c et au 08d.
"""

from __future__ import annotations

from dataclasses import dataclass

from v2engine.decision import anticipation_share
from v2engine.geometry import Vec2, clamp_to_pitch
from v2engine.movement import PlayerState
from v2engine.vision import seen_by

EXTRAPOLATION_HORIZON_S = 2.0
_NOW_S = 1e-9  # une observation de cet instant est une vue : âge nul


@dataclass(frozen=True)
class MemoryReading:
    """Ce que la mémoire d'un joueur vaut sur les joueurs qu'il ne voit pas à cet instant : âge moyen de leur dernière
    vue (s), erreur moyenne et maximale entre leur position perçue et leur position réelle (m). Zéros s'il les voit tous."""
    unseen: int = 0
    age_mean_s: float = 0.0
    error_mean_m: float = 0.0
    error_max_m: float = 0.0


class PerceptionMemory:
    """Dernière observation (x, y, vx, vy, instant) de chaque joueur par chaque observateur. Lecture pure pour le jeu."""

    def __init__(self, players: list[PlayerState], now_s: float) -> None:
        self._seen: dict[str, dict[str, tuple[float, float, float, float, float]]] = {}
        for observer in players:
            self._seen[observer.name] = {p.name: self._observation(p, now_s) for p in players if p is not observer}

    @staticmethod
    def _observation(p: PlayerState, now_s: float) -> tuple[float, float, float, float, float]:
        return (p.position.x, p.position.y, p.velocity.x, p.velocity.y, now_s)

    def update(self, players: list[PlayerState], now_s: float) -> None:
        """Rafraîchit ce que chacun voit à cet instant ; un joueur jamais observé l'est à sa première apparition."""
        for observer in players:
            memory = self._seen.get(observer.name)
            if memory is None:
                memory = self._seen[observer.name] = {}
            for p in seen_by(observer, players):
                memory[p.name] = self._observation(p, now_s)
            if len(memory) < len(players) - 1:
                for p in players:
                    if p is not observer and p.name not in memory:
                        memory[p.name] = self._observation(p, now_s)

    def age_s(self, observer: str, observed: str, now_s: float) -> float:
        """Âge de la dernière vue de `observed` par `observer` (0 : il le voit maintenant)."""
        return max(0.0, now_s - self._seen[observer][observed][4])

    def perceived_position(self, observer: PlayerState, observed: str, now_s: float, share: float | None = None) -> Vec2:
        """Position de `observed` telle que `observer` la perçoit : dernière vue, prolongée de sa vitesse d'alors pendant
        l'âge de la vue (au plus `EXTRAPOLATION_HORIZON_S`), pour la part que son Anticipation prolonge."""
        x, y, vx, vy, seen_s = self._seen[observer.name][observed]
        age = min(now_s - seen_s, EXTRAPOLATION_HORIZON_S)
        if age <= _NOW_S:
            return Vec2(x, y)
        reach = (anticipation_share(observer) if share is None else share) * age
        return clamp_to_pitch(Vec2(x + vx * reach, y + vy * reach))

    def error_m(self, observer: PlayerState, observed: PlayerState, now_s: float) -> float:
        """Écart entre la position perçue de `observed` et sa position réelle."""
        return self.perceived_position(observer, observed.name, now_s).distance_to(observed.position)

    def reading(self, observer: PlayerState, others: list[PlayerState], now_s: float) -> MemoryReading:
        """Mémoire de `observer` sur ceux de `others` qu'il ne voit pas à cet instant."""
        share = anticipation_share(observer)
        ages, errors = [], []
        for other in others:
            age = self.age_s(observer.name, other.name, now_s)
            if age > _NOW_S:
                ages.append(age)
                errors.append(self.perceived_position(observer, other.name, now_s, share).distance_to(other.position))
        if not ages:
            return MemoryReading()
        return MemoryReading(len(ages), sum(ages) / len(ages), sum(errors) / len(errors), max(errors))
