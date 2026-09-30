"""SQUELETTE -- selection d'une Phrase pour un (scenario, joueur, contexte)
donnes. Aucune implementation dans cette session (voir contrainte du brief :
"ne jamais generer de phrase dans cette session").

Algorithme prevu (une fois la banque livree) :
    1. scenario_engine.load_scenario(code) -- 404 explicite si absent.
    2. scenario_engine.load_variants(scenario.id), ne garder que is_active=1 ;
       si aucune variante specifique ne "matche" mieux le contexte (logique
       de matching a definir avec la banque), retomber sur celle(s)
       is_default=1.
    3. Pour chaque variante candidate, scenario_engine.load_phrases(variant.id).
    4. Filtrer les phrases dont une condition `mandatory=True` echoue (voir
       PhraseCondition) -- ECARTEES, pas depriorisees.
    5. Pour chaque phrase restante, verifier phrase_cooldowns : PAS de ligne
       ou cooldown_matches NULL -> phrase REFUSEE (contrainte explicite du
       brief : "cooldown obligatoire"). Puis anti_repeat.recency_penalty +
       anti_repeat.similarity_penalty pondèrent le candidat (poids reduit,
       pas forcement exclu, sauf cooldown strictement non ecoule).
    6. Tirage pondere (poids variante x poids phrase x penalites) parmi les
       candidats restants, avec `rng` injectable pour la reproductibilite
       des tests (voir tests/test_phrase_selector.py : "tirage reproductible
       avec seed").
    7. 0 candidat apres filtrage -> fallback explicite (a definir : phrase
       generique de secours, ou exception dediee -- pas un texte invente a
       la volee).
"""

from __future__ import annotations

import random
from sqlite3 import Connection

from engine.models import MatchContext, Phrase, Player


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
