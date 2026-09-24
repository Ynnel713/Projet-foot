"""Bibliothèque de gabarits de mise en scène d'un but -- 12 patrons
distincts (contre-attaque, construction placée, corner, penalty...), chacun
décrit en pseudo-keyframes RELATIFS (position normalisée [0, 1] à un
instant relatif [0, 1] de la durée du gabarit) plutôt qu'en coordonnées
absolues. C'est ICI, dans la diversité des 12 scripts, que vient la
variété visuelle des buts rejoués -- pas d'un tirage aléatoire de
trajectoire (voir objectif de ce module, docs/simulation_physique_archi.md).

Chaque gabarit expose une fonction autonome `build_xxx(event, lineup,
start_positions) -> Sequence` (voir la liste en bas de fichier), toutes
construites par un même moteur générique (`build_from_template`) à partir
d'un script déclaratif (`Template`) -- la duplication de code entre les 12
gabarits reste minimale, mais chacun est un point d'entrée indépendant et
testable isolément (voir tests/test_templates.py).

`pick_template(context)` sélectionne un gabarit pondéré par `Template.weight`
ET par la plausibilité du gabarit dans le contexte de CE but précis (minute,
écart au score, poste du buteur, poste du passeur -- voir `TemplateContext`)
: la part de hasard se limite à CE choix, jamais à l'exécution d'un gabarit
une fois choisi (`build_from_template` est une fonction pure).

Ce module dépend de `ligue1sim.events` (pour `GoalEvent`), `ligue1sim.lineup`
(pour `Lineup`), `ligue1sim.players` (pour `Player`/`GOALKEEPER`) et
`ligue1sim.pitch_geometry` (référentiel normalisé) -- mais jamais l'inverse,
conformément à l'invariant 1 (le moteur ne dépend jamais de l'habillage).
"""

# DETTE -- 2026-09-23 -- `build_from_template` fige le ballon sur sa dernière
# position connue quand `ball_owner=None` à un `t_ratio` sans que
# `Template.ball_position` ne porte d'entrée pour ce même `t_ratio` (voir la
# résolution de `ball_x`/`ball_y` dans `build_from_template`) -- impact :
# `corner` (t_ratio=0.6, "ballon disputé" du centre) et `recuperation_haute`
# (t_ratio=0.3, "ballon disputé" du pressing), les 2 seuls gabarits sur 12 à
# poser `ball_owner=None` -- corrigés ici via `ball_position` (brief du
# 23/09/2026, Tâche 2 "ball_owner=None debt"). Piste de correction pérenne :
# faire porter `ball_position` par TOUT gabarit futur qui pose
# `ball_owner=None`, sous peine du même repli (désormais visible, voir le
# `logging.warning` dans `build_from_template`, mais pas éliminé).

from __future__ import annotations

import hashlib
import logging
import math
import random
from dataclasses import dataclass, replace
from typing import Callable

from ligue1sim.animation.ball import BALL_FLIGHT
from ligue1sim.animation.types import BallState, Keyframe, PlayerId, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint, center_of
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, Player

_logger = logging.getLogger(__name__)

# --- Ancrages de fin d'un rôle -------------------------------------------
# Un rôle progresse (voir RoleFrame.progress) de sa position de départ RÉELLE
# (start_positions, sa position de formation) vers l'un de ces ancrages.
ANCHOR_SCORER = "scorer_zone"  # event.zone (centre de la zone de tir/but)
ANCHOR_ASSIST = "assist_zone"  # event.assist_zone si présent, sinon repli sur ANCHOR_SCORER
ANCHOR_STATIC = "static"  # reste à sa position de départ (progress ignoré)
ANCHOR_LATERAL_SHIFT = "lateral_shift"  # décalage latéral FIXE (voir _LATERAL_SHIFT_M) depuis le départ -- un pas de côté, jamais une vraie course (brief du 23/09/2026, penalty.support1/support2)

# Amplitude du décalage pour ANCHOR_LATERAL_SHIFT -- 1,5 m (une enjambée
# latérale). Corrigé le 23/09/2026 (suite) : la première valeur (25 cm,
# combinée au progress=0.05 déjà présent dans le gabarit) donnait un
# déplacement réel de 1,25 cm -- 0,14 px sur le canvas 1200x780, du
# "léger frémissement" au sens littéral mais en pratique invisible à
# l'œil nu. 1,5 m ici, combiné au nouveau progress=0.4 du gabarit (voir
# penalty.support1/support2), donne 60 cm réels de déplacement final --
# visible, subtil, crédible pour un joueur qui piétine avant un penalty.
_LATERAL_SHIFT_M = 1.5


@dataclass(frozen=True)
class TemplateContext:
    """Signaux disponibles pour pondérer le choix d'un gabarit (voir
    `pick_template`) -- dérivés de l'événement et du contexte du match,
    jamais inventés.

    `assist_poste` : le moteur (ligue1sim.events) ne distingue pas les
    "types" de passe décisive (centre, passe en profondeur...) -- ce champ
    en est un PROXY, approximé par le poste du passeur (un ailier évoque un
    centre, un milieu offensif une passe en profondeur), documenté comme
    approximation plutôt que présenté comme une vraie donnée de jeu.

    `goal_diff_before` -- et pas "after" -- délibérément : c'est le rapport
    de force AVANT ce but qui influence le STYLE de jeu qui y mène (une
    équipe menée cherche l'urgence, une équipe qui mène déjà peut se
    permettre la patience), pas le score une fois ce but inscrit. Utilisé
    par `_urgency_factor` (voir plus bas) -- avant le 23/09/2026, ce champ
    existait déjà mais n'était lu par AUCUNE fonction `context_score` : la
    pondération par score n'avait donc jamais d'effet réel, quelle que soit
    la valeur transmise. Corrigé."""

    minute: int
    goal_diff_before: int  # buts de l'équipe qui va marquer MOINS l'adversaire, AVANT ce but (positif = elle menait déjà)
    scorer_poste: str
    assist_poste: str | None
    penalty: bool
    # "league" | "cup" | "continental" -- convention par chaîne, voir CardEvent.card_type dans
    # ligue1sim.events. Un seul gabarit en tient compte aujourd'hui (_score_but_gag) : les enjeux
    # d'une compétition à élimination laissent moins de place à un but chaotique/rigolo.
    competition_type: str


def context_from_event(
    event: GoalEvent,
    *,
    scorer_poste: str,
    assist_poste: str | None,
    goal_diff_before: int,
    competition_type: str,
) -> TemplateContext:
    """Construit un `TemplateContext` à partir d'un `GoalEvent` réel et des
    quelques informations qu'il ne porte pas lui-même (poste des joueurs
    impliqués, écart au score AVANT ce but, type de compétition -- à
    calculer côté appelant, qui a accès à l'état du match, pas ce module)."""
    return TemplateContext(
        minute=event.minute,
        goal_diff_before=goal_diff_before,
        scorer_poste=scorer_poste,
        assist_poste=assist_poste,
        penalty=event.penalty,
        competition_type=competition_type,
    )


# --- Script canonique d'un gabarit ---------------------------------------


