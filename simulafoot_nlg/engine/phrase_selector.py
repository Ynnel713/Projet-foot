"""Selection d'une Phrase pour un (scenario, joueur, contexte) donnes.

Algorithme de `select` (decisions D1, alpha, D9, D10 ; SPEC_ANTI_REPEAT.md sections 6 et 10) :

    1. Le scenario est charge (KeyError s'il est inconnu) ; ses variantes ACTIVES sont ordonnees :
       les non-defaut (SURNOM, PENALTY...) par poids decroissant puis `id` croissant, puis la variante
       `is_default` en dernier. C'est l'ordre NORMAL (un DEFAUT essaye d'abord n'aurait presque jamais
       0 candidat et les SURNOM ne sortiraient jamais).
    2. Pour CHAQUE variante, UNE fois (garde-fou anti-boucle), dans cet ordre :
         a. conditions : les phrases dont une condition `mandatory` echoue sont ECARTEES (jamais
            deprioritisees) ; les phrases de secours (`is_fallback`) et inactives ne sont jamais dans
            le pool normal ;
         b. cooldown : une phrase dont le cooldown n'est pas ecoule pour ce joueur (recency_penalty,
            EN MATCHS) est ecartee ; une phrase sans cooldown est refusee. Le cooldown n'est JAMAIS
            relache ni contourne par la cascade ;
         c. alpha : palier SPECIFIQUE d'abord (au moins une condition joueur, <= 70 % des joueurs de
            champ), sinon palier GENERIQUE -- c'est aussi le "repli cooldown" : si tous les specifiques
            sont en cooldown, les generiques servent au lieu de bloquer ;
         d. rendu : chaque candidat du palier est rendu (template_filler.render puis
            post_process.apply) ; un candidat dont un slot ne se resout pas (SlotResolutionError) est
            ecarte ("phrase invalide, en choisir une autre") ;
         e. tirage pondere : poids de la variante x poids de la phrase x (1 - similarity_penalty du
            texte rendu) ; si tous les poids sont nuls, tirage uniforme (une penalite ne vide jamais le
            palier) ; rng derive de `seed` (explicite, jamais d'horloge).
       La premiere variante qui produit un candidat sert ; aucune fusion de variantes.
    3. Cascade epuisee (toutes les variantes actives a sec, jusqu'a la variante par defaut) : repli
       final sur la phrase de secours du scenario (D10), rendue comme les autres ; UN seul WARNING
       enrichi (scenario, variantes ecartees, repli) signale que le scenario est sous-alimente. Pas de
       phrase de secours en base : le meme WARNING, puis AucunCandidatError. Aucun log pour le passage
       normal SURNOM -> DEFAUT.

`select` retourne SelectionResult(phrase, rendered_text) (D11) et ne fait AUCUNE ecriture : l'enregistrement de l'usage est anti_repeat.update_cooldown, appele
par l'appelant (jamais pour une phrase de secours, que log_usage refuse).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from sqlite3 import Connection
from typing import Any

from engine.anti_repeat import CooldownManquantError, recency_penalty, similarity_penalty
from engine.conditions import evaluate_condition
from engine.models import MatchContext, Phrase, Player, SelectionResult, Variant
from engine.post_process import apply
from engine.profile_engine import validate_match_sequence
from engine.scenario_engine import load_phrases, load_scenario, load_variants
from engine.selectivity import Selectivite
from engine.template_filler import SlotResolutionError, derive_rng, render

logger = logging.getLogger(__name__)


class AucunCandidatError(LookupError):
    """Aucune phrase disponible pour ce scenario : toutes les variantes actives sont a sec et le
    scenario n'a pas de phrase de secours."""


def candidats(phrases: Sequence[Phrase], player: Player, context: MatchContext) -> list[Phrase]:
    """Phrases d'un pool qui PEUVENT sortir pour (`player`, `context`) : actives, hors phrases de
    secours (`is_fallback` : jamais dans le pool normal, decision D10 -- elles ne sortent que par le
    repli final) et dont TOUTES les conditions `mandatory` sont satisfaites (une condition qui
    echoue ECARTE la phrase, elle ne la deprioritise pas). Les conditions non `mandatory` ne filtrent
    pas. Une condition invalide (nom inconnu) leve ValueError : jamais ecartee en silence.
    L'ordre du pool est conserve."""
    return [
        phrase
        for phrase in phrases
        if phrase.is_active
        and not phrase.is_fallback
        and all(evaluate_condition(c, player, context) for c in phrase.conditions if c.mandatory)
    ]


def paliers(pool: Sequence[Phrase], selectivite: Selectivite) -> tuple[list[Phrase], list[Phrase]]:
    """(specifiques, generiques) : partition du pool selon la selectivite (<= 70 % des joueurs de
    champ et au moins une condition joueur : specifique, voir engine/selectivity.py). Politique alpha :
    `select` tente les specifiques, puis les generiques seulement si aucun specifique ne sort."""
    specifiques = [p for p in pool if selectivite.est_specifique(p)]
    generiques = [p for p in pool if not selectivite.est_specifique(p)]
    return specifiques, generiques


def ordonner_variantes(variantes: Sequence[Variant]) -> list[Variant]:
    """Ordre d'essai de la cascade (decision D1) : variantes ACTIVES seulement, les non-defaut
    d'abord par poids decroissant puis `id` croissant (deterministe), puis la variante `is_default`."""
    actives = [v for v in variantes if v.is_active]
    return sorted(actives, key=lambda v: (v.is_default, -v.weight, v.id))


