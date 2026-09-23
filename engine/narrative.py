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
from dataclasses import dataclass, field, replace

import numpy as np
from random import Random

from ligue1sim.animation.templates import TEMPLATES, TemplateContext, pick_template
from ligue1sim.events import (
    PENALTY_SPOT_ZONE,
    CardEvent,
    GoalEvent,
    MatchEvents,
    PlayerMatchStat,
    SubstitutionEvent,
)
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import GRID_COLUMNS, GRID_ROWS, PitchPoint, Zone, center_of
from ligue1sim.players import GOALKEEPER, Player, position_group
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

# Penaltys ratés (brief "canvas player", 23/09/2026, Tâche 2) -- issues
# propres au tir au but, distinctes de `_NON_GOAL_OUTCOMES` (un "tacle" ou un
# "degagement" n'a pas de sens sur un penalty, personne d'autre que le
# tireur et le gardien n'intervient). Ordres de grandeur donnés par le brief
# (~60% arrêt, ~15% poteau/barre combiné, ~25% hors cadre) -- poteau et barre
# ne sont pas distingués dans la donnée fournie, répartis à parts égales
# faute de source plus précise (même esprit que _NON_GOAL_OUTCOME_WEIGHTS :
# ajustable, documenté, pas une vérité absolue).
_MISSED_PENALTY_OUTCOMES = ("arret", "poteau", "hors_cadre", "barre")
_MISSED_PENALTY_OUTCOME_WEIGHTS = (0.60, 0.075, 0.25, 0.075)

# Calibration du volume de penaltys ratés (Tâche 2.1/2.2) -- G mesuré sur
# 1000 matchs simulés (seed 2026_09_23, pipeline identique à
# tests/test_narrative.py::_simulate_n, équipes note=70 vs note=70) : 247
# buts sur gabarit "penalty" (`NarrativeEvent.gabarit == "penalty"` ET
# `event_type == BUT`) sur 2736 buts totaux -- G = 247/1000 = 0.247 penaltys
# marqués/match. Mesure ponctuelle (script non conservé, comme les autres
# constantes calibrées de ce module) figée ici en constante, valeur
# rapportée telle quelle dans le retour de tâche.
_MEASURED_PENALTY_GOALS_PER_MATCH = 0.247  # G
_TARGET_MISSED_PENALTY_RATIO = 0.76  # T -- cible fournie par le brief (moyenne europeenne)
# Formule (Tâche 2.2) : le ratio global visé est
#   T = marqués / (marqués + ratés)
# <=> marqués = T * (marqués + ratés)
# <=> marqués * (1 - T) = T * ratés
# <=> ratés = marqués * (1 - T) / T
# Avec marqués ~ G (moyenne mesurée), R = G * (1 - T) / T est la moyenne de
# ratés à générer par match pour que le ratio global observé converge vers T.
_MISSED_PENALTY_POISSON_MEAN = (  # R
    _MEASURED_PENALTY_GOALS_PER_MATCH * (1 - _TARGET_MISSED_PENALTY_RATIO) / _TARGET_MISSED_PENALTY_RATIO
)

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

