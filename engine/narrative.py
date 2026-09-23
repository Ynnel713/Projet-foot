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


class MinuteCollisionError(RuntimeError):
    """Deux buts EXISTANTS (donnée du moteur de résultats, pas une erreur de
    génération narrative) tombent à la même minute -- voir docs/
    narrative_timeline_schema.md, "Invariants structurels", et brief
    "narrative engine foundations" Tâche 3.3 : "remontée, pas de correction
    silencieuse". Mesuré sur 2000 matchs de contrôle (voir retour de tâche) :
    ~3.95% des matchs simulés ont au moins une collision (même équipe ou
    équipes opposées, à peu près à parts égales) -- le moteur de résultats
    n'évite pas les collisions de minute entre deux `GoalEvent`, dette
    propre au moteur de résultats, non corrigée ici (règle d'escalade :
    aucun changement au moteur de résultats)."""


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


class AntiRepetitionUnsatisfiableError(RuntimeError):
    """Une règle anti-répétition (Tâche 5) est structurellement impossible à
    satisfaire sur CE match précis -- PAS une correction silencieuse ni une
    priorité implicite entre règles (brief, "Si une règle est incompatible
    avec une autre, remontée -- pas de priorité silencieuse"). Cas identifié
    en implémentant ce module : deux buts PENALTY réels consécutifs dans la
    timeline (`GoalEvent.penalty=True`) forcent chacun le gabarit "penalty"
    (`_score_penalty` renvoie 0.0 pour tout autre gabarit dès que
    `context.penalty=True`, voir templates.py -- "penalty" est alors le SEUL
    gabarit éligible) : la règle 5.1 (pas de répétition immédiate du couple)
    ne peut alors PHYSIQUEMENT pas être respectée, quel que soit le nombre
    de tentatives. Voir le retour de tâche pour le taux mesuré sur 1000
    matchs -- non corrigé ici, une décision sur les PARAMÈTRES (pas les
    règles) reste à prendre avec Olivier."""


def _pick_minute(rng: Random, taken_minutes: list[int]) -> int:
    for _ in range(_MAX_DRAW_ATTEMPTS):
        candidate = rng.randint(1, _MATCH_MINUTES)
        if all(abs(candidate - m) >= _MIN_MINUTE_GAP for m in taken_minutes):
            return candidate
    raise AntiRepetitionUnsatisfiableError(
        f"impossible de placer une occasion respectant l'écart minimum de {_MIN_MINUTE_GAP}min "
        f"après {_MAX_DRAW_ATTEMPTS} tentatives (minutes déjà prises : {sorted(taken_minutes)}) -- "
        "remontée Tâche 5 : paramètres à ajuster, pas les règles."
    )


def _pick_gabarit(
    rng: Random,
    context: TemplateContext,
    last_gabarit_declinaison: tuple[str, str] | None,
    gabarit_sequence: list[str],
) -> str:
    """Retirage contraint (Tâche 5.1/5.7, PAS un filtre post-hoc) : retire
    tant que le candidat répète le couple (gabarit, déclinaison) précédent
    OU crée un pattern cyclique de période <= `_MAX_CYCLE_PERIOD` sur la
    séquence des gabarits. Déclinaison toujours `"default"` pour l'instant
    (voir docs/narrative_timeline_schema.md) : la règle 5.1 porte déjà sur
    le couple pour s'assouplir automatiquement quand les déclinaisons
    s'enrichiront (brief séparé).

    Lève `AntiRepetitionUnsatisfiableError` si aucun candidat valide n'existe
    (voir sa docstring -- cas confirmé : deux penalties consécutifs)."""
    for _ in range(_MAX_DRAW_ATTEMPTS):
        candidate = pick_template(context, rng=rng)
        if last_gabarit_declinaison is not None and (candidate, "default") == last_gabarit_declinaison:
            continue
        if _has_cyclic_pattern(gabarit_sequence + [candidate]):
            continue
        return candidate
    raise AntiRepetitionUnsatisfiableError(
        f"impossible de tirer un gabarit respectant les règles anti-répétition après {_MAX_DRAW_ATTEMPTS} "
        f"tentatives (dernier couple : {last_gabarit_declinaison}, séquence : {gabarit_sequence}, "
        f"contexte : {context!r}) -- remontée Tâche 5 : paramètres à ajuster, pas les règles."
    )