@dataclass(frozen=True)
class RoleFrame:
    """Position relative d'UN rôle à `t_ratio` ∈ [0, 1] de la durée du
    gabarit. `progress` ∈ [0, 1] interpole entre la position de départ
    RÉELLE de ce rôle (sa position de formation, voir `start_positions`) et
    son ancrage de fin (voir `Role.end_anchor`) : 0.0 = encore à son point
    de départ, 1.0 = arrivé à l'ancrage."""

    t_ratio: float
    progress: float


@dataclass(frozen=True)
class Role:
    """Un acteur du gabarit. `name` est résolu vers un vrai joueur par
    `_resolve_roles` ("scorer"/"assist" depuis l'événement lui-même, tout
    autre nom depuis les coéquipiers restants, voir cette fonction).
    `frames` doit couvrir EXACTEMENT les mêmes `t_ratio` que les autres
    rôles actifs du même gabarit (vérifié par `_validate_template`)."""

    name: str
    end_anchor: str
    frames: tuple[RoleFrame, ...]


@dataclass(frozen=True)
class Template:
    """Un gabarit de mise en scène complet -- pure donnée, voir
    `build_from_template` pour le moteur générique qui l'exécute.

    `weight` : poids de base du tirage (voir `pick_template`), pondéré par
    `context_score(context)` -- le produit des deux doit être > 0 pour que
    ce gabarit reste éligible pour un but donné."""

    name: str
    weight: float
    duration: float  # secondes
    roles: tuple[Role, ...]
    tags: tuple[tuple[float, str], ...]  # (t_ratio, tag) -- étiquette du Keyframe à ce t_ratio, "" si absent
    ball_owner: tuple[tuple[float, str | None], ...]  # (t_ratio, nom du rôle porteur, ou None)
    context_score: Callable[[TemplateContext], float]
    ball_height: tuple[tuple[float, float], ...] = ()  # (t_ratio, z) -- 0.0 (au sol) si absent pour ce t_ratio
    # (t_ratio, position normalisée (x, y)) -- position EXPLICITE du ballon à
    # ce t_ratio quand `ball_owner` y vaut `None` (voir DETTE en tête de
    # fichier). Absent de ce tuple pour un `t_ratio` donné où `ball_owner`
    # vaut `None` -> `build_from_template` retombe sur la dernière position
    # connue et émet un avertissement (dette non corrigée pour ce gabarit,
    # jamais une erreur). Position FIXE, pas recalculée depuis
    # `event.zone`/`assist_zone` : `Template` reste event-agnostic partout
    # ailleurs (même esprit que `ball_height`), une intervention minimale ne
    # justifie pas d'en faire la première exception.
    ball_position: tuple[tuple[float, tuple[float, float]], ...] = ()
    # Coup franc/penalty : la séquence démarre une fois le tireur DÉJÀ en
    # position (près du ballon), pas à sa position de formation -- un rôle
    # peut donc légitimement porter le ballon dès t=0 avec un progress non
    # nul (voir tests/test_templates.py::TestNoRoleReliesOnReactionDelay,
    # brief du 23/09/2026 "structural restart-aware rule").
    starts_at_restart: bool = False
    # (t_ratio, physics_tag) -- comportement de trajectoire du ballon pour
    # le segment qui DÉMARRE à ce Keyframe, voir animation.ball et
    # Keyframe.physics_tag (types.py). Modification chirurgicale du
    # 23/09/2026 (phase 3.2, brief "tag-driven trajectory with fallback
    # inference") : SEULS les cas non-ambigus sont taggés explicitement ici
    # -- tout t_ratio absent de ce tuple reste physics_tag=None, et
    # animation.ball.ball_state_at infère un comportement par défaut. Ne
    # PAS chercher à tagger exhaustivement chaque segment de chaque gabarit.
    physics_tags: tuple[tuple[float, str], ...] = ()
    # Ce gabarit se termine par un tir/tête/déviation vers le but -- brief
    # "ball flight after shot" (24/09/2026), voir docs/ball_flight_design.md
    # section 1.3/1.4 : True sur les 12 gabarits actuels (chacun se termine
    # par un rôle qui frappe/dévie vers le but, vérifié gabarit par gabarit
    # dans le design, pas supposé). Seul déclencheur STRUCTUREL -- la
    # décision d'ajouter réellement un segment `ball_flight` à l'exécution
    # dépend aussi de l'`outcome` transmis à `build_from_template` (absent
    # -> comportement actuel inchangé, voir sa docstring).
    has_ball_flight: bool = False


def _validate_template(template: Template) -> None:
    """Tous les rôles d'un même gabarit doivent partager EXACTEMENT le même
    ensemble de `t_ratio` -- le moteur générique (`build_from_template`) ne
    sait pas interpoler entre deux rôles désynchronisés, c'est une
    contrainte d'AUTEUR du gabarit, vérifiée ici plutôt que découverte en
    silence à l'exécution."""
    if not template.roles:
        raise ValueError(f"Gabarit {template.name!r} sans aucun rôle")
    reference = {frame.t_ratio for frame in template.roles[0].frames}
    for role in template.roles[1:]:
        ratios = {frame.t_ratio for frame in role.frames}
        if ratios != reference:
            raise ValueError(
                f"Gabarit {template.name!r} : le rôle {role.name!r} a des t_ratio {sorted(ratios)} "
                f"différents du rôle {template.roles[0].name!r} {sorted(reference)}"
            )


# --- Résolution des rôles vers de vrais joueurs --------------------------


def player_id_of(player: Player) -> PlayerId:
    """Même repli que `events._player_seed_id` côté moteur : `Player.id` si
    connu, sinon le nom (toujours présent)."""
    return player.id if player.id is not None else player.name


# Ordre gardien -> défenseurs -> milieux -> attaquants, utilisé UNIQUEMENT
# pour dériver un numéro de maillot plausible (voir `numeros_by_player_id`).
_NUMERO_GROUP_ORDER = {GOALKEEPER: 0, DEFENDER: 1, MIDFIELDER: 2, ATTACKER: 3}


def numeros_by_player_id(lineup: Lineup) -> dict[PlayerId, int]:
    """Numéro de maillot 1-11 (Point 2 du bilan simulation physique du
    23/09/2026, RosterEntry.numero) -- DÉRIVÉ de la compo, jamais une vraie
    donnée : `Player` ne porte aucun numéro de maillot dans le modèle de
    données actuel (voir docs/simulation_physique_archi.md, à corriger un
    jour par une vraie colonne "Numéro" dans data/joueurs.xlsx, hors scope
    ici). Gardien toujours 1, puis les 10 joueurs de champ triés par groupe
    de poste puis nom, pour un résultat stable et déterministe.

    Volontairement PAS l'index de `lineup.players` lui-même : cet ordre
    reflète l'algorithme d'appariement de `lineup._assign_slots` (tri par
    note décroissante, pas par poste), le gardien n'y est donc PAS garanti
    en première position -- un numéro dérivé de cet ordre brut serait
    instable et n'aurait "GK=1" que par coïncidence.

    `lineup.substitutes` (brief "canvas player consolidation", 23/09/2026,
    Tâche 2) reçoit des numéros 12+ (même tri groupe+nom, à la suite des 11
    titulaires) -- vide par défaut, donc AUCUN changement de comportement
    pour un `Lineup` sans remplaçants (tout le code/tests existants avant
    cette Tâche 2 continuent de voir exactement les mêmes numéros 1-11)."""
    ordered = sorted(lineup.players, key=lambda p: (_NUMERO_GROUP_ORDER.get(p.group, 4), p.name))
    numeros = {player_id_of(p): numero for numero, p in enumerate(ordered, start=1)}
    ordered_subs = sorted(lineup.substitutes, key=lambda p: (_NUMERO_GROUP_ORDER.get(p.group, 4), p.name))
    numeros.update({player_id_of(p): numero for numero, p in enumerate(ordered_subs, start=len(ordered) + 1)})
    return numeros


