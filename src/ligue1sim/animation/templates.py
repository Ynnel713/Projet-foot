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

from ligue1sim.animation.ball import BALL_FLIGHT, PASS_GROUND, _drag_progress
from ligue1sim.animation.motion import max_speed_normalized
from ligue1sim.animation.types import BallState, Keyframe, PlayerId, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import (
    PENALTY_AREA_DEPTH_M,
    PENALTY_SPOT_DISTANCE_M,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    PitchPoint,
    center_of,
)
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, Player

_logger = logging.getLogger(__name__)

# --- Ancrages de fin d'un rôle -------------------------------------------
# Un rôle progresse (voir RoleFrame.progress) de sa position de départ RÉELLE
# (start_positions, sa position de formation) vers l'un de ces ancrages.
ANCHOR_SCORER = "scorer_zone"  # event.zone (centre de la zone de tir/but)
ANCHOR_ASSIST = "assist_zone"  # event.assist_zone si présent, sinon repli sur ANCHOR_SCORER
ANCHOR_STATIC = "static"  # reste à sa position de départ (progress ignoré)
ANCHOR_PENALTY_SPOT = "penalty_spot"  # point de penalty réglementaire (PENALTY_SPOT_DISTANCE_M de la ligne de but, y = 0,5), indépendant de event.zone -- Phase 6 B6-a
ANCHOR_FREE_KICK_SPOT = "free_kick_spot"  # point du coup franc direct, tiré de event_ref (voir free_kick_spot), indépendant de event.zone -- Phase 6 B7-a
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

# Phase 6, B6-a (08/10/2026) -- point de penalty réglementaire : 11 m de la ligne de but adverse (x = 1), sur l'axe (y = 0,5).
# Remplace la zone de l'événement (case de la grille : centre à 13,12 m de la ligne et 4,25 m de l'axe, perturbée de plus par
# `engine/narrative.py`, ticket 24), qui n'est plus lue pour un penalty. Constantes produit validées par le propriétaire.
_PENALTY_SPOT = PitchPoint(x=1.0 - PENALTY_SPOT_DISTANCE_M / PITCH_LENGTH_M, y=0.5)
_PENALTY_RUNUP_MIN_M = 6.0  # longueur de l'élan du tireur : 6 à 9 m
_PENALTY_RUNUP_MAX_M = 9.0
_PENALTY_RUNUP_ANGLE_MAX_DEG = 10.0  # angle d'approche : +-10 degres autour de l'axe tireur -> but (aléa D8)

# Phase 6, B7-a (14/10/2026) -- point du coup franc direct : constantes produit validées par le propriétaire. Remplace la zone de
# l'événement (case de la grille perturbée par `engine/narrative.py` : 31 à 53 m du but, médiane 45 m, jamais sous 25 m), qui n'est
# plus lue pour un coup franc. Le ballon est posé hors de la surface de réparation (sinon ce serait un penalty).
_FREE_KICK_DISTANCE_MIN_M = 18.0  # distance au centre du but : de 18 à 30 m (zone d'un coup franc direct)
_FREE_KICK_DISTANCE_MAX_M = 30.0
_FREE_KICK_LATERAL_MAX_M = 12.0  # décalage latéral |y| de 0 à 12 m, côté tiré par hachage (au-delà : situation de centre)
_FREE_KICK_RUNUP_MIN_M = 4.0  # élan : 4 à 7 m (3 à 5 pas ; le penalty est à 6 à 9 m)
_FREE_KICK_RUNUP_MAX_M = 7.0
_FREE_KICK_RUNUP_ANGLE_STRAIGHT_DEG = 10.0  # frappé : +-10 degrés de l'axe ballon -> but
_FREE_KICK_RUNUP_ANGLE_CURL_MIN_DEG = 20.0  # enroulé : 20 à 40 degrés de l'axe, côté tiré par hachage (on prend un enroulé de biais)
_FREE_KICK_RUNUP_ANGLE_CURL_MAX_DEG = 40.0
_FREE_KICK_INWARD_CURVE_P = 0.75  # courbure rentrante (vers l'axe du but) pour 75 % des enroulés, sortante pour 25 %


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


# --- Géométrie de rôle (chantier 1, sous-étape 1a) -------------------------
# Un rôle AVEC géométrie ne part plus de sa position de formation : son ancrage de fin W est un point cible dérivé de l'événement, et son
# départ est dérivé de W et de sa position de formation P0 (voir `geometry_start`), de façon que la course reste réalisable :
#   - ratio : distance / (durée du segment x vmax du poste) <= `_RUN_RATIO_MAX` sur chaque segment ;
#   - accélération : distance <= `_RUN_ACCEL_COEFF` x durée² sur chaque segment (le pic d'accélération de la courbe de motion.py vaut
#     4,44 x distance / durée², soit moins de 10 m/s²).
GEOM_ZONE = "zone"  # W = centre de event.zone
GEOM_ASSIST_ZONE = "assist_zone"  # W = centre de event.assist_zone (repli : event.zone)
GEOM_BEHIND_ZONE = "behind_zone"  # W = à `cap_m` de event.zone, dans la direction de event.assist_zone tournée de `angle_deg` (au moins `_BEHIND_MIN_M`)
GEOM_TOWARD_GOAL = "toward_goal"  # W = à `cap_m` de event.zone, vers le centre du but adverse

_RUN_RATIO_MAX = 0.5  # marge de conception sous la limite de 0,55 de motion.py (soumise à validation du propriétaire)
_RUN_ACCEL_COEFF = 2.25  # m/s² : 10 m/s² / 4,44, pic d'accélération de la courbe d'ease (soumise à validation du propriétaire)
_BEHIND_MIN_M = 6.0  # distance minimale de W à event.zone pour GEOM_BEHIND_ZONE


@dataclass(frozen=True)
class RoleGeometry:
    """Cible et plafond de course d'un rôle. `cap_m` / `angle_deg` : voir GEOM_BEHIND_ZONE et GEOM_TOWARD_GOAL. `run_cap_m` : plafond de
    course supplémentaire (m), `None` = seulement celui de la vitesse et de l'accélération. `preferred_postes` : pour un rôle générique
    (support), postes attendus du joueur tiré par `_resolve_roles` ; vide = tous les postes de champ."""

    target: str
    cap_m: float = 0.0
    angle_deg: float = 0.0
    run_cap_m: float | None = None
    preferred_postes: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Role:
    """Un acteur du gabarit. `name` est résolu vers un vrai joueur par
    `_resolve_roles` ("scorer"/"assist" depuis l'événement lui-même, tout
    autre nom depuis les coéquipiers restants, voir cette fonction).
    `frames` doit couvrir EXACTEMENT les mêmes `t_ratio` que les autres
    rôles actifs du même gabarit (vérifié par `_validate_template`).
    `geometry` : voir `RoleGeometry` ; renseignée, elle remplace `end_anchor` (ignoré) et la position de départ du rôle."""

    name: str
    end_anchor: str
    frames: tuple[RoleFrame, ...]
    geometry: RoleGeometry | None = None


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
    # Phase 6, B8-a (14/10/2026) : `False` = ce gabarit ne reçoit PAS de contrôle au sol (voir `_insert_ground_controls`). Les deux gabarits
    # qui finissent de la tête (`corner`, `debordement_centre_tete`) reçoivent un ballon aérien : leur contrôle relève de B8-c.
    ground_control: bool = True
    # Phase 6, B8-c1 (14/10/2026) : `True` = le dernier keyframe est un contact AÉRIEN (tête ou volée sur un centre) : le ballon y arrive, et en repart,
    # à la hauteur du contact tirée par `_contact_height_m` (`ball.py` lit `Keyframe.ball.z`, voir sa docstring de module).
    aerial_contact: bool = False


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


def _pick_support(
    candidates: list[Player], start_positions: dict[PlayerId, PitchPoint], target: PitchPoint, preferred_postes: frozenset[str]
) -> Player | None:
    """Support tactique (chantier 1, 1b) : parmi les candidats dont le poste est attendu (tous si aucun ne l'est, ou si `preferred_postes`
    est vide), celui dont la position de formation est la plus proche de `target`. Égalité (arrondie à 1e-6 m) : ordre alphabétique du
    nom. Déterministe, sans hachage. `None` sans candidat."""
    pool = [p for p in candidates if p.poste in preferred_postes] or candidates

    def key(player: Player) -> tuple[float, str]:
        start = start_positions[player_id_of(player)]
        return (round(math.hypot((start.x - target.x) * PITCH_LENGTH_M, (start.y - target.y) * PITCH_WIDTH_M), 6), player.name)

    return min(pool, key=key, default=None)


