"""Assemble une `Sequence` complète pour un but déjà décidé par le moteur --
choisit un gabarit (`templates.pick_template`) et l'exécute
(`templates.BUILDERS`), en calant le résultat sur ce que le moteur a déjà
décidé : le buteur finit TOUJOURS buteur, le passeur TOUJOURS passeur
(garanti par construction dans `templates.build_from_template`, jamais
recalculé ici), et la minute réelle est ajoutée aux métadonnées de la
`Sequence`. Étape 2.3 de la feuille de route, voir
docs/simulation_physique_archi.md.

Ne touche à AUCUNE probabilité du moteur Poisson (`ligue1sim.simulation`/
`ligue1sim.events`) : la seule part de hasard de ce module est le CHOIX du
gabarit (`templates.pick_template`), via un générateur local et
déterministe (voir `deterministic_rng`, même principe que
`events._deterministic_rng`) -- jamais le flux `random`/`np.random` global
qui pilote le tirage du buteur/de la minute/du carton dans
`ligue1sim.events`.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, replace

from ligue1sim.animation.motion import _background_position_at
from ligue1sim.animation.spatial import PitchLayoutState, placed_player_to_normalized
from ligue1sim.animation.templates import (
    BUILDERS,
    context_from_event,
    numeros_by_player_id,
    penalty_ball_side,
    pick_template,
    player_id_of,
    strike_type_for,
)
from ligue1sim.animation.types import BackgroundTrack, PlayerId, RosterEntry, Sequence
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint
from ligue1sim.pitch_layout import place_starting_xi
from ligue1sim.players import GOALKEEPER, Player


@dataclass(frozen=True)
class MatchState:
    """Contexte du match au moment d'un but, nécessaire pour pondérer le
    choix du gabarit (voir `templates.TemplateContext`) -- ce que
    `generate_sequence` ne peut pas déduire de `event`/`lineup` seuls.

    `goal_diff_before` : écart au score AVANT ce but (positif = l'équipe qui
    marque menait déjà), voir `templates.TemplateContext.goal_diff_before`
    pour pourquoi "before" et pas "after". `minute` : généralement identique
    à `event.minute`, gardé ici pour que `MatchState` reste un contexte de
    match autonome (calculable une fois, avant de savoir quel événement il
    accompagnera). `competition_type` : "league" | "cup" | "continental"."""

    goal_diff_before: int
    minute: int
    competition_type: str


def deterministic_rng(match_id: str, event_index: int) -> random.Random:
    """Générateur aléatoire local et déterministe pour le choix du gabarit
    d'un événement -- même principe que `events._deterministic_rng` (hash
    sha256, pas `hash()` qui est aléatoire d'un process Python à l'autre) :
    la même combinaison `(match_id, event_index)` retombe toujours sur le
    même gabarit, sans jamais consommer le flux `random`/`np.random`
    global."""
    digest = hashlib.sha256(f"{match_id}|{event_index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _start_positions(lineup: Lineup, state: PitchLayoutState) -> dict[PlayerId, PitchPoint]:
    """Convertit les positions de formation (référentiel `pitch_layout`) en
    référentiel normalisé, indexées par `PlayerId` (voir
    `templates.player_id_of`). `PlacedPlayer` ne porte qu'un nom
    (`PlayerMatchStat` n'a pas d'identifiant) -- jointure par nom avec les
    vrais `Player` de `lineup` pour retrouver leur `PlayerId`."""
    players_by_name = {p.name: p for p in lineup.players}
    positions: dict[PlayerId, PitchPoint] = {}
    for placed in state.placed_players:
        player = players_by_name.get(placed.stat.player_name)
        if player is None:
            continue  # joueur suivi par pitch_layout mais absent de `lineup` (compo désynchronisée) -- ignoré
        positions[player_id_of(player)] = placed_player_to_normalized(placed, attacking_up=state.attacking_up)
    return positions


def generate_sequence(
    event: GoalEvent,
    lineup: Lineup,
    pitch_layout_state: PitchLayoutState,
    match_state: MatchState,
    rng: random.Random,
    *,
    match_id: str = "",
    event_index: int = 0,
) -> Sequence:
    """Assemble la `Sequence` d'un but déjà décidé par le moteur.

    1. Convertit `pitch_layout_state` en `start_positions` normalisés.
    2. Résout le poste du buteur/passeur et construit `templates.TemplateContext`
       à partir de `lineup` + `match_state` (voir `MatchState` -- corrige le
       bug du 22/09/2026 où `goal_diff_after` était toujours à 0, contexte
       neutre, faute d'un état de score transmis à cette fonction).
    3. `templates.pick_template(context, rng=rng)` choisit un gabarit.
    4. `templates.BUILDERS[nom](event, lineup, start_positions)` l'exécute
       -- le buteur/passeur y terminent DÉJÀ exactement sur `event.zone`/
       `event.assist_zone` (garanti par `templates.build_from_template`,
       rien à recaler ici).
    5. La minute réelle (et `match_id`/`event_index`) est ajoutée à
       `Sequence.meta`, en plus de ce que le gabarit y a déjà mis.

    `rng` : construire via `deterministic_rng(match_id, event_index)` pour
    un résultat reproductible sans re-simuler le match."""
    start_positions = _start_positions(lineup, pitch_layout_state)

    players_by_name = {p.name: p for p in lineup.players}
    scorer = players_by_name.get(event.scorer)
    if scorer is None:
        raise ValueError(f"Buteur {event.scorer!r} introuvable dans la compo fournie")
    assist_player = players_by_name.get(event.assist) if event.assist else None

    context = context_from_event(
        event,
        scorer_poste=scorer.poste,
        assist_poste=assist_player.poste if assist_player is not None else None,
        goal_diff_before=match_state.goal_diff_before,
        competition_type=match_state.competition_type,
    )
    template_name = pick_template(context, rng=rng)
    sequence = BUILDERS[template_name](event, lineup, start_positions)

    return replace(
        sequence,
        meta={**sequence.meta, "minute": event.minute, "match_id": match_id, "event_index": event_index},
    )


# --- Point 1 du bilan simulation physique (23/09/2026) : les 22 joueurs --
# Une Sequence de gabarit ne suit que ses 2-4 joueurs actifs (buteur,
# passeur, support*) -- rendue telle quelle, la scène montrerait 3 ronds sur
# un terrain vide, pas du Football Manager. `enrich_with_background`
# complète la Sequence déjà construite avec les 18-20 joueurs "décor" (le
# reste de l'équipe qui marque + les 11 adverses, gardien compris), chacun
# un micro-mouvement déterministe (`BackgroundTrack`), jamais un rôle de
# gabarit. NE TOUCHE PAS à templates.py : part d'une Sequence déjà produite
# par un gabarit et la complète, les 12 gabarits restent inchangés.

# --- Règles de drift PAR RÔLE TACTIQUE (Point 2 du brief du 23/09/2026) --
# Remplace la première version (Point 1) qui faisait dériver TOUT le monde
# vers le ballon, uniformément -- incohérent pour un fan de foot : un ailier
# côté opposé au ballon ne s'y précipite pas (il tient sa largeur ou fait un
# appel), un latéral qui défend ne monte pas, un attaquant ne redescend
# jamais vers son propre but. Toujours "pas d'IA" : une poignée de branches
# par poste/côté du ballon/phase (équipe qui attaque ou défend), amplitude
# déterministe (hash sha256, voir `_deterministic_unit`), jamais aléatoire.
# Ces règles ne visent PAS le réalisme parfait (voir consigne d'Olivier) --
# seulement une cohérence tactique de base, pour qu'un œil de fan de foot ne
# tique pas devant le GIF de validation (scripts/preview_background.py).

_DEFENDER_X_RANGE = (0.03, 0.06)  # donné par Olivier
_DEFENDER_Y_MAX = 0.02  # donné par Olivier
_MID_X_RANGE = (0.02, 0.04)  # non quantifié dans le bilan initial -- extrapolé par analogie avec les défenseurs
_MID_Y_MAX = 0.015
_WINGER_SUPPORT_X_RANGE = (0.02, 0.04)  # ailier côté ballon : soutien proche du porteur
_WINGER_SUPPORT_Y_MAX = 0.01  # "dans le couloir" -- moins de latéral qu'un MC, pour ne pas rentrer dans l'axe
_WINGER_HOLD_MAGNITUDE = 0.01  # ailier côté opposé qui "tient la largeur" -- quasi immobile
_FORWARD_RUN_X_RANGE = (0.02, 0.04)  # appel en profondeur (ailier opposé) / appel (BU) -- toujours vers l'avant, jamais vers son propre but
_STRIKER_HOLD_MAGNITUDE = 0.008  # BU qui "reste haut" -- quasi immobile, jamais vers le ballon
_MAX_DRIFT_MAGNITUDE = 0.05  # ~5% du terrain, borne globale donnée par Olivier -- absorbe l'essentiel du risque d'erreur sur les fourchettes ci-dessus

# --- Gardien actif, brief 1/2 (24/09/2026) : position de base + réaction --
# latérale passive (suivi du ballon, sans plongeon -- voir brief 2). Un
# gardien reste un joueur "décor" (`BackgroundTrack`, jamais un rôle de
# gabarit, voir `_tactical_drift` ci-dessous) : ce chantier ne touche donc
# QUE (1) le point de départ de son `BackgroundTrack` (`_gk_base_position`,
# remplace la position issue de la formation générique `pitch_layout`,
# pensée pour l'écran "stade" et pas pour ce rôle) et (2) l'amplitude de son
# drift latéral (`_GK_LATERAL_MAX_M`, remplace l'ancien `_GK_Y_MAX`) -- valeurs
# choisies pour ce brief, documentées ci-dessous, jamais "données par
# Olivier" comme les fourchettes tactiques au-dessus.
_GK_BASE_ADVANCE_M = 3.0  # avancée par défaut depuis SA ligne de but -- dans sa surface de but (5,5 m de profondeur, voir docs/visual_backlog.md #4), cohérent avec un gardien qui ne colle pas sa ligne sans sortir en sweeper-keeper
_GK_BASE_Y = 0.5  # centre de sa cage, latéralement -- le but est centré sur le terrain (référentiel `pitch_geometry`)
_GK_LATERAL_MAX_M = 2.5  # amplitude latérale max du suivi passif -- nettement en-deçà de la demi-largeur du but (3,66 m : but réglementaire 7,32 m), pour ne JAMAIS dépasser les poteaux même au pic du hash déterministe (voir _tactical_drift)


def _gk_base_position(team_side: str) -> tuple[float, float]:
    """Position de base du gardien (Tâche 1 du brief "gardien actif" 1/2) :
    sur SA ligne de but, `_GK_BASE_ADVANCE_M` mètres devant, centré entre les
    poteaux (`_GK_BASE_Y`). Référentiel : celui, PARTAGÉ, de la `Sequence`
    (voir `pitch_geometry` -- x=progression vers le but adverse, y=latéral,
    0-1) : le but de l'équipe qui marque ("scorer") est à x=0, celui de
    l'adversaire ("opponent", celui qui encaisse) est à x=1 -- symétrique de
    `_forward_sign`. Remplace la position de formation (`pitch_layout`,
    ~10,5 m avancée pour un gardien) par une position pensée pour CE rôle,
    indépendante du dispositif tactique choisi."""
    advance = _GK_BASE_ADVANCE_M / PITCH_LENGTH_M
    x = advance if team_side == "scorer" else 1.0 - advance
    return (x, _GK_BASE_Y)


# --- Phase 6, B6-d (14/10/2026) : réaction du gardien sur penalty, Option 2 stricte -------------------------------------
# Seul le DRIFT du gardien adverse change (amplitude et côté), uniquement pour le gabarit `penalty` : le contrat `Sequence`
# (types.py, serialize.py, motion.py) est intact, donc AUCUN délai de réaction ni durée de plongeon (Bloc A, A1.2). Constantes
# validées par le propriétaire. Tout est tiré par sha256 de `player_id|event_ref|sel` (`_event_unit`).
_GK_PENALTY_MAX_M = (2.2, 2.8)  # maximum d'amplitude tiré par événement (sel `gk_amp`) ; 2,8 m = borne dure, sous les poteaux (3,66 m)
_GK_PENALTY_WRONG_P = {"penalty_fort": 0.5, "penalty_place": 0.4, "penalty_contre_pied": 1.0}  # but : part du mauvais côté, par type (2d) -- donne 0,3*0,5 + 0,5*0,4 + 0,2*1 = 55 % au global (2c)
_GK_PENALTY_WRONG_AMP = (0.40, 0.90)  # but, mauvais côté : fraction du maximum (sel `gk_amp_wrong`)
_GK_PENALTY_SHORT_REACH = (0.40, 0.75)  # but, bon côté : fraction de la distance requise (sel `gk_short`), jamais le ballon
_GK_PENALTY_MISS_AMP = (0.40, 1.00)  # hors cadre / poteau / barre : fraction du maximum (sel `gk_amp_miss`)
_GK_PENALTY_MISS_OUTCOMES = ("hors_cadre", "poteau", "barre")


def _span(unit: float, lo_hi: tuple[float, float]) -> float:
    return lo_hi[0] + unit * (lo_hi[1] - lo_hi[0])


def _penalty_gk_drift(player_id: PlayerId, event_ref: str, ball_y: float, outcome: str | None) -> tuple[float, float]:
    """Drift latéral `(0.0, dy)` du gardien adverse sur un penalty (B6-d). `ball_y` : y final du ballon (normalisé).

    CONVENTION B6-b AJUSTÉE (côté du gardien vs côté du ballon, `templates.penalty_ball_side`) : sur `penalty_contre_pied`, le
    gardien s'engage du côté OPPOSÉ au ballon, sauf si l'issue est un arrêt, auquel cas il finit du côté du ballon. Le
    « contre-pied » décrit la trajectoire de la frappe, pas le plongeon d'un arrêt.

    `outcome=None` (appel sans issue : scripts, tests) : amplitude seule, vers le ballon, fraction `drift_y` du maximum.
    Arrêt : bon côté, atteint le y du ballon (plafonné à `_GK_PENALTY_MAX_M[1]`). But : mauvais côté avec la probabilité du type
    (`_GK_PENALTY_WRONG_P`), sinon bon côté mais court. Hors cadre / poteau / barre : côté 50/50 (sel `gk_side_miss`), toujours
    opposé pour un contre-pied. Toute autre issue : comme sans issue."""
    cap_m = _GK_PENALTY_MAX_M[1]
    max_m = _span(_event_unit(player_id, event_ref, "gk_amp"), _GK_PENALTY_MAX_M)
    ball_dy_m = (ball_y - _GK_BASE_Y) * PITCH_WIDTH_M
    ball_side = math.copysign(1.0, ball_dy_m) if ball_dy_m else float(penalty_ball_side(event_ref))
    required_m = min(abs(ball_dy_m), cap_m)
    contre_pied = strike_type_for("penalty", event_ref).name == "penalty_contre_pied"

    if outcome == "arret":
        dy_m = ball_side * required_m if ball_dy_m else 0.0
    elif outcome == "but":
        wrong_p = _GK_PENALTY_WRONG_P[strike_type_for("penalty", event_ref).name]
        if _event_unit(player_id, event_ref, "gk_side") < wrong_p:
            dy_m = -ball_side * _span(_event_unit(player_id, event_ref, "gk_amp_wrong"), _GK_PENALTY_WRONG_AMP) * max_m
        else:
            dy_m = ball_side * _span(_event_unit(player_id, event_ref, "gk_short"), _GK_PENALTY_SHORT_REACH) * required_m
    elif outcome in _GK_PENALTY_MISS_OUTCOMES:
        toward_ball = not contre_pied and _event_unit(player_id, event_ref, "gk_side_miss") < 0.5
        dy_m = (ball_side if toward_ball else -ball_side) * _span(_event_unit(player_id, event_ref, "gk_amp_miss"), _GK_PENALTY_MISS_AMP) * max_m
    else:  # sans issue : amplitude seule, plancher de dérive conservé (ballon à l'axe -> `_tactical_drift` donnait déjà 0 avant le plancher)
        dy_m = ball_side * _event_unit(player_id, event_ref, "drift_y") * max_m if ball_dy_m else 0.0
        return _floor_drift_magnitude(0.0, dy_m / PITCH_WIDTH_M, player_id, event_ref)
    return (0.0, dy_m / PITCH_WIDTH_M)


# --- Phase 6, B7-d (14/10/2026) : gardien adverse d'un coup franc direct, même option « stricte » que B6-d ----------------------
# Seuls changent le point de départ et le DRIFT du gardien, pour le seul gabarit `coup_franc` (aucun délai ni plongeon : Bloc A, A1.2).
# Constantes validées par le propriétaire ; l'amplitude, le « mauvais côté » de repli, la portée courte et les ratés reprennent celles de
# B6-d (`_GK_PENALTY_*`). Tout est tiré par sha256 de `player_id|event_ref|sel` (`_event_unit`).
_GK_FREE_KICK_ADVANCE_M = (1.0, 2.0)  # avancée de départ depuis sa ligne, tirée par événement (sel `gk_fk_adv`) ; remplace `_GK_BASE_ADVANCE_M` (3,0 m) pour ce seul gabarit
_GK_FREE_KICK_OFFSET_M = (1.0, 2.0)  # décalage latéral de départ, du côté du ballon (sel `gk_fk_offset`)
_GK_FREE_KICK_WRONG_P = {"coup_franc_enroule": 0.35, "coup_franc_frappe": 0.25}  # but : part du mauvais côté, par type de frappe
_GK_FREE_KICK_MAX_Y_M = _GK_LATERAL_MAX_M  # |y| final borné (2,5 m du centre, poteaux à 3,66 m) : le départ décalé ne doit pas pousser le gardien contre un poteau


def _free_kick_gk_start(player_id: PlayerId, event_ref: str, ball_y: float) -> tuple[float, float]:
    """Point de départ du gardien adverse sur coup franc (B7-d) : `_GK_FREE_KICK_ADVANCE_M` devant sa ligne, décalé de
    `_GK_FREE_KICK_OFFSET_M` du côté du ballon (`ball_y` : y du ballon posé ; au centre exact, côté tiré par hachage)."""
    advance_m = _span(_event_unit(player_id, event_ref, "gk_fk_adv"), _GK_FREE_KICK_ADVANCE_M)
    offset_m = _span(_event_unit(player_id, event_ref, "gk_fk_offset"), _GK_FREE_KICK_OFFSET_M)
    if ball_y != _GK_BASE_Y:
        side = math.copysign(1.0, ball_y - _GK_BASE_Y)
    else:
        side = 1.0 if _event_unit(player_id, event_ref, "gk_fk_side") < 0.5 else -1.0
    return (1.0 - advance_m / PITCH_LENGTH_M, _GK_BASE_Y + side * offset_m / PITCH_WIDTH_M)


def _free_kick_gk_drift(
    player_id: PlayerId, event_ref: str, start_y: float, target_y: float, outcome: str | None
) -> tuple[float, float]:
    """Drift latéral `(0.0, dy)` du gardien adverse sur un coup franc (B7-d), même logique que `_penalty_gk_drift`. `start_y` : y de
    départ du gardien ; `target_y` : y final du ballon (la cible du tir, ou le point posé pour `tacle` / `degagement`).

    Arrêt : bon côté, atteint le y du ballon (déplacement plafonné à `_GK_PENALTY_MAX_M[1]`). But : mauvais côté avec la probabilité du
    type de frappe (`_GK_FREE_KICK_WRONG_P`), sinon bon côté mais court. Hors cadre / poteau / barre : côté 50/50. Toute autre issue
    (`tacle`, `degagement`) ou sans issue : vers le ballon, fraction `drift_y` du maximum, plancher de dérive conservé. Dans tous les cas
    la position finale reste à moins de `_GK_FREE_KICK_MAX_Y_M` du centre."""
    cap_m = _GK_PENALTY_MAX_M[1]
    max_m = _span(_event_unit(player_id, event_ref, "gk_amp"), _GK_PENALTY_MAX_M)
    start_m = (start_y - _GK_BASE_Y) * PITCH_WIDTH_M
    need_m = (target_y - _GK_BASE_Y) * PITCH_WIDTH_M - start_m  # déplacement signé qui amènerait le gardien au y du ballon
    side = math.copysign(1.0, need_m) if need_m else (1.0 if _event_unit(player_id, event_ref, "gk_fk_side") < 0.5 else -1.0)
    required_m = min(abs(need_m), cap_m)

    if outcome == "arret":
        dy_m = side * required_m
    elif outcome == "but":
        wrong_p = _GK_FREE_KICK_WRONG_P[strike_type_for("coup_franc", event_ref).name]
        if _event_unit(player_id, event_ref, "gk_side") < wrong_p:
            dy_m = -side * _span(_event_unit(player_id, event_ref, "gk_amp_wrong"), _GK_PENALTY_WRONG_AMP) * max_m
        else:
            dy_m = side * _span(_event_unit(player_id, event_ref, "gk_short"), _GK_PENALTY_SHORT_REACH) * required_m
    elif outcome in _GK_PENALTY_MISS_OUTCOMES:
        toward_ball = _event_unit(player_id, event_ref, "gk_side_miss") < 0.5
        dy_m = (side if toward_ball else -side) * _span(_event_unit(player_id, event_ref, "gk_amp_miss"), _GK_PENALTY_MISS_AMP) * max_m
    else:
        dy_m = side * _event_unit(player_id, event_ref, "drift_y") * max_m
        dy_m = max(-_GK_FREE_KICK_MAX_Y_M - start_m, min(_GK_FREE_KICK_MAX_Y_M - start_m, dy_m))
        return _floor_drift_magnitude(0.0, dy_m / PITCH_WIDTH_M, player_id, event_ref)
    dy_m = max(-_GK_FREE_KICK_MAX_Y_M - start_m, min(_GK_FREE_KICK_MAX_Y_M - start_m, dy_m))
    return (0.0, dy_m / PITCH_WIDTH_M)


def _deterministic_unit(key: object, salt: str) -> float:
    """Fraction déterministe dans [0, 1) -- même principe que
    `motion._start_offset` (hash sha256, jamais `hash()` ni `random`) :
    utilisée pour donner à chaque joueur "décor" une amplitude de drift
    stable dans sa fourchette de poste (ou, pour la ligne de défenseurs
    centraux, une amplitude stable partagée par toute la ligne -- `key` peut
    alors être une chaîne descriptive plutôt qu'un `PlayerId`)."""
    digest = hashlib.sha256(f"{salt}|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _event_unit(player_id: PlayerId, event_ref: str, salt: str) -> float:
    """Fraction déterministe dans [0, 1) propre à un COUPLE (joueur, événement) -- Phase 6, B6-c. Hachage sha256 de
    `player_id|event_ref|salt` (jamais `hash()` ni `random`) : le sel est fixe, un par usage ("drift_x", "drift_y",
    "winger_choice", "hold_width", "striker_choice", "hold_high", "drift_floor_side"). Avant B6-c la clé était
    `player_id` seul, donc un même joueur "décor" dérivait de la même façon dans tous ses clips ; les amplitudes
    (fourchettes par rôle) ne changent pas, seule la fraction tirée dans la fourchette varie avec l'événement.
    `event_ref` vide (appel direct sans événement, tests) : tirage stable mais sans variété par événement."""
    digest = hashlib.sha256(f"{player_id}|{event_ref}|{salt}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _toward(target: float, start: float, magnitude: float) -> float:
    """Déplacement signé de `start` vers `target`, amplitude `magnitude` --
    0.0 si `start == target` (pas de direction arbitraire par division par
    zéro)."""
    delta = target - start
    return math.copysign(magnitude, delta) if delta else 0.0


def _side_of(y: float) -> str:
    """"Gauche"/"droite" du terrain (latéral, référentiel normalisé, voir
    pitch_geometry) -- seule la comparaison entre deux `_side_of` compte
    (même côté ou non), jamais la valeur absolue."""
    return "left" if y < 0.5 else "right"


def _forward_sign(team_side: str) -> float:
    """+1.0 pour l'équipe qui marque (son but adverse est à x=1 dans le
    référentiel PARTAGÉ de la Sequence, voir `spatial.py`), -1.0 pour
    l'adversaire (le sien est à x=0) -- direction "vers l'avant" pour un
    appel en profondeur (ailier) ou un appel (BU), jamais vers son propre
    but quel que soit le côté du ballon."""
    return 1.0 if team_side == "scorer" else -1.0


def _clamped(dx: float, dy: float) -> tuple[float, float]:
    magnitude = math.hypot(dx, dy)
    if magnitude > _MAX_DRIFT_MAGNITUDE:
        scale = _MAX_DRIFT_MAGNITUDE / magnitude
        return dx * scale, dy * scale
    return dx, dy


def _cb_line_drift(team_key: str, avg_cb_y: float, ball_y: float) -> tuple[float, float]:
    """Compactage de la ligne de défenseurs centraux vers le côté ballon --
    UN SEUL drift calculé par équipe (pas par `DC` individuellement),
    appliqué tel quel à chaque `DC` de la ligne (voir `enrich_with_background`)
    : une ligne de défense compacte se déplace comme un bloc, pas chaque
    joueur séparément (sinon la ligne se déforme au lieu de coulisser)."""
    unit = _deterministic_unit(team_key, "cb_line")
    return (0.0, _toward(ball_y, avg_cb_y, _DEFENDER_Y_MAX * unit))


# Plancher 0,5 m (fix "enforce minimum drift", 24/09/2026, voir
# docs/render_diagnostic.md, Problème 2) : un figurant doit toujours être
# perceptible à l'écran, même dans un rôle à faible amplitude (couverture,
# reste haut). La formule ci-dessous (plafond par rôle × fraction
# déterministe) ne garantissait aucun minimum -- un tirage proche de 0
# produisait un joueur visuellement figé (mesuré jusqu'à 7 mm sur 8,5 s,
# voir le diagnostic), alors que la RÉDUCTION d'amplitude pour ces rôles est
# volontaire, pas leur immobilité totale.
# Phase 6, B6-c, décision A3 du propriétaire (10/2026), borne basse relevée à 0,2 m (option 1B, 14/10/2026) : le plancher n'est plus fixe à 0,5 m (22,1 % des dérives valaient alors exactement
# 0,5 m, d'où 20,1 % de paires (joueur, événement) identiques d'un événement à l'autre) ; il est tiré par couple (joueur, événement) dans
# [`_MIN_DRIFT_MAGNITUDE_M`, `_MAX_DRIFT_FLOOR_M`] = [0,2 ; 0,5] m. L'amplitude maximale d'un plancher ne dépasse jamais 0,5 m.
_MIN_DRIFT_MAGNITUDE_M = 0.2  # plus petit plancher possible (0,1 m en A3, remonté à 0,2 m : 22 % de décors presque figés sinon)
_MAX_DRIFT_FLOOR_M = 0.5  # plus grand plancher possible (ancien plancher fixe)


def _floor_drift_magnitude(dx: float, dy: float, player_id: PlayerId, event_ref: str = "") -> tuple[float, float]:
    """Applique le plancher (tiré dans [`_MIN_DRIFT_MAGNITUDE_M`,
    `_MAX_DRIFT_FLOOR_M`] par `player_id|event_ref|drift_floor_mag`) à un
    drift déjà calculé -- mise à l'échelle UNIFORME (préserve le signe/la direction de chaque
    composante, donc toute contrainte tactique déjà encodée dans `dx`/`dy`
    par l'appelant reste respectée), jamais un plafond touché (`_clamped`,
    `_MAX_DRIFT_MAGNITUDE=0.05` normalisé, très au-dessus de 0,5 m dans tous
    les cas, voir plus haut) : ce plancher ne peut donc jamais entrer en
    conflit avec un plafond existant. Cas dégénéré (`dx == dy == 0.0`, ex.
    `_toward` quand la cible == le départ) : aucune direction à l'échelle,
    le plancher s'applique alors UNIQUEMENT en latéral (jamais en
    profondeur, pour ne jamais introduire une avancée non voulue), signe
    déterministe par joueur."""
    floor_m = _MIN_DRIFT_MAGNITUDE_M + (_MAX_DRIFT_FLOOR_M - _MIN_DRIFT_MAGNITUDE_M) * _event_unit(player_id, event_ref, "drift_floor_mag")
    magnitude_m = math.hypot(dx * PITCH_LENGTH_M, dy * PITCH_WIDTH_M)
    if magnitude_m >= floor_m:
        return dx, dy
    if magnitude_m < 1e-12:
        sign = 1.0 if _event_unit(player_id, event_ref, "drift_floor_side") < 0.5 else -1.0
        return 0.0, sign * floor_m / PITCH_WIDTH_M
    scale = floor_m / magnitude_m
    return dx * scale, dy * scale


def _tactical_drift(
    poste: str,
    player_id: PlayerId,
    team_side: str,
    start: tuple[float, float],
    ball_target: tuple[float, float],
    cb_line_drift: tuple[float, float],
    event_ref: str = "",
) -> tuple[float, float]:
    """`_tactical_drift_unfloored` (règles tactiques par rôle) + plancher
    `_MIN_DRIFT_MAGNITUDE_M` (voir sa docstring) -- point d'entrée public
    inchangé, tous les appelants existants (`enrich_with_background`, tests)
    passent par ici."""
    dx, dy = _tactical_drift_unfloored(poste, player_id, team_side, start, ball_target, cb_line_drift, event_ref)
    return _floor_drift_magnitude(dx, dy, player_id, event_ref)


def _tactical_drift_unfloored(
    poste: str,
    player_id: PlayerId,
    team_side: str,
    start: tuple[float, float],
    ball_target: tuple[float, float],
    cb_line_drift: tuple[float, float],
    event_ref: str = "",
) -> tuple[float, float]:
    """Micro-mouvement déterministe d'un joueur "décor", réglé par RÔLE
    TACTIQUE plutôt qu'uniformément "vers le ballon" (voir le bloc de
    commentaires ci-dessus). `ball_target` : position du ballon au dernier
    keyframe de la Sequence -- là où l'action aboutit, pas une cible qui
    suit le ballon en continu (un seul drift calculé une fois, voir
    `BackgroundTrack`). `cb_line_drift` : le drift partagé de toute la ligne
    de défenseurs centraux (voir `_cb_line_drift`), utilisé tel quel pour un
    `DC` -- ignoré pour tout autre poste. Plancher de visibilité appliqué
    par l'appelant public `_tactical_drift`, pas ici (cette fonction ne
    calcule QUE la direction/l'amplitude tactique brute)."""
    start_x, start_y = start
    ball_x, ball_y = ball_target
    same_side = _side_of(start_y) == _side_of(ball_y)
    forward = _forward_sign(team_side)
    x_unit = _event_unit(player_id, event_ref, "drift_x")
    y_unit = _event_unit(player_id, event_ref, "drift_y")

    if poste == GOALKEEPER:
        # Réaction latérale passive (Tâche 2, brief "gardien actif" 1/2) :
        # suit le ballon en y, ne bouge JAMAIS en x (reste à sa position de
        # base, voir `_gk_base_position` -- x=0.0 ici est un delta, pas une
        # position absolue, cohérent avec le reste de `_tactical_drift`).
        max_shift = _GK_LATERAL_MAX_M / PITCH_WIDTH_M
        return (0.0, _toward(ball_y, start_y, max_shift * y_unit))

    if poste == "DC":
        return cb_line_drift

    if poste in ("LB", "RB"):
        if not same_side:
            # Latéral côté opposé : rentre dans l'axe pour couvrir (rest
            # defense), jamais vers le ballon.
            return _clamped(0.0, _toward(0.5, start_y, _DEFENDER_Y_MAX * y_unit))
        dy = _toward(ball_y, start_y, _DEFENDER_Y_MAX * 0.5 * y_unit)
        if team_side == "scorer":
            # Latéral côté ballon, équipe qui attaque : monte.
            x_lo, x_hi = _DEFENDER_X_RANGE
            dx = forward * (x_lo + (x_hi - x_lo) * x_unit)
            return _clamped(dx, dy)
        # Latéral côté ballon, équipe qui défend : reste, couvre sur place.
        return _clamped(0.0, dy)

    if poste in ("MDC", "MC", "MOC"):
        # Rapprochement du porteur (MOC traité comme un milieu central,
        # non distingué dans le brief).
        x_lo, x_hi = _MID_X_RANGE
        dx = _toward(ball_x, start_x, x_lo + (x_hi - x_lo) * x_unit)
        dy = _toward(ball_y, start_y, _MID_Y_MAX * y_unit)
        return _clamped(dx, dy)

    if poste in ("AG", "AD"):
        if same_side:
            # Ailier côté ballon : soutien proche du porteur, dans le couloir.
            x_lo, x_hi = _WINGER_SUPPORT_X_RANGE
            dx = _toward(ball_x, start_x, x_lo + (x_hi - x_lo) * x_unit)
            dy = _toward(ball_y, start_y, _WINGER_SUPPORT_Y_MAX * y_unit)
            return _clamped(dx, dy)
        # Ailier côté opposé : tient la largeur OU appel en profondeur --
        # choix déterministe seedé par joueur, jamais un mélange des deux.
        if _event_unit(player_id, event_ref, "winger_choice") < 0.5:
            hold_unit = _event_unit(player_id, event_ref, "hold_width")
            dy = math.copysign(_WINGER_HOLD_MAGNITUDE * hold_unit, start_y - 0.5) if start_y != 0.5 else 0.0
            return (0.0, dy)
        x_lo, x_hi = _FORWARD_RUN_X_RANGE
        return (forward * (x_lo + (x_hi - x_lo) * x_unit), 0.0)

    # BU / SA / ATT : reste haut OU fait un appel -- jamais ne redescend
    # vers le ballon (même choix seedé que l'ailier côté opposé, cible
    # différente).
    if _event_unit(player_id, event_ref, "striker_choice") < 0.5:
        hold_unit = _event_unit(player_id, event_ref, "hold_high")
        return (forward * _STRIKER_HOLD_MAGNITUDE * hold_unit, 0.0)
    x_lo, x_hi = _FORWARD_RUN_X_RANGE
    return (forward * (x_lo + (x_hi - x_lo) * x_unit), 0.0)


def _opponent_positions(opponent_lineup: Lineup, en_jeu: dict[str, PitchPoint | None] | None = None) -> dict[PlayerId, PitchPoint]:
    """Place les 11 adverses sur LEUR PROPRE référentiel (`pitch_layout`,
    peu importe le `attacking_up` choisi ici -- voir plus bas) puis les
    reflète dans le référentiel PARTAGÉ de la Sequence, où x=1 est déjà le
    but adverse du point de vue de l'équipe qui marque (voir
    `spatial.placed_player_to_normalized`) -- même principe que
    `scripts/preview_motion.py._away_static_points`. Le choix de
    `attacking_up=True` pour LEUR PROPRE placement est arbitraire : seul le
    reflet en x compte pour les recaler dans le référentiel partagé, la
    latéralité (y) n'est jamais affectée par `attacking_up`.

    `en_jeu` (étape 0b-2 du Bloc A) : `{nom: point}` des joueurs SUR LE TERRAIN à la minute de l'événement ; `None` (défaut) : comportement historique, les
    11 titulaires. Le point est `None` pour un titulaire (il garde sa position de formation, calculée sur les 11 titulaires COMPLETS : aucune ligne n'est
    recalée quand un joueur sort) et la position propre d'un remplaçant dans le repère de son équipe (comme `_substitute_start_position`, dont le point est
    reflété ici comme celui d'un titulaire). Un titulaire absent de `en_jeu` n'est pas placé ; un remplaçant absent de `en_jeu` ou à point `None` non plus.
    Par défaut l'attribut `en_jeu` d'un `Lineup` enrichi (voir `engine/narrative_player.py`) est lu ; un paramètre explicite le remplace."""
    if en_jeu is None:
        en_jeu = getattr(opponent_lineup, "en_jeu", None)
    stats = [
        PlayerMatchStat(
            player_name=p.name, club_name=opponent_lineup.club_name, poste=p.poste, started=True,
            band=opponent_lineup.bands.get(p.name),
        )
        for p in opponent_lineup.players
    ]
    placed = place_starting_xi(stats, attacking_up=True)
    players_by_name = {p.name: p for p in opponent_lineup.players}
    positions: dict[PlayerId, PitchPoint] = {}
    for pl in placed:
        player = players_by_name.get(pl.stat.player_name)
        if player is None:
            continue  # même repli que _start_positions : compo désynchronisée, ignoré
        if en_jeu is not None and player.name not in en_jeu:
            continue  # titulaire absent du terrain (remplacé ou expulsé) : sa place n'est PAS recalée pour les autres
        own_frame = placed_player_to_normalized(pl, attacking_up=True)
        positions[player_id_of(player)] = PitchPoint(x=1.0 - own_frame.x, y=own_frame.y)
    if en_jeu is not None:
        for substitute in opponent_lineup.substitutes:
            point = en_jeu.get(substitute.name)
            if point is not None:
                positions[player_id_of(substitute)] = PitchPoint(x=1.0 - point.x, y=point.y)
    return positions


# Phase 6, B7-b (14/10/2026) -- mur d'un coup franc direct : constantes produit validées par le propriétaire. L'écartement dépasse de
# 1 µm le seuil de `motion._AVOIDANCE_TRIGGER_M` (1,5 m) : `_apply_avoidance` ne pousse que sous ce seuil (`dist < 1,5`), donc le mur reste
# aligné sans toucher `motion.py` (à 1,5 m pile, une erreur d'arrondi pourrait déclencher une poussée de l'ordre de 1e-10 m).
_WALL_DISTANCE_M = 9.15  # du ballon, sur la ligne ballon -> centre du but
_WALL_SPACING_M = 1.5 + 1e-6
_WALL_SIZE_BY_MAX_DISTANCE_M = ((20.0, 5), (26.0, 4))  # distance ballon-but <= 20 m : 5 joueurs ; <= 26 m : 4 ; au-delà : 3
_WALL_SIZE_DEFAULT = 3


def _free_kick_wall(sequence: Sequence, opponent_positions: dict[PlayerId, PitchPoint], opponent_by_id: dict) -> tuple[dict[PlayerId, tuple[float, float]], tuple[float, float]]:
    """Mur d'un coup franc (B7-b) : `({joueur: emplacement}, dérive partagée)`, en coordonnées normalisées. n adversaires de champ (jamais
    le gardien) -- les n plus proches du milieu du mur, `_WALL_SIZE_BY_MAX_DISTANCE_M` -- sont alignés perpendiculairement à la ligne
    ballon -> centre du but, centrés sur elle, à `_WALL_DISTANCE_M` du ballon. L'ordre le long du mur suit leur position actuelle
    (aucun croisement). Dérive PARTAGÉE (même principe que `_cb_line_drift` : un bloc glisse d'un seul tenant, l'écartement ne bouge
    pas) : latérale, d'amplitude tirée dans [`_MIN_DRIFT_MAGNITUDE_M`, `_MAX_DRIFT_FLOOR_M`], donc le plancher de chaque joueur est respecté."""
    ball = sequence.keyframes[0].ball  # ballon posé (B7-a) : même point sur tous les keyframes avant la frappe
    ball_x_m, ball_y_m = ball.x * PITCH_LENGTH_M, ball.y * PITCH_WIDTH_M
    to_goal_x, to_goal_y = PITCH_LENGTH_M - ball_x_m, PITCH_WIDTH_M / 2.0 - ball_y_m
    distance_m = math.hypot(to_goal_x, to_goal_y)
    ux, uy = to_goal_x / distance_m, to_goal_y / distance_m
    px, py = -uy, ux  # perpendiculaire au tir
    size = next((n for limit_m, n in _WALL_SIZE_BY_MAX_DISTANCE_M if distance_m <= limit_m), _WALL_SIZE_DEFAULT)
    center_x_m, center_y_m = ball_x_m + _WALL_DISTANCE_M * ux, ball_y_m + _WALL_DISTANCE_M * uy

    def _metres(point: PitchPoint) -> tuple[float, float]:
        return point.x * PITCH_LENGTH_M, point.y * PITCH_WIDTH_M

    field = sorted((pid for pid in opponent_positions if opponent_by_id[pid].poste != GOALKEEPER), key=str)  # ordre stable (déterminisme)
    members = sorted(field, key=lambda pid: math.hypot(_metres(opponent_positions[pid])[0] - center_x_m, _metres(opponent_positions[pid])[1] - center_y_m))[:size]
    members.sort(key=lambda pid: (_metres(opponent_positions[pid])[0] - center_x_m) * px + (_metres(opponent_positions[pid])[1] - center_y_m) * py)
    starts = {
        pid: (
            (center_x_m + (k - (size - 1) / 2.0) * _WALL_SPACING_M * px) / PITCH_LENGTH_M,
            (center_y_m + (k - (size - 1) / 2.0) * _WALL_SPACING_M * py) / PITCH_WIDTH_M,
        )
        for k, pid in enumerate(members)
    }
    event_ref = sequence.event_ref
    magnitude_m = _MIN_DRIFT_MAGNITUDE_M + (_MAX_DRIFT_FLOOR_M - _MIN_DRIFT_MAGNITUDE_M) * _event_unit("wall", event_ref, "wall_drift_mag")
    sign = 1.0 if _event_unit("wall", event_ref, "wall_drift_side") < 0.5 else -1.0
    return starts, (sign * magnitude_m * px / PITCH_LENGTH_M, sign * magnitude_m * py / PITCH_WIDTH_M)


# --- Chantier "mouvement collectif", Phase 1 (16/10/2026) : dispersion des lignes de départ ------------------------------
# PRD/PLAN validés par le propriétaire (docs/PRD.md, docs/PLAN.md) : les joueurs de décor sont alignés en rangées parfaites
# à leur position de départ (`place_starting_xi`, `src/ligue1sim/pitch_layout.py` -- fichier NON touché, exception demandée
# et accordée pour CE fichier (`sequence_generator.py`) seulement). Écart latéral déterministe appliqué APRÈS la position de
# formation mais AVANT `_tactical_drift`, pour que la direction du drift (`_toward`) se recalcule depuis le nouveau départ et
# reste cohérente. Sel dédié ("start_dispersion", jamais partagé avec `_tactical_drift`) : un même sel aurait corrélé
# artificiellement l'écart de départ et la direction du drift pendant l'action, faussant à la fois le réalisme et la mesure
# de dispersion. Jamais en profondeur (toujours `(0.0, dy)`) : préserve l'ordre des lignes tactiques et l'amplitude déjà
# calibrée de `_tactical_drift`/`_cb_line_drift`, qui n'ont pas besoin d'être retouchés. Exclu : le gardien (position déjà
# recalculée par `_gk_base_position`, hors sujet "ligne") et les membres du mur de coup franc (`wall_starts`, alignement
# tactique volontaire) -- appliqué uniquement dans la branche "cas général" de chaque appelant.
_START_DISPERSION_MAX_M = 1.0  # amplitude latérale max, proposée en conception, validée par le propriétaire (16/10/2026)


def _start_dispersion(player_id: PlayerId, event_ref: str) -> tuple[float, float]:
    """Écart latéral déterministe (chantier mouvement collectif, Phase 1) : tirage SIGNÉ (centré sur 0, pas uniquement d'un
    côté) dans `[-_START_DISPERSION_MAX_M, _START_DISPERSION_MAX_M]`, sha256 de `player_id|event_ref|"start_dispersion"`
    (`_event_unit`). `(0.0, dy)` normalisé : à additionner à la position de départ issue de la formation, jamais à sa cible."""
    unit = _event_unit(player_id, event_ref, "start_dispersion")
    dy_m = (unit * 2.0 - 1.0) * _START_DISPERSION_MAX_M
    return (0.0, dy_m / PITCH_WIDTH_M)


# --- Chantier "mouvement collectif", Phase 2 (16/10/2026) : trajectoire à plusieurs points -------------------------------
# PRD/PLAN validés par le propriétaire : le drift d'un joueur de décor était une ligne droite (`start` -> `start + drift`,
# un seul segment). Exception accordée (16/10/2026) pour `types.py` (nouveau champ optionnel `BackgroundTrack.points`,
# rétrocompatible) et `motion.py` (`_background_position_at` découpe la trajectoire en plusieurs segments égaux quand
# `points` est renseigné, voir sa docstring) -- ici, dans `sequence_generator.py` (déjà autorisé), on calcule SEULEMENT
# les points eux-mêmes. `_DRIFT_WAYPOINT_COUNT = 2` : validé par le propriétaire (16/10/2026). Chaque point est décalé
# PERPENDICULAIREMENT au segment direct start->end (jamais le long, qui changerait juste la vitesse de parcours, pas le
# tracé) -- sel dédié par point ("drift_waypoint|k", jamais partagé avec `_start_dispersion`/`_tactical_drift`).
_DRIFT_WAYPOINT_COUNT = 2  # points intermédiaires, validé par le propriétaire (16/10/2026)
_DRIFT_WAYPOINT_JITTER_MAX_M = 0.5  # écart perpendiculaire max au tracé direct, proposé en conception (16/10/2026)


def _drift_waypoints(player_id: PlayerId, event_ref: str, start: tuple[float, float], drift: tuple[float, float]) -> tuple[tuple[float, float], ...] | None:
    """Points intermédiaires du trajet `start -> start + drift` d'un joueur de décor (chantier mouvement collectif,
    Phase 2) : `_DRIFT_WAYPOINT_COUNT` points espacés également sur le tracé direct, chacun décalé perpendiculairement
    d'un écart signé déterministe dans `[-_DRIFT_WAYPOINT_JITTER_MAX_M, _DRIFT_WAYPOINT_JITTER_MAX_M]`. `None` si le
    joueur ne bouge pas (`drift` nul) : aucune direction à partir de laquelle calculer une perpendiculaire."""
    end = (start[0] + drift[0], start[1] + drift[1])
    length_m = math.hypot((end[0] - start[0]) * PITCH_LENGTH_M, (end[1] - start[1]) * PITCH_WIDTH_M)
    if length_m <= 1e-9:
        return None
    ux_m, uy_m = (end[0] - start[0]) * PITCH_LENGTH_M / length_m, (end[1] - start[1]) * PITCH_WIDTH_M / length_m
    perp_x_m, perp_y_m = -uy_m, ux_m
    points = []
    for k in range(1, _DRIFT_WAYPOINT_COUNT + 1):
        progress_k = k / (_DRIFT_WAYPOINT_COUNT + 1)
        base_x, base_y = start[0] + drift[0] * progress_k, start[1] + drift[1] * progress_k
        offset_m = (_event_unit(player_id, f"{event_ref}|{k}", "drift_waypoint") * 2.0 - 1.0) * _DRIFT_WAYPOINT_JITTER_MAX_M
        points.append((base_x + perp_x_m * offset_m / PITCH_LENGTH_M, base_y + perp_y_m * offset_m / PITCH_WIDTH_M))
    return tuple(points)


# --- Chantier "mouvement collectif", Phase 3 (16/10/2026) : initiatives de soutien par poste --------------------------
# PRD/PLAN validés par le propriétaire (docs/PRD.md, docs/PLAN.md, section Phase 3) : un joueur de décor éligible peut,
# selon son poste ET son camp dans CETTE séquence, REMPLACER son `_tactical_drift` habituel par une initiative de
# soutien identifiable -- jamais additif, jamais pour un gardien, un membre du mur de coup franc, ou un remplaçant
# en_jeu (position réelle suivie, pas une ligne de formation de référence, même raison que Phase 1).
#
# Camp = direction, JAMAIS l'inverse (voir `tests.test_sequence_generator.TestTacticalDrift.
# test_opponent_fullbacks_never_push_forward_end_to_end`, invariant déjà testé avant ce chantier : le modèle ne capture
# qu'UNE SEULE phase de jeu par clip, `team_side="scorer"` toujours en attaque, `"opponent"` toujours en défense sur
# CETTE séquence précise) :
#   - LB/RB (dédoublement offensif) : UNIQUEMENT côté `scorer` -- un latéral adverse ne monte jamais pendant que son
#     équipe encaisse, quel que soit son profil.
#   - BU/SA/ATT (repli défensif) : UNIQUEMENT côté `opponent` -- un attaquant de l'équipe qui marque ne redescend pas
#     défendre pendant sa propre action.
#   - MC/MDC (décision du propriétaire 16/10/2026, anticipe Phase 4) : les DEUX camps, direction forcée par le camp
#     comme les deux groupes ci-dessus (+1 côté scorer, -1 côté opponent) -- jamais par l'attribut. MOC volontairement
#     exclu (décision du propriétaire) : déjà regroupé avec MDC/MC dans `_tactical_drift_unfloored` mais jugé trop
#     proche du jeu pour une initiative distincte.
#
# L'attribut du joueur module la FRÉQUENCE (probabilité de tirage), jamais le sens : Work Rate côté `scorer` (rejoindre
# l'attaque, profil "box-to-box"), Positioning côté `opponent` (repli défensif, profil défensif) -- voir
# `_support_initiative_probability`.
#
# Secteur tactiquement crédible = rectangle couloir (± `_SUPPORT_LANE_M[poste]`, latéral) x profondeur (jusqu'à
# `_SUPPORT_INITIATIVE_MAX_M`, signée par le camp), réduit par le plafond d'amplitude global (cercle
# `_SUPPORT_INITIATIVE_MAX_M`, mise à l'échelle uniforme si dépassé -- même principe que `_floor_drift_magnitude`) :
# un couloir plus étroit que le plafond (LB/RB, MC/MDC) est donc un VRAI filtre, pas un rayon redondant avec
# l'amplitude max (un rayon simple centré au même point ne rejette jamais rien qu'elle ne rejette déjà). Vérifié sur
# CHAQUE image du clip par construction : `_drift_waypoints`/`motion._background_position_at` interpolent une
# trajectoire monotone par segments entre `start` et `start + drift`, jamais un rebond hors de ce segment.
_SUPPORT_INITIATIVE_PROBABILITY = 0.40  # tirage par joueur éligible et par clip (LB/RB, BU/SA/ATT, MC/MDC sans attribut connu), sel dédié, validé (16/10/2026)
_SUPPORT_MIDFIELD_PROBABILITY_RANGE = (0.20, 0.60)  # MC/MDC avec l'attribut pertinent connu : probabilité linéaire sur l'échelle FM 1-20, validé (16/10/2026)
_SUPPORT_INITIATIVE_MAX_M = 12.0  # amplitude max d'une initiative (vs _MAX_DRIFT_MAGNITUDE ~5 % du terrain pour le petit drift existant), validé (16/10/2026)
_SUPPORT_LANE_M = {  # demi-largeur de couloir latéral max par poste, validé (16/10/2026)
    "LB": 6.0, "RB": 6.0,
    "MC": 8.0, "MDC": 8.0,
    "BU": 10.0, "SA": 10.0, "ATT": 10.0,
}
_SUPPORT_OVERLAP_POSTES = frozenset({"LB", "RB"})  # dédoublement offensif, côté scorer uniquement (PRD, pas de choix)
_SUPPORT_COVER_POSTES = frozenset({"BU", "SA", "ATT"})  # repli défensif, côté opponent uniquement (PRD, pas de choix)
_SUPPORT_MIDFIELD_POSTES = frozenset({"MC", "MDC"})  # les deux camps, direction forcée par le camp


def _support_initiative_eligible(poste: str, team_side: str) -> bool:
    """Un seul mécanisme actif par (poste, camp) à la fois -- voir le bloc de commentaires ci-dessus pour pourquoi
    LB/RB et BU/SA/ATT sont restreints à un seul camp chacun."""
    if poste in _SUPPORT_OVERLAP_POSTES:
        return team_side == "scorer"
    if poste in _SUPPORT_COVER_POSTES:
        return team_side == "opponent"
    return poste in _SUPPORT_MIDFIELD_POSTES


def _support_initiative_probability(poste: str, team_side: str, player: Player | None) -> float:
    """Probabilité de tirage (`_support_initiative_selected`). LB/RB, BU/SA/ATT : `_SUPPORT_INITIATIVE_PROBABILITY`
    fixe. MC/MDC : modulée par l'attribut pertinent pour CE camp (Work Rate côté `scorer`, Positioning côté
    `opponent`), linéaire sur `_SUPPORT_MIDFIELD_PROBABILITY_RANGE` pour l'échelle FM 1-20. Attribut manquant
    (`player.attributes` `None`/incomplet, ~93 % des joueurs au 26/09/2026, voir `players.FM_ATTRIBUTE_CATEGORIES`) :
    comportement par défaut cohérent (exigence Phase 4 du PLAN), retombe sur `_SUPPORT_INITIATIVE_PROBABILITY`."""
    if poste not in _SUPPORT_MIDFIELD_POSTES:
        return _SUPPORT_INITIATIVE_PROBABILITY
    attributes = player.attributes if player is not None else None
    attribute_name = "Work Rate" if team_side == "scorer" else "Positioning"
    value = attributes.get(attribute_name) if attributes else None
    if value is None:
        return _SUPPORT_INITIATIVE_PROBABILITY
    lo, hi = _SUPPORT_MIDFIELD_PROBABILITY_RANGE
    unit = max(0.0, min(1.0, (value - 1) / 19.0))
    return lo + unit * (hi - lo)


def _support_initiative_selected(player_id: PlayerId, event_ref: str, probability: float) -> bool:
    """Tirage déterministe (sel dédié `"support_initiative_select"`, jamais partagé) : True si CE joueur initie un
    mouvement de soutien sur CE clip, à `probability` (voir `_support_initiative_probability`)."""
    return _event_unit(player_id, event_ref, "support_initiative_select") < probability


def _support_initiative_direction(poste: str, team_side: str) -> float:
    """+1.0 = vers l'avant (rejoint l'attaque / dédoublement), -1.0 = vers l'arrière (repli défensif) -- TOUJOURS
    déterminé par le camp (voir le bloc de commentaires ci-dessus), jamais par l'attribut.

    Piste de lecture pour MC/MDC : cette fonction renvoie exactement `_forward_sign(team_side)` pour ce groupe (+1
    côté scorer, -1 côté opponent). `_support_initiative` multiplie ensuite ce résultat PAR `_forward_sign(team_side)`
    une seconde fois -- le signe final est donc TOUJOURS +1 pour MC/MDC, quel que soit le camp. Ce n'est pas un bug :
    dans le référentiel partagé de la `Sequence`, le but que rejoint un scorer ET le but propre vers lequel un
    opponent se replie sont tous les deux à x=1 (voir `_gk_base_position`), donc la même direction absolue est
    attendue dans les deux cas."""
    if poste in _SUPPORT_OVERLAP_POSTES:
        return 1.0
    if poste in _SUPPORT_COVER_POSTES:
        return -1.0
    return 1.0 if team_side == "scorer" else -1.0


def _support_initiative(poste: str, player_id: PlayerId, team_side: str, event_ref: str) -> tuple[float, float]:
    """Initiative de soutien (chantier mouvement collectif, Phase 3) -- REMPLACE `_tactical_drift` pour le joueur
    tiré (`_support_initiative_selected`), jamais additif. Profondeur tirée dans `[0, _SUPPORT_INITIATIVE_MAX_M]`
    (sel `"support_depth"`), signée par `_support_initiative_direction` puis par `_forward_sign(team_side)` (même
    convention que `_tactical_drift_unfloored`). Latéral tiré, signé et centré, dans `[-_SUPPORT_LANE_M[poste],
    _SUPPORT_LANE_M[poste]]` (sel `"support_lateral"`, même tirage centré que `_start_dispersion`). Mis à l'échelle
    uniforme si le total dépasse `_SUPPORT_INITIATIVE_MAX_M` (préserve la direction, jamais un plafond en conflit
    avec le couloir -- même principe que `_floor_drift_magnitude`)."""
    direction = _support_initiative_direction(poste, team_side)
    forward = _forward_sign(team_side)
    depth_m = _event_unit(player_id, event_ref, "support_depth") * _SUPPORT_INITIATIVE_MAX_M
    lateral_m = (_event_unit(player_id, event_ref, "support_lateral") * 2.0 - 1.0) * _SUPPORT_LANE_M[poste]
    total_m = math.hypot(depth_m, lateral_m)
    if total_m > _SUPPORT_INITIATIVE_MAX_M:
        scale = _SUPPORT_INITIATIVE_MAX_M / total_m
        depth_m, lateral_m = depth_m * scale, lateral_m * scale
    return (forward * direction * depth_m / PITCH_LENGTH_M, lateral_m / PITCH_WIDTH_M)


def _drift_or_support_initiative(
    poste: str,
    player_id: PlayerId,
    team_side: str,
    start: tuple[float, float],
    ball_target: tuple[float, float],
    cb_line_drift: tuple[float, float],
    event_ref: str,
    player: Player | None,
    eligible: bool,
) -> tuple[float, float]:
    """`_tactical_drift`, SAUF si `eligible` (poste/camp/hors remplaçant -- voir appelants) ET le tirage
    `_support_initiative_selected` retombe dessus : alors `_support_initiative` REMPLACE `_tactical_drift` pour ce
    joueur sur ce clip, jamais additif. Point d'entrée commun aux 3 sites de construction de `BackgroundTrack`
    (`enrich_with_background` x2, `opponent_field_tracks`), pour garantir leur parité par construction."""
    if eligible and _support_initiative_selected(player_id, event_ref, _support_initiative_probability(poste, team_side, player)):
        return _support_initiative(poste, player_id, team_side, event_ref)
    return _tactical_drift(poste, player_id, team_side, start, ball_target, cb_line_drift, event_ref)


def enrich_with_background(
    sequence: Sequence,
    opponent_lineup: Lineup,
    outcome: str | None = None,
    en_jeu: dict[str, PitchPoint | None] | None = None,
    scorer_lineup: Lineup | None = None,
) -> Sequence:
    """Complète une `Sequence` déjà produite (par `generate_sequence`, ou
    directement un gabarit) avec les joueurs "décor" : le reste de l'équipe
    qui marque (`sequence.roster` sans rôle de gabarit) et les 11 adverses
    au complet, gardien compris (voir le bloc de commentaires ci-dessus pour
    le contexte). `opponent_lineup` : la compo de l'équipe qui encaisse --
    jamais connue de `generate_sequence`, qui ne suit que l'équipe qui
    marque ; c'est à l'appelant (le futur `build_animation`, phase 4) de la
    fournir séparément.

    Étapes : (1) identifie les joueurs actifs (`roster[id].role is not
    None`) -- tout le reste de l'équipe qui marque devient "décor" ; (2) les
    retire des `Keyframe.players` (un joueur ne peut pas être suivi par les
    deux systèmes à la fois, voir invariant 3 de `Sequence`) ; (3) place les
    11 adverses (`_opponent_positions`) ; (4) calcule la ligne de défenseurs
    centraux (`_cb_line_drift`) et un `BackgroundTrack` par joueur décor
    (`_tactical_drift`, réglé par rôle tactique -- voir Point 2 du brief du
    23/09/2026) POUR CHAQUE ÉQUIPE séparément -- pour le gardien de chaque
    équipe, le `start` de formation est remplacé par `_gk_base_position`
    (brief "gardien actif" 1/2, 24/09/2026) ; (5) étend `roster` avec les
    11 adverses (numéro dérivé via `templates.numeros_by_player_id`,
    `team_side="opponent"`).

    `outcome` (B6-d) : issue de l'occasion (`NarrativeEvent.outcome`), lue SEULEMENT pour le gardien adverse d'un penalty
    (`_penalty_gk_drift`). `None` (défaut, tous les appelants hors `narrative_player`) : amplitude seule. Aucun effet hors penalty.

    `en_jeu` (étape 0b-2) : joueurs adverses sur le terrain, voir `_opponent_positions`. `None` et sans attribut `en_jeu` sur `opponent_lineup` : comportement
    historique, bit à bit.

    `scorer_lineup` (chantier mouvement collectif, Phase 3) : `Lineup` de l'équipe qui marque, pour résoudre le `Player` (donc ses
    `attributes`) d'un MC/MDC tiré pour une initiative de soutien -- voir `_support_initiative_probability`. `None` (défaut, tout
    appelant qui ne fournit pas cette exception) : les MC/MDC côté scorer retombent sur la probabilité par défaut fixe
    (`_SUPPORT_INITIATIVE_PROBABILITY`, 40 %, comme LB/RB et BU/SA/ATT), jamais une erreur -- seul `engine/narrative_player.py` la
    fournit en production."""
    if en_jeu is None:
        en_jeu = getattr(opponent_lineup, "en_jeu", None)
    active_ids = {player_id for player_id, entry in sequence.roster.items() if entry.role is not None}
    inactive_scorer_ids = set(sequence.roster) - active_ids
    ball_target = (sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y)

    stripped_keyframes = [
        replace(kf, players={pid: pos for pid, pos in kf.players.items() if pid in active_ids})
        for kf in sequence.keyframes
    ]

    background: dict[PlayerId, BackgroundTrack] = {}

    scorer_starts = {player_id: sequence.keyframes[0].players[player_id] for player_id in inactive_scorer_ids}
    scorer_cb_ys = [pos[1] for pid, pos in scorer_starts.items() if sequence.roster[pid].poste == "DC"]
    scorer_cb_drift = _cb_line_drift(
        f"{sequence.event_ref}|scorer", sum(scorer_cb_ys) / len(scorer_cb_ys), ball_target[1]
    ) if scorer_cb_ys else (0.0, 0.0)
    scorer_players_by_name = {p.name: p for p in scorer_lineup.players} if scorer_lineup is not None else {}
    for player_id, start in scorer_starts.items():
        entry = sequence.roster[player_id]
        if entry.poste == GOALKEEPER:
            start = _gk_base_position("scorer")
        else:
            dx, dy = _start_dispersion(player_id, sequence.event_ref)
            start = (start[0] + dx, start[1] + dy)
        drift = _drift_or_support_initiative(
            entry.poste, player_id, "scorer", start, ball_target, scorer_cb_drift, sequence.event_ref,
            scorer_players_by_name.get(entry.nom), _support_initiative_eligible(entry.poste, "scorer"),
        )
        points = _drift_waypoints(player_id, sequence.event_ref, start, drift)
        background[player_id] = BackgroundTrack(start=start, drift=drift, points=points)

    opponent_positions = _opponent_positions(opponent_lineup, en_jeu)
    opponent_by_id = {player_id_of(p): p for p in (list(opponent_lineup.players) + (list(opponent_lineup.substitutes) if en_jeu is not None else []))}
    opponent_numeros = numeros_by_player_id(opponent_lineup)
    opponent_cb_ys = [point.y for pid, point in opponent_positions.items() if opponent_by_id[pid].poste == "DC"]
    opponent_cb_drift = _cb_line_drift(
        f"{sequence.event_ref}|opponent", sum(opponent_cb_ys) / len(opponent_cb_ys), ball_target[1]
    ) if opponent_cb_ys else (0.0, 0.0)

    wall_starts, wall_drift = _free_kick_wall(sequence, opponent_positions, opponent_by_id) if sequence.meta.get("template") == "coup_franc" else ({}, (0.0, 0.0))
    # En_jeu (étape 0b-2) : la position d'un remplaçant entré en jeu est une position RÉELLE suivie, pas une ligne de
    # formation théorique -- hors sujet "dispersion des lignes" (docs/PLAN.md, Phase 1), jamais dispersée.
    substitute_ids = {player_id_of(p) for p in opponent_lineup.substitutes}

    opponent_roster: dict[PlayerId, RosterEntry] = {}
    for player_id, point in opponent_positions.items():
        player = opponent_by_id[player_id]
        start = _gk_base_position("opponent") if player.poste == GOALKEEPER else (point.x, point.y)
        if player.poste == GOALKEEPER and sequence.meta.get("template") == "coup_franc":
            start = _free_kick_gk_start(player_id, sequence.event_ref, sequence.keyframes[0].ball.y)  # B7-d : départ moins avancé, côté ballon
        points = None
        if player_id in wall_starts:
            start, drift = wall_starts[player_id], wall_drift  # B7-b : mur d'un coup franc, dérive partagée -- tracé direct
            # conservé à dessein (Phase 2 ne s'applique pas ici) : un mur avance en bloc, pas joueur par joueur.
        elif player.poste == GOALKEEPER and sequence.meta.get("template") == "penalty":
            drift = _penalty_gk_drift(player_id, sequence.event_ref, ball_target[1], outcome)
        elif player.poste == GOALKEEPER and sequence.meta.get("template") == "coup_franc":
            drift = _free_kick_gk_drift(player_id, sequence.event_ref, start[1], ball_target[1], outcome)  # B7-d
        else:
            if player.poste != GOALKEEPER and player_id not in substitute_ids:
                dx, dy = _start_dispersion(player_id, sequence.event_ref)
                start = (start[0] + dx, start[1] + dy)
            eligible = _support_initiative_eligible(player.poste, "opponent") and player_id not in substitute_ids
            drift = _drift_or_support_initiative(
                player.poste, player_id, "opponent", start, ball_target, opponent_cb_drift, sequence.event_ref, player, eligible,
            )
            points = _drift_waypoints(player_id, sequence.event_ref, start, drift)
        background[player_id] = BackgroundTrack(start=start, drift=drift, points=points)
        opponent_roster[player_id] = RosterEntry(
            nom=player.name,
            poste=player.poste,
            role=None,
            numero=opponent_numeros[player_id],
            team_side="opponent",
        )

    return replace(
        sequence,
        keyframes=stripped_keyframes,
        roster={**sequence.roster, **opponent_roster},
        background=background,
    )


# --- Phase 6, B8-b (14/10/2026) : adversaires de champ à un instant donné, pour la pression sur un contrôle ---------------------
# Les gabarits (`templates.py`) ne connaissent que l'équipe qui marque ; la pression d'un adversaire sur une réception demande ses positions
# AVANT que `enrich_with_background` ne les place. Ces deux fonctions recalculent, avec le même code (`_opponent_positions`, `_cb_line_drift`,
# `_tactical_drift`), les pistes des adversaires de champ ; `tests/test_sequence_generator.py` vérifie qu'elles égalent `Sequence.background`.
# Le gardien est exclu (il ne presse pas), ainsi que les cas particuliers du coup franc (mur) et du penalty, sans réception au sol.


def opponent_field_tracks(
    opponent_lineup: Lineup, event_ref: str, ball_target: tuple[float, float], en_jeu: dict[str, PitchPoint | None] | None = None
) -> dict[PlayerId, BackgroundTrack]:
    """Pistes (`BackgroundTrack`) des adversaires de champ, identiques à celles que `enrich_with_background` leur donne pour la même
    `event_ref` et la même cible du ballon (`ball_target` : position du dernier keyframe de la `Sequence`). `en_jeu` (étape 0b-2) : comme pour
    `enrich_with_background`, seuls les adversaires sur le terrain comptent (pression B8-b)."""
    if en_jeu is None:
        en_jeu = getattr(opponent_lineup, "en_jeu", None)
    positions = _opponent_positions(opponent_lineup, en_jeu)
    by_id = {player_id_of(p): p for p in (list(opponent_lineup.players) + (list(opponent_lineup.substitutes) if en_jeu is not None else []))}
    cb_ys = [point.y for pid, point in positions.items() if by_id[pid].poste == "DC"]
    cb_drift = _cb_line_drift(f"{event_ref}|opponent", sum(cb_ys) / len(cb_ys), ball_target[1]) if cb_ys else (0.0, 0.0)
    substitute_ids = {player_id_of(p) for p in opponent_lineup.substitutes}  # en_jeu : position réelle suivie, jamais dispersée
    tracks: dict[PlayerId, BackgroundTrack] = {}
    for pid, point in positions.items():
        if by_id[pid].poste == GOALKEEPER:
            continue
        if pid in substitute_ids:
            start = (point.x, point.y)
        else:
            dx, dy = _start_dispersion(pid, event_ref)
            start = (point.x + dx, point.y + dy)
        eligible = _support_initiative_eligible(by_id[pid].poste, "opponent") and pid not in substitute_ids
        drift = _drift_or_support_initiative(
            by_id[pid].poste, pid, "opponent", start, ball_target, cb_drift, event_ref, by_id[pid], eligible,
        )
        tracks[pid] = BackgroundTrack(start=start, drift=drift, points=_drift_waypoints(pid, event_ref, start, drift))
    return tracks


def nearest_opponent_distance_m(
    tracks: dict[PlayerId, BackgroundTrack], point: tuple[float, float], t: float, duration: float
) -> float | None:
    """Distance (m) de `point` (position normalisée) à l'adversaire de champ le plus proche à l'instant `t` d'une `Sequence` de durée
    `duration` ; `None` sans adversaire."""
    best: float | None = None
    for track in tracks.values():
        ox, oy = _background_position_at(track, t, duration)
        d = math.hypot((ox - point[0]) * PITCH_LENGTH_M, (oy - point[1]) * PITCH_WIDTH_M)
        if best is None or d < best:
            best = d
    return best