def _resolve_roles(event: GoalEvent, lineup: Lineup, role_names: tuple[str, ...]) -> dict[str, Player]:
    """Associe chaque rôle nommé d'un gabarit à un vrai joueur de `lineup`.
    "scorer"/"assist" sont résolus depuis l'événement lui-même, jamais
    inventés -- un rôle "assist" sans passeur réel (`event.assist is None`)
    est simplement absent du résultat (le gabarit continue sans lui, voir
    `build_from_template`). Les rôles génériques ("support1", "support2"...)
    sont comblés par les coéquipiers restants (hors gardien, hors
    scorer/assist déjà pris), triés par nom pour un résultat déterministe :
    `build_from_template` est une fonction PURE, jamais un tirage.

    `lineup.players` ET `lineup.substitutes` (brief "canvas player
    consolidation", 23/09/2026, Tâche 2) sont tous deux éligibles à
    n'importe quel rôle -- un buteur/passeur/coéquipier générique peut être
    un remplaçant entré en jeu, pas seulement un titulaire. `substitutes`
    vide par défaut : comportement inchangé pour tout appelant antérieur à
    cette Tâche 2."""
    roster = list(lineup.players) + list(lineup.substitutes)
    by_name = {p.name: p for p in roster}
    resolved: dict[str, Player] = {}
    used_names: set[str] = set()

    if "scorer" in role_names:
        scorer = by_name.get(event.scorer)
        if scorer is None:
            raise ValueError(f"Buteur {event.scorer!r} introuvable dans la compo fournie")
        resolved["scorer"] = scorer
        used_names.add(scorer.name)

    if "assist" in role_names and event.assist is not None:
        assist = by_name.get(event.assist)
        if assist is None:
            raise ValueError(f"Passeur {event.assist!r} introuvable dans la compo fournie")
        resolved["assist"] = assist
        used_names.add(assist.name)

    remaining_generic = [name for name in role_names if name not in resolved and name != "assist"]
    candidates = sorted(
        (p for p in roster if p.group != GOALKEEPER and p.name not in used_names), key=lambda p: p.name
    )
    for role_name, player in zip(remaining_generic, candidates):
        resolved[role_name] = player
        used_names.add(player.name)

    return resolved


# --- Moteur générique ------------------------------------------------------


def _lerp(a: PitchPoint, b: PitchPoint, progress: float) -> PitchPoint:
    clamped = min(1.0, max(0.0, progress))
    return PitchPoint(x=a.x + (b.x - a.x) * clamped, y=a.y + (b.y - a.y) * clamped)


def _anchor_point(anchor: str, start: PitchPoint, event: GoalEvent) -> PitchPoint:
    if anchor == ANCHOR_STATIC:
        return start
    if anchor == ANCHOR_SCORER:
        return center_of(event.zone)
    if anchor == ANCHOR_ASSIST:
        zone = event.assist_zone if event.assist_zone is not None else event.zone
        return center_of(zone)
    if anchor == ANCHOR_LATERAL_SHIFT:
        return PitchPoint(x=start.x, y=start.y + _LATERAL_SHIFT_M / PITCH_WIDTH_M)
    raise ValueError(f"Ancrage de rôle inconnu : {anchor!r}")


# --- Vol du ballon après la frappe (`ball_flight`) --------------------------
# Brief "ball flight after shot" (24/09/2026), voir docs/ball_flight_design.md
# -- segment ajouté APRÈS le dernier segment porté (approche/centre/corner
# actuel, inchangé) : le ballon quitte enfin le pied du tireur pour une
# trajectoire explicite vers une cible dérivée de l'ISSUE réelle de l'action
# (`NarrativeEvent.outcome`, transmis par `narrative_player.py`, voir Tâche 2
# du brief -- absent ici : `outcome` reste un paramètre OPTIONNEL de
# `build_from_template`, `None` préserve exactement le comportement actuel).
#
# Géométrie de la cage (référentiel normalisé, voir pitch_geometry.py) : but
# adverse sur la ligne x=1.0, centré y=0.5, largeur réglementaire 7,32m
# (+/-3,66m), hauteur réglementaire 2,44m -- PAS de `Zone` (grille
# GRID_COLUMNS x GRID_ROWS) : une case de la grille existante (~8,75m de
# large) est plus large que le but lui-même, trop grossière (voir design
# doc, section 1.2).
_GOAL_Y_CENTER = 0.5
_GOAL_HALF_WIDTH_Y = 3.66 / PITCH_WIDTH_M
_GOAL_Y_MIN = _GOAL_Y_CENTER - _GOAL_HALF_WIDTH_Y  # ~0.4462
_GOAL_Y_MAX = _GOAL_Y_CENTER + _GOAL_HALF_WIDTH_Y  # ~0.5538

# Vitesse cible du vol (Tâche 2.7/4.4 du brief) -- référence donnée par le
# propriétaire : un tir réel de Ligue 1 part à 25-30 m/s, intervalle accepté
# [15, 35] m/s. Tirage déterministe (voir `_flight_unit`), jamais `random`
# global.
_FLIGHT_MIN_SPEED_MPS = 15.0
_FLIGHT_MAX_SPEED_MPS = 35.0

# Issues qui interrompent l'action AVANT le tir (défenseur intervient) --
# aucun `ball_flight` pour celles-ci (design doc, section 1.4). Toute AUTRE
# valeur d'`outcome` non listée ci-dessous ET absente de `_flight_target`
# lève une erreur explicite plutôt que de retomber silencieusement sur
# "pas de vol" -- une issue inconnue est une dérive du modèle de données à
# signaler, pas un cas à absorber sans bruit.
_NO_FLIGHT_OUTCOMES = frozenset({"tacle", "degagement"})