def _hors_cooldown(conn: Connection, pool: Sequence[Phrase], player: Player, match_sequence: int) -> list[Phrase]:
    """Phrases dont le cooldown est ecoule pour `player` ; une phrase sans cooldown est refusee
    (regle "cooldown obligatoire") avec un WARNING (l'import l'interdit : donnees incoherentes)."""
    retenues = []
    for phrase in pool:
        try:
            if recency_penalty(conn, phrase, player, match_sequence=match_sequence) == 0.0:
                retenues.append(phrase)
        except CooldownManquantError:
            logger.warning("Phrase %s refusee : aucun cooldown defini (phrase_cooldowns).", phrase.id)
    return retenues


def _rendre_palier(
    conn: Connection,
    palier: Sequence[Phrase],
    variante: Variant,
    scenario_code: str,
    player: Player,
    context: MatchContext,
    *,
    seed: int | str,
    match_sequence: int,
    dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None,
) -> list[tuple[Phrase, str, float]]:
    """(phrase, texte rendu, poids) pour chaque candidat du palier, par `id` croissant ; un candidat
    dont un slot ne se resout pas est ecarte. poids = poids variante x phrase x (1 - similarite)."""
    rendus = []
    for phrase in sorted(palier, key=lambda p: p.id):
        try:
            brut = render(
                phrase,
                player,
                context,
                seed=seed,
                scenario_code=scenario_code,
                variant_code=variante.code,
                dictionaries=dictionaries,
            )
        except SlotResolutionError as exc:
            logger.debug("Phrase %s ecartee : %s", phrase.id, exc)
            continue
        texte = apply(brut)
        penalite = similarity_penalty(conn, texte, player, match_sequence=match_sequence)
        rendus.append((phrase, texte, variante.weight * phrase.weight * (1.0 - penalite)))
    return rendus


def _phrase_de_secours(
    conn: Connection, variantes: Sequence[Variant]
) -> tuple[Phrase, Variant] | None:
    """La phrase de secours du scenario (D10), portee par sa variante par defaut."""
    for variante in variantes:
        if variante.is_default:
            for phrase in load_phrases(conn, variante.id):
                if phrase.is_fallback:
                    return phrase, variante
    return None


def select(
    conn: Connection,
    scenario_code: str,
    player: Player,
    context: MatchContext,
    *,
    seed: int | str,
    match_sequence: int,
    selectivite: Selectivite,
    dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> SelectionResult:
    """Selectionne UNE phrase et la rend : `SelectionResult(phrase, rendered_text)` (D11 ; voir
    l'algorithme en tete de module). `rendered_text` est le texte final (slots resolus, puis
    post_process.apply), celui a afficher et a enregistrer par update_cooldown -- sauf pour une phrase
    de secours (`phrase.is_fallback`), que log_usage refuse.

    `seed` et `match_sequence` sont OBLIGATOIRES et par mot-cle : la graine rend tout le tirage et
    tout le rendu reproductibles ; `match_sequence` (rang du match, None refuse sans repli) est
    l'unite du cooldown et de la fenetre de similarite. Leve KeyError si le scenario est inconnu,
    AucunCandidatError si le scenario est a sec ET sans phrase de secours."""
    match_sequence = validate_match_sequence(match_sequence)
    scenario = load_scenario(conn, scenario_code)
    if scenario is None:
        raise KeyError(f"Scenario inconnu : {scenario_code!r}")

    variantes = load_variants(conn, scenario.id)
    ecartees: list[Variant] = []
    for variante in ordonner_variantes(variantes):
        pool = _hors_cooldown(conn, candidats(load_phrases(conn, variante.id), player, context), player, match_sequence)
        for palier in paliers(pool, selectivite):
            rendus = _rendre_palier(
                conn, palier, variante, scenario_code, player, context,
                seed=seed, match_sequence=match_sequence, dictionaries=dictionaries,
            )
            if not rendus:
                continue
            poids = [p for _, _, p in rendus]
            rng = derive_rng(seed, scenario_code, variante.code, "select")
            choix = rng.choices(rendus, weights=poids if any(poids) else None, k=1)[0]
            return SelectionResult(choix[0], choix[1])
        ecartees.append(variante)

    secours = _phrase_de_secours(conn, variantes)
    if secours is None:
        _signaler_scenario_a_sec(scenario_code, ecartees, repli="aucun")
        raise AucunCandidatError(f"Scenario {scenario_code!r} : aucune phrase disponible, ni phrase de secours.")
    phrase, variante = secours
    _signaler_scenario_a_sec(scenario_code, ecartees, repli=f"phrase de secours #{phrase.id} ({variante.code})")
    brut = render(
        phrase, player, context, seed=seed, scenario_code=scenario_code, variant_code=variante.code, dictionaries=dictionaries
    )
    return SelectionResult(phrase, apply(brut))


def _signaler_scenario_a_sec(scenario_code: str, ecartees: Sequence[Variant], *, repli: str) -> None:
    """WARNING UNIQUE et enrichi (D10-warn), emis quand la cascade entiere -- jusqu'a la variante par
    defaut -- n'a produit aucun candidat : le scenario est sous-alimente (c'est le signal qui dira si
    l'enrichissement des donnees joueur a fait son effet). Contient le code du scenario, les variantes
    ecartees (code et id) et le repli retenu."""
    logger.warning(
        "Scenario %s a sec : variantes ecartees = [%s] ; repli = %s",
        scenario_code,
        ", ".join(f"{v.code}#{v.id}" for v in ecartees) or "aucune",
        repli,
    )