# Retirage contraint (Tâche 5) avant d'abandonner et de retomber sur le
# "meilleur essai" (voir _pick_minute et consorts) -- releve de 200 a 5000
# (brief "canvas player consolidation", 23/09/2026, Tâche 4) : cause
# identifiee du flake ~1/9 runs sur test_generated_events_respect_anti_repetition
# (voir retour de tache pour le detail complet) -- PAS une fenetre de
# tolerance statistique comme le laissait supposer l'intitule de la Tâche 4,
# mais un espace de recherche combinatoire qui devient tres etroit dans le
# cas limite d'un match a occasions denses : avec _POISSON_MAX=22 fillers
# deja tires (Tâche 4 du brief "narrative engine foundations") PLUS un
# penalty rate (Tâche 2 du brief "canvas player") a placer en plus, les 22
# minutes deja prises peuvent ne laisser qu'UN SEUL minute valide (a >=3min
# de toutes les autres, voir _MIN_MINUTE_GAP) sur les 90 possibles -- a 200
# tirages aleatoires uniformes sur [1,90], la probabilite de RATER cette
# unique minute valide est (89/90)^200 ~= 10.8%, largement suffisant pour
# expliquer le flake observe. A 5000 tirages, cette meme probabilite tombe a
# (89/90)^5000 ~= 4e-25 -- practiquement nul, sans changer la regle
# elle-meme (toujours >=3min exactement, jamais assoupli).
_MAX_DRAW_ATTEMPTS = 5000

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
    # `home_lineup`/`away_lineup.substitutes` désormais peuplés (Tâche 2,
    # brief "canvas player consolidation", 23/09/2026) -- voir
    # `_lineup_with_substitutes` : ancienne limite ("home_squad/away_squad
    # nécessaire pour résoudre le poste d'un buteur remplaçant, absent de
    # home_lineup/away_lineup") corrigée directement à la source ici, plus
    # besoin de redescendre jusqu'à `home_squad`/`away_squad` pour ça.
    home_lineup: Lineup  # ratings (pick_best_formation) -- onze de départ + substitutes
    away_lineup: Lineup
    # Qui a RÉELLEMENT joué (titulaires + entrants, voir MatchEvents) --
    # conservé pour compatibilité (`_pick_main_player` etc. en dépendent
    # toujours), plus la seule source de `home_lineup.substitutes` ci-dessus.
    home_squad: list[PlayerMatchStat]
    away_squad: list[PlayerMatchStat]
    date: str | None = None
    competition_type: str | None = None
    # Extension du 23/09/2026 (brief "canvas player consolidation", Tâche 1,
    # décision explicite d'Olivier) : cartons/remplacements RÉELS de ce
    # match, extraits tels quels de `MatchEvents.cards`/`.substitutions`
    # (aucune donnée inventée) -- nécessaires pour peupler
    # `NarrativeEvent`/`Clip.interval_events` côté canvas (voir
    # `engine/narrative_player.py`).
    cards: tuple[CardEvent, ...] = ()
    substitutions: tuple[SubstitutionEvent, ...] = ()


def _player_from_stat(stat: PlayerMatchStat) -> Player:
    """Reconstruit un `Player` complet à partir d'un `PlayerMatchStat` (voir
    `events.py` -- porte déjà `poste`/`note`/`age`/`nationalite`, un profil
    joueur "indépendant du match", pas seulement des stats de ce match précis).
    `prenom=stat.player_name, nom=""` : `Player.name` (`f"{prenom} {nom}".strip()`)
    redonne alors EXACTEMENT `stat.player_name`, quel que soit son contenu
    (avec ou sans espace) -- même repli que partout ailleurs dans ce module
    pour ne jamais désynchroniser un nom entre deux représentations d'un
    même joueur. `id=None` (inconnu ici) : `templates.player_id_of` retombe
    déjà sur le nom dans ce cas, comportement existant, pas un nouveau cas
    à gérer."""
    return Player(
        prenom=stat.player_name, nom="", nationalite=stat.nationalite, age=stat.age,
        poste=stat.poste, note=stat.note, club=stat.club_name, championnat="",
    )