def _flight_unit(event_ref: str, salt: str) -> float:
    """Fraction déterministe dans [0, 1) -- même principe que
    `ball._deterministic_unit`/`motion._start_offset` (hash sha256, jamais
    `hash()` ni `random`). Copie locale plutôt qu'import de `animation.ball`
    -- même convention que `motion.py`/`ball.py` eux-mêmes, qui se
    réimplémentent chacun leur propre `_real_distance_m` pour ne pas se
    coupler entre modules."""
    digest = hashlib.sha256(f"ball_flight|{salt}|{event_ref}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _flight_target(outcome: str, event_ref: str) -> tuple[float, float, float] | None:
    """Point cible `(x, y, z)` du vol dérivé de `outcome` (design doc,
    section 1.2) -- `None` pour une issue qui n'a pas de vol
    (`_NO_FLIGHT_OUTCOMES`). `z` en MÈTRES (convention `BallState.z`), `x`/`y`
    normalisés -- `x` peut légitimement dépasser 1.0 pour l'issue "but" (le
    filet est physiquement derrière la ligne, hors terrain)."""
    if outcome in _NO_FLIGHT_OUTCOMES:
        return None
    if outcome == "but":
        x = 1.00 + _flight_unit(event_ref, "x") * 0.02
        y = _GOAL_Y_MIN + _flight_unit(event_ref, "y") * (_GOAL_Y_MAX - _GOAL_Y_MIN)
        z = _flight_unit(event_ref, "z") * 2.40
        return (x, y, z)
    if outcome == "arret":
        x = 0.98 + _flight_unit(event_ref, "x") * 0.02
        y = 0.47 + _flight_unit(event_ref, "y") * 0.06
        z = _flight_unit(event_ref, "z") * 2.0
        return (x, y, z)
    if outcome == "poteau":
        x = 1.00 + (_flight_unit(event_ref, "x") - 0.5) * 0.01
        left_post = _flight_unit(event_ref, "side") < 0.5
        base_y = _GOAL_Y_MIN if left_post else _GOAL_Y_MAX
        y = base_y + (_flight_unit(event_ref, "y") - 0.5) * 0.01
        z = _flight_unit(event_ref, "z") * 2.2
        return (x, y, z)
    if outcome == "barre":
        x = 1.00 + (_flight_unit(event_ref, "x") - 0.5) * 0.01
        y = _GOAL_Y_MIN + _flight_unit(event_ref, "y") * (_GOAL_Y_MAX - _GOAL_Y_MIN)
        z = 2.35 + _flight_unit(event_ref, "z") * (2.44 - 2.35)
        return (x, y, z)
    if outcome == "hors_cadre":
        x = 0.97 + _flight_unit(event_ref, "x") * 0.06
        wide_right = _flight_unit(event_ref, "side") >= 0.5
        y = (
            _GOAL_Y_MAX + _flight_unit(event_ref, "y") * (1.0 - _GOAL_Y_MAX)
            if wide_right
            else _flight_unit(event_ref, "y") * _GOAL_Y_MIN
        )
        z = _flight_unit(event_ref, "z") * 3.5
        return (x, y, z)
    raise ValueError(
        f"outcome {outcome!r} inconnu de _flight_target -- ni dans _NO_FLIGHT_OUTCOMES "
        "ni dans les issues avec cible (but/arret/poteau/barre/hors_cadre), voir "
        "docs/ball_flight_design.md section 1.2"
    )


def _flight_distance_m(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    """Distance 3D (m) entre deux points `(x, y, z)` -- `x`/`y` normalisés
    (voir `PITCH_LENGTH_M`/`PITCH_WIDTH_M`), `z` deja en metres. Corrige le
    24/09/2026 (2D -> 3D) : la duree du vol calculee sur la seule distance
    x/y sous-estimait le trajet reel quand la cible est haute par rapport a
    une distance horizontale courte (ex. tete proche du but envoyee
    "hors_cadre", z jusqu'a 3,5m) -- vitesse 3D realisee alors superieure au
    tirage voulu. Signature volontairement large (3-uplet, pas 2) pour que
    l'oubli de z ne puisse plus se reproduire au meme endroit."""
    dx_m = (b[0] - a[0]) * PITCH_LENGTH_M
    dy_m = (b[1] - a[1]) * PITCH_WIDTH_M
    dz_m = b[2] - a[2]
    return math.hypot(math.hypot(dx_m, dy_m), dz_m)


def build_from_template(
    template: Template,
    event: GoalEvent,
    lineup: Lineup,
    start_positions: dict[PlayerId, PitchPoint],
    outcome: str | None = None,
) -> Sequence:
    """Moteur générique partagé par les 12 gabarits (voir en bas de fichier
    pour leurs wrappers `build_xxx`). Fonction PURE : mêmes entrées, même
    `Sequence`, aucun tirage aléatoire -- la part de hasard de ce module se
    limite au CHOIX du gabarit (`pick_template`), jamais à son exécution.

    `outcome` (brief "ball flight after shot", 24/09/2026, voir
    docs/ball_flight_design.md) : paramètre OPTIONNEL, `None` par défaut --
    préserve EXACTEMENT le comportement d'avant ce brief (aucun segment
    `ball_flight` ajouté). Transmis par `narrative_player.py` depuis
    `NarrativeEvent.outcome` (Tâche 2 du brief) ; si fourni ET
    `template.has_ball_flight`, un segment de vol est ajouté après le
    dernier segment porté -- voir `_flight_target`. `outcome in
    ("tacle", "degagement")` : aucun vol (action interrompue avant le tir),
    voir `_NO_FLIGHT_OUTCOMES`."""
    _validate_template(template)

    role_names = tuple(role.name for role in template.roles)
    resolved = _resolve_roles(event, lineup, role_names)
    role_ids = {name: player_id_of(player) for name, player in resolved.items()}
    role_starts = {name: start_positions[role_ids[name]] for name in resolved}
    role_by_player_id = {player_id: role_name for role_name, player_id in role_ids.items()}
    # + lineup.substitutes (Tâche 2) : un rôle résolu vers un remplaçant
    # (voir _resolve_roles) doit rester trouvable ici pour construire son
    # RosterEntry -- substitutes vide par défaut, comportement inchangé sinon.
    players_by_id = {player_id_of(p): p for p in list(lineup.players) + list(lineup.substitutes)}
    numeros = numeros_by_player_id(lineup)
    roster = {
        player_id: RosterEntry(
            nom=players_by_id[player_id].name,
            poste=players_by_id[player_id].poste,
            role=role_by_player_id.get(player_id),
            numero=numeros[player_id],
            team_side="scorer",
        )
        for player_id in start_positions
    }
    role_ends = {
        role.name: _anchor_point(role.end_anchor, role_starts[role.name], event)
        for role in template.roles
        if role.name in resolved
    }

    tags_by_ratio = dict(template.tags)
    ball_owner_by_ratio = dict(template.ball_owner)
    ball_height_by_ratio = dict(template.ball_height)
    ball_position_by_ratio = dict(template.ball_position)
    physics_tags_by_ratio = dict(template.physics_tags)
    timeline = sorted({frame.t_ratio for role in template.roles for frame in role.frames})

    keyframes: list[Keyframe] = []
    last_ball_xy = center_of(event.zone)
    for t_ratio in timeline:
        players: dict[PlayerId, tuple[float, float]] = {
            player_id: (point.x, point.y) for player_id, point in start_positions.items()
        }
        for role in template.roles:
            if role.name not in resolved:
                continue
            frame = next((f for f in role.frames if f.t_ratio == t_ratio), None)
            if frame is None:
                continue
            point = _lerp(role_starts[role.name], role_ends[role.name], frame.progress)
            players[role_ids[role.name]] = (point.x, point.y)

        owner_role = ball_owner_by_ratio.get(t_ratio)
        owner_id: PlayerId | None = None
        if owner_role is not None and owner_role in role_ids:
            owner_id = role_ids[owner_role]
            ball_x, ball_y = players[owner_id]
        elif t_ratio in ball_position_by_ratio:
            ball_x, ball_y = ball_position_by_ratio[t_ratio]
        else:
            ball_x, ball_y = last_ball_xy.x, last_ball_xy.y
            _logger.warning(
                "%s@t_ratio=%s : ball_owner=None sans ball_position -- ballon figé sur sa dernière "
                "position connue (dette du 23/09/2026, voir DETTE en tête de templates.py)",
                template.name, t_ratio,
            )
        last_ball_xy = PitchPoint(x=ball_x, y=ball_y)

        keyframes.append(
            Keyframe(
                t=t_ratio * template.duration,
                ball=BallState(x=ball_x, y=ball_y, z=ball_height_by_ratio.get(t_ratio, 0.0), spin=0.0, owner_id=owner_id),
                players=players,
                tag=tags_by_ratio.get(t_ratio, ""),
                physics_tag=physics_tags_by_ratio.get(t_ratio),
            )
        )

    event_ref = f"goal:{event.club_name}:{event.scorer}:{event.minute}"
    duration = template.duration

    if outcome is not None and template.has_ball_flight:
        target = _flight_target(outcome, event_ref)
        if target is not None:
            target_x, target_y, target_z = target
            start_z = keyframes[-1].ball.z
            distance_m = _flight_distance_m((last_ball_xy.x, last_ball_xy.y, start_z), (target_x, target_y, target_z))
            speed_mps = _FLIGHT_MIN_SPEED_MPS + _flight_unit(event_ref, "speed") * (
                _FLIGHT_MAX_SPEED_MPS - _FLIGHT_MIN_SPEED_MPS
            )
            flight_duration = distance_m / speed_mps if speed_mps > 0 else 0.0
            flight_start_players = keyframes[-1].players
            keyframes[-1] = replace(keyframes[-1], physics_tag=BALL_FLIGHT)
            keyframes.append(
                Keyframe(
                    t=duration + flight_duration,
                    ball=BallState(x=target_x, y=target_y, z=target_z, spin=0.0, owner_id=None),
                    players=flight_start_players,
                    tag="vol",
                    physics_tag=None,
                )
            )
            duration += flight_duration

    return Sequence(
        event_ref=event_ref,
        keyframes=keyframes,
        duration=duration,
        meta={"template": template.name, "roles": {name: player.name for name, player in resolved.items()}},
        roster=roster,
    )


# --- Les 12 gabarits -------------------------------------------------------
#
# `context_score` : multiplicateurs volontairement modestes et documentés
# (même esprit que les constantes de events.py -- ajustables, pas une
# vérité absolue), pas un modèle statistique. Un score de 0.0 exclut le
# gabarit pour ce contexte (ex. "penalty" hors penalty).

_ATTACKING_POSTES = {"AG", "AD", "BU", "SA", "MOC", "ATT"}
_CREATIVE_MIDFIELD_POSTES = {"MC", "MDC", "MOC"}
_WIDE_POSTES = {"AG", "AD"}
_AERIAL_POSTES = {"DC", "BU", "SA"}


def _urgency_factor(goal_diff_before: int) -> float:
    """Facteur d'urgence dérivé du rapport de force AVANT le but -- >1 si
    l'équipe était menée (urgence, pousse vers des schémas directs/rapides),
    <1 si elle menait déjà confortablement (peut se permettre la patience).
    Paliers volontairement modestes et documentés (même esprit que le reste
    des `context_score`), pas un modèle statistique calibré sur de vraies
    données -- voir `TemplateContext.goal_diff_before`."""
    if goal_diff_before <= -2:
        return 1.6
    if goal_diff_before == -1:
        return 1.3
    if goal_diff_before == 0:
        return 1.0
    if goal_diff_before == 1:
        return 0.85
    return 0.65  # goal_diff_before >= 2 : équipe déjà nettement devant


def _score_default(_: TemplateContext) -> float:
    return 1.0


def _score_contre_attaque(context: TemplateContext) -> float:
    if context.penalty:
        return 0.0
    base = 1.4 if context.assist_poste in _CREATIVE_MIDFIELD_POSTES else 1.0
    return base * _urgency_factor(context.goal_diff_before)


def _score_construction_placee(context: TemplateContext) -> float:
    if context.penalty:
        return 0.0
    base = 1.3 if context.assist_poste in _CREATIVE_MIDFIELD_POSTES | {"DC", "LB", "RB"} else 0.8
    # Inverse de l'urgence : une équipe qui mène déjà peut se permettre de
    # construire patiemment, une équipe menée n'en a pas le luxe.
    return base / _urgency_factor(context.goal_diff_before)


def _score_debordement_centre_tete(context: TemplateContext) -> float:
    if context.penalty:
        return 0.0
    boost = 1.0
    if context.scorer_poste in _AERIAL_POSTES:
        boost *= 1.6
    if context.assist_poste in _WIDE_POSTES:
        boost *= 1.6
    return boost


def _score_percee_individuelle(context: TemplateContext) -> float:
    if context.penalty or context.assist_poste is not None:
        return 0.0 if context.penalty else 0.6
    base = 1.8 if context.scorer_poste in _ATTACKING_POSTES else 0.9
    return base * _urgency_factor(context.goal_diff_before)


def _score_une_deux(context: TemplateContext) -> float:
    if context.penalty or context.assist_poste is None:
        return 0.0 if context.penalty else 0.5
    return 1.5 if context.assist_poste in _ATTACKING_POSTES else 0.8


def _score_coup_franc(context: TemplateContext) -> float:
    return 0.0 if context.penalty else 0.5


def _score_corner(context: TemplateContext) -> float:
    if context.penalty:
        return 0.0
    return 1.3 if context.scorer_poste in _AERIAL_POSTES else 0.6


def _score_profondeur_1v1(context: TemplateContext) -> float:
    if context.penalty or context.assist_poste is None:
        return 0.0 if context.penalty else 0.5
    boost = 1.0
    if context.assist_poste in _CREATIVE_MIDFIELD_POSTES:
        boost *= 1.5
    if context.scorer_poste in _ATTACKING_POSTES:
        boost *= 1.4
    return boost


def _score_recuperation_haute(context: TemplateContext) -> float:
    if context.penalty or context.assist_poste is not None:
        return 0.0 if context.penalty else 0.5
    base = 1.4 if context.scorer_poste in _ATTACKING_POSTES else 0.9
    return base * _urgency_factor(context.goal_diff_before)


def _score_decalage_enroulee(context: TemplateContext) -> float:
    if context.penalty:
        return 0.0
    return 1.7 if context.scorer_poste in _WIDE_POSTES else 0.7


def _score_penalty(context: TemplateContext) -> float:
    return 5.0 if context.penalty else 0.0


def _score_but_gag(context: TemplateContext) -> float:
    # Rare par construction (poids de base bas) -- le moteur n'a aucune
    # notion de "contre son camp"/déviation (voir GoalEvent, toujours
    # crédité au vrai buteur de l'équipe qui marque), ce gabarit habille
    # donc un but ordinaire d'un mouvement chaotique, juste pour la
    # variété visuelle, jamais une vraie mécanique de jeu.
    if context.penalty:
        return 0.0
    # Moins plausible dans un match à élimination directe (coupe/continentale)
    # qu'en championnat -- les enjeux laissent moins de place à un but chaotique.
    return 0.6 if context.competition_type != "league" else 1.0


_TEMPLATE_CONTRE_ATTAQUE = Template(
    name="contre_attaque",
    weight=1.2,
    duration=8.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (bug corrigé le 23/09/2026 : un
        # ANCHOR_STATIC fige la cible = le départ, donc TOUT progress non nul
        # à côté est mort -- support1 restait immobile malgré le 0.3 déclaré,
        # alors qu'il porte le ballon à t=0). support1 récupère le ballon
        # profond, le CONDUIT vers l'avant (30% du chemin vers la zone de tir)
        # jusqu'à la passe à `assist` (t_ratio=0.4), PUIS CONTINUE d'avancer
        # en décélérant (0.3 -> 0.4 sur les 60% restants de la séquence,
        # correction du 23/09/2026 suite 2 : un arrêt net juste après la
        # passe lisait comme "il a débranché", pas une décélération naturelle
        # de coureur qui accompagne brièvement l'action avant de ralentir).
        # Cible = zone de TIR (ANCHOR_SCORER), pas la zone de passe
        # (ANCHOR_ASSIST) : c'est vers le BUT que le porteur progresse, la
        # passe n'est qu'une étape -- COUPLAGE ASSUMÉ : la direction exacte
        # de support1 dépend donc de où `event.zone` tombe (le tir peut être
        # excentré), pas d'une direction "devant lui" indépendante. Dans ce
        # gabarit, avec le buteur qui fait son appel globalement dans l'axe,
        # l'effet reste plausible ; pas généralisé à un anchor dédié
        # (ANCHOR_CARRIER_FORWARD) tant qu'un seul gabarit en a besoin.
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.3), RoleFrame(1.0, 0.4))),
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.2), RoleFrame(1.0, 1.0))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.35), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "recuperation"), (0.4, "progression"), (1.0, "tir")),
    ball_owner=((0.0, "support1"), (0.4, "assist"), (1.0, "scorer")),
    context_score=_score_contre_attaque,
    physics_tags=((0.4, "shot"),),  # dernier segment (0.4 -> 1.0) : le tir au but
    has_ball_flight=True,
)