def _resolve_roles(
    event: GoalEvent,
    lineup: Lineup,
    role_names: tuple[str, ...],
    roles: tuple[Role, ...] = (),
    start_positions: dict[PlayerId, PitchPoint] | None = None,
) -> dict[str, Player]:
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
    cette Tâche 2.

    Chantier 1, 1b : un rôle générique dont `roles` porte une géométrie est tiré TACTIQUEMENT (`_pick_support` : poste attendu, le plus
    proche de sa cible, d'après `start_positions`), dans l'ordre alphabétique des noms de rôle (support1 avant support2), avant les
    rôles génériques sans géométrie, qui restent tirés par ordre alphabétique des noms de joueur parmi les joueurs restants."""
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

    tactical = sorted(
        (r for r in roles if r.geometry is not None and r.name in role_names and r.name not in ("scorer", "assist")), key=lambda r: r.name
    ) if start_positions is not None else []
    for role in tactical:
        field = [p for p in roster if p.group != GOALKEEPER and p.name not in used_names and player_id_of(p) in start_positions]
        chosen = _pick_support(field, start_positions, geometry_target(role.geometry, event), role.geometry.preferred_postes)
        if chosen is not None:
            resolved[role.name] = chosen
            used_names.add(chosen.name)
    tactical_names = {r.name for r in tactical}
    remaining_generic = [name for name in role_names if name not in resolved and name != "assist" and name not in tactical_names]
    candidates = sorted(
        (p for p in roster if p.group != GOALKEEPER and p.name not in used_names), key=lambda p: p.name
    )
    for role_name, player in zip(remaining_generic, candidates):
        resolved[role_name] = player
        used_names.add(player.name)

    return resolved


# --- Moteur générique ------------------------------------------------------


def _unit_m(ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """Vecteur unitaire a -> b (m) ; (-1, 0), vers son propre but, si a et b coïncident."""
    d = math.hypot(bx - ax, by - ay)
    return ((bx - ax) / d, (by - ay) / d) if d > 1e-9 else (-1.0, 0.0)


def geometry_target(geometry: RoleGeometry, event: GoalEvent) -> PitchPoint:
    """Ancrage de fin W d'un rôle avec géométrie (voir GEOM_*). Fonction pure."""
    zone = center_of(event.zone)
    assist = center_of(event.assist_zone if event.assist_zone is not None else event.zone)
    if geometry.target == GEOM_ZONE:
        return zone
    if geometry.target == GEOM_ASSIST_ZONE:
        return assist
    zx, zy = zone.x * PITCH_LENGTH_M, zone.y * PITCH_WIDTH_M
    if geometry.target == GEOM_TOWARD_GOAL:
        ux, uy = _unit_m(zx, zy, PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)
        distance_m = geometry.cap_m
    elif geometry.target == GEOM_BEHIND_ZONE:
        ax, ay = assist.x * PITCH_LENGTH_M, assist.y * PITCH_WIDTH_M
        ux, uy = _unit_m(zx, zy, ax, ay)
        angle = math.radians(geometry.angle_deg)
        ux, uy = ux * math.cos(angle) - uy * math.sin(angle), ux * math.sin(angle) + uy * math.cos(angle)
        distance_m = min(geometry.cap_m, max(math.hypot(ax - zx, ay - zy), _BEHIND_MIN_M))
    else:
        raise ValueError(f"Cible de géométrie inconnue : {geometry.target!r}")
    x, y = zx + distance_m * ux, zy + distance_m * uy
    return PitchPoint(x=min(PITCH_LENGTH_M, max(0.0, x)) / PITCH_LENGTH_M, y=min(PITCH_WIDTH_M, max(0.0, y)) / PITCH_WIDTH_M)


def role_run_limit_m(frames: tuple[RoleFrame, ...], duration_s: float, v_max_mps: float, run_cap_m: float | None = None) -> float:
    """Longueur de course maximale (m) de départ -> ancrage : sur CHAQUE segment où la progression varie de `dp`, la distance `L x dp` doit
    respecter le ratio (`_RUN_RATIO_MAX` x vmax x durée) ET l'accélération (`_RUN_ACCEL_COEFF` x durée²). 0 si le rôle ne bouge jamais."""
    limit = math.inf
    for a, b in zip(frames, frames[1:]):
        dp = abs(b.progress - a.progress)
        if dp <= 1e-9:
            continue
        segment_s = (b.t_ratio - a.t_ratio) * duration_s
        limit = min(limit, _RUN_RATIO_MAX * v_max_mps * segment_s / dp, _RUN_ACCEL_COEFF * segment_s**2 / dp)
    if limit == math.inf:
        return 0.0
    return limit if run_cap_m is None else min(limit, run_cap_m)


def geometry_start(target: PitchPoint, home: PitchPoint, limit_m: float) -> PitchPoint:
    """Départ d'un rôle avec géométrie : sur la droite `target` -> `home` (sa position de formation), à min(|home - target|, `limit_m`) de
    `target`. Un joueur déjà à portée garde sa position de formation."""
    dx, dy = (home.x - target.x) * PITCH_LENGTH_M, (home.y - target.y) * PITCH_WIDTH_M
    distance_m = math.hypot(dx, dy)
    if distance_m <= limit_m:
        return home
    k = limit_m / distance_m
    return PitchPoint(x=target.x + dx * k / PITCH_LENGTH_M, y=target.y + dy * k / PITCH_WIDTH_M)


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
    if anchor == ANCHOR_PENALTY_SPOT:
        return _PENALTY_SPOT
    if anchor == ANCHOR_FREE_KICK_SPOT:
        return free_kick_spot(f"goal:{event.club_name}:{event.scorer}:{event.minute}")
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
# propriétaire : un tir réel de Ligue 1 part à 25-30 m/s. Depuis la Phase 6 B5 (08/10/2026), la vitesse dépend du TYPE de
# frappe (`STRIKE_TYPES` plus bas : de 12 m/s pour une tête à 35 m/s pour une frappe tendue), au lieu de l'ancien
# intervalle unique [15, 35] m/s. Tirage déterministe (voir `_flight_unit`), jamais `random` global.

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


# Phase 6, Bloc B5 (08/10/2026) -- types de frappe. Le type, donc le SPIN et la VITESSE du vol (`ball_flight`), se tire
# par hachage déterministe de `event_ref` (`_flight_unit`, jamais `random`), parmi les types COHERENTS avec le gabarit
# (`_STRIKE_TYPE_WEIGHTS`). Seul le rendu du vol change : la cible, l'issue, le score et la minute ne dépendent pas du
# type. Le spin est posé sur la keyframe qui DEMARRE le vol (pas sur la conduite `shot`, qui reste droite : le ballon
# ne quitte plus son porteur). Fourchettes et fréquences cibles : décisions de l'architecte du 08/10/2026
# (docs/phase6_block_b_audit.md, section B5).
@dataclass(frozen=True)
class StrikeType:
    name: str
    spin_min: float  # rad/s (signe : sens de la courbure par rapport au sens de la frappe)
    spin_max: float
    speed_min: float  # m/s
    speed_max: float
    # Placement de la cible (penaltys seulement, B6-b) : |y| en mètres depuis l'axe du but, et hauteur z en mètres. `None` :
    # la cible reste celle de `_flight_target` (issue seule).
    y_abs_min_m: float | None = None
    y_abs_max_m: float | None = None
    z_min_m: float | None = None
    z_max_m: float | None = None
    # B7-a : nom exposé au NLG quand il diffère du nom interne (`coup_franc_enroule` -> `shot_enroule_leger`) : le contrat du NLG
    # ne connaît que les 9 types de B5 / B6-b, voir `nlg_name` et `engine/narrative.py`.
    nlg_alias: str | None = None
    # B7-a : `spin_min`/`spin_max` sont des MODULES, le signe est tiré par `strike_spin_for` (rentrant / sortant).
    curve_side_drawn: bool = False

    @property
    def nlg_name(self) -> str:
        return self.nlg_alias or self.name


STRIKE_TYPES: dict[str, StrikeType] = {
    t.name: t
    for t in (
        StrikeType("shot_tendu", 0.0, 0.0, 30.0, 35.0),
        StrikeType("shot_enroule_leger", 20.0, 30.0, 20.0, 28.0),
        StrikeType("shot_enroule_fort", 50.0, 80.0, 20.0, 28.0),
        StrikeType("shot_exterieur_pied", -30.0, -20.0, 22.0, 30.0),
        StrikeType("reprise_vollee", 10.0, 15.0, 25.0, 32.0),
        StrikeType("tete", 0.0, 0.0, 12.0, 18.0),
        # Phase 6, B6-b (08/10/2026) -- types de penalty, constantes validées par le propriétaire. Le type ne choisit JAMAIS l'issue :
        # il donne la vitesse, le spin et, pour un BUT seulement, le placement ; le gardien (B6-d) en dépend.
        StrikeType("penalty_fort", 0.0, 0.0, 29.0, 33.0, 2.4, 3.4, 1.0, 2.0),  # frappe puissante, mi-hauteur à haut, près d'un poteau
        StrikeType("penalty_place", 20.0, 30.0, 21.0, 25.0, 2.8, 3.5, 0.1, 0.8),  # placée, ras de terre à mi-hauteur basse (spin : traînée seule)
        StrikeType("penalty_contre_pied", 0.0, 0.0, 24.0, 28.0, 1.0, 2.8, 0.3, 1.2),  # côté opposé au plongeon du gardien (B6-d)
        # Phase 6, B7-a (14/10/2026) -- types de coup franc direct, constantes validées par le propriétaire. Noms internes : le NLG
        # reçoit `shot_enroule_leger` / `shot_tendu` (`nlg_name`), son contrat n'est pas modifié.
        StrikeType("coup_franc_enroule", 45.0, 70.0, 24.0, 30.0, nlg_alias="shot_enroule_leger", curve_side_drawn=True),  # 86 à 108 km/h, 7 à 11 tours/s
        StrikeType("coup_franc_frappe", -5.0, 5.0, 28.0, 35.0, nlg_alias="shot_tendu"),  # 100 à 126 km/h, quasi sans rotation
    )
}

# Gabarit -> poids des types possibles (somme 1). Cohérence type / gabarit : `decalage_enroulee` ne produit QUE
# `shot_enroule_fort` ; les gabarits de tête produisent `tete` (majoritaire) ou `reprise_vollee` ; les gabarits de
# récupération / déviation produisent `reprise_vollee` ; un penalty a ses 3 types (B6-b), un coup franc direct ses 2 types (B7-a) ;
# les autres frappes au pied se répartissent entre tendu, enroulé léger et extérieur du pied.
# Poids du « pool pied » recalibrés le 08/10/2026 (revue de l'architecte : `shot_tendu` à 39,4 % pour une cible de 35 %) :
# 0,70 / 0,19 / 0,11 -> 0,64 / 0,22 / 0,14.
_FOOT_POOL = (("shot_tendu", 0.64), ("shot_enroule_leger", 0.22), ("shot_exterieur_pied", 0.14))
_HEAD_POOL = (("tete", 0.90), ("reprise_vollee", 0.10))
_STRIKE_TYPE_WEIGHTS: dict[str, tuple[tuple[str, float], ...]] = {
    "decalage_enroulee": (("shot_enroule_fort", 1.0),),
    "debordement_centre_tete": _HEAD_POOL,
    "corner": _HEAD_POOL,
    "recuperation_haute": (("reprise_vollee", 1.0),),
    "but_gag": (("reprise_vollee", 1.0),),
    "penalty": (("penalty_fort", 0.30), ("penalty_place", 0.50), ("penalty_contre_pied", 0.20)),
    # B7-a : 55 % enroulé / 30 % frappé / 15 % indirect, l'indirect n'existant pas encore : renormalisé en 55/85 et 30/85
    # (64,7 % / 35,3 %). Quand l'indirect viendra : 0,55 / 0,30 / 0,15 et un passeur force l'indirect.
    "coup_franc": (("coup_franc_enroule", 55 / 85), ("coup_franc_frappe", 30 / 85)),
    "contre_attaque": _FOOT_POOL,
    "construction_placee": _FOOT_POOL,
    "percee_individuelle": _FOOT_POOL,
    "profondeur_1v1": _FOOT_POOL,
    "une_deux": _FOOT_POOL,
}


def strike_type_for(gabarit: str, event_ref: str) -> StrikeType:
    """Type de frappe déterministe de `event_ref` pour ce gabarit (tirage cumulatif sur `_STRIKE_TYPE_WEIGHTS`)."""
    unit = _flight_unit(event_ref, "strike_type")
    cumulative = 0.0
    pool = _STRIKE_TYPE_WEIGHTS[gabarit]
    for name, weight in pool:
        cumulative += weight
        if unit < cumulative:
            return STRIKE_TYPES[name]
    return STRIKE_TYPES[pool[-1][0]]


def strike_spin_for(strike: StrikeType, event_ref: str) -> float:
    spin = strike.spin_min + _flight_unit(event_ref, "spin") * (strike.spin_max - strike.spin_min)
    return spin * _free_kick_curve_sign(event_ref) if strike.curve_side_drawn else spin


def strike_speed_for(strike: StrikeType, event_ref: str) -> float:
    return strike.speed_min + _flight_unit(event_ref, "speed") * (strike.speed_max - strike.speed_min)


def penalty_ball_side(event_ref: str) -> int:
    """Côté du ballon d'un penalty, +1 ou -1 (signe de l'écart latéral à l'axe du but), déterministe (sha256 de `event_ref`).
    Convention PARTAGÉE avec le gardien (B6-d) : pour un type `penalty_contre_pied`, le gardien plonge du côté OPPOSÉ."""
    return 1 if _flight_unit(event_ref, "penalty_side") >= 0.5 else -1


def _penalty_target(outcome: str, event_ref: str, strike: StrikeType) -> tuple[float, float, float] | None:
    """Cible d'un penalty selon son TYPE (B6-b) pour l'issue `but` SEULEMENT ; toutes les autres issues (arrêt, hors cadre,
    poteau, barre, ou sans vol) gardent la cible de `_flight_target` : l'issue décide, le type ne fait que la forme du vol.
    L'arrêt garde sa cible centrale (y dans +-2,2 m, voir `_flight_target` et `engine/ball_events.py`, parade B4) : un placement
    de type jusqu'à 3,5 m de l'axe sortirait de la portée du gardien (glissement de 2,5 m) -- à traiter avec B6-d."""
    if outcome != "but" or strike.y_abs_min_m is None:
        return _flight_target(outcome, event_ref)
    y_m = penalty_ball_side(event_ref) * (strike.y_abs_min_m + _flight_unit(event_ref, "y") * (strike.y_abs_max_m - strike.y_abs_min_m))
    z = strike.z_min_m + _flight_unit(event_ref, "z") * (strike.z_max_m - strike.z_min_m)
    x = 1.00 + _flight_unit(event_ref, "x") * 0.02
    return (x, _GOAL_Y_CENTER + y_m / PITCH_WIDTH_M, z)


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


# --- Phase 6, B8-a (14/10/2026) : contrôles au sol ----------------------------------------------------------------------------
# Avant B8-a, une réception (changement de porteur) était un keyframe où le ballon se collait au centre du joueur : un contrôle de durée
# zéro, à distance zéro. Pour chaque réception AU SOL d'un gabarit (`Template.ground_control`), on insère maintenant un segment de contrôle :
# le ballon arrive au pied du joueur (0,3 à 0,6 m de son centre, du côté du pied qui contrôle), le geste dure 0,15 à 0,30 s, puis la conduite
# reprend (le ballon rejoint le centre du joueur au keyframe suivant, comme avant). Un contrôle approximatif ou lourd éloigne le ballon de 1 à 3 m
# puis le joueur le reprend (0,4 à 0,8 s) : EFFET VISUEL SEUL, le porteur reste le même et l'issue de l'action n'est jamais modifiée.
# Tout est tiré par sha256 de `event_ref` (`_flight_unit`, jamais `random`). Constantes validées par le propriétaire (voir `_CONTROL_LOOSE_HEAVY_P` pour les probabilités approximatif / lourd).
_CONTROL_GESTURE_P = (0.85, 0.10, 0.05)  # pied naturel / pied faible / semelle, sur une passe au sol
_CONTROL_SOLE_MAX_ARRIVAL_M_S = 8.0  # la semelle n'existe que si le ballon arrive à 8 m/s au plus
_CONTROL_FOOT_DURATION_S = (0.15, 0.25)
_CONTROL_SOLE_DURATION_S = (0.20, 0.30)
_CONTROL_CLEAN_DISTANCE_M = (0.30, 0.60)  # ballon - centre du joueur après un contrôle propre
_CONTROL_LOOSE_DISTANCE_M = (1.0, 2.0)  # contrôle approximatif : jusqu'à 2 m
_CONTROL_HEAVY_DISTANCE_M = (2.0, 3.0)  # contrôle lourd : jusqu'à 3 m
_CONTROL_ARRIVAL_EXTRA_M = 0.25  # le ballon arrive 25 cm plus loin que sa position après amorti : il s'amortit pendant le geste (choix d'implémentation)
_CONTROL_RECOVERY_S = (0.4, 0.8)  # reprise du ballon échappé
_CONTROL_MIN_RECOVERY_S = 0.2  # sous cette durée disponible, le contrôle redevient propre
_CONTROL_ANGLE_JITTER_DEG = 10.0  # aléa de direction borné, déterministe
_CONTROL_FOOT_ANGLE_DEG = (30.0, 60.0)  # écart à l'axe de course, vers le pied qui contrôle (choix d'implémentation)
_CONTROL_SOLE_ANGLE_DEG = (10.0, 25.0)  # la semelle garde le ballon plus dans l'axe (choix d'implémentation)
_CONTROL_ESCAPE_ANGLE_DEG = 15.0  # le ballon échappé part devant, légèrement vers le côté du pied (choix d'implémentation)
# (approximatif, lourd). VALIDÉ par le propriétaire (14/10/2026) : approximatif pied naturel 10 %, pied faible 35 %, semelle 0 % ; lourd
# 2 % pied naturel (rare) et 10 % pied faible (plus fréquent). B8-b les fera dépendre de la qualité technique et de la pression.
_CONTROL_LOOSE_HEAVY_P = {"pied_naturel": (0.10, 0.02), "pied_faible": (0.35, 0.10), "semelle": (0.0, 0.0)}
_CONTROL_ROOM_RATIO = 0.8  # un contrôle (et sa reprise) occupe au plus 80 % de l'intervalle entre deux keyframes d'origine
_RIGHT_FOOTED_P = 0.78  # pied inconnu : droitier avec cette probabilité (292 D pour 81 G dans les données connues de la Ligue 1)


# --- Phase 6, B8-c1 (14/10/2026) : hauteur du contact aérien (tête, volée) ---------------------------------------------------------
# Constantes validées par le propriétaire. Le type de frappe (`strike_type_for`) décide : `tete` = 1,6 à 2,2 m (arrivée du centre ET départ du vol),
# `reprise_vollee` = 0,4 à 1,0 m. Hauteur tirée par sha256 de `event_ref` (`_flight_unit`, jamais `random`).
_HEAD_CONTACT_Z_M = (1.6, 2.2)
_VOLLEY_CONTACT_Z_M = (0.4, 1.0)


def _contact_height_m(gabarit: str, event_ref: str) -> float:
    lo, hi = _VOLLEY_CONTACT_Z_M if strike_type_for(gabarit, event_ref).name == "reprise_vollee" else _HEAD_CONTACT_Z_M
    return lo + _flight_unit(event_ref, "contact_height") * (hi - lo)


# --- Phase 6, B8-b (14/10/2026) : modulation du contrôle par la pression et la qualité technique ---------------------------------
# Constantes validées par le propriétaire. La pression `p` ∈ [0 ; 1] combine trois signaux (proximité de l'adversaire de champ le plus proche à
# la réception, vitesse d'arrivée du ballon, contexte) ; la qualité `q` (échelle des attributs FM) combine First Touch, Technique et, sous
# pression seulement, Composure. Les probabilités de base (`_CONTROL_LOOSE_HEAVY_P`) sont REDISTRIBUÉES, pas augmentées : `_PRESSURE_MEAN` recentre.
# Sans `opponent_lineup` (tous les appelants hors `narrative_player`), aucune modulation : comportement de B8-a.
_PRESSURE_WEIGHTS = (0.5, 0.3, 0.2)  # proximité / vitesse / contexte
_PRESSURE_DISTANCE_M = (1.5, 8.0)  # adversaire à 1,5 m ou moins : 1 ; à 8 m ou plus : 0 (le seuil bas est celui de l'évitement de motion.py)
_PRESSURE_ARRIVAL_M_S = (12.0, 24.0)  # ballon à 12 m/s ou moins : 0 ; à 24 m/s ou plus : 1
_PRESSURE_CONTEXT_P = 0.5  # style Pressing de l'adversaire : 0,5 ; gabarit `recuperation_haute` : 0,5 ; cumulables (max 1)
_PRESSURE_MEAN = 0.15  # pression moyenne : la modulation ne s'applique qu'à l'écart à cette valeur
_PRESSURE_EFFECT = 0.25  # +25 points de contrôle approximatif à pression pleine (par rapport à la pression moyenne)
_QUALITY_NEUTRAL = 59.0  # sans attributs : aucun effet de la qualité
_QUALITY_EFFECT = 0.12  # -12 points de contrôle approximatif pour +20 de qualité
_QUALITY_SCALE = 20.0
_QUALITY_COMPOSURE_SHARE = 0.5  # sous pression pleine, Composure pèse pour moitié dans la qualité
_QUALITY_FIRST_TOUCH_SHARE = 0.6  # q_base = 0,6 × First Touch + 0,4 × Technique
_WEAK_FOOT_EFFECT = 0.06  # -6 points de contrôle approximatif par cran de `weak_foot` au-dessus de 3 (pied faible uniquement)
_LOOSE_RANGE = (0.01, 0.60)  # bornes de la probabilité de contrôle approximatif
_HEAVY_MAX = 0.25  # plafond du contrôle lourd, proportionnel à l'approximatif


@dataclass(frozen=True)
class _PressureContext:
    """Ce dont `_insert_ground_controls` a besoin pour mesurer la pression : `distance_at(point, t)` (m, adversaire de champ le plus proche,
    `None` sans adversaire) et les deux signaux de contexte."""

    distance_at: Callable[[tuple[float, float], float], float | None]
    pressing_style: bool
    recuperation_haute: bool


def _linear_unit(value: float, zero_at: float, one_at: float) -> float:
    """0 en `zero_at`, 1 en `one_at`, linéaire entre les deux (`zero_at` > `one_at` accepté), borné à [0 ; 1]."""
    return min(1.0, max(0.0, (value - zero_at) / (one_at - zero_at)))


def _pressure_index(distance_m: float | None, arrival_m_s: float, context: _PressureContext) -> float:
    """Pression p ∈ [0 ; 1] = 0,5 × proximité + 0,3 × vitesse d'arrivée + 0,2 × contexte."""
    w_d, w_v, w_c = _PRESSURE_WEIGHTS
    p_d = 0.0 if distance_m is None else _linear_unit(distance_m, _PRESSURE_DISTANCE_M[1], _PRESSURE_DISTANCE_M[0])
    p_v = _linear_unit(arrival_m_s, *_PRESSURE_ARRIVAL_M_S)
    p_c = min(1.0, _PRESSURE_CONTEXT_P * context.pressing_style + _PRESSURE_CONTEXT_P * context.recuperation_haute)
    return min(1.0, max(0.0, w_d * p_d + w_v * p_v + w_c * p_c))


def _technical_quality(player: Player, pressure: float) -> float:
    """Qualité technique q : (1 - 0,5 p) × (0,6 First Touch + 0,4 Technique) + 0,5 p × Composure ; 59 (neutre) si un des trois attributs manque."""
    attributes = player.attributes
    if not attributes or any(name not in attributes for name in ("First Touch", "Technique", "Composure")):
        return _QUALITY_NEUTRAL
    base = _QUALITY_FIRST_TOUCH_SHARE * attributes["First Touch"] + (1.0 - _QUALITY_FIRST_TOUCH_SHARE) * attributes["Technique"]
    share = _QUALITY_COMPOSURE_SHARE * pressure
    return (1.0 - share) * base + share * attributes["Composure"]


def _modulated_loose_heavy(gesture: str, pressure: float, quality: float, weak_foot: float | None) -> tuple[float, float]:
    """(P approximatif, P lourd) modulés : base + 0,25 (p - 0,15) - 0,12 (q - 59) / 20 [- 0,06 (weak_foot - 3) au pied faible], bornés à
    [1 % ; 60 %] ; le lourd reste proportionnel (base_lourd × P / base), plafonné à 25 %. La semelle (base 0 %) n'est jamais modulée."""
    base_loose, base_heavy = _CONTROL_LOOSE_HEAVY_P[gesture]
    if base_loose <= 0.0:
        return base_loose, base_heavy
    loose = base_loose + _PRESSURE_EFFECT * (pressure - _PRESSURE_MEAN) - _QUALITY_EFFECT * (quality - _QUALITY_NEUTRAL) / _QUALITY_SCALE
    if gesture == "pied_faible" and weak_foot is not None:
        loose -= _WEAK_FOOT_EFFECT * (weak_foot - 3.0)
    loose = min(_LOOSE_RANGE[1], max(_LOOSE_RANGE[0], loose))
    return loose, min(_HEAVY_MAX, base_heavy * loose / base_loose)


def _control_span(unit: float, lo_hi: tuple[float, float]) -> float:
    return lo_hi[0] + unit * (lo_hi[1] - lo_hi[0])


def _strong_foot(player: Player, player_id: PlayerId) -> str:
    """Pied fort du joueur : `Player.pied` ("D" / "G") s'il est connu, sinon tiré par sha256 de `player_id`."""
    if player.pied in ("D", "G"):
        return player.pied
    return "D" if _flight_unit(str(player_id), "strong_foot") < _RIGHT_FOOTED_P else "G"


def _control_gesture(arrival_m_s: float, unit: float) -> str:
    """Geste du contrôle : pied naturel 85 %, pied faible 10 %, semelle 5 % (seulement si le ballon arrive à 8 m/s au plus ; sinon
    pied naturel et pied faible gardent leurs poids relatifs)."""
    natural, weak, _sole = _CONTROL_GESTURE_P
    if arrival_m_s <= _CONTROL_SOLE_MAX_ARRIVAL_M_S:
        return "pied_naturel" if unit < natural else "pied_faible" if unit < natural + weak else "semelle"
    return "pied_naturel" if unit * (natural + weak) < natural else "pied_faible"


def _insert_ground_controls(
    template: Template,
    keyframes: list[Keyframe],
    players_by_id: dict[PlayerId, Player],
    event_ref: str,
    pressure_context: _PressureContext | None = None,
) -> list[Keyframe]:
    """Insère un segment de contrôle à chaque réception au sol (voir le bloc de commentaires ci-dessus). Une réception est un keyframe
    dont le porteur change pour un joueur (pas `None`) ; une réception à position de ballon explicite (`Template.ball_position`) n'est pas
    touchée. Réception NON finale : le keyframe garde son instant, le ballon y est au pied (`C0`), puis un keyframe de fin de geste
    (et, si le ballon s'est échappé, un keyframe de reprise). Réception FINALE (le joueur frappe aussitôt) : la fenêtre PRÉCÈDE le keyframe
    de frappe, qui reste inchangé, pour ne pas allonger le gabarit. Les joueurs des keyframes insérés sont sur la droite entre les keyframes
    voisins ; le tag du premier keyframe inséré porte le geste (`controle_<geste>`), `Keyframe.tag` n'étant jamais lu par le rendu.

    B8-b : avec `pressure_context`, les probabilités d'un contrôle approximatif / lourd sont modulées par la pression à la réception et la
    qualité technique du récepteur (`_modulated_loose_heavy`) ; sans, ce sont les probabilités de base de B8-a."""
    n = len(keyframes)
    if not template.ground_control or n < 2:
        return keyframes
    explicit_times = {ratio * template.duration for ratio, _ in template.ball_position}
    receptions = [
        i for i in range(1, n)
        if keyframes[i].ball.owner_id is not None
        and keyframes[i].ball.owner_id != keyframes[i - 1].ball.owner_id
        and keyframes[i].ball.owner_id in players_by_id
        and keyframes[i].t not in explicit_times
    ]
    if not receptions:
        return keyframes
    length_m, width_m = PITCH_LENGTH_M, PITCH_WIDTH_M

    def position_m(kf: Keyframe, player_id: PlayerId) -> tuple[float, float]:
        x, y = kf.players[player_id]
        return x * length_m, y * width_m

    def heading(i: int, owner: PlayerId) -> tuple[float, float]:
        a, b = (i, i + 1) if i < n - 1 else (i - 1, i)
        (ax, ay), (bx, by) = position_m(keyframes[a], owner), position_m(keyframes[b], owner)
        norm = math.hypot(bx - ax, by - ay)
        return ((bx - ax) / norm, (by - ay) / norm) if norm > 1e-9 else (1.0, 0.0)

    def offset(head: tuple[float, float], angle_deg: float, distance_m: float) -> tuple[float, float]:
        """Décalage normalisé : `distance_m` dans la direction `head` tournée de `angle_deg` (positif = vers la droite du joueur)."""
        a = math.radians(angle_deg)
        right = (-head[1], head[0])
        return (
            distance_m * (math.cos(a) * head[0] + math.sin(a) * right[0]) / length_m,
            distance_m * (math.cos(a) * head[1] + math.sin(a) * right[1]) / width_m,
        )

    def blend(a: Keyframe, b: Keyframe, t: float) -> dict[PlayerId, tuple[float, float]]:
        f = (t - a.t) / (b.t - a.t)
        return {pid: (ax + (b.players[pid][0] - ax) * f, ay + (b.players[pid][1] - ay) * f) for pid, (ax, ay) in a.players.items()}

    inserted: dict[int, list[Keyframe]] = {}
    modified: dict[int, Keyframe] = {}
    for i in receptions:
        kf, previous = keyframes[i], keyframes[i - 1]
        owner = kf.ball.owner_id
        ref = f"{event_ref}|control{i}"
        dist_m = math.hypot((kf.ball.x - previous.ball.x) * length_m, (kf.ball.y - previous.ball.y) * width_m)
        dt = kf.t - previous.t
        arrival = (dist_m / dt) * _drag_progress(1.0, dist_m)[1] if dist_m > 1e-9 and dt > 0 else 0.0  # vitesse d'arrivée du ballon
        gesture = _control_gesture(arrival, _flight_unit(ref, "gesture"))
        strong = _strong_foot(players_by_id[owner], owner)
        foot = strong if gesture != "pied_faible" else ("G" if strong == "D" else "D")
        side = 1.0 if foot == "D" else -1.0
        d = _control_span(_flight_unit(ref, "duration"), _CONTROL_SOLE_DURATION_S if gesture == "semelle" else _CONTROL_FOOT_DURATION_S)
        loose_p, heavy_p = _CONTROL_LOOSE_HEAVY_P[gesture]
        if pressure_context is not None and gesture != "semelle":
            # Réception FINALE : le ballon arrive une durée de geste avant le keyframe de frappe ; sinon, au keyframe de réception.
            at_t = max(previous.t, kf.t - d) if i == n - 1 else kf.t
            receiver = blend(previous, kf, at_t)[owner] if i == n - 1 else kf.players[owner]
            pressure = _pressure_index(pressure_context.distance_at(receiver, at_t), arrival, pressure_context)
            loose_p, heavy_p = _modulated_loose_heavy(
                gesture, pressure, _technical_quality(players_by_id[owner], pressure), players_by_id[owner].weak_foot
            )
        quality = _flight_unit(ref, "quality")
        kind = "lourd" if quality < heavy_p else "approximatif" if quality < heavy_p + loose_p else "propre"
        recovery = _control_span(_flight_unit(ref, "recovery"), _CONTROL_RECOVERY_S) if kind != "propre" else 0.0

        # Place disponible dans l'intervalle voisin ; partagée avec la réception finale quand les deux fenêtres se touchent.
        last = i == n - 1
        t_a, t_b = (keyframes[i - 1].t, kf.t) if last else (kf.t, keyframes[i + 1].t)
        shared = (last and (n - 2) in receptions) or (i == n - 2 and (n - 1) in receptions)
        room = _CONTROL_ROOM_RATIO * (t_b - t_a) * (0.5 if shared else 1.0)
        d = min(d, room)
        if d + recovery > room:
            recovery = max(0.0, room - d)
        if recovery < _CONTROL_MIN_RECOVERY_S:
            recovery, kind = 0.0, "propre"

        head = heading(i, owner)
        jitter = _CONTROL_ANGLE_JITTER_DEG * (2.0 * _flight_unit(ref, "jitter") - 1.0)
        foot_angle = _control_span(_flight_unit(ref, "angle"), _CONTROL_SOLE_ANGLE_DEG if gesture == "semelle" else _CONTROL_FOOT_ANGLE_DEG)
        settled_m = _control_span(_flight_unit(ref, "distance"), _CONTROL_CLEAN_DISTANCE_M)
        clean = offset(head, side * foot_angle + jitter, settled_m)
        arrival_shift = offset(head, side * foot_angle + jitter, settled_m + _CONTROL_ARRIVAL_EXTRA_M)  # où le ballon arrive, avant l'amorti
        escape_range = _CONTROL_HEAVY_DISTANCE_M if kind == "lourd" else _CONTROL_LOOSE_DISTANCE_M
        escape = offset(
            head, side * _CONTROL_ESCAPE_ANGLE_DEG + _CONTROL_ANGLE_JITTER_DEG * (2.0 * _flight_unit(ref, "escape_jitter") - 1.0),
            _control_span(_flight_unit(ref, "escape"), escape_range),
        )

        def ball_at(players: dict[PlayerId, tuple[float, float]], shift: tuple[float, float]) -> BallState:
            px, py = players[owner]
            return BallState(x=px + shift[0], y=py + shift[1], z=0.0, spin=0.0, owner_id=owner)

        tag = f"controle_{gesture}"
        if last:
            t0 = kf.t - (d + recovery)
            first_players = blend(previous, kf, t0)
            # Le segment qui précède le keyframe de frappe garde le tag du segment d'origine (`previous.physics_tag`, par exemple `shot`).
            controls = [Keyframe(t=t0, ball=ball_at(first_players, arrival_shift), players=first_players, tag=tag, physics_tag=previous.physics_tag)]
            if recovery > 0.0:
                t1 = t0 + d
                players_1 = blend(previous, kf, t1)
                controls[0] = replace(controls[0], physics_tag=PASS_GROUND)
                controls.append(Keyframe(t=t1, ball=ball_at(players_1, escape), players=players_1, tag=f"{tag}_{kind}", physics_tag=previous.physics_tag))
            inserted[i] = controls
        else:
            following = keyframes[i + 1]
            t1 = kf.t + d
            players_1 = blend(kf, following, t1)
            reception_players = kf.players
            modified[i] = replace(kf, ball=ball_at(reception_players, arrival_shift), physics_tag=PASS_GROUND)
            if recovery > 0.0:
                t2 = t1 + recovery
                players_2 = blend(kf, following, t2)
                inserted[i] = [
                    Keyframe(t=t1, ball=ball_at(players_1, escape), players=players_1, tag=f"{tag}_{kind}", physics_tag=PASS_GROUND),
                    Keyframe(t=t2, ball=ball_at(players_2, clean), players=players_2, tag="reprise_conduite", physics_tag=kf.physics_tag),
                ]
            else:
                inserted[i] = [Keyframe(t=t1, ball=ball_at(players_1, clean), players=players_1, tag=tag, physics_tag=kf.physics_tag)]

    result: list[Keyframe] = []
    for i, kf in enumerate(keyframes):
        if i == n - 1 and i in inserted:
            result.extend(inserted[i])  # réception finale : la fenêtre précède le keyframe de frappe
            result.append(kf)
        else:
            result.append(modified.get(i, kf))
            result.extend(inserted.get(i, []))
    return result


def build_from_template(
    template: Template,
    event: GoalEvent,
    lineup: Lineup,
    start_positions: dict[PlayerId, PitchPoint],
    outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
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
    voir `_NO_FLIGHT_OUTCOMES`.

    `opponent_lineup` (Phase 6, B8-b) : compo de l'équipe qui encaisse, OPTIONNELLE. Fournie (par `narrative_player`), elle permet de moduler
    les contrôles au sol par la pression adverse et la qualité technique du récepteur (voir `_insert_ground_controls`) ; `None` (défaut,
    tous les autres appelants) : comportement de B8-a, bit à bit."""
    _validate_template(template)

    role_names = tuple(role.name for role in template.roles)
    resolved = _resolve_roles(event, lineup, role_names, template.roles, start_positions)
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
    role_ends: dict[str, PitchPoint] = {}
    for role in template.roles:
        if role.name not in resolved:
            continue
        if role.geometry is None:
            role_ends[role.name] = _anchor_point(role.end_anchor, role_starts[role.name], event)
            continue
        target = geometry_target(role.geometry, event)  # chantier 1 : départ dérivé de la cible, course réalisable
        v_max_mps = max_speed_normalized(resolved[role.name].poste) * PITCH_LENGTH_M
        limit_m = role_run_limit_m(role.frames, template.duration, v_max_mps, role.geometry.run_cap_m)
        role_starts[role.name] = geometry_start(target, role_starts[role.name], limit_m)
        role_ends[role.name] = target

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
            if t_ratio in ball_position_by_ratio:
                # Ballon POSE (penalty, B6-a) : position explicite, le tireur reste le « porteur » (nom affiché à l'arrivée).
                ball_x, ball_y = ball_position_by_ratio[t_ratio]
            else:
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
    if template.aerial_contact:  # B8-c1 : contact de la tête / volée en hauteur ; le centre y arrive, le vol en part
        keyframes[-1] = replace(keyframes[-1], ball=replace(keyframes[-1].ball, z=_contact_height_m(template.name, event_ref)))
    duration = template.duration

    # Plan du vol, calculé AVANT l'insertion des contrôles (qui ne touche ni le dernier keyframe ni son ballon) : la cible du ballon et la
    # durée totale servent à situer les adversaires (B8-b), exactement comme le fera `enrich_with_background`.
    flight: tuple[tuple[float, float, float], float] | None = None
    if outcome is not None and template.has_ball_flight:
        strike = strike_type_for(template.name, event_ref)
        target = _penalty_target(outcome, event_ref, strike) if template.name == "penalty" else _flight_target(outcome, event_ref)
        if target is not None:
            distance_m = _flight_distance_m((last_ball_xy.x, last_ball_xy.y, keyframes[-1].ball.z), target)
            speed_mps = strike_speed_for(strike, event_ref)
            flight = (target, distance_m / speed_mps if speed_mps > 0 else 0.0)

    pressure_context = None
    if opponent_lineup is not None and template.ground_control:
        from ligue1sim.animation.sequence_generator import nearest_opponent_distance_m, opponent_field_tracks  # import tardif : sequence_generator importe ce module
        from ligue1sim.coaches import coach_styles

        ball_target = (flight[0][0], flight[0][1]) if flight else (keyframes[-1].ball.x, keyframes[-1].ball.y)
        total_duration = duration + (flight[1] if flight else 0.0)
        tracks = opponent_field_tracks(opponent_lineup, event_ref, ball_target)
        pressure_context = _PressureContext(
            distance_at=lambda point, t: nearest_opponent_distance_m(tracks, point, t, total_duration),
            pressing_style="Pressing" in coach_styles(opponent_lineup.club_name),
            recuperation_haute=(template.name == "recuperation_haute"),
        )
    keyframes = _insert_ground_controls(template, keyframes, players_by_id, event_ref, pressure_context)  # B8-a : segment de contrôle à chaque réception au sol

    if flight is not None:
        (target_x, target_y, target_z), flight_duration = flight
        flight_start_players = keyframes[-1].players
        keyframes[-1] = replace(
            keyframes[-1],
            physics_tag=BALL_FLIGHT,
            ball=replace(keyframes[-1].ball, spin=strike_spin_for(strike, event_ref)),
        )
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
    # Chantier 1, 1d (15/10/2026) : durée 8,0 -> 9,0 s et géométrie de rôle sur les trois rôles (cibles inchangées -- support1/scorer
    # -> zone de tir, assist -> zone d'assist). support1 devient en plus un rôle TACTIQUE (`_resolve_roles`/`_pick_support`, 1b) : le
    # joueur récupérateur profond est désormais le joueur de champ dont la position de formation est la plus proche de la zone de tir,
    # parmi les postes attendus pour ce rôle (DC, LB, RB, MDC, MC -- proposés en conception, à confirmer par la mesure réelle).
    duration=9.0,
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
        Role(
            "support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.3), RoleFrame(1.0, 0.4)),
            geometry=RoleGeometry(GEOM_ZONE, preferred_postes=frozenset({"DC", "LB", "RB", "MDC", "MC"})),
        ),
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.2), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ASSIST_ZONE)),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.35), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ZONE)),
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
    # Chantier 1, 1c (15/10/2026) : géométrie de rôle sur les deux rôles, cible inchangée (assist -> zone d'assist, scorer -> zone de
    # tir, comme avant) -- seul le DÉPART devient réaliste (dérivé de la formation, course plafonnée), l'arrivée ne bouge pas.
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.6, 0.7), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ASSIST_ZONE)),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.6, 0.4), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ZONE)),
    ),
    tags=((0.0, "debordement"), (0.6, "centre"), (1.0, "tete")),
    ball_owner=((0.0, "assist"), (0.6, "assist"), (1.0, "scorer")),
    context_score=_score_debordement_centre_tete,
    physics_tags=((0.6, "cross"),),  # dernier segment (0.6 -> 1.0) : le centre en cloche jusqu'à la tête (B8-c1 : était `shot`, un ballon au sol)
    has_ball_flight=True,
    ground_control=False,  # B8-a : finition de la tête, réception AÉRIENNE (B8-c)
    aerial_contact=True,  # B8-c1 : le centre arrive à la hauteur de la tête (ou de la volée), le vol en part
)

_TEMPLATE_PERCEE_INDIVIDUELLE = Template(
    name="percee_individuelle",
    weight=0.9,
    # Chantier 1, 1c (15/10/2026) : durée 7,0 -> 8,0 s et géométrie de rôle sur le scorer (cible event.zone, inchangée -- seul le
    # départ devient réaliste, dérivé de la formation et plafonné par la course réalisable sur la durée du gabarit).
    duration=8.0,
    roles=(
        Role(
            "scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.35), RoleFrame(0.75, 0.7), RoleFrame(1.0, 1.0)),
            geometry=RoleGeometry(GEOM_ZONE),
        ),
    ),
    tags=((0.0, "controle"), (0.4, "dribble"), (0.75, "dribble"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.4, "scorer"), (0.75, "scorer"), (1.0, "scorer")),
    context_score=_score_percee_individuelle,
    physics_tags=((0.75, "shot"),),  # dernier segment (0.75 -> 1.0) : le tir au but
    has_ball_flight=True,
)

_TEMPLATE_UNE_DEUX = Template(
    name="une_deux",
    weight=0.8,
    # Chantier 1, 1d (15/10/2026) : durée 4,0 -> 5,0 s et géométrie de rôle sur les deux rôles (cibles inchangées -- assist -> zone
    # d'assist, scorer -> zone de tir). Pas de rôle générique ici (pas de "support1") : aucun volet tactique pour ce gabarit.
    #
    # Résiduel mesuré (100 matchs, graine d'audit 20260923, scripts/measure_geometry.py) : la passe scorer -> assist à t_ratio=0,5 passe
    # de 52 à 6 clips sur 94 au-dessus de 30 m/s (amélioration nette, mais pas nulle). Aucune exigence actuellement testée n'est violée
    # (EG-JOU-11 / ticket 47 restent "Planifié") -- à reprendre en 1g/1h avec le résiduel de `profondeur_1v1` (1c), pas dans ce commit.
    duration=5.0,
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.5), RoleFrame(1.0, 0.5)), geometry=RoleGeometry(GEOM_ASSIST_ZONE)),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.5, 0.6), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ZONE)),
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
    # Phase 6, B7-a (14/10/2026) : même chronologie que le penalty (B6-a). Le ballon est POSÉ au point du coup franc (z = 0,
    # immobile, `ball_position`) et le tireur part d'un point d'élan (4 à 7 m, `free_kick_runup_start`), attend (0 -> 0.25, 1,25 s),
    # s'élance (0.25 -> 0.8 : 85 % de la course) puis arrive sur le ballon (0.8 -> 1.0) et frappe à t_ratio = 1.0. Le point change
    # à chaque coup franc : `build_coup_franc` remplace `ball_position` par événement (valeur par défaut ci-dessous : 24 m, axe).
    roles=(Role("scorer", ANCHOR_FREE_KICK_SPOT, (RoleFrame(0.0, 0.0), RoleFrame(0.25, 0.0), RoleFrame(0.8, 0.85), RoleFrame(1.0, 1.0))),),
    tags=((0.0, "placement"), (0.25, "attente"), (0.8, "elan"), (1.0, "frappe")),
    ball_owner=((0.0, "scorer"), (0.25, "scorer"), (0.8, "scorer"), (1.0, "scorer")),
    ball_position=tuple((t, (1.0 - 24.0 / PITCH_LENGTH_M, 0.5)) for t in (0.0, 0.25, 0.8, 1.0)),
    context_score=_score_coup_franc,
    starts_at_restart=True,
    physics_tags=((0.8, "shot"),),  # dernier segment (0.8 -> 1.0) : ballon immobile (posé), puis ball_flight
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
    # B8-c1 (14/10/2026), option B du propriétaire : la durée reste 7,0 s (celle d'avant), le buteur garde donc son budget-temps. Le centre part PLUS TARD
    # (t = 4,9 s, t_ratio 0,7) et dure 2,1 s comme avant : il arrive à t = 7,0 s, à la hauteur du contact (`aerial_contact`), où le buteur le reprend. Le
    # segment « ballon disputé » qui rebondissait 2,8 s au sol (t = 4,2 à 7,0 s) n'existe plus ; l'assist termine sa marche au poteau de corner (t_ratio 0,6 -> 0,7,
    # progress 0,95 -> 1,0 : il bouge, le ballon aussi) avant de centrer. Les rôles gardent leurs positions d'avant à 0,0 / 0,3 / 0,6 / 1,0 ; la position à 0,7 est celle de la courbe d'avant à t = 4,9 s.
    duration=7.0,
    roles=(
        Role("assist", ANCHOR_ASSIST, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.4), RoleFrame(0.6, 0.95), RoleFrame(0.7, 1.0), RoleFrame(1.0, 1.0))),
        Role("support1", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.2), RoleFrame(0.6, 0.5), RoleFrame(0.7, 0.51), RoleFrame(1.0, 0.55))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.15), RoleFrame(0.6, 0.6), RoleFrame(0.7, 0.65), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "preparation"), (0.3, "montee"), (0.6, "attente"), (0.7, "centre"), (1.0, "tete")),
    ball_owner=((0.0, "assist"), (0.3, "assist"), (0.6, "assist"), (0.7, "assist"), (1.0, "scorer")),
    context_score=_score_corner,
    # Table des tags de corner : segments [0.0 -> 0.7] pass_ground inféré (l'assist porte le ballon au sol vers le point de corner, puis attend) ; segment
    # [0.7 -> 1.0] cross (le centre en vol : il arrive à la hauteur du contact, `aerial_contact`) ; le vol de la tête (`ball_flight`) part de cette hauteur.
    # Le segment `deflect` « ballon disputé » d'avant B8-c1 n'existe plus pour ce gabarit.
    physics_tags=((0.0, "pass_ground"), (0.7, "cross")),
    has_ball_flight=True,
    ground_control=False,  # B8-a : finition de la tête, réception AÉRIENNE (B8-c)
    aerial_contact=True,  # B8-c1 : le centre arrive à la hauteur de la tête (ou de la volée), le vol en part
)

_TEMPLATE_PROFONDEUR_1V1 = Template(
    name="profondeur_1v1",
    weight=0.9,
    # Chantier 1, 1c (15/10/2026) : durée 6,0 -> 7,0 s et géométrie de rôle sur le scorer SEUL (cible event.zone, inchangée). L'assist
    # ne bouge quasiment pas (progress 0,2 au maximum) : pas de géométrie ajoutée, gain de réalisme marginal pour un risque de
    # régression couplée au contrôle au sol (décision explicite, 1c).
    #
    # Effet de bord mesuré (100 matchs, graine d'audit 20260923, scripts/measure_geometry.py) : la passe assist -> scorer à t_ratio=0,3
    # (ball_owner) est mesurée entre la position FIXE de l'assist et celle du scorer à 30 % de sa progression -- cette dernière est
    # désormais plus avancée vers la zone de tir (départ rapproché par la géométrie), ce qui allonge ce segment précis plus vite que son
    # temps imparti ne croît. 14 clips sur 1552 passent le seuil de 30 m/s (0 avant 1c), uniquement sur ce gabarit. Aucune exigence
    # actuellement testée n'est violée (EG-JOU-11 / ticket 47 restent "Planifié", pas encore gardés par un test automatique) -- à
    # reprendre en 1g/1h (ticket 47) avant de considérer le chantier 1 clos, pas dans ce commit.
    duration=7.0,
    roles=(
        # ANCHOR_SCORER, pas ANCHOR_STATIC (fix du 23/09/2026) : le passeur
        # en profondeur doit suivre sa passe d'un ou deux pas plutôt que
        # rester planté après avoir lâché le ballon (t_ratio=0.3). Progress
        # relevé 0.1 -> 0.15/0.2, couplage à event.zone assumé (voir
        # contre_attaque).
        Role("assist", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.15), RoleFrame(1.0, 0.2))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.3, 0.3), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ZONE)),
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
    # Chantier 1, 1c (15/10/2026) : durée 6,0 -> 7,0 s et géométrie de rôle sur le scorer SEUL (cible event.zone, inchangée). L'assist
    # reste ANCHOR_STATIC sans géométrie : il ne bouge jamais (progress toujours 0), rien à réaliser.
    duration=7.0,
    roles=(
        Role("assist", ANCHOR_STATIC, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.0), RoleFrame(1.0, 0.0))),
        Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.3), RoleFrame(1.0, 1.0)), geometry=RoleGeometry(GEOM_ZONE)),
    ),
    tags=((0.0, "decalage"), (0.4, "controle"), (1.0, "enroulee")),
    ball_owner=((0.0, "assist"), (0.4, "scorer"), (1.0, "scorer")),
    context_score=_score_decalage_enroulee,
    physics_tags=((0.4, "shot"),),  # dernier segment (0.4 -> 1.0) : l'enroulée
    has_ball_flight=True,
)

_TEMPLATE_PENALTY = Template(
    # Enrichi le 23/09/2026 (audit visuel) : 1 rôle -> 3 (deux coéquipiers à l'entrée de la surface, à l'affût d'un rebond).
    # Phase 6, B6-a (08/10/2026) : le ballon est POSÉ au point de penalty (`ball_position`, ne bouge plus avec le tireur) ;
    # le tireur part d'un point d'élan situé à 6-9 m du ballon (voir `build_penalty`), attend (0 -> 0.25, 1 s), s'élance
    # (0.25 -> 0.8 : 85 % de la course) puis arrive sur le ballon (0.8 -> 1.0) et frappe à t_ratio = 1.0 (vitesse de course
    # de 3 m/s en moyenne, environ 6 m/s au plus pour un élan de 9 m).
    name="penalty",
    weight=0.6,
    duration=4.0,
    roles=(
        # ANCHOR_LATERAL_SHIFT : pas de côté fixe de 1,5 m, progress 0.4 -> 60 cm réels (fix du 23/09/2026, voir _LATERAL_SHIFT_M).
        Role("support1", ANCHOR_LATERAL_SHIFT, (RoleFrame(0.0, 0.0), RoleFrame(0.25, 0.4), RoleFrame(0.8, 0.4), RoleFrame(1.0, 0.4))),
        Role("support2", ANCHOR_LATERAL_SHIFT, (RoleFrame(0.0, 0.0), RoleFrame(0.25, 0.4), RoleFrame(0.8, 0.4), RoleFrame(1.0, 0.4))),
        # Du point d'élan (start_positions, surchargé par build_penalty) au point de penalty.
        Role("scorer", ANCHOR_PENALTY_SPOT, (RoleFrame(0.0, 0.0), RoleFrame(0.25, 0.0), RoleFrame(0.8, 0.85), RoleFrame(1.0, 1.0))),
    ),
    tags=((0.0, "placement"), (0.25, "attente"), (0.8, "elan"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.25, "scorer"), (0.8, "scorer"), (1.0, "scorer")),
    ball_position=tuple((t, (_PENALTY_SPOT.x, _PENALTY_SPOT.y)) for t in (0.0, 0.25, 0.8, 1.0)),
    context_score=_score_penalty,
    starts_at_restart=True,
    physics_tags=((0.8, "shot"),),  # dernier segment (0.8 -> 1.0) : ballon immobile (posé), puis ball_flight
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
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["contre_attaque"], event, lineup, start_positions, outcome, opponent_lineup)


def build_construction_placee(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["construction_placee"], event, lineup, start_positions, outcome, opponent_lineup)


def build_debordement_centre_tete(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["debordement_centre_tete"], event, lineup, start_positions, outcome, opponent_lineup)


def build_percee_individuelle(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["percee_individuelle"], event, lineup, start_positions, outcome, opponent_lineup)


def build_une_deux(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["une_deux"], event, lineup, start_positions, outcome, opponent_lineup)


def free_kick_spot(event_ref: str) -> PitchPoint:
    """Point du coup franc direct (B7-a) : distance au centre du but dans [max(18 ; racine(16,5² + y²)) ; 30] m et décalage latéral
    |y| de 0 à 12 m, côté gauche ou droit tiré par hachage. Le plancher racine(16,5² + y²) garde le ballon HORS de la surface de
    réparation (16,5 m de la ligne de but), sinon la faute serait un penalty. Déterministe (sha256 de `event_ref`)."""
    lateral_m = _flight_unit(event_ref, "fk_lateral") * _FREE_KICK_LATERAL_MAX_M
    side = 1.0 if _flight_unit(event_ref, "fk_side") >= 0.5 else -1.0
    distance_min_m = max(_FREE_KICK_DISTANCE_MIN_M, math.hypot(PENALTY_AREA_DEPTH_M, lateral_m))
    distance_m = distance_min_m + _flight_unit(event_ref, "fk_distance") * (_FREE_KICK_DISTANCE_MAX_M - distance_min_m)
    depth_m = math.sqrt(distance_m**2 - lateral_m**2)  # profondeur depuis la ligne de but : >= 16,5 m par construction
    return PitchPoint(x=1.0 - depth_m / PITCH_LENGTH_M, y=0.5 + side * lateral_m / PITCH_WIDTH_M)


def _free_kick_curve_sign(event_ref: str) -> float:
    """Signe du spin d'un coup franc enroulé (B7-a). Un spin > 0 gonfle la trajectoire vers les y croissants (`ball._perp_unit`) : la
    courbure est RENTRANTE (le ballon vise à l'extérieur puis revient vers l'axe du but) quand le gonflement est du côté du ballon,
    soit le signe de `y - 0,5` ; SORTANTE sinon. Rentrante pour 75 % des coups francs (`_FREE_KICK_INWARD_CURVE_P`)."""
    ball_side = 1.0 if free_kick_spot(event_ref).y >= 0.5 else -1.0
    inward = _flight_unit(event_ref, "fk_curve_inward") < _FREE_KICK_INWARD_CURVE_P
    return ball_side if inward else -ball_side


def free_kick_runup_start(event_ref: str) -> PitchPoint:
    """Point d'élan du tireur (B7-a) : 4 à 7 m du ballon, sous un angle par rapport à l'axe ballon -> centre du but de +-10 degrés
    pour un frappé, de 20 à 40 degrés (côté tiré par hachage) pour un enroulé. Déterministe (sha256 de `event_ref`)."""
    spot = free_kick_spot(event_ref)
    length_m = _FREE_KICK_RUNUP_MIN_M + _flight_unit(event_ref, "fk_runup_length") * (_FREE_KICK_RUNUP_MAX_M - _FREE_KICK_RUNUP_MIN_M)
    if strike_type_for("coup_franc", event_ref).name == "coup_franc_frappe":
        angle = math.radians((2.0 * _flight_unit(event_ref, "fk_runup_angle") - 1.0) * _FREE_KICK_RUNUP_ANGLE_STRAIGHT_DEG)
    else:
        magnitude = _FREE_KICK_RUNUP_ANGLE_CURL_MIN_DEG + _flight_unit(event_ref, "fk_runup_angle") * (
            _FREE_KICK_RUNUP_ANGLE_CURL_MAX_DEG - _FREE_KICK_RUNUP_ANGLE_CURL_MIN_DEG
        )
        angle = math.radians(magnitude if _flight_unit(event_ref, "fk_runup_side") >= 0.5 else -magnitude)
    ball_x_m, ball_y_m = spot.x * PITCH_LENGTH_M, spot.y * PITCH_WIDTH_M
    to_goal_x, to_goal_y = PITCH_LENGTH_M - ball_x_m, PITCH_WIDTH_M / 2.0 - ball_y_m
    norm = math.hypot(to_goal_x, to_goal_y)
    ux, uy = to_goal_x / norm, to_goal_y / norm  # axe ballon -> centre du but
    nx, ny = -uy, ux
    return PitchPoint(
        x=(ball_x_m - length_m * (math.cos(angle) * ux + math.sin(angle) * nx)) / PITCH_LENGTH_M,
        y=(ball_y_m - length_m * (math.cos(angle) * uy + math.sin(angle) * ny)) / PITCH_WIDTH_M,
    )


def build_coup_franc(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    """Phase 6, B7-a : le ballon est posé au point du coup franc (`free_kick_spot`, la zone de l'événement n'est plus lue) et le
    tireur s'élance depuis un point d'élan (`free_kick_runup_start`). Le gabarit est reconstruit PAR ÉVÉNEMENT (le point varie)."""
    scorer = _resolve_roles(event, lineup, ("scorer",))["scorer"]
    event_ref = f"goal:{event.club_name}:{event.scorer}:{event.minute}"
    spot = free_kick_spot(event_ref)
    base = TEMPLATES["coup_franc"]
    template = replace(base, ball_position=tuple((t, (spot.x, spot.y)) for t, _ in base.ball_position))
    starts = {**start_positions, player_id_of(scorer): free_kick_runup_start(event_ref)}
    return build_from_template(template, event, lineup, starts, outcome, opponent_lineup)


def build_corner(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["corner"], event, lineup, start_positions, outcome, opponent_lineup)


def build_profondeur_1v1(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["profondeur_1v1"], event, lineup, start_positions, outcome, opponent_lineup)


def build_recuperation_haute(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["recuperation_haute"], event, lineup, start_positions, outcome, opponent_lineup)


# Brief "real Magnus effect" (23/09/2026), Tâche 3, puis Phase 6 B5 (08/10/2026) : le spin de la frappe enroulée n'est plus
# une constante posée ici sur la conduite (`shot`) ET sur le vol, mais le spin du type `shot_enroule_fort` (50 à 80 rad/s),
# posé sur le SEUL vol par `build_from_template` (voir `STRIKE_TYPES`). Ce gabarit garde son constructeur dédié pour que
# `BUILDERS` reste inchangé. DETTE (voir `docs/ball_flight_design.md`, "Dette connue") : résidu de vitesse 3D instantanée
# > 35 m/s possible (pic dû à la décélération de B1 ; 140 vols sur 1 259 en B5, tous `shot_tendu`), voir docs/phase6_block_b_audit.md.
def build_decalage_enroulee(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["decalage_enroulee"], event, lineup, start_positions, outcome, opponent_lineup)


def penalty_runup_start(event_ref: str) -> PitchPoint:
    """Point d'élan du tireur (B6-a) : à `_PENALTY_RUNUP_MIN_M` - `_PENALTY_RUNUP_MAX_M` du point de penalty, sous un angle de
    +-`_PENALTY_RUNUP_ANGLE_MAX_DEG` degrés par rapport à l'axe tireur -> but. Déterministe (sha256 de `event_ref`)."""
    length_m = _PENALTY_RUNUP_MIN_M + _flight_unit(event_ref, "penalty_runup_length") * (_PENALTY_RUNUP_MAX_M - _PENALTY_RUNUP_MIN_M)
    angle = math.radians((2.0 * _flight_unit(event_ref, "penalty_runup_angle") - 1.0) * _PENALTY_RUNUP_ANGLE_MAX_DEG)
    return PitchPoint(
        x=_PENALTY_SPOT.x - length_m * math.cos(angle) / PITCH_LENGTH_M,
        y=_PENALTY_SPOT.y - length_m * math.sin(angle) / PITCH_WIDTH_M,
    )


def build_penalty(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    """Phase 6, B6-a : le ballon est posé au point de penalty réglementaire (la zone de l'événement n'est plus lue) et le
    tireur s'élance depuis un point d'élan (`penalty_runup_start`) : seule la position de départ du tireur est remplacée."""
    scorer = _resolve_roles(event, lineup, ("scorer",))["scorer"]
    event_ref = f"goal:{event.club_name}:{event.scorer}:{event.minute}"
    starts = {**start_positions, player_id_of(scorer): penalty_runup_start(event_ref)}
    return build_from_template(TEMPLATES["penalty"], event, lineup, starts, outcome, opponent_lineup)


def build_but_gag(
    event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint], outcome: str | None = None,
    opponent_lineup: Lineup | None = None,
) -> Sequence:
    return build_from_template(TEMPLATES["but_gag"], event, lineup, start_positions, outcome, opponent_lineup)


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
