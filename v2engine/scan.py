"""Scan visuel (ticket v2-realisme/08c) : un joueur tourne brièvement la tête pour voir hors de son cône (08a) et
rafraîchir sa mémoire de perception (08b). Calculé et tracé au 08c, sans effet sur le jeu ; depuis le 08d la mémoire qu'il
rafraîchit nourrit la décision du porteur (le « il ne suit plus le ballon » reste sans consommateur : défenseur et appels
dans le dos, 08e).

Constantes validées par le propriétaire (13/11/2026, « fais tout dans le même ticket » après la proposition) :
- Un scan dure `SCAN_DURATION_S` (0,3 s) ; pendant ce temps il voit tout autour de lui (cône de 100° + environ 80° de
  rotation de tête, valeur courante, soit 180° de part et d'autre du cap). Durée : non trouvée, choix de modèle.
- Fréquence de base, par Vision : 99 -> 0,6 scan/s, 55 -> 0,3, 11 -> 0,1. Réel : Lampard 0,62 et Gerrard 0,61 scan/s sur
  les 10 s avant la réception (Jordet, 2013, Premier League) ; environ 3 scans en 10 s en moyenne (Jordet et al. 2020,
  Frontiers in Psychology) ; le bas (0,1) : non trouvé. Ces taux sont mesurés avant la réception ; hors de cette fenêtre :
  non trouvé, le même taux est appliqué à tout joueur sans ballon.
- Gêne : fréquence × (1 − 0,5 × `possession.pressure`) ; réel : moins de scans sous forte pression (Jordet et al. 2020),
  ampleur non retrouvée.
- Vitesse : fréquence × (1 − 0,5 × vitesse / vitesse de pointe) ; effet de la vitesse : non trouvé, choix de modèle.
- Porteur : fréquence × part de temps tête haute selon une note composée 0,6 × Dribbling + 0,4 × Technique (cumul permis
  par la règle R2 révisée) : 99 -> 100 %, 55 -> 60 %, 11 -> 25 % ; non trouvé.
Vision règle déjà la portée des passes envisagées (`decision.visible_teammates`) : le scan ne la touche pas, il rafraîchit
seulement la mémoire (règle R1). Le poste n'est pas un paramètre : l'écart entre milieux et attaquants (Jordet) émerge de
Vision. Tirage : flux `regard`, indépendant des autres (`flux.py`).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from v2engine.condition import effective_rating
from v2engine.flux import REGARD
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.possession import pressure
from v2engine.trace import ScanEvent

SCAN_DURATION_S = 0.3
_RATE_BY_VISION = ((11.0, 0.1), (55.0, 0.3), (99.0, 0.6))  # (Vision, scans par seconde)
PRESSURE_PENALTY = 0.5  # part de la fréquence perdue à pression maximale
SPEED_PENALTY = 0.5  # part de la fréquence perdue à vitesse de pointe
DRIBBLING_PART, TECHNIQUE_PART = 0.6, 0.4  # note de conduite tête haute du porteur
_HEAD_UP_BY_TOUCH = ((11.0, 0.25), (55.0, 0.6), (99.0, 1.0))  # (note composée, part du temps tête haute)
RATE_REFRESH_S = 0.5  # la fréquence suit la gêne et la vitesse, recalculée à ce pas (coût), décalée d'un joueur à l'autre


def _interpolate(points: Sequence[tuple[float, float]], note: float) -> float:
    """Valeur linéaire entre les repères (note, valeur), bornée aux extrémités."""
    note = min(max(note, points[0][0]), points[-1][0])
    (n0, v0), (n1, v1) = next(pair for pair in zip(points, points[1:]) if note <= pair[1][0])
    return v0 + (note - n0) / (n1 - n0) * (v1 - v0)


def head_up_share(player: PlayerState) -> float:
    """Part du temps où le porteur garde la tête haute : plus il est à l'aise balle au pied (Dribbling et Technique
    cumulés), moins il a besoin de regarder le ballon (08c)."""
    note = (DRIBBLING_PART * effective_rating(player, "Dribbling") + TECHNIQUE_PART * effective_rating(player, "Technique"))
    return _interpolate(_HEAD_UP_BY_TOUCH, note)


def scan_rate_per_s(player: PlayerState, opponents: Sequence[PlayerState], has_ball: bool) -> float:
    """Scans par seconde du joueur : Vision, moins la gêne subie et la vitesse, réduite encore par la tête basse du
    porteur."""
    rate = _interpolate(_RATE_BY_VISION, effective_rating(player, "Vision"))
    if has_ball:
        rate *= head_up_share(player)
    rate *= 1.0 - PRESSURE_PENALTY * pressure(player, opponents)
    rate *= 1.0 - SPEED_PENALTY * min(1.0, player.velocity.length() / max_speed_mps(effective_rating(player, "Pace")))
    return rate


class ScanTracker:
    """Qui est en train de scanner. Un scan démarre au hasard (flux `regard`), à la fréquence du joueur, et dure
    `SCAN_DURATION_S`. Lecture seule pour le jeu : seul le flux `regard` est tiré."""

    def __init__(self) -> None:
        self._until: dict[str, float] = {}
        self._rate: dict[str, float] = {}
        self._refreshed: dict[str, float] = {}

    def update(self, players: Sequence[PlayerState], holder: str | None, now_s: float, dt: float,
               sink: list[ScanEvent] | None = None) -> set[str]:
        """Joueurs qui scannent à cet instant ; chaque début de scan est ajouté à `sink` s'il est donné."""
        scanning: set[str] = set()
        for p in players:
            name = p.name
            if now_s < self._until.get(name, -1.0) - 1e-9:
                scanning.add(name)
                continue
            if name not in self._rate or now_s - self._refreshed[name] >= RATE_REFRESH_S - 1e-9:
                opponents = [o for o in players if o.team != p.team]
                self._rate[name] = scan_rate_per_s(p, opponents, name == holder)
                # premier calcul décalé de 0 à 0,4 s selon l'arrivée : le recalcul ne tombe pas au même pas pour tous
                self._refreshed[name] = now_s - (0.1 * (len(self._refreshed) % 5) if name not in self._refreshed else 0.0)
            if REGARD.random() < 1.0 - math.exp(-self._rate[name] * dt):
                self._until[name] = now_s + SCAN_DURATION_S
                scanning.add(name)
                if sink is not None:
                    sink.append(ScanEvent(now_s / 60.0, p.team, name, name == holder))
        return scanning