_TEMPLATE_CONSTRUCTION_PLACEE = Template(
    name="construction_placee",
    weight=1.0,
    duration=14.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (fix du 23/09/2026, même bug que
        # contre_attaque.support1) : support1 porte le ballon de t=0 à t=0.3
        # ("circulation") avant de le céder à assist -- un porteur qui
        # circule sans bouger contredit son propre tag. Progress final relevé
        # 0.25 -> 0.35 pour éviter le même arrêt net qu'à la Tâche 1 après
        # la passe. Couplage à event.zone assumé, voir contre_attaque.
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.2), RoleFrame(0.6, 0.25), RoleFrame(1.0, 0.35))),
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.15), RoleFrame(0.6, 0.5), RoleFrame(1.0, 1.0))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.1), RoleFrame(0.6, 0.4), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "recuperation"), (0.3, "circulation"), (0.6, "progression"), (1.0, "tir")),
    ball_owner=((0.0, "support1"), (0.3, "support1"), (0.6, "assist"), (1.0, "scorer")),
    context_score=_score_construction_placee,
    physics_tags=((0.6, "shot"),),  # dernier segment (0.6 -> 1.0) : le tir au but
    has_ball_flight=True,
)

_TEMPLATE_DEBORDEMENT = Template(
    name="debordement_centre_tete",
    weight=1.0,
    duration=6.0,
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.6, 0.7), RoleFrame(1.0, 1.0))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.6, 0.4), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "debordement"), (0.6, "centre"), (1.0, "tete")),
    ball_owner=((0.0, "assist"), (0.6, "assist"), (1.0, "scorer")),
    ball_height=((0.6, 0.6), (1.0, 0.3)),
    context_score=_score_debordement_centre_tete,
    physics_tags=((0.6, "shot"),),  # dernier segment (0.6 -> 1.0) : la tête au but
    has_ball_flight=True,
)

