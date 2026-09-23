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

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from ligue1sim.animation.types import BallState, Keyframe, PlayerId, RosterEntry, Sequence
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_WIDTH_M, PitchPoint, center_of
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, Player

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
    instable et n'aurait "GK=1" que par coïncidence."""
    ordered = sorted(lineup.players, key=lambda p: (_NUMERO_GROUP_ORDER.get(p.group, 4), p.name))
    return {player_id_of(p): numero for numero, p in enumerate(ordered, start=1)}


def _resolve_roles(event: GoalEvent, lineup: Lineup, role_names: tuple[str, ...]) -> dict[str, Player]:
    """Associe chaque rôle nommé d'un gabarit à un vrai joueur de `lineup`.
    "scorer"/"assist" sont résolus depuis l'événement lui-même, jamais
    inventés -- un rôle "assist" sans passeur réel (`event.assist is None`)
    est simplement absent du résultat (le gabarit continue sans lui, voir
    `build_from_template`). Les rôles génériques ("support1", "support2"...)
    sont comblés par les coéquipiers restants (hors gardien, hors
    scorer/assist déjà pris), triés par nom pour un résultat déterministe :
    `build_from_template` est une fonction PURE, jamais un tirage."""
    by_name = {p.name: p for p in lineup.players}
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
        (p for p in lineup.players if p.group != GOALKEEPER and p.name not in used_names), key=lambda p: p.name
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


def build_from_template(
    template: Template,
    event: GoalEvent,
    lineup: Lineup,
    start_positions: dict[PlayerId, PitchPoint],
) -> Sequence:
    """Moteur générique partagé par les 12 gabarits (voir en bas de fichier
    pour leurs wrappers `build_xxx`). Fonction PURE : mêmes entrées, même
    `Sequence`, aucun tirage aléatoire -- la part de hasard de ce module se
    limite au CHOIX du gabarit (`pick_template`), jamais à son exécution."""
    _validate_template(template)

    role_names = tuple(role.name for role in template.roles)
    resolved = _resolve_roles(event, lineup, role_names)
    role_ids = {name: player_id_of(player) for name, player in resolved.items()}
    role_starts = {name: start_positions[role_ids[name]] for name in resolved}
    role_by_player_id = {player_id: role_name for role_name, player_id in role_ids.items()}
    players_by_id = {player_id_of(p): p for p in lineup.players}
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
        else:
            ball_x, ball_y = last_ball_xy.x, last_ball_xy.y
        last_ball_xy = PitchPoint(x=ball_x, y=ball_y)

        keyframes.append(
            Keyframe(
                t=t_ratio * template.duration,
                ball=BallState(x=ball_x, y=ball_y, z=ball_height_by_ratio.get(t_ratio, 0.0), spin=0.0, owner_id=owner_id),
                players=players,
                tag=tags_by_ratio.get(t_ratio, ""),
            )
        )

    return Sequence(
        event_ref=f"goal:{event.club_name}:{event.scorer}:{event.minute}",
        keyframes=keyframes,
        duration=template.duration,
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
)

_TEMPLATE_PERCEE_INDIVIDUELLE = Template(
    name="percee_individuelle",
    weight=0.9,
    duration=7.0,
    roles=(Role("scorer", ANCHOR_SCORER, (RoleFrame(0.0, 0.0), RoleFrame(0.4, 0.35), RoleFrame(0.75, 0.7), RoleFrame(1.0, 1.0))),),
    tags=((0.0, "controle"), (0.4, "dribble"), (0.75, "dribble"), (1.0, "tir")),
    ball_owner=((0.0, "scorer"), (0.4, "scorer"), (0.75, "scorer"), (1.0, "scorer")),
    context_score=_score_percee_individuelle,
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
    context_score=_score_corner,
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
    context_score=_score_recuperation_haute,
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


def build_contre_attaque(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["contre_attaque"], event, lineup, start_positions)


def build_construction_placee(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["construction_placee"], event, lineup, start_positions)


def build_debordement_centre_tete(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["debordement_centre_tete"], event, lineup, start_positions)


def build_percee_individuelle(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["percee_individuelle"], event, lineup, start_positions)


def build_une_deux(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["une_deux"], event, lineup, start_positions)


def build_coup_franc(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["coup_franc"], event, lineup, start_positions)


def build_corner(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["corner"], event, lineup, start_positions)


def build_profondeur_1v1(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["profondeur_1v1"], event, lineup, start_positions)


def build_recuperation_haute(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["recuperation_haute"], event, lineup, start_positions)


def build_decalage_enroulee(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["decalage_enroulee"], event, lineup, start_positions)


def build_penalty(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["penalty"], event, lineup, start_positions)


def build_but_gag(event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence:
    return build_from_template(TEMPLATES["but_gag"], event, lineup, start_positions)


BUILDERS: dict[str, Callable[[GoalEvent, Lineup, dict[PlayerId, PitchPoint]], Sequence]] = {
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
