"""Moteur narratif : construit une `Timeline` d'occasions déterministe à
partir d'un match déjà décidé par le moteur de résultats
(`ligue1sim.simulation`) -- brief "narrative engine foundations"
(23/09/2026), PREMIER d'une série (variation paramétrique des gabarits,
branchement canvas, extension à 25-30 gabarits, calibrage sur données
réelles : tout ça est hors scope ici).

Consommateur PUR du moteur de résultats (`ligue1sim.schedule`/`events`/
`lineup`) et de `animation.templates` (`TEMPLATES`/`pick_template`) : ne
modifie ni l'un ni l'autre. Le score final et les buts existants sont un
INVARIANT ABSOLU -- ce module ne fait qu'habiller un résultat déjà tranché
d'occasions intercalées, jamais le recalculer.

PRIORITÉ DES CONTRAINTES (brief "constraint priority", 23/09/2026, Tâche 1) :
  1. Score final inchangé.
  2. Buts existants à leur minute exacte, buteur exact, gabarit réel (penalty reste penalty).
  3. Anti-répétition (gabarit+déclinaison, joueur principal) et écart minimum : UNIQUEMENT sur les `generated_events`.
  4. Le réel prime -- aucune règle n'est appliquée NI vérifiée sur les `existing_events` (buts) : si le réel impose une répétition ou une proximité, on l'accepte.

DETTE -- 2026-09-23 -- `MatchResult` n'existe nulle part dans le moteur de
résultats (`Match`/`MatchEvents`/`Lineup` sont 3 objets séparés, voir
`ligue1sim.schedule`/`events`/`lineup`) : aucune notion de DATE dans tout le
modèle de données (confirmé par le docstring de `simulation.py` lui-même),
et `competition_type` n'est jamais calculé en production (toujours fourni
par l'appelant, voir `animation.templates.context_from_event`). Décision
validée avec Olivier (brief "narrative engine foundations", 23/09/2026) :
`MatchResult` est une convention PROPRE à ce module, assemblée UNIQUEMENT
via `match_result_from` (point d'entrée unique -- aucun assemblage manuel
de `MatchResult` ailleurs dans le code de production) ; `date`/
`competition_type` restent optionnels (`None` si non fournis par
l'appelant), jamais inventés ici. Impact : la seed (`_derive_seed`) inclut
`date` tel quel (y compris `None`, stringifié) -- deux matchs SANS date entre
les mêmes équipes au même score produiraient la même seed (collision rare,
documentée, pas corrigée : hors scope, l'appelant d'un futur brief fournira
une vraie date/un vrai identifiant si la collision devient un problème réel).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np
from random import Random

from ligue1sim.animation.templates import TEMPLATES, TemplateContext, pick_template
from ligue1sim.events import GoalEvent, MatchEvents, PlayerMatchStat
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import PitchPoint, Zone, center_of
from ligue1sim.players import GOALKEEPER, position_group
from ligue1sim.schedule import Match

BUT = "but"
OCCASION = "occasion"
_EVENT_TYPES = frozenset({BUT, OCCASION})

_OUTCOME_BUT = "but"
# Issues d'une occasion non transformée -- poids choisis par plausibilité
# (un arrêt du gardien est l'issue la plus fréquente d'une vraie occasion,
# un poteau la plus rare), pas mesurés sur données réelles (hors scope ici,
# voir "calibrage sur données réelles" dans les briefs futurs de la série).
_NON_GOAL_OUTCOMES = ("arret", "hors_cadre", "tacle", "degagement", "poteau")
_NON_GOAL_OUTCOME_WEIGHTS = (0.40, 0.25, 0.15, 0.10, 0.10)

# Poisson tronquée (Tâche 4.1) -- cible ~15 occasions (buts + intercalées).
# Bornes [10, 22] : en dessous de 10, un résumé devient trop pauvre pour
# porter une narration crédible (moins d'une occasion toutes les 9 minutes) ;
# au-dessus de 22, le résumé dépasserait la cible de lecture de 1 à 3 minutes
# (voir contexte du brief) même à un rythme soutenu par occasion.
_POISSON_TARGET = 15
_POISSON_MIN = 10
_POISSON_MAX = 22
_POISSON_RESAMPLE_ATTEMPTS = 1000

# Écart minimum entre deux événements consécutifs (Tâche 5.3) -- en dessous
# de 3 minutes, deux occasions seraient difficile à distinguer une fois
# branchées au canvas (un gabarit dure 4 à 8s de "temps de jeu perçu", pas
# 3 minutes réelles, mais l'écart minute à minute reste le seul signal
# temporel dont ce brief dispose) ; au-dessus, on perd en densité pour
# atteindre ~15 occasions sur 90 minutes (15*3=45min de contrainte minimale,
# confortable ; un écart de 6min ne laisserait que 15 slots sur 90, trop
# tendu pour les tirages qui doivent aussi éviter les minutes de buts réels).
_MIN_MINUTE_GAP = 3
_MATCH_MINUTES = 90

# Pattern cyclique (Tâche 5.7) -- période maximale détectée, sur la SEULE
# séquence des gabarits (pas les couples gabarit+déclinaison, pour attraper
# aussi une alternance du type corner-A, corner-B, corner-A, corner-B qui
# échapperait à une règle formulée sur le couple).
_MAX_CYCLE_PERIOD = 5

_MAX_DRAW_ATTEMPTS = 200  # retirage contraint (Tâche 5) avant d'abandonner et de remonter

# Modulation par force des équipes (Tâche 4.2) -- `att_rating` (secteur
# offensif de la Lineup réellement alignée) plutôt que `rating` (moyenne
# plate) : ce sont les occasions D'ATTAQUE qu'on répartit, `att_rating` est
# la donnée la plus directement pertinente déjà exposée par le moteur
# (`Lineup.att_rating`, voir lineup.py). Repli sur `rating` si `att_rating`
# vaut 0.0 (secteur vide dans une compo dégradée/synthétique, voir
# `Lineup.att_rating` docstring). `p_home = att_dom / (att_dom + att_ext)`
# lissé à 70% vers 0.5 (`_RATING_SMOOTHING`) : un lissage complet (100%)
# annulerait la modulation demandée par la Tâche 4 ; un lissage nul (0%)
# donnerait des répartitions trop extrêmes pour un écart de rating modéré,
# peu crédible pour un résumé de match "normal". Valeur choisie pour que la
# Tâche 4.3 (test statistique) détecte un écart significatif sur un vrai
# écart de rating, sans réduire à néant les occasions de l'équipe la plus
# faible.
_RATING_SMOOTHING = 0.7


@dataclass(frozen=True)
class MatchResult:
    """Convention PROPRE à ce module (voir DETTE en tête de fichier) --
    assemblée uniquement via `match_result_from`, jamais construite à la
    main ailleurs."""

    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    goals: list[GoalEvent]
    home_lineup: Lineup  # ratings (pick_best_formation) -- onze de départ
    away_lineup: Lineup
    # Qui a RÉELLEMENT joué (titulaires + entrants, voir MatchEvents) --
    # nécessaire pour résoudre le poste d'un buteur remplaçant (absent de
    # `home_lineup`/`away_lineup`, qui ne portent que le onze de départ).
    home_squad: list[PlayerMatchStat]
    away_squad: list[PlayerMatchStat]
    date: str | None = None
    competition_type: str | None = None


def match_result_from(
    match: Match,
    events: MatchEvents,
    home_lineup: Lineup,
    away_lineup: Lineup,
    *,
    date: str | None = None,
    competition_type: str | None = None,
) -> MatchResult:
    """Point d'entrée UNIQUE pour assembler un `MatchResult` à partir des
    briques existantes du moteur de résultats (`Match`/`MatchEvents`/
    `Lineup`) -- découple `narrative.py` de la structure exacte du moteur de
    résultats. Tous les appelants (tests, canvas, scripts) passent par ici ;
    aucun assemblage manuel de `MatchResult` en dehors de cette fonction."""
    if match.home_goals is None or match.away_goals is None:
        raise ValueError(f"match {match.home} vs {match.away} pas encore joué (home_goals/away_goals=None)")
    if events is None:
        raise ValueError(f"match {match.home} vs {match.away} sans MatchEvents (compos dégradées/synthétiques ?)")
    return MatchResult(
        home_team=match.home,
        away_team=match.away,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        goals=list(events.goals),
        home_lineup=home_lineup,
        away_lineup=away_lineup,
        home_squad=list(events.home_lineup),
        away_squad=list(events.away_lineup),
        date=date,
        competition_type=competition_type,
    )


@dataclass(frozen=True)
class NarrativeEvent:
    minute: int
    event_type: str  # "but" | "occasion"
    gabarit: str
    declinaison: str  # "default" pour l'instant, voir docs/narrative_timeline_schema.md
    team: str  # home_team ou away_team de la Sequence/MatchResult
    main_player: str
    involved_players: tuple[str, ...]
    outcome: str
    start_position: tuple[float, float] | None
    starts_at_restart: bool


@dataclass(frozen=True)
class Timeline:
    match_id: str
    seed: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_rating: float
    away_rating: float
    competition_type: str | None
    events: list[NarrativeEvent]


def _derive_seed(match: MatchResult) -> int:
    """Hash SHA256 (via `hashlib`, jamais `hash()` -- qui varie d'un process
    à l'autre selon `PYTHONHASHSEED`, voir `sys.flags.hash_randomization`)
    sur `(home_team, away_team, date, home_goals, away_goals)`, même
    principe que `events._deterministic_rng`/`animation.ball._deterministic_unit`
    déjà dans ce projet -- stable bit à bit entre deux runs, deux machines,
    deux versions de Python (SHA256 est un algorithme standard, pas une
    fonction de hash de table dépendante de l'implémentation)."""
    key = f"{match.home_team}|{match.away_team}|{match.date}|{match.home_goals}|{match.away_goals}"
    digest = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _truncated_poisson_count(seed: int) -> int:
    """Tirage Poisson(λ=15) tronqué à [10, 22] par rejet -- générateur numpy
    LOCAL (`np.random.default_rng(seed)`, jamais l'état global `np.random`),
    même seed que le reste du tirage donc reproductible. `numpy` est déjà
    une dépendance du projet (voir pyproject.toml), pas une nouvelle."""
    generator = np.random.default_rng(seed)
    for _ in range(_POISSON_RESAMPLE_ATTEMPTS):
        n = int(generator.poisson(_POISSON_TARGET))
        if _POISSON_MIN <= n <= _POISSON_MAX:
            return n
    raise RuntimeError(
        f"Poisson(λ={_POISSON_TARGET}) n'a produit aucune valeur dans [{_POISSON_MIN},{_POISSON_MAX}] "
        f"en {_POISSON_RESAMPLE_ATTEMPTS} tirages -- bornes probablement trop étroites, à revoir."
    )


def _home_occasion_share(match: MatchResult) -> float:
    home_att = match.home_lineup.att_rating or match.home_lineup.rating
    away_att = match.away_lineup.att_rating or match.away_lineup.rating
    total = home_att + away_att
    raw_p_home = 0.5 if total <= 0 else home_att / total
    return 0.5 + (raw_p_home - 0.5) * _RATING_SMOOTHING


def _has_cyclic_pattern(gabarits: list[str], max_period: int = _MAX_CYCLE_PERIOD) -> bool:
    """Détecte un pattern cyclique de période <= `max_period` dans la
    séquence des gabarits (Tâche 5.7) : pour chaque période `p` de 1 à
    `max_period`, cherche une fenêtre où le bloc `[i:i+p]` se répète au
    moins deux fois consécutives (`[i+p:i+2p]`) -- attrape aussi bien
    `A,A` (p=1) que `corner,contre_attaque,corner,contre_attaque` (p=2)."""
    n = len(gabarits)
    for period in range(1, max_period + 1):
        for i in range(n - 2 * period + 1):
            if gabarits[i : i + period] == gabarits[i + period : i + 2 * period]:
                return True
    return False


def _squad_lookup(squad: list[PlayerMatchStat]) -> dict[str, PlayerMatchStat]:
    return {p.player_name: p for p in squad}


def _pick_minute(rng: Random, taken_minutes: list[int]) -> int:
    """Retirage contraint parmi les minutes déjà prises par d'AUTRES
    `generated_events` UNIQUEMENT (jamais les minutes de buts réels, voir
    PRIORITÉ DES CONTRAINTES en tête de fichier) -- espace largement
    suffisant par construction ([1, 90], au plus `_POISSON_MAX` occasions
    espacées de `_MIN_MINUTE_GAP`min), le repli "meilleur essai" ci-dessous
    ne devrait donc jamais s'activer en pratique ; gardé par défense plutôt
    que supprimé, pour ne jamais planter sur un cas limite non anticipé."""
    candidate = rng.randint(1, _MATCH_MINUTES)
    for _ in range(_MAX_DRAW_ATTEMPTS):
        if all(abs(candidate - m) >= _MIN_MINUTE_GAP for m in taken_minutes):
            return candidate
        candidate = rng.randint(1, _MATCH_MINUTES)
    return candidate  # meilleur essai après _MAX_DRAW_ATTEMPTS tentatives, voir docstring


def _pick_gabarit(
    rng: Random,
    context: TemplateContext,
    last_gabarit_declinaison: tuple[str, str] | None,
    gabarit_sequence: list[str],
) -> str:
    """Retirage contraint (Tâche 5.1/5.7 du brief précédent, PAS un filtre
    post-hoc) parmi les `generated_events` précédents UNIQUEMENT (jamais un
    but réel adjacent, voir PRIORITÉ DES CONTRAINTES) : retire tant que le
    candidat répète le couple (gabarit, déclinaison) précédent OU crée un
    pattern cyclique de période <= `_MAX_CYCLE_PERIOD` sur la séquence des
    `generated_events`. Repli "meilleur essai" -- voir `_pick_minute`."""
    candidate = pick_template(context, rng=rng)
    for _ in range(_MAX_DRAW_ATTEMPTS):
        pair_repeats = last_gabarit_declinaison is not None and (candidate, "default") == last_gabarit_declinaison
        if not pair_repeats and not _has_cyclic_pattern(gabarit_sequence + [candidate]):
            return candidate
        candidate = pick_template(context, rng=rng)
    return candidate  # meilleur essai après _MAX_DRAW_ATTEMPTS tentatives, voir docstring de _pick_minute


def _pick_main_player(rng: Random, squad: list[PlayerMatchStat], excluded_name: str | None) -> PlayerMatchStat:
    """Retirage contraint parmi les joueurs de champ (le gardien n'est
    jamais le protagoniste d'une occasion offensive, même invention premier
    jet -- pas de donnée réelle pour arbitrer ce cas). `excluded_name` : le
    protagoniste du `generated_event` PRÉCÉDENT uniquement (jamais un but
    réel adjacent, voir PRIORITÉ DES CONTRAINTES -- le lookahead vers un but
    suivant du brief précédent est retiré, il n'a plus lieu d'être)."""
    candidates = [p for p in squad if position_group(p.poste) != GOALKEEPER]
    candidate = rng.choice(candidates)
    for _ in range(_MAX_DRAW_ATTEMPTS):
        if candidate.player_name != excluded_name:
            return candidate
        candidate = rng.choice(candidates)
    return candidate  # meilleur essai après _MAX_DRAW_ATTEMPTS tentatives, voir docstring de _pick_minute


def _goal_diff_before_minute(goals: list[GoalEvent], minute: int, team: str, home_team: str, away_team: str) -> int:
    """Différentiel de buts pour `team` à partir des buts réels STRICTEMENT
    antérieurs à `minute` (utilisé pour `existing_events` ET
    `generated_events` -- un `generated_event` n'a pas d'ordre d'apparition
    propre dans les données d'entrée, seulement sa minute)."""
    home_before = sum(1 for g in goals if g.minute < minute and g.club_name == home_team)
    away_before = sum(1 for g in goals if g.minute < minute and g.club_name == away_team)
    return (home_before - away_before) if team == home_team else (away_before - home_before)


def _existing_events(match: MatchResult, rng: Random) -> list[NarrativeEvent]:
    """Un `NarrativeEvent` par but réel (`match.goals`), dans leur ORDRE
    D'APPARITION d'entrée (Tâche 1.3 : "insérés tels quels, triés par minute
    puis par ordre d'apparition" -- le tri par minute est fait par
    `build_timeline` via un tri STABLE, voir sa docstring ; ici on ne fait
    que préserver l'ordre d'apparition initial en traitant `match.goals`
    dans son ordre propre, jamais réordonné).

    AUCUN retirage contraint : `pick_template` est appelé UNE SEULE FOIS par
    but, sans vérifier ni gabarit précédent, ni pattern cyclique, ni joueur
    précédent -- les buts réels sont HORS PÉRIMÈTRE des règles
    anti-répétition (PRIORITÉ DES CONTRAINTES, point 4). Un penalty réel
    retombe naturellement sur le gabarit `"penalty"` (`_score_penalty` dans
    templates.py le rend seul éligible dès que `context.penalty=True`,
    aucun code spécial nécessaire ici)."""
    home_squad_lookup = _squad_lookup(match.home_squad)
    away_squad_lookup = _squad_lookup(match.away_squad)
    home_score = away_score = 0
    events: list[NarrativeEvent] = []

    for goal in match.goals:
        team = match.home_team if goal.club_name == match.home_team else match.away_team
        squad_lookup = home_squad_lookup if team == match.home_team else away_squad_lookup
        scorer_stat = squad_lookup.get(goal.scorer)
        scorer_poste = scorer_stat.poste if scorer_stat is not None else None
        assist_stat = squad_lookup.get(goal.assist) if goal.assist else None
        assist_poste = assist_stat.poste if assist_stat is not None else None
        own_before, opp_before = (home_score, away_score) if team == match.home_team else (away_score, home_score)
        context = TemplateContext(
            minute=goal.minute, goal_diff_before=own_before - opp_before,
            scorer_poste=scorer_poste, assist_poste=assist_poste,
            penalty=goal.penalty, competition_type=match.competition_type or "league",
        )
        gabarit = pick_template(context, rng=rng)
        involved = (goal.scorer, goal.assist) if goal.assist else (goal.scorer,)
        events.append(NarrativeEvent(
            minute=goal.minute, event_type=BUT, gabarit=gabarit, declinaison="default", team=team,
            main_player=goal.scorer, involved_players=involved, outcome=_OUTCOME_BUT,
            start_position=_zone_center(goal.zone), starts_at_restart=TEMPLATES[gabarit].starts_at_restart,
        ))
        if team == match.home_team:
            home_score += 1
        else:
            away_score += 1

    return events


def _generated_events(match: MatchResult, rng: Random, n_fillers: int) -> list[NarrativeEvent]:
    """`n_fillers` occasions inventées, triées par minute -- SEULES
    concernées par les règles anti-répétition/écart minimum (PRIORITÉ DES
    CONTRAINTES, point 3), vérifiées uniquement entre `generated_events`
    (jamais contre un `existing_event` adjacent)."""
    home_squad_lookup = _squad_lookup(match.home_squad)
    away_squad_lookup = _squad_lookup(match.away_squad)
    home_occasion_share = _home_occasion_share(match)

    minutes: list[int] = []
    for _ in range(n_fillers):
        minutes.append(_pick_minute(rng, minutes))
    minutes.sort()

    last_pair: tuple[str, str] | None = None
    last_main_player: str | None = None
    gabarit_sequence: list[str] = []
    events: list[NarrativeEvent] = []

    for minute in minutes:
        team = match.home_team if rng.random() < home_occasion_share else match.away_team
        squad_lookup = home_squad_lookup if team == match.home_team else away_squad_lookup
        squad = match.home_squad if team == match.home_team else match.away_squad
        main_player_stat = _pick_main_player(rng, squad, last_main_player)
        goal_diff_before = _goal_diff_before_minute(match.goals, minute, team, match.home_team, match.away_team)
        context = TemplateContext(
            minute=minute, goal_diff_before=goal_diff_before,
            scorer_poste=main_player_stat.poste, assist_poste=None,
            penalty=False, competition_type=match.competition_type or "league",
        )
        gabarit = _pick_gabarit(rng, context, last_pair, gabarit_sequence)
        main_player = main_player_stat.player_name
        involved = _involved_players(rng, gabarit, main_player, squad_lookup)
        outcome = rng.choices(_NON_GOAL_OUTCOMES, weights=_NON_GOAL_OUTCOME_WEIGHTS, k=1)[0]

        events.append(NarrativeEvent(
            minute=minute, event_type=OCCASION, gabarit=gabarit, declinaison="default", team=team,
            main_player=main_player, involved_players=involved, outcome=outcome,
            start_position=None,  # pas de zone réelle pour une occasion inventée -- non inventée non plus, voir schema
            starts_at_restart=TEMPLATES[gabarit].starts_at_restart,
        ))
        last_pair = (gabarit, "default")
        last_main_player = main_player
        gabarit_sequence.append(gabarit)

    return events


def build_timeline(match: MatchResult) -> Timeline:
    """Construit la `Timeline` d'un match déjà décidé (score et buts
    IMMUABLES, voir docs/narrative_timeline_schema.md, section "Invariants
    structurels", et PRIORITÉ DES CONTRAINTES en tête de fichier). AUCUN
    match n'est rejeté : `existing_events` (buts réels, hors périmètre des
    règles anti-répétition) et `generated_events` (occasions inventées, SEULES
    soumises à ces règles) sont construits séparément puis fusionnés par un
    tri STABLE sur la minute -- à minute égale, l'ordre de la CONCATÉNATION
    (`existing_events` d'abord, dans leur ordre d'apparition d'entrée, PUIS
    `generated_events` dans leur ordre de génération) est préservé, exactement
    la "règle de tri secondaire stable" de la Tâche 1.3.

    Déterministe : seed dérivée du match (`_derive_seed`), générateurs
    locaux (`random.Random`/`np.random.default_rng`) seedés explicitement,
    jamais l'état aléatoire global Python/numpy."""
    seed = _derive_seed(match)
    rng = Random(seed)

    existing_events = _existing_events(match, rng)

    total_occasions = max(_truncated_poisson_count(seed), len(match.goals))
    n_fillers = total_occasions - len(match.goals)
    generated_events = _generated_events(match, rng, n_fillers)

    events = sorted(existing_events + generated_events, key=lambda e: e.minute)  # tri stable, voir docstring

    match_id = f"{match.home_team}-{match.away_team}-{match.date}"
    return Timeline(
        match_id=match_id, seed=seed,
        home_team=match.home_team, away_team=match.away_team,
        home_goals=match.home_goals, away_goals=match.away_goals,
        home_rating=match.home_lineup.rating, away_rating=match.away_lineup.rating,
        competition_type=match.competition_type, events=events,
    )


def _zone_center(zone: Zone | None) -> tuple[float, float] | None:
    if zone is None:
        return None
    point: PitchPoint = center_of(zone)
    return (point.x, point.y)


def _involved_players(rng: Random, gabarit: str, main_player: str, squad_lookup: dict[str, PlayerMatchStat]) -> tuple[str, ...]:
    """`main_player` + un second joueur si le gabarit a plus d'un rôle
    scripté (`Template.roles`, champ public -- ne résout PAS les rôles vers
    de vrais joueurs comme le ferait `build_from_template` : hors scope de
    ce brief, voir "Mapping vers canvas" dans docs/narrative_timeline_schema.md,
    le branchement canvas d'un brief futur fera cette résolution complète)."""
    n_roles = len(TEMPLATES[gabarit].roles)
    if n_roles <= 1:
        return (main_player,)
    candidates = [name for name, stat in squad_lookup.items() if name != main_player and position_group(stat.poste) != GOALKEEPER]
    if not candidates:
        return (main_player,)
    return (main_player, rng.choice(candidates))