_TEMPLATE_PERCEE_INDIVIDUELLE = Template(
    name="percee_individuelle",
    weight=0.9,
    duration=7.0,
    roles=(Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.35), RoleFrame(0.75, 0.7), RoleFrame(1.0, 1.0))),),
    tags=((0.0, "controle"), (0.4, "dribble"), (0.75, "dribble"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.4, "scorer"), (0.75, "scorer"), (1.0, "scorer")),
    context_score=_score_percee_individuelle,
    physics_tags=((0.75, "shot"),),  # dernier segment (0.75 -> 1.0) : le tir au but
    has_ball_flight=True,
)

_TEMPLATE_UNE_DEUX = Template(
    name="une_deux",
    weight=0.8,
    duration=4.0,
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.5), RoleFrame(1.0, 0.5))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.6), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "passe"), (0.5, "remise"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.5, "assist"), (1.0, "scorer")),
    context_score=_score_une_deux,
    physics_tags=((0.5, "shot"),),  # dernier segment (0.5 -> 1.0) : le tir au but
    has_ball_flight=True,
)

_TEMPLATE_COUP_FRANC = Template(
    name="coup_franc",
    weight=0.4,
    duration=5.0,
    # ANCHOR_SCORER, pas ANCHOR_STATIC : le tireur est déjà positionné près du
    # ballon au coup franc (frame 0 proche de la zone), pas à sa position de
    # formation d'origine -- peu de déplacement, mais vers le bon point.
    roles=(Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.8), RoleFrame(0.7, 0.9), RoleFrame(1.0, 1.0))),),
    tags=((0.0, "placement"), (0.7, "elan"), (1.0, "frappe")),
    ball_owner=((0.0, "scorer"), (0.7, "scorer"), (1.0, "scorer")),
    context_score=_score_coup_franc,
    starts_at_restart=True,
    physics_tags=((0.7, "shot"),),  # dernier segment (0.7 -> 1.0) : la frappe
    has_ball_flight=True,
)

_TEMPLATE_CORNER = Template(
    # Enrichi le 23/09/2026 (audit visuel, scripts/preview_templates.py) :
    # 2 rôles -> 3 (ajout de "support1", un appel au premier poteau qui
    # attire des défenseurs sans être lui-même le buteur -- un vrai corner
    # implique presque toujours plusieurs coureurs, pas un duel à un seul
    # attaquant), 3 keyframes -> 4 (phase de préparation visible avant la
    # montée en zone).
    name="corner",
    weight=0.5,
    duration=7.0,
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.4), RoleFrame(0.6, 1.0), RoleFrame(1.0, 1.0))),
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.2), RoleFrame(0.6, 0.5), RoleFrame(1.0, 0.55))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.15), RoleFrame(0.6, 0.6), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "preparation"), (0.3, "montee"), (0.6, "centre"), (1.0, "tete")),
    ball_owner=((0.0, "assist"), (0.3, "assist"), (0.6, None), (1.0, "scorer")),
    ball_height=((0.0, 0.0), (0.3, 0.0), (0.6, 0.8), (1.0, 0.3)),
    # Position fixe approximative (voir la docstring du champ sur Template) :
    # zone de réception typique d'un corner (six mètres, entre le point de
    # centre et le but) -- sans elle, le segment "cross" 0.3->0.6 partirait
    # d'un ballon figé sur sa dernière position connue (dette ball_owner=None,
    # voir DETTE en tête de fichier) : un centre immobile en plein vol.
    ball_position=((0.6, (0.93, 0.5)),),
    context_score=_score_corner,
    # Table des tags de corner (brief "corner tags decision", 23/09/2026) --
    # tranche le conflit cross/deflect signalé sur la keyframe "ballon
    # disputé" (t=0.6) : ce n'est pas UN segment ambigu, ce sont DEUX
    # segments distincts de part et d'autre de cette keyframe, chacun avec
    # son propre tag.
    # segment [0.0 -> 0.3] : pass_ground -- assist porte le ballon au sol en marchant vers le point de corner
    # segment [0.3 -> 0.6] : cross -- le centre lui-même, ballon en vol vers la zone disputée (keyframe "centre")
    # segment [0.6 -> 1.0] : deflect -- ballon disputé au contact (owner=None à 0.6, keyframe "ballon disputé") avant la tête du buteur
    physics_tags=((0.0, "pass_ground"), (0.3, "cross"), (0.6, "deflect")),
    has_ball_flight=True,
)