def _lineup_with_substitutes(lineup: Lineup, squad: list[PlayerMatchStat]) -> Lineup:
    """`lineup` (onze de départ) + `.substitutes` peuplé depuis `squad`
    (`MatchEvents.home_lineup`/`.away_lineup`, TOUT l'effectif ayant
    réellement joué -- titulaires ET entrants, voir `PlayerMatchStat.started`)
    -- Tâche 2, brief "canvas player consolidation", 23/09/2026. Lecture
    seule sur des données déjà produites par le moteur de résultats, rien
    d'inventé : un remplaçant qui n'est jamais entré en jeu n'apparaît pas
    dans `squad` (`_play_match_squad` ne construit d'entrée que pour les
    entrants réels), donc pas non plus ici."""
    substitutes = [_player_from_stat(stat) for stat in squad if not stat.started]
    return replace(lineup, substitutes=substitutes)


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
        home_lineup=_lineup_with_substitutes(home_lineup, events.home_lineup),
        away_lineup=_lineup_with_substitutes(away_lineup, events.away_lineup),
        home_squad=list(events.home_lineup),
        away_squad=list(events.away_lineup),
        date=date,
        competition_type=competition_type,
        cards=tuple(events.cards),
        substitutions=tuple(events.substitutions),
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
    # Extension du 23/09/2026 (brief "canvas player", Tâche 3, décision
    # explicite d'Olivier -- hors du périmètre initial du brief, autorisée
    # pour débloquer engine/narrative_player.py) : zone normalisée (x, y),
    # dérivée du gabarit + d'un léger décalage déterministe seedé par la
    # position finale de l'événement dans Timeline.events (voir
    # _narrative_event_zone/build_timeline) -- TOUJOURS peuplée (jamais None,
    # contrairement à start_position), pour TOUT événement (but ET occasion,
    # y compris les buts réels : même convention partout, voir
    # _narrative_event_zone). Placeholder à la construction (0.0, 0.0),
    # écrasée par build_timeline une fois l'index final connu -- ne jamais
    # lire cette valeur avant le retour de build_timeline.
    zone: tuple[float, float] = (0.0, 0.0)
    # Extension du 23/09/2026 (brief "canvas player consolidation", Tache 3,
    # decision explicite d'Olivier) : MEME modele que `zone` ci-dessus (une
    # zone de base par gabarit + decalage deterministe seede par l'index
    # final, voir `_narrative_event_assist_zone`) -- TOUJOURS peuplee,
    # jamais `None`. Consommee par `narrative_player._build_clip_frames`
    # comme `GoalEvent.assist_zone` (`ANCHOR_ASSIST` dans
    # `templates.build_from_template`) -- pour un gabarit SANS role
    # "assist" (ex. `recuperation_haute`, `penalty`, `but_gag`), cette
    # valeur existe pour la coherence du schema mais n'est jamais
    # effectivement consommee (aucun role n'y reference). Meme placeholder
    # (0.0, 0.0) a la construction, meme avertissement : ne jamais lire
    # avant le retour de build_timeline.
    assist_zone: tuple[float, float] = (0.0, 0.0)


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
    # Extension du 23/09/2026 (brief "canvas player", Tâche 3, décision
    # explicite d'Olivier) : RÉFÉRENCE directe vers les Lineup du MatchResult
    # d'entrée (onze de départ -- porte aussi `.substitutes` depuis la
    # Tâche 2 de la consolidation du 23/09/2026, voir
    # `_lineup_with_substitutes`), jamais une copie -- nécessaire pour que
    # narrative_player.build_clips puisse construire une Sequence réelle
    # sans revenir au MatchResult d'origine (Timeline doit rester
    # auto-suffisante pour le rendu, voir docstring de module).
    home_lineup: Lineup
    away_lineup: Lineup
    # Extension du 23/09/2026 (brief "canvas player consolidation", Tâche 1,
    # décision explicite d'Olivier) : RÉFÉRENCE directe vers
    # `MatchResult.cards`/`.substitutions` (cartons/remplacements réels),
    # jamais une copie -- nécessaire pour que `narrative_player.build_clips`
    # peuple `Clip.interval_events` sans revenir au `MatchResult` d'origine.
    cards: tuple[CardEvent, ...]
    substitutions: tuple[SubstitutionEvent, ...]
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


