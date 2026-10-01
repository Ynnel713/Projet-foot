"""SQUELETTE -- selection d'une Phrase pour un (scenario, joueur, contexte)
donnes. Aucune implementation dans cette session (voir contrainte du brief :
"ne jamais generer de phrase dans cette session").

Algorithme prevu (une fois la banque livree) :
    1. scenario_engine.load_scenario(code) -- 404 explicite si absent.
    2. scenario_engine.load_variants(scenario.id), ne garder que is_active=1,
       puis ORDONNER les variantes (decision D1 du 01/10/2026, SPEC_ANTI_REPEAT.md
       section 6) : les variantes NON par defaut (SURNOM, etc.) d'abord, triees
       par weight decroissant (ties -> variant.id croissant, deterministe), puis
       la variante is_default en dernier. Une phrase SURNOM dont la condition
       matche PRIME sur toute phrase DEFAUT ; sinon on retombe sur DEFAUT.
       (Ordre inverse -- DEFAUT d'abord, SURNOM si DEFAUT n'a aucun candidat --
       rejete : avec des phrases sans condition en repli, DEFAUT n'a jamais 0
       candidat et les SURNOM ne sortiraient jamais.)
    3. Pour chaque variante candidate, scenario_engine.load_phrases(variant.id).
    4. Filtrer les phrases dont une condition `mandatory=True` echoue (voir
       PhraseCondition) -- ECARTEES, pas depriorisees.
    5. Pour chaque phrase restante, verifier phrase_cooldowns : PAS de ligne
       ou cooldown_matches NULL -> phrase REFUSEE (contrainte explicite du
       brief : "cooldown obligatoire"). Puis anti_repeat.recency_penalty +
       anti_repeat.similarity_penalty pondèrent le candidat (poids reduit,
       pas forcement exclu, sauf cooldown strictement non ecoule).
    6. POLITIQUE ALPHA (decision du 01/10/2026, SPEC_ANTI_REPEAT.md sections
       6 et 9) puis tirage pondere :
         a. Partitionner les candidats restants (etapes 4 et 5) en
            SPECIFIQUES -- au moins une condition joueur, de selectivite
            <= 70 % des joueurs de champ (meme critere que la regle de
            domination) -- et GENERIQUES (sans condition joueur, ou condition
            plus large que 70 %). La selectivite est mesuree hors ligne
            (scripts/audit_conditions_pilote.py) ; comment la rendre
            disponible a l'execution (colonne, calcul a l'import) reste a
            trancher a l'implementation.
         b. Au moins un candidat specifique : le tirage se fait UNIQUEMENT
            parmi les specifiques. Les generiques sont un REPLI : retenus
            seulement quand aucun specifique n'est eligible (conditions non
            satisfaites, ou cooldown non ecoule -- le repli sur cooldown
            epuise remplace un blocage).
         c. Tirage pondere (poids variante x poids phrase x penalites) dans
            le palier retenu, avec `rng` injectable pour la reproductibilite
            des tests (voir tests/test_phrase_selector.py : "tirage
            reproductible avec seed").
       (Ce palier remplace le tirage uniforme parmi TOUTES les candidates, qui
       etait l'option beta, ecartee.)
    7. CASCADE DE VARIANTES SI 0 CANDIDAT -- c'est l'ordre NORMAL d'essai de
       l'etape 2 (SURNOM -> DEFAUT), pas un repli exceptionnel : la plupart des
       evenements n'ont aucun SURNOM eligible et sont servis par DEFAUT
       (decision du 01/10/2026, voir
       AUDIT_COUVERTURE_DONNEES_JOUEUR.md -- garde-fou sain pour les
       scenarios a faible densite de donnees joueur, ex. GESTE_SIGNATURE
       conditionne a 86% de ses phrases sur preferred_moves, renseigne a
       ~5-90% des joueurs selon l'etat de l'enrichissement en cours) :
         a. Si l'etape 4 (ou le cooldown de l'etape 5) ecarte TOUTES les
            phrases de la variante courante (0 survivante), NE PAS s'arreter
            la : essayer la variante SUIVANTE de l'ordre de l'etape 2, une
            seule fois chacune :
              i.  les variantes non-is_default, triees par weight
                  decroissant (ties -> variant.id croissant, deterministe) ;
              ii. la variante is_default en dernier recours.
         b. Chaque variante de la cascade repasse par les etapes 4 et 5
            A L'IDENTIQUE (conditions mandatory + cooldown obligatoire ne
            sont jamais contournes par le fallback -- la cascade change de
            POOL de phrases, jamais les regles qui les filtrent).
         c. Des qu'une variante de la cascade produit >= 1 candidat, on
            s'arrete la (etape 6 sur ce pool) -- pas de fusion de plusieurs
            variantes en un seul tirage.
         d. GARDE-FOU anti-boucle : chaque variante active du scenario est
            tentee au plus une fois par appel a `select` -- la cascade est
            bornee par le nombre de variantes, jamais un retry illimite.
         e. LOGGING obligatoire, mais PAS pour le passage normal SURNOM ->
            DEFAUT (il inonderait les logs) : niveau WARNING uniquement quand
            la variante is_default elle-meme rend 0 candidat (le scenario est
            sous-alimente), avec au minimum scenario_code, variant_id
            ecarte(s), variant_id de repli retenu (ou absence totale si meme
            la cascade echoue).
            Objectif explicite : rendre OBSERVABLE en production qu'un
            scenario est en train de "mourir" sur sa variante principale
            faute de donnee joueur -- c'est ce signal qui dira si
            l'enrichissement preferred_moves (cible 90%, voir
            ENRICHISSEMENT_PREFERRED_MOVES.md) a fait son effet, sans
            attendre un nouvel audit manuel.
       Seulement si la cascade entiere (etape 7.a-d) n'a produit 0
       candidat sur AUCUNE variante active -> fallback final explicite
       (toujours a definir : phrase generique de secours au niveau du
       SCENARIO, ou exception dediee -- pas un texte invente a la volee).
       Ce dernier cas doit rester rarissime une fois la cascade en place ;
       s'il se repete, c'est le signal que le scenario entier (toutes
       variantes confondues) est sous-alimente, pas juste une variante.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from sqlite3 import Connection

from engine.conditions import evaluate_condition
from engine.models import MatchContext, Phrase, Player
from engine.selectivity import Selectivite


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
    champ et au moins une condition joueur : specifique, voir engine/selectivity.py)."""
    specifiques = [p for p in pool if selectivite.est_specifique(p)]
    generiques = [p for p in pool if not selectivite.est_specifique(p)]
    return specifiques, generiques