_TEMPLATE_PROFONDEUR_1V1 = Template(
    name="profondeur_1v1",
    weight=0.9,
    duration=6.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (fix du 23/09/2026) : le passeur
        # en profondeur doit suivre sa passe d'un ou deux pas plutôt que
        # rester planté après avoir lâché le ballon (t_ratio=0.3). Progress
        # relevé 0.1 -> 0.15/0.2, couplage à event.zone assumé (voir
        # contre_attaque).
        Role("assist", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.15), RoleFrame(1.0, 0.2))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.3), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "appel"), (0.3, "passe"), (1.0, "1v1")),
    ball_owner=((0.0, "assist"), (0.3, "scorer"), (1.0, "scorer")),
    context_score=_score_profondeur_1v1,
    physics_tags=((0.3, "shot"),),  # dernier segment (0.3 -> 1.0) : le 1v1 conclu au tir
    has_ball_flight=True,
)

_TEMPLATE_RECUPERATION_HAUTE = Template(
    # Enrichi le 23/09/2026 (audit visuel) : 1 rôle/2 keyframes (le plus
    # pauvre des 12 à l'origine) -> 3 rôles/4 keyframes. Un pressing haut
    # efficace est presque toujours collectif (2 joueurs qui referment
    # ensemble l'espace) plutôt qu'un attaquant qui récupère seul ET
    # marque seul -- "support1"/"support2" pressent, "support1" récupère,
    # relais rapide vers "scorer" qui conclut ("immédiate" reste vrai : le
    # temps entre récupération et tir est court, voir la durée).
    name="recuperation_haute",
    weight=0.8,
    duration=5.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (fix du 23/09/2026) : le
        # commentaire ci-dessus décrit un pressing ACTIF ("support1/support2
        # pressent, support1 récupère") -- un presseur immobile contredit
        # son propre texte. Progress final relevé (0.4->0.5, 0.45->0.55) :
        # les deux avancent ensemble en pressant vers l'avant, couplage à
        # event.zone assumé (voir contre_attaque).
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.3), RoleFrame(0.55, 0.4), RoleFrame(1.0, 0.5))),
        Role("support2", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.35), RoleFrame(0.55, 0.45), RoleFrame(1.0, 0.55))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.2), RoleFrame(0.55, 0.5), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "pressing"), (0.3, "pressing"), (0.55, "recuperation"), (1.0, "tir")),
    ball_owner=((0.0, "support1"), (0.3, None), (0.55, "support1"), (1.0, "scorer")),
    # Position fixe approximative (voir la docstring du champ sur Template,
    # même dette ball_owner=None que corner ci-dessus) -- zone de pressing/
    # ballon disputé, dans la moitié offensive. Repérée en écrivant
    # test_no_immobile_segment_in_flight_actions (Tâche 2) : sans elle, le
    # segment [0.0 -> 0.3] (inféré pass_ground, porteur=support1 à t=0) part
    # et arrive au même point figé -- ballon immobile en plein pressing.
    ball_position=((0.3, (0.6, 0.5)),),
    context_score=_score_recuperation_haute,
    # t=0.3 : porteur=None (ballon disputé pendant le pressing) -> deflect.
    # 0.55 (dernier segment avant 1.0) : shot, le tir de conclusion.
    physics_tags=((0.3, "deflect"), (0.55, "shot")),
    has_ball_flight=True,
)

_TEMPLATE_DECALAGE_ENROULEE = Template(
    name="decalage_enroulee",
    weight=0.9,
    duration=6.0,
    roles=(
        Role("assist", ANCHOR_STATIC, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.0), RoleFrame(1.0, 0.0))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.3), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "decalage"), (0.4, "controle"), (1.0, "enroulee")),
    ball_owner=((0.0, "assist"), (0.4, "scorer"), (1.0, "scorer")),
    context_score=_score_decalage_enroulee,
    physics_tags=((0.4, "shot"),),  # dernier segment (0.4 -> 1.0) : l'enroulée
    has_ball_flight=True,
)

_TEMPLATE_PENALTY = Template(
    # Enrichi le 23/09/2026 (audit visuel) : 1 rôle -> 3 (deux coéquipiers
    # à l'entrée de la surface, à l'affût d'un rebond -- une scène de
    # penalty réaliste n'est jamais un tireur totalement seul sur le
    # terrain). Phase de préparation/attente désormais explicite avant
    # l'élan (0.0 -> 0.5), pas juste un élan puis un tir.
    name="penalty",
    weight=0.6,
    duration=4.0,
    roles=(
        # ANCHOR_LATERAL_SHIFT, pas ANCHOR_STATIC (fix du 23/09/2026) : le
        # commentaire promettait un "léger frémissement d'anticipation", mais
        # ANCHOR_STATIC fige la cible = le départ -- AUCUNE valeur de
        # progress, même petite, ne peut y produire le moindre mouvement
        # (`_lerp(x,x,p)=x`). Restent à l'entrée de la surface : pas
        # ANCHOR_SCORER, ils n'ont aucune raison de converger vers le point
        # de penalty -- juste un pas de côté fixe (_LATERAL_SHIFT_M, 1,5 m).
        # Progress relevé 0.05 -> 0.4 (fix "suite 2" du 23/09/2026) : la
        # première version (25 cm x 0.05 = 1,25 cm réels, 0,14 px) était
        # mathématiquement non nulle mais visuellement invisible -- 1,5 m x
        # 0.4 = 60 cm réels, un pas de côté visible et crédible.
        Role("support1", ANCHOR_LATERAL_SHIFT, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.4), RoleFrame(0.85, 0.4), RoleFrame(1.0, 0.4))),
        Role("support2", ANCHOR_LATERAL_SHIFT, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.4), RoleFrame(0.85, 0.4), RoleFrame(1.0, 0.4))),
        # ANCHOR_SCORER, pas ANCHOR_STATIC : le tireur est déjà debout devant
        # le ballon au point de penalty (frame 0 très proche de la zone),
        # pas à sa position de formation d'origine.
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.85), RoleFrame(0.5, 0.9), RoleFrame(0.85, 0.95), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "placement"), (0.5, "attente"), (0.85, "elan"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.5, "scorer"), (0.85, "scorer"), (1.0, "scorer")),
    context_score=_score_penalty,
    starts_at_restart=True,
    physics_tags=((0.85, "shot"),),  # dernier segment (0.85 -> 1.0) : le tir
    has_ball_flight=True,
)