# --- Zone dérivée du gabarit (Tâche 3, décision explicite d'Olivier du
# 23/09/2026) -----------------------------------------------------------
#
# `NarrativeEvent.zone` alimente `GoalEvent.zone`-équivalent côté
# `narrative_player.build_clips` -> `templates.build_from_template`
# (ANCHOR_SCORER) : c'est la zone où l'action DÉCISIVE (tir/tête) converge,
# pas littéralement "où le mouvement démarre" malgré le nom du champ -- même
# convention que `GoalEvent.zone` déjà existant côté moteur (`events._shot_zone`),
# et même lecture déjà faite de `NarrativeEvent.start_position` ("but:
# center_of(GoalEvent.zone)", voir docs/narrative_timeline_schema.md). Une
# zone de base par gabarit choisie pour rester géométriquement plausible UNE
# FOIS CONSOMMÉE par ANCHOR_SCORER (toujours dans le tiers offensif, jamais
# dans son propre camp -- un `contre_attaque` littéralement ancré en zone
# défensive ferait converger le tir du buteur dans SA PROPRE moitié de
# terrain, faux) tout en reflétant la nature de l'action via sa position
# exacte dans ce tiers (une tête de corner/débordement plutôt excentrée près
# du petit rectangle, un une-deux/un but_gag à bout portant, un penalty
# exactement au point réglementaire -- déjà la vraie zone d'un penalty côté
# moteur, `events.PENALTY_SPOT_ZONE`, aucune divergence).
_GABARIT_BASE_ZONE: dict[str, Zone] = {
    "contre_attaque": Zone(col=9, row=4),
    "construction_placee": Zone(col=9, row=4),
    "debordement_centre_tete": Zone(col=10, row=2),
    "percee_individuelle": Zone(col=9, row=4),
    "une_deux": Zone(col=10, row=4),
    "coup_franc": Zone(col=7, row=4),
    "corner": Zone(col=10, row=1),
    "profondeur_1v1": Zone(col=10, row=4),
    "recuperation_haute": Zone(col=10, row=4),
    "decalage_enroulee": Zone(col=9, row=2),
    "penalty": PENALTY_SPOT_ZONE,
    "but_gag": Zone(col=11, row=4),
}
_ZONE_JITTER_COLS = 1  # ecart max en colonnes autour de la zone de base du gabarit
_ZONE_JITTER_ROWS = 2  # ecart max en lignes -- variation laterale un peu plus large que la variation en profondeur


def _narrative_event_zone(gabarit: str, index: int) -> tuple[float, float]:
    """Zone déterministe d'un `NarrativeEvent`, dérivée de son gabarit
    (`_GABARIT_BASE_ZONE`) et perturbée par un petit décalage déterministe
    (hash sha256, même principe que le reste du module) seedé par `index` --
    la position FINALE de l'événement dans `Timeline.events` (post tri, voir
    `build_timeline`) : deux occasions du même gabarit dans le même match ne
    partent jamais du même point, mais un même `(match, index)` retombe
    toujours sur la même zone (déterminisme)."""
    base = _GABARIT_BASE_ZONE[gabarit]
    digest = hashlib.sha256(f"zone|{gabarit}|{index}".encode()).digest()
    col_fraction = int.from_bytes(digest[:4], "big") / 2**32  # [0, 1)
    row_fraction = int.from_bytes(digest[4:8], "big") / 2**32
    col_offset = round((col_fraction * 2 - 1) * _ZONE_JITTER_COLS)
    row_offset = round((row_fraction * 2 - 1) * _ZONE_JITTER_ROWS)
    col = min(max(base.col + col_offset, 0), GRID_COLUMNS - 1)
    row = min(max(base.row + row_offset, 0), GRID_ROWS - 1)
    point = center_of(Zone(col=col, row=row))
    return (point.x, point.y)


# --- Zone d'assist derivee du gabarit (Tache 3, brief "canvas player
# consolidation", 23/09/2026, decision explicite d'Olivier) ---------------
#
# Meme principe que _GABARIT_BASE_ZONE/_narrative_event_zone ci-dessus, mais
# pour ANCHOR_ASSIST (templates.py) plutot que ANCHOR_SCORER -- consomme
# comme GoalEvent.assist_zone par narrative_player._build_clip_frames. Les 3
# exemples du brief sont repris tels quels : un corner joue a deux part
# d'une zone proche du tireur (corner, col=11 -- litteralement le coin), un
# une-deux part d'une zone intermediaire (une_deux, milieu de terrain), un
# contre part de la moitie defensive (contre_attaque, col=2). Les 4 autres
# gabarits AVEC un role "assist" (construction_placee, debordement_centre_tete,
# profondeur_1v1, decalage_enroulee) suivent le meme esprit -- une zone
# plausible pour le POINT DE DEPART/relais de la passe decisive de ce
# gabarit precis, plus reculee/excentree que sa zone de tir (_GABARIT_BASE_ZONE).
# Les gabarits SANS role "assist" (percee_individuelle, coup_franc,
# recuperation_haute, penalty, but_gag -- voir templates.py, Template.roles)
# recoivent tout de meme une valeur : jamais consommee par
# build_from_template pour ces gabarits (aucun role n'y pointe), presente
# uniquement pour que NarrativeEvent.assist_zone ne soit JAMAIS None (Tache
# 3.3), coherence de schema plutot qu'un cas particulier a gerer partout.
_GABARIT_ASSIST_BASE_ZONE: dict[str, Zone] = {
    "contre_attaque": Zone(col=2, row=4),  # moitie defensive (exemple explicite du brief)
    "construction_placee": Zone(col=3, row=4),  # circulation profonde, avant la progression vers l'avant
    "debordement_centre_tete": Zone(col=9, row=1),  # aile, juste avant le centre
    "une_deux": Zone(col=7, row=4),  # zone intermediaire (exemple explicite du brief)
    "corner": Zone(col=11, row=0),  # proche du tireur, au coin (exemple explicite du brief)
    "profondeur_1v1": Zone(col=6, row=4),  # milieu de terrain, avant la passe en profondeur
    "decalage_enroulee": Zone(col=8, row=3),  # cote fort, juste avant le tireur qui enroule
    # Gabarits sans role "assist" -- voir le paragraphe ci-dessus.
    "percee_individuelle": Zone(col=5, row=4),
    "coup_franc": Zone(col=7, row=4),
    "recuperation_haute": Zone(col=6, row=4),
    "penalty": PENALTY_SPOT_ZONE,
    "but_gag": Zone(col=10, row=4),
}


