"""Fabrique de scènes de test du moteur V2 (ticket v2-realisme/01f), partagée par les fichiers `test_v2engine_*.py`.

Quatre aides, dans l'ordre d'usage :

- `player(nom, équipe, x, y, poste, **attributs)` : un `PlayerState` arrêté à (x, y), qui a cette place pour cible de
  formation. Pace, Acceleration et Stamina valent 60 par défaut. Un `_` dans le nom d'un attribut devient une espace
  (`Off_the_Ball=80` donne « Off the Ball »).
- `with_attribute(joueurs, attribut, valeur, only=nom)` : copie des joueurs avec l'attribut réglé sur tous, ou sur un
  seul. Les joueurs d'origine ne changent pas.
- `Scene` et `run(scène, secondes)` : joueurs, ballon et composants collectifs (défense, bloc, suivi de situation,
  transition), puis N pas de la boucle de match dans l'ordre de `match.simulate_match`. Un composant à `None` n'est
  pas mis à jour, comme dans les scènes réduites des tests existants. `Scene.full` crée tous les composants comme le
  match. `until` arrête la boucle dès qu'une condition est vraie.
- `ab(joueurs, construire, secondes, graine, mesure, attribut, valeur, only=nom)` : même scène, même graine, deux
  profils (A d'origine, B avec l'attribut réglé). Rend (mesure de A, mesure de B). `fingerprint` résume l'état d'une
  scène ; `Scene.log` garde l'empreinte de chaque pas.

Exemple :

    players = [player("Porteur", x=50), player("Def", "away", x=55)]
    a, b = ab(players, lambda ps: Scene.full(ps, holder="Porteur"), 5.0, 3, lambda s: s.ball.holder,
              "Tackling", 99, only="Def")
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TypeVar

from v2engine.anticipation import reaction_delay_s
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.cerveau import Intention
from v2engine.defense import DefensiveRoles
from v2engine.geometry import Vec2
from v2engine.match import _resolve_player_collisions, _step_ball, _step_player
from v2engine.movement import PlayerState
from v2engine.situation import SituationTracker
from v2engine.transition import TransitionPlay

T = TypeVar("T")

# Notes lues par le moteur dans un champ dédié de `PlayerState` et non dans `attributes` (recopiées à la construction
# des joueurs, `match._build_players`) : les régler doit aussi régler le champ, sinon la note n'a aucun effet.
DEDICATED_FIELDS = {"Pace": "pace", "Acceleration": "acceleration", "Stamina": "stamina"}


def _copy(p: PlayerState, **changes) -> PlayerState:
    return replace(p, attributes=dict(p.attributes) if p.attributes else None, **changes)


def player(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "MC", *,
           pace: float = 60, acceleration: float = 60, stamina: float = 60, **attributes: int) -> PlayerState:
    """`Pace=…`, `Acceleration=…` ou `Stamina=…` passés en attributs règlent aussi le champ dédié."""
    attrs = {k.replace("_", " "): v for k, v in attributes.items()}
    state = PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                        acceleration=acceleration, stamina=stamina, home_target=Vec2(x, y), attributes=attrs or None)
    return replace(state, **{f: attrs[a] for a, f in DEDICATED_FIELDS.items() if a in attrs})


def with_attribute(players: list[PlayerState], attribute: str, value: int, only: str | None = None) -> list[PlayerState]:
    """Copies indépendantes des joueurs ; l'attribut réglé sur tous ou sur `only` (et son champ dédié s'il en a un)."""
    field_change = {DEDICATED_FIELDS[attribute]: value} if attribute in DEDICATED_FIELDS else {}
    return [replace(_copy(p), attributes={**(p.attributes or {}), attribute: value}, **field_change)
            if only is None or p.name == only else _copy(p) for p in players]


@dataclass
class Scene:
    players: list[PlayerState]
    ball: BallState
    defense: DefensiveRoles | None = None
    bloc: Bloc | None = None
    situations: SituationTracker | None = None
    transition: TransitionPlay | None = None
    runs: dict[str, tuple[Vec2, float]] | None = None
    intentions: dict[str, Intention] | None = None
    start_s: float = 0.0  # instant du premier pas
    log: list[str] = field(default_factory=list)  # empreinte de chaque pas joué
    dt: float = 0.1
    scored: str | None = None  # équipe qui vient de marquer au dernier pas, relue par le suivi de situation

    @property
    def now_s(self) -> float:
        """Instant du prochain pas, `départ + k × dt` comme dans `simulate_match` (sans cumul d'arrondis)."""
        return self.start_s + len(self.log) * self.dt

    @classmethod
    def full(cls, players: list[PlayerState], holder: str | None = None, ball_at: Vec2 | None = None,
             start_s: float = 0.0) -> Scene:
        """Scène avec tous les composants du match ; le ballon est au pied de `holder`, ou libre en `ball_at`."""
        at = next(p.position for p in players if p.name == holder) if holder else (ball_at or Vec2(52.5, 34.0))
        ball = BallState(position=at, velocity=Vec2(0.0, 0.0), holder=holder)
        return cls(players, ball, DefensiveRoles(), Bloc.from_players(players),
                   SituationTracker(delays_s={p.name: reaction_delay_s(p) for p in players}), TransitionPlay(), {}, {},
                   start_s)

    def get(self, name: str) -> PlayerState:
        return next(p for p in self.players if p.name == name)


def run(scene: Scene, seconds: float, until: Callable[[Scene], bool] | None = None) -> bool:
    """Joue `seconds` de match (pas de `scene.dt`) dans l'ordre de `match.simulate_match` ; rend True si `until` a
    arrêté la boucle. ponytail: copie de la boucle de `simulate_match` (sans période, temps additionnel ni trace) ; à
    aligner si l'ordre des mises à jour du match change."""
    dt = scene.dt
    for _ in range(round(seconds / dt)):
        now = scene.now_s
        if scene.situations is not None:
            scene.situations.update(now, scene.ball, scene.players, scene.scored)
        if scene.transition is not None and scene.situations is not None:
            scene.transition.update(scene.situations, scene.ball, scene.players, now)
        if scene.bloc is not None:
            scene.bloc.update(scene.players, scene.ball, now)
        if scene.defense is not None:
            scene.defense.update(scene.players, scene.ball, scene.bloc, now,
                                 scene.situations.current if scene.situations is not None else None)
        scene.players = [_step_player(p, scene.ball, dt, now / 60.0, scene.players, scene.runs, scene.intentions,
                                      scene.situations, scene.bloc, scene.defense, scene.transition)
                         for p in scene.players]
        _resolve_player_collisions(scene.players)
        # mode de transition (contre-attaque, conservation) lu par les décisions du porteur, comme dans le match
        scene.scored = _step_ball(scene.ball, dt, scene.players, now, None, None,
                                  scene.transition.mode if scene.transition is not None else None)
        scene.log.append(fingerprint(scene))
        if until is not None and until(scene):
            return True
    return False


def fingerprint(scene: Scene) -> str:
    """Empreinte exacte (positions et vitesses non arrondies) des joueurs et du ballon."""
    state = [(p.name, p.position, p.velocity) for p in scene.players]
    state.append((scene.ball.holder, scene.ball.position, scene.ball.velocity))
    return hashlib.sha256(repr(state).encode()).hexdigest()[:16]


def ab(players: list[PlayerState], make: Callable[[list[PlayerState]], Scene], seconds: float, seed: int,
       measure: Callable[[Scene], T], attribute: str, value: int, only: str | None = None) -> tuple[T, T]:
    """Même scène, même graine : A avec `players` tels quels, B avec `attribute` à `value` (sur `only` ou sur tous).
    `make` construit la scène à partir des joueurs (copiés : A et B ne partagent aucun état), après le réglage, pour
    que bloc et délais de réaction lisent le profil B."""
    results = []
    for profile in ([replace(p) for p in players], with_attribute(players, attribute, value, only)):
        scene = make(profile)
        random.seed(seed)  # ponytail: flux global (D-V06) ; un flux par sous-système arrive avec v2-realisme/01a
        run(scene, seconds)
        results.append(measure(scene))
    return results[0], results[1]