_TEMPLATE_BUT_GAG = Template(
    # Enrichi le 23/09/2026 (audit visuel) : 2 rôles/3 keyframes -> 3
    # rôles/4 keyframes -- une vraie scène de but chaotique implique
    # généralement plusieurs contacts successifs (double rebond), pas une
    # seule déviation nette.
    name="but_gag",
    weight=0.15,
    duration=5.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (fix du 23/09/2026) : support1
        # touche le ballon à t=0.35 ("premier_contact"), support2 à t=0.65
        # ("rebond") -- une déviation implique un léger mouvement du joueur
        # qui dévie, pas une immobilité totale. Progress final relevé
        # (0.15->0.3, 0.2->0.35) pour rendre le déplacement effectif après
        # le contact, couplage à event.zone assumé (voir contre_attaque).
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.35, 0.15), RoleFrame(0.65, 0.15), RoleFrame(1.0, 0.3))),
        Role("support2", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.35, 0.1), RoleFrame(0.65, 0.25), RoleFrame(1.0, 0.35))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.35, 0.3), RoleFrame(0.65, 0.6), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "centre"), (0.35, "premier_contact"), (0.65, "rebond"), (1.0, "but")),
    # (1.0, "scorer") et pas None : un ball_owner absent retombe sur la
    # DERNIÈRE position connue (voir build_from_template), donc le ballon
    # n'atteindrait jamais event.zone si le dernier point restait sans
    # porteur -- repéré visuellement via scripts/preview_templates.py.
    ball_owner=((0.0, "scorer"), (0.35, "support1"), (0.65, "support2"), (1.0, "scorer")),
    context_score=_score_but_gag,
    physics_tags=((0.65, "shot"),),  # dernier segment (0.65 -> 1.0) : la déviation finale au but
    has_ball_flight=True,
)

TEMPLATES: dict[str, Template] = {
    template.name: template
    for template in (
        _TEMPLATE_CONTRE_ATTAQUE,
        _TEMPLATE_CONSTRUCTION_PLACEE,
        _TEMPLATE_DEBORDEMENT,
        _TEMPLATE_PERCEE_INDIVIDUELLE,
        _TEMPLATE_UNE_DEUX,
        _TEMPLATE_COUP_FRANC,
        _TEMPLATE_CORNER,
        _TEMPLATE_PROFONDEUR_1V1,
        _TEMPLATE_RECUPERATION_HAUTE,
        _TEMPLATE_DECALAGE_ENROULEE,
        _TEMPLATE_PENALTY,
        _TEMPLATE_BUT_GAG,
    )
}


def build_contre_attaque(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["contre_attaque"], event, lineup, start_positions, outcome)


def build_construction_placee(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["construction_placee"], event, lineup, start_positions, outcome)


def build_debordement_centre_tete(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["debordement_centre_tete"], event, lineup, start_positions, outcome)


def build_percee_individuelle(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["percee_individuelle"], event, lineup, start_positions, outcome)


def build_une_deux(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["une_deux"], event, lineup, start_positions, outcome)


def build_coup_franc(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["coup_franc"], event, lineup, start_positions, outcome)


def build_corner(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["corner"], event, lineup, start_positions, outcome)


def build_profondeur_1v1(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["profondeur_1v1"], event, lineup, start_positions, outcome)


def build_recuperation_haute(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["recuperation_haute"], event, lineup, start_positions, outcome)


# Brief "real Magnus effect" (23/09/2026), Tâche 3 -- SEUL point de vérité
# pour le spin du tir enroulé de decalage_enroulee (rad/s, voir
# `BallState.spin` / `animation.ball._MAGNUS_K`) : un futur ajustement de
# calibration se fait ICI, nulle part ailleurs. Valeur choisie par calcul
# inverse (pas au jugé) sur la géométrie réelle du gabarit (fixture standard
# de tests/test_templates.py : distance ≈ 14.6 m, durée du segment shot
# (0.4->1.0) = 3.6 s) pour une courbure cible d'environ 1 m au pic (~s=0.5,
# milieu du segment shot) -- voir `_behavior_shot`/`_MAGNUS_K` pour la
# formule exacte (a = _MAGNUS_K·spin·v, offset_pic = 0.5·a·(durée/2)²).
# 50.0 rad/s (~8 tours/s) donne 0.98 m sur cette géométrie -- crédible pour
# une "frappe enroulée" (le nom même du gabarit), visible à l'œil sans être
# une parabole exagérée. `build_from_template` reste générique et continue
# de poser `spin=0.0` par défaut (aucun changement au moteur) : ce wrapper
# poste-traite la Sequence pour renseigner le spin SEULEMENT sur la/les
# keyframe(s) où un segment courbé démarre -- `physics_tag == "shot"`
# (segment d'approche existant, inchangé) ET, depuis le brief "ball flight
# after shot" (24/09/2026), `physics_tag == BALL_FLIGHT` (le vol lui-même,
# voir `_behavior_ball_flight` : la courbure Magnus doit se conserver sur le
# vol, section 1.1 du design doc, pas seulement sur l'approche).
_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S = 50.0
_DECALAGE_ENROULEE_CURVED_TAGS = frozenset({"shot", BALL_FLIGHT})


def build_decalage_enroulee(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    sequence = build_from_template(TEMPLATES["decalage_enroulee"], event, lineup, start_positions, outcome)
    keyframes = [
        replace(kf, ball=replace(kf.ball, spin=_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S))
        if kf.physics_tag in _DECALAGE_ENROULEE_CURVED_TAGS
        else kf
        for kf in sequence.keyframes
    ]
    return replace(sequence, keyframes=keyframes)


def build_penalty(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["penalty"], event, lineup, start_positions, outcome)


def build_but_gag(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None
) -> Sequence:
    return build_from_template(TEMPLATES["but_gag"], event, lineup, start_positions, outcome)


BUILDERS: dict[str, Callable[..., Sequence]] = {
    "contre_attaque": build_contre_attaque,
    "construction_placee": build_construction_placee,
    "debordement_centre_tete": build_debordement_centre_tete,
    "percee_individuelle": build_percee_individuelle,
    "une_deux": build_une_deux,
    "coup_franc": build_coup_franc,
    "corner": build_corner,
    "profondeur_1v1": build_profondeur_1v1,
    "recuperation_haute": build_recuperation_haute,
    "decalage_enroulee": build_decalage_enroulee,
    "penalty": build_penalty,
    "but_gag": build_but_gag,
}


def pick_template(context: TemplateContext, *, rng: random.Random | None = None) -> str:
    """Tire le NOM d'un gabarit parmi `TEMPLATES`, pondéré par
    `weight * context_score(context)` -- seuls les gabarits dont le score
    effectif est strictement positif restent éligibles (ex. "penalty" est
    exclu hors penalty, voir `_score_penalty`). `rng` : générateur fourni
    pour la reproductibilité (même principe que `events._deterministic_rng`),
    sinon le module `random` global.

    Lève `ValueError` si aucun gabarit n'est éligible (ne devrait jamais
    arriver : au moins un gabarit generique a toujours un score positif)."""
    generator = rng or random
    scored = [(name, template.weight * template.context_score(context)) for name, template in TEMPLATES.items()]
    eligible = [(name, score) for name, score in scored if score > 0]
    if not eligible:
        raise ValueError(f"Aucun gabarit éligible pour ce contexte : {context!r}")
    names, weights = zip(*eligible)
    return generator.choices(names, weights=weights, k=1)[0]