def _narrative_event_assist_zone(gabarit: str, index: int) -> tuple[float, float]:
    """MEME mecanique que `_narrative_event_zone` (gabarit + decalage
    deterministe seede par l'index final) mais sur `_GABARIT_ASSIST_BASE_ZONE`
    -- sel de hash DIFFERENT ("assist_zone|..." vs "zone|...") pour que le
    decalage d'assist_zone ne soit jamais exactement correle a celui de
    zone (deux perturbations independantes, meme si deterministes toutes
    les deux)."""
    base = _GABARIT_ASSIST_BASE_ZONE[gabarit]
    digest = hashlib.sha256(f"assist_zone|{gabarit}|{index}".encode()).digest()
    col_fraction = int.from_bytes(digest[:4], "big") / 2**32
    row_fraction = int.from_bytes(digest[4:8], "big") / 2**32
    col_offset = round((col_fraction * 2 - 1) * _ZONE_JITTER_COLS)
    row_offset = round((row_fraction * 2 - 1) * _ZONE_JITTER_ROWS)
    col = min(max(base.col + col_offset, 0), GRID_COLUMNS - 1)
    row = min(max(base.row + row_offset, 0), GRID_ROWS - 1)
    point = center_of(Zone(col=col, row=row))
    return (point.x, point.y)


