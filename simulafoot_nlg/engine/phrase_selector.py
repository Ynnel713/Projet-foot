"""Selection d'une Phrase pour un (scenario, joueur, contexte) donnes.

Algorithme de `select` (decisions D1, D9, D10, revisees le 02/10/2026 ; SPEC_ANTI_REPEAT.md sections 6 et 10) :

    1. Le scenario est charge (KeyError s'il est inconnu) ; ses variantes ACTIVES sont reparties en
       variantes de CONTEXTE (ni DEFAUT ni SURNOM : PENALTY...), ordonnees par poids decroissant puis `id`,
       et variantes d'ATTRIBUT (DEFAUT et SURNOM).
    2. Les variantes de contexte gardent leur priorite : la premiere qui produit un candidat sert (un but sur
       penalty se raconte avec une phrase de penalty, pas avec un generique tire au sort).
    3. Sinon, UN tirage pondere sur l'ensemble des candidats de DEFAUT et de SURNOM (plus de priorite dure
       SURNOM > DEFAUT, ni specifique > generique : elles servaient le meme modele a tout joueur remplissant
       une condition large). Pour chaque variante :
         a. conditions : les phrases dont une condition `mandatory` echoue sont ECARTEES (jamais
            deprioritisees) ; les phrases de secours (`is_fallback`) et inactives ne sont jamais dans
            le pool normal ;
         b. cooldown JOUEUR : une phrase dont le cooldown n'est pas ecoule pour ce joueur (recency_penalty,
            EN MATCHS) est ecartee ; une phrase sans cooldown est refusee. Jamais relache ;
         c. rendu : chaque candidat est rendu (template_filler.render puis post_process.apply) ; un candidat
            dont un slot ne se resout pas (SlotResolutionError) est ecarte ;
         d. poids = poids de la variante x poids de la phrase x `POIDS_SURNOM` (0.35 pour la variante SURNOM)
            x `Selectivite.facteur_ciblage` (1.0 discriminante <= 20 %, 0.4 large >= 30 %) x (1 - similarite
            du texte rendu, meme joueur) x (1 - recency_penalty_global) : une phrase deja servie dans le match
            pour N'IMPORTE quel joueur a un poids nul, puis penalise 3 matchs (anti_repeat).
       Le rng est derive de `seed` (explicite, jamais d'horloge). Si tous les poids sont nuls, le cooldown
       global est relache (le pool epuise par la seule memoire inter-joueurs retombe sur les poids de base,
       DEFAUT en tete) ; si ce n'est pas encore assez, tirage uniforme : une penalite ne vide jamais le pool.
    4. Cascade epuisee (aucun candidat dans aucune variante) : repli final sur la phrase de secours du
       scenario (D10), rendue comme les autres ; UN seul WARNING enrichi (scenario, variantes ecartees,
       repli) signale que le scenario est sous-alimente. Pas de phrase de secours en base : le meme WARNING,
       puis AucunCandidatError.

`select` retourne SelectionResult(phrase, rendered_text) (D11) et ne fait AUCUNE ecriture : l'enregistrement de l'usage est anti_repeat.update_cooldown, appele
par l'appelant (jamais pour une phrase de secours, que log_usage refuse).
"""

from __future__ import annotations

import logging
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Any

from engine.anti_repeat import CooldownManquantError, recency_penalty, recency_penalty_global, similarity_penalty
from engine.conditions import evaluate_condition
from engine.models import MatchContext, Phrase, Player, SelectionResult, Variant
from engine.post_process import apply
from engine.profile_engine import validate_match_sequence
from engine.scenario_engine import load_phrases, load_scenario, load_variants
from engine.selectivity import Selectivite
from engine.template_filler import SlotResolutionError, derive_rng, render

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Rendu:
    """Un candidat rendu : sa phrase, son texte final, son poids de base et sa penalite inter-joueurs."""

    phrase: Phrase
    texte: str
    poids: float
    penalite_globale: float


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


#: Poids de la variante SURNOM face a DEFAUT (1.0) : un modele a surnom reste possible sans dominer.
POIDS_SURNOM = 0.35
CODE_SURNOM = "SURNOM"


def _est_de_contexte(variante: Variant) -> bool:
    """Variante ni DEFAUT ni SURNOM (PENALTY...) : elle se declenche sur le contexte, elle garde sa priorite."""
    return not variante.is_default and variante.code != CODE_SURNOM


def variantes_de_contexte(variantes: Sequence[Variant]) -> list[Variant]:
    """Variantes de contexte ACTIVES, par poids decroissant puis `id` croissant (deterministe)."""
    return sorted((v for v in variantes if v.is_active and _est_de_contexte(v)), key=lambda v: (-v.weight, v.id))


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


def _rendre(
    conn: Connection,
    pool: Sequence[Phrase],
    variante: Variant,
    scenario_code: str,
    player: Player,
    context: MatchContext,
    selectivite: Selectivite,
    *,
    seed: int | str,
    match_sequence: int,
    dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None,
) -> list[_Rendu]:
    """Un `_Rendu` par candidat de `pool` (par `id` croissant) ; un candidat dont un slot ne se resout pas est ecarte."""
    rendus = []
    for phrase in sorted(pool, key=lambda p: p.id):
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
        poids = variante.weight * phrase.weight * selectivite.facteur_ciblage(phrase) * (1.0 - penalite)
        if variante.code == CODE_SURNOM:
            poids *= POIDS_SURNOM
        rendus.append(_Rendu(phrase, texte, poids, recency_penalty_global(conn, phrase, match_sequence=match_sequence)))
    return rendus


def _tirer(rendus: Sequence[_Rendu], rng: random.Random) -> SelectionResult:
    """Tirage pondere. Poids = poids de base x (1 - penalite globale) ; tous nuls : la memoire inter-joueurs est
    relachee (poids de base) ; encore tous nuls : tirage uniforme."""
    poids = [r.poids * (1.0 - r.penalite_globale) for r in rendus]
    if not any(poids):
        poids = [r.poids for r in rendus]
    choix = rng.choices(rendus, weights=poids if any(poids) else None, k=1)[0]
    return SelectionResult(choix.phrase, choix.texte)


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
    actives = sorted((v for v in variantes if v.is_active), key=lambda v: v.id)

    def rendre(variante: Variant) -> list[_Rendu]:
        pool = _hors_cooldown(conn, candidats(load_phrases(conn, variante.id), player, context), player, match_sequence)
        return _rendre(
            conn, pool, variante, scenario_code, player, context, selectivite,
            seed=seed, match_sequence=match_sequence, dictionaries=dictionaries,
        )

    for variante in variantes_de_contexte(variantes):
        rendus = rendre(variante)
        if rendus:
            return _tirer(rendus, derive_rng(seed, scenario_code, variante.code, "select"))
    rendus = [r for v in actives if not _est_de_contexte(v) for r in rendre(v)]
    if rendus:
        return _tirer(rendus, derive_rng(seed, scenario_code, "POOL", "select"))
    ecartees = actives

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