def _pick_main_player(rng: Random, squad: list[PlayerMatchStat], excluded_names: frozenset[str]) -> PlayerMatchStat:
    """Retirage contraint (Tâche 5.2) parmi les joueurs de champ (le gardien
    n'est jamais le protagoniste d'une occasion offensive, même invention
    premier jet -- pas de donnée réelle pour arbitrer ce cas). `excluded_names`
    porte le protagoniste de l'événement PRÉCÉDENT et, si l'événement SUIVANT
    est un but réel déjà connu (la `slots` list est triée en amont), son
    buteur aussi -- sans ce lookahead, une occasion inventée juste avant un
    but pouvait retomber par hasard sur le même joueur que ce but (non
    corrigible a posteriori, le buteur réel est immuable)."""
    candidates = [p for p in squad if position_group(p.poste) != GOALKEEPER]
    for _ in range(_MAX_DRAW_ATTEMPTS):
        candidate = rng.choice(candidates)
        if candidate.player_name not in excluded_names:
            return candidate
    raise AntiRepetitionUnsatisfiableError(
        f"impossible de tirer un joueur principal hors de {sorted(excluded_names)!r} après {_MAX_DRAW_ATTEMPTS} tentatives."
    )


def build_timeline(match: MatchResult) -> Timeline:
    """Construit la `Timeline` d'un match déjà décidé (score et buts
    IMMUABLES, voir docs/narrative_timeline_schema.md, section "Invariants
    structurels"). Déterministe : seed dérivée du match (`_derive_seed`),
    générateurs locaux (`random.Random`/`np.random.default_rng`) seedés
    explicitement, jamais l'état aléatoire global Python/numpy."""
    seed = _derive_seed(match)
    rng = Random(seed)

    home_squad_lookup = _squad_lookup(match.home_squad)
    away_squad_lookup = _squad_lookup(match.away_squad)

    goal_minutes = [g.minute for g in match.goals]
    if len(goal_minutes) != len(set(goal_minutes)):
        raise MinuteCollisionError(
            f"{match.home_team} vs {match.away_team} : deux buts existants à la même minute "
            f"({sorted(m for m in goal_minutes if goal_minutes.count(m) > 1)}) -- remontée Tâche 3.3, "
            "pas de correction silencieuse."
        )

    total_occasions = max(_truncated_poisson_count(seed), len(match.goals))
    n_fillers = total_occasions - len(match.goals)

    taken_minutes = list(goal_minutes)
    filler_minutes: list[int] = []
    for _ in range(n_fillers):
        minute = _pick_minute(rng, taken_minutes)
        taken_minutes.append(minute)
        filler_minutes.append(minute)

    # (minute, is_goal, GoalEvent|None) -- fusionne buts réels et occasions
    # inventées en une seule timeline triée AVANT de générer le contenu de
    # chaque événement (nécessaire pour calculer goal_diff_before dans le
    # bon ordre chronologique, et pour le lookahead de `_pick_main_player`).
    slots: list[tuple[int, GoalEvent | None]] = [(g.minute, g) for g in match.goals]
    slots += [(m, None) for m in filler_minutes]
    slots.sort(key=lambda s: s[0])

    # Deux buts RÉELS consécutifs (aucune occasion inventée entre les deux)
    # marqués par le MÊME buteur : la règle 5.2 (pas de répétition immédiate
    # de joueur principal) est alors structurellement impossible à respecter
    # -- le buteur réel est immuable (Tâche 3), rien à retirer. Même
    # traitement que les deux penalties consécutifs (voir
    # AntiRepetitionUnsatisfiableError) : remontée, pas de violation
    # silencieuse de la règle.
    for (_m_a, goal_a), (_m_b, goal_b) in zip(slots, slots[1:]):
        if goal_a is not None and goal_b is not None and goal_a.scorer == goal_b.scorer:
            raise AntiRepetitionUnsatisfiableError(
                f"{match.home_team} vs {match.away_team} : deux buts réels consécutifs "
                f"({goal_a.minute}min, {goal_b.minute}min) du même buteur ({goal_a.scorer!r}) -- "
                "règle 5.2 structurellement impossible à respecter, remontée."
            )

    home_score = away_score = 0
    last_pair: tuple[str, str] | None = None
    last_main_player: str | None = None
    gabarit_sequence: list[str] = []
    events: list[NarrativeEvent] = []
    home_occasion_share = _home_occasion_share(match)

    for i, (minute, goal) in enumerate(slots):
        if goal is not None:
            team = match.home_team if goal.club_name == match.home_team else match.away_team
            squad_lookup = home_squad_lookup if team == match.home_team else away_squad_lookup
            scorer_stat = squad_lookup.get(goal.scorer)
            scorer_poste = scorer_stat.poste if scorer_stat is not None else None
            assist_stat = squad_lookup.get(goal.assist) if goal.assist else None
            assist_poste = assist_stat.poste if assist_stat is not None else None
            own_score_before, opp_score_before = (home_score, away_score) if team == match.home_team else (away_score, home_score)
            context = TemplateContext(
                minute=minute, goal_diff_before=own_score_before - opp_score_before,
                scorer_poste=scorer_poste, assist_poste=assist_poste,
                penalty=goal.penalty, competition_type=match.competition_type or "league",
            )
            gabarit = _pick_gabarit(rng, context, last_pair, gabarit_sequence)
            main_player = goal.scorer
            involved = (goal.scorer, goal.assist) if goal.assist else (goal.scorer,)
            start_position = _zone_center(goal.zone)
            outcome = _OUTCOME_BUT
            if team == match.home_team:
                home_score += 1
            else:
                away_score += 1
        else:
            team = match.home_team if rng.random() < home_occasion_share else match.away_team
            squad_lookup = home_squad_lookup if team == match.home_team else away_squad_lookup
            squad = match.home_squad if team == match.home_team else match.away_squad
            excluded_names = {last_main_player} if last_main_player is not None else set()
            if i + 1 < len(slots) and slots[i + 1][1] is not None:
                excluded_names.add(slots[i + 1][1].scorer)  # lookahead, voir docstring de _pick_main_player
            main_player_stat = _pick_main_player(rng, squad, frozenset(excluded_names))
            own_score_before, opp_score_before = (home_score, away_score) if team == match.home_team else (away_score, home_score)
            context = TemplateContext(
                minute=minute, goal_diff_before=own_score_before - opp_score_before,
                scorer_poste=main_player_stat.poste, assist_poste=None,
                penalty=False, competition_type=match.competition_type or "league",
            )
            gabarit = _pick_gabarit(rng, context, last_pair, gabarit_sequence)
            main_player = main_player_stat.player_name
            involved = _involved_players(rng, gabarit, main_player, squad_lookup)
            start_position = None  # pas de zone réelle pour une occasion inventée -- non inventé non plus, voir schema
            outcome = rng.choices(_NON_GOAL_OUTCOMES, weights=_NON_GOAL_OUTCOME_WEIGHTS, k=1)[0]

        events.append(NarrativeEvent(
            minute=minute, event_type=BUT if goal is not None else OCCASION,
            gabarit=gabarit, declinaison="default", team=team,
            main_player=main_player, involved_players=involved, outcome=outcome,
            start_position=start_position, starts_at_restart=TEMPLATES[gabarit].starts_at_restart,
        ))
        last_pair = (gabarit, "default")
        last_main_player = main_player
        gabarit_sequence.append(gabarit)

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