def _missed_penalty_seed(seed: int) -> int:
    """Seed dérivée (hash sha256 salé, même principe que `_derive_seed`) --
    délibérément DIFFÉRENTE de `seed` lui-même (utilisé tel quel par
    `_truncated_poisson_count`) : un générateur numpy local et indépendant
    évite de corréler artificiellement le nombre de penaltys ratés au nombre
    total d'occasions du match (deux tirages Poisson avec la MÊME seed
    produiraient des valeurs corrélées, ce n'est pas le comportement voulu)."""
    digest = hashlib.sha256(f"missed_penalty|{seed}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _missed_penalty_count(seed: int) -> int:
    """Tirage Poisson(λ=R) NON tronqué (Tâche 2.3 -- contrairement à
    `_truncated_poisson_count`, aucune borne [min, max] : R est petit
    (~0.08, voir _MISSED_PENALTY_POISSON_MEAN), la quasi-totalité des matchs
    tirent 0 ou 1, un tronquage n'a pas de sens ici)."""
    generator = np.random.default_rng(_missed_penalty_seed(seed))
    return int(generator.poisson(_MISSED_PENALTY_POISSON_MEAN))


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


_MISSED_PENALTY_KIND = "missed_penalty"
_FILLER_KIND = "filler"
_MISSED_PENALTY_PAIR = ("penalty", "default")  # gabarit fixe d'un penalty rate, voir _generated_events


def _repair_consecutive_missed_penalties(
    rng: Random, pending: list[tuple[int, str]], taken_minutes: list[int]
) -> list[tuple[int, str]]:
    """Deux penaltys ratés consécutifs (aucun `filler` entre les deux, une
    fois `pending` trié par minute) violeraient la règle anti-répétition
    immédiate ((gabarit, déclinaison) répété, voir _MISSED_PENALTY_PAIR) --
    le SEUL cas possible : un `filler` ne tire jamais le gabarit "penalty"
    (`_score_penalty` vaut 0 tant que `context.penalty=False`, toujours le
    cas pour un `filler`, voir `_generated_events`). Repli identique à
    `_pick_minute`/`_pick_gabarit` (retirage contraint, meilleur essai après
    `_MAX_DRAW_ATTEMPTS`) -- mais ici le gabarit est fixe (un penalty raté
    EST "penalty"), seul le levier MINUTE peut lever la collision : on
    redéplace le second penalty raté du couple, jamais son gabarit."""
    pending = sorted(pending, key=lambda pair: pair[0])
    for _ in range(_MAX_DRAW_ATTEMPTS):
        collision_idx = next(
            (i for i in range(1, len(pending)) if pending[i][1] == pending[i - 1][1] == _MISSED_PENALTY_KIND),
            None,
        )
        if collision_idx is None:
            return pending
        old_minute, kind = pending[collision_idx]
        taken_minutes.remove(old_minute)
        new_minute = _pick_minute(rng, taken_minutes)
        taken_minutes.append(new_minute)
        pending[collision_idx] = (new_minute, kind)
        pending.sort(key=lambda pair: pair[0])
    return pending  # meilleur essai apres _MAX_DRAW_ATTEMPTS tentatives, voir docstring de _pick_minute


def _generated_events(match: MatchResult, rng: Random, n_fillers: int, n_missed_penalties: int) -> list[NarrativeEvent]:
    """`n_fillers` occasions inventées + `n_missed_penalties` penaltys ratés
    (Tâche 2.3/2.4), fusionnés et triés par minute -- SEULES catégories
    concernées par les règles anti-répétition/écart minimum (PRIORITÉ DES
    CONTRAINTES, point 3), vérifiées uniquement entre `generated_events`
    (jamais contre un `existing_event` adjacent). Un penalty raté est un
    `generated_event` comme un autre pour ces règles : gabarit fixé à
    "penalty" (jamais tiré via `pick_template`, voir _MISSED_PENALTY_PAIR),
    déclinaison "default", jamais compté dans le score (`outcome` tiré parmi
    _MISSED_PENALTY_OUTCOMES, jamais "but")."""
    home_squad_lookup = _squad_lookup(match.home_squad)
    away_squad_lookup = _squad_lookup(match.away_squad)
    home_occasion_share = _home_occasion_share(match)

    taken_minutes: list[int] = []
    pending: list[tuple[int, str]] = []
    for _ in range(n_fillers):
        minute = _pick_minute(rng, taken_minutes)
        taken_minutes.append(minute)
        pending.append((minute, _FILLER_KIND))
    for _ in range(n_missed_penalties):
        minute = _pick_minute(rng, taken_minutes)
        taken_minutes.append(minute)
        pending.append((minute, _MISSED_PENALTY_KIND))
    pending = _repair_consecutive_missed_penalties(rng, pending, taken_minutes)

    last_pair: tuple[str, str] | None = None
    last_main_player: str | None = None
    gabarit_sequence: list[str] = []
    events: list[NarrativeEvent] = []

    for minute, kind in pending:
        team = match.home_team if rng.random() < home_occasion_share else match.away_team
        squad_lookup = home_squad_lookup if team == match.home_team else away_squad_lookup
        squad = match.home_squad if team == match.home_team else match.away_squad
        main_player_stat = _pick_main_player(rng, squad, last_main_player)
        main_player = main_player_stat.player_name

        if kind == _MISSED_PENALTY_KIND:
            gabarit = _MISSED_PENALTY_PAIR[0]
            involved = _involved_players(rng, gabarit, main_player, squad_lookup)
            outcome = rng.choices(_MISSED_PENALTY_OUTCOMES, weights=_MISSED_PENALTY_OUTCOME_WEIGHTS, k=1)[0]
            # Zone RÉELLE, pas inventée : un penalty part TOUJOURS du même
            # point réglementaire (PENALTY_SPOT_ZONE, voir events.py), à la
            # différence d'une occasion générique dont start_position reste
            # None (voir plus bas) -- ce n'est pas une zone devinée.
            start_position = _zone_center(PENALTY_SPOT_ZONE)
        else:
            goal_diff_before = _goal_diff_before_minute(match.goals, minute, team, match.home_team, match.away_team)
            context = TemplateContext(
                minute=minute, goal_diff_before=goal_diff_before,
                scorer_poste=main_player_stat.poste, assist_poste=None,
                penalty=False, competition_type=match.competition_type or "league",
            )
            gabarit = _pick_gabarit(rng, context, last_pair, gabarit_sequence)
            involved = _involved_players(rng, gabarit, main_player, squad_lookup)
            outcome = rng.choices(_NON_GOAL_OUTCOMES, weights=_NON_GOAL_OUTCOME_WEIGHTS, k=1)[0]
            start_position = None  # pas de zone réelle pour une occasion inventée -- non inventée non plus, voir schema

        events.append(NarrativeEvent(
            minute=minute, event_type=OCCASION, gabarit=gabarit, declinaison="default", team=team,
            main_player=main_player, involved_players=involved, outcome=outcome,
            start_position=start_position,
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
    n_missed_penalties = _missed_penalty_count(seed)
    generated_events = _generated_events(match, rng, n_fillers, n_missed_penalties)
    # Repli niveau-sequence (brief "canvas player consolidation", 23/09/2026,
    # Tache 4) : un penalty rate a un gabarit FIXE ("penalty", voir
    # _MISSED_PENALTY_PAIR) qui ne passe jamais par _pick_gabarit, donc
    # jamais verifie contre _has_cyclic_pattern au moment de son insertion --
    # contrairement a un filler, dont le gabarit est un candidat substituable.
    # Consequence precise (cas reproduit et trace) : un filler peut etre un
    # choix VALIDE au moment de son tirage (la sequence est encore trop
    # courte pour reveler la fenetre p<=5 concernee), puis un penalty rate
    # inséré PLUS TARD à une position qui referme retroactivement ce motif --
    # sans qu'aucun retirage individuel n'ait jamais vu la violation. Ce
    # n'est PAS le meme mecanisme que _MAX_DRAW_ATTEMPTS (repli par candidat)
    # ci-dessus : ici le repli porte sur la SEQUENCE ENTIERE, seul niveau ou
    # la violation devient visible. Aucun assouplissement de la regle
    # (periode <= _MAX_CYCLE_PERIOD reste identique) -- seule la granularite
    # du retirage change, elle devient en pratique PLUS stricte qu'avant
    # (couvre aussi les fenetres closes par un penalty raté, invisibles au
    # niveau candidat).
    for _ in range(_MAX_DRAW_ATTEMPTS):
        if not _has_cyclic_pattern([e.gabarit for e in generated_events]):
            break
        generated_events = _generated_events(match, rng, n_fillers, n_missed_penalties)
    # meilleur essai après _MAX_DRAW_ATTEMPTS tentatives, voir docstring de _pick_minute

    events = sorted(existing_events + generated_events, key=lambda e: e.minute)  # tri stable, voir docstring
    # Zone (Tâche 3, décision du 23/09/2026) : seedée par la position FINALE
    # (post-tri) -- appliquée ici, pas dans _existing_events/_generated_events,
    # qui ne connaissent pas encore cet ordre final au moment où ils
    # construisent chaque NarrativeEvent (voir _narrative_event_zone).
    events = [
        replace(e, zone=_narrative_event_zone(e.gabarit, i), assist_zone=_narrative_event_assist_zone(e.gabarit, i))
        for i, e in enumerate(events)
    ]

    match_id = f"{match.home_team}-{match.away_team}-{match.date}"
    return Timeline(
        match_id=match_id, seed=seed,
        home_team=match.home_team, away_team=match.away_team,
        home_goals=match.home_goals, away_goals=match.away_goals,
        home_rating=match.home_lineup.rating, away_rating=match.away_lineup.rating,
        competition_type=match.competition_type,
        home_lineup=match.home_lineup, away_lineup=match.away_lineup,
        cards=match.cards, substitutions=match.substitutions,
        events=events,
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
