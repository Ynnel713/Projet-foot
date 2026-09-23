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

from ligue1sim.animation.spatial import PitchLayoutState, placed_player_to_normalized
from ligue1sim.animation.templates import BUILDERS, context_from_event, numeros_by_player_id, pick_template, player_id_of
from ligue1sim.animation.types import BackgroundTrack, PlayerId, RosterEntry, Sequence
from ligue1sim.events import GoalEvent, PlayerMatchStat
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PitchPoint
from ligue1sim.pitch_layout import place_starting_xi


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
_GK_Y_MAX = 0.02  # donné par Olivier
_MAX_DRIFT_MAGNITUDE = 0.05  # ~5% du terrain, borne globale donnée par Olivier -- absorbe l'essentiel du risque d'erreur sur les fourchettes ci-dessus


def _deterministic_unit(key: object, salt: str) -> float:
    """Fraction déterministe dans [0, 1) -- même principe que
    `motion._start_offset` (hash sha256, jamais `hash()` ni `random`) :
    utilisée pour donner à chaque joueur "décor" une amplitude de drift
    stable dans sa fourchette de poste (ou, pour la ligne de défenseurs
    centraux, une amplitude stable partagée par toute la ligne -- `key` peut
    alors être une chaîne descriptive plutôt qu'un `PlayerId`)."""
    digest = hashlib.sha256(f"{salt}|{key}".encode()).digest()
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


def _tactical_drift(
    poste: str,
    player_id: PlayerId,
    team_side: str,
    start: tuple[float, float],
    ball_target: tuple[float, float],
    cb_line_drift: tuple[float, float],
) -> tuple[float, float]:
    """Micro-mouvement déterministe d'un joueur "décor", réglé par RÔLE
    TACTIQUE plutôt qu'uniformément "vers le ballon" (voir le bloc de
    commentaires ci-dessus). `ball_target` : position du ballon au dernier
    keyframe de la Sequence -- là où l'action aboutit, pas une cible qui
    suit le ballon en continu (un seul drift calculé une fois, voir
    `BackgroundTrack`). `cb_line_drift` : le drift partagé de toute la ligne
    de défenseurs centraux (voir `_cb_line_drift`), utilisé tel quel pour un
    `DC` -- ignoré pour tout autre poste."""
    start_x, start_y = start
    ball_x, ball_y = ball_target
    same_side = _side_of(start_y) == _side_of(ball_y)
    forward = _forward_sign(team_side)
    x_unit = _deterministic_unit(player_id, "drift_x")
    y_unit = _deterministic_unit(player_id, "drift_y")

    if poste == "GK":
        # Micro-shift latéral suivant le ballon, reste sur sa ligne (x=0).
        return (0.0, _toward(ball_y, start_y, _GK_Y_MAX * y_unit))

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
        if _deterministic_unit(player_id, "winger_choice") < 0.5:
            hold_unit = _deterministic_unit(player_id, "hold_width")
            dy = math.copysign(_WINGER_HOLD_MAGNITUDE * hold_unit, start_y - 0.5) if start_y != 0.5 else 0.0
            return (0.0, dy)
        x_lo, x_hi = _FORWARD_RUN_X_RANGE
        return (forward * (x_lo + (x_hi - x_lo) * x_unit), 0.0)

    # BU / SA / ATT : reste haut OU fait un appel -- jamais ne redescend
    # vers le ballon (même choix seedé que l'ailier côté opposé, cible
    # différente).
    if _deterministic_unit(player_id, "striker_choice") < 0.5:
        hold_unit = _deterministic_unit(player_id, "hold_high")
        return (forward * _STRIKER_HOLD_MAGNITUDE * hold_unit, 0.0)
    x_lo, x_hi = _FORWARD_RUN_X_RANGE
    return (forward * (x_lo + (x_hi - x_lo) * x_unit), 0.0)


def _opponent_positions(opponent_lineup: Lineup) -> dict[PlayerId, PitchPoint]:
    """Place les 11 adverses sur LEUR PROPRE référentiel (`pitch_layout`,
    peu importe le `attacking_up` choisi ici -- voir plus bas) puis les
    reflète dans le référentiel PARTAGÉ de la Sequence, où x=1 est déjà le
    but adverse du point de vue de l'équipe qui marque (voir
    `spatial.placed_player_to_normalized`) -- même principe que
    `scripts/preview_motion.py._away_static_points`. Le choix de
    `attacking_up=True` pour LEUR PROPRE placement est arbitraire : seul le
    reflet en x compte pour les recaler dans le référentiel partagé, la
    latéralité (y) n'est jamais affectée par `attacking_up`."""
    stats = [
        PlayerMatchStat(player_name=p.name, club_name=opponent_lineup.club_name, poste=p.poste, started=True)
        for p in opponent_lineup.players
    ]
    placed = place_starting_xi(stats, attacking_up=True)
    players_by_name = {p.name: p for p in opponent_lineup.players}
    positions: dict[PlayerId, PitchPoint] = {}
    for pl in placed:
        player = players_by_name.get(pl.stat.player_name)
        if player is None:
            continue  # même repli que _start_positions : compo désynchronisée, ignoré
        own_frame = placed_player_to_normalized(pl, attacking_up=True)
        positions[player_id_of(player)] = PitchPoint(x=1.0 - own_frame.x, y=own_frame.y)
    return positions


def enrich_with_background(sequence: Sequence, opponent_lineup: Lineup) -> Sequence:
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
    23/09/2026) POUR CHAQUE ÉQUIPE séparément ; (5) étend `roster` avec les
    11 adverses (numéro dérivé via `templates.numeros_by_player_id`,
    `team_side="opponent"`)."""
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
    for player_id, start in scorer_starts.items():
        entry = sequence.roster[player_id]
        drift = _tactical_drift(entry.poste, player_id, "scorer", start, ball_target, scorer_cb_drift)
        background[player_id] = BackgroundTrack(start=start, drift=drift)

    opponent_positions = _opponent_positions(opponent_lineup)
    opponent_by_id = {player_id_of(p): p for p in opponent_lineup.players}
    opponent_numeros = numeros_by_player_id(opponent_lineup)
    opponent_cb_ys = [point.y for pid, point in opponent_positions.items() if opponent_by_id[pid].poste == "DC"]
    opponent_cb_drift = _cb_line_drift(
        f"{sequence.event_ref}|opponent", sum(opponent_cb_ys) / len(opponent_cb_ys), ball_target[1]
    ) if opponent_cb_ys else (0.0, 0.0)

    opponent_roster: dict[PlayerId, RosterEntry] = {}
    for player_id, point in opponent_positions.items():
        player = opponent_by_id[player_id]
        start = (point.x, point.y)
        drift = _tactical_drift(player.poste, player_id, "opponent", start, ball_target, opponent_cb_drift)
        background[player_id] = BackgroundTrack(start=start, drift=drift)
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