def palier_retenu(pool: Sequence[Phrase], selectivite: Selectivite) -> list[Phrase]:
    """Politique alpha (decision du 01/10/2026) : s'il y a au moins un candidat SPECIFIQUE, le tirage
    se fait UNIQUEMENT parmi les specifiques ; les generiques sont un REPLI, retenus seulement quand
    aucun specifique n'est eligible (aucun ne satisfait ses conditions, ou -- le pool etant deja
    filtre par le cooldown -- tous sont en cooldown : le repli sur cooldown epuise remplace un
    blocage). Pool vide -> liste vide."""
    specifiques, generiques = paliers(pool, selectivite)
    return specifiques or generiques


def select(
    conn: Connection,
    scenario_code: str,
    player: Player,
    context: MatchContext,
    *,
    rng: random.Random | None = None,
) -> Phrase:
    """Selectionne UNE Phrase pour `player` dans le contexte `context`, pour
    le scenario `scenario_code`. `rng` : generateur injectable (defaut :
    `random.Random()` global) pour des tirages reproductibles en test.

    Leve NotImplementedError tant que la banque de phrases n'est pas livree
    -- voir l'algorithme prevu ci-dessus en tete de module."""
    raise NotImplementedError(
        "phrase_selector.select : squelette non implémenté -- en attente de la "
        "banque de phrases (voir data/seed/scenarios.yml). Algorithme prévu : "
        "docstring de engine/phrase_selector.py."
    )
