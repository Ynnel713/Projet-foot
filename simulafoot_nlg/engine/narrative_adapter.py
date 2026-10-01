"""Decide du scenario de commentaire d'un evenement valide : (event_type, gabarit, outcome) -> code.

`event_to_scenario` est l'UNIQUE decideur du `scenario_code` (decision D12) : ni le contrat des dicts
(event_contract), ni les adaptateurs de la racine (event_adapters) ne le choisissent.

FAITS DE LA RACINE (engine/narrative.py, templates.py, verifies le 01/10/2026) :
  - `event_type` du NarrativeEvent : "but" ou "occasion" ; cartons et remplacements viennent d'ailleurs.
  - Les 12 gabarits, dont `corner` et `coup_franc`, apparaissent sur des BUTS ET sur des OCCASIONS
    (hors `penalty`, reserve aux penaltys : un but, ou une occasion ratee dont l'outcome est arret,
    poteau, hors_cadre ou barre).
  - outcome d'une occasion : arret, hors_cadre, tacle, degagement, poteau (+ barre pour un penalty).

REGLES, par ordre de priorite :
  1. outcome `poteau` ou `barre`            -> None : aucun pilote ne sait commenter un contact avec le
     montant ou la barre (les textes de TIR_NON_CADRE decrivent un tir a cote ou au-dessus). Evenement
     NON COMMENTE en V2.1 (v2.2 : scenario dedie). Vaut aussi pour un penalty.
  2. occasion, outcome `arret`              -> ARRET_GARDIEN, quel que soit le gabarit (penalty compris :
     le gardien est l'acteur, voir event_contract).
  3. occasion de gabarit `penalty`          -> PENALTY_RATE (outcome hors_cadre).
  4. occasion, `hors_cadre`                 -> TIR_NON_CADRE ; `tacle` / `degagement` -> DEFENSE.
  5. but de gabarit coup_franc / construction_placee / corner -> COUP_FRANC / CONSTRUCTION / CORNER ;
     tout autre but (dont `penalty`, qui active la variante PENALTY de BUT par condition de gabarit) -> BUT.
  6. carton `yellow` -> CARTON_JAUNE ; `direct` / `second_yellow` -> CARTON_ROUGE ; remplacement -> REMPLACEMENT.

LIMITE CONNUE (a valider au titre de D12) : (but, corner) -> CORNER : le pool CORNER (30 phrases)
melange des corners reussis et des corners rates (une douzaine de phrases decrivent un corner sans
but), et aucune condition d'outcome n'existe : un but sur corner peut recevoir un texte de corner rate.

Un scenario IMPORTE qui n'est atteint par aucune regle est declare, avec sa raison, dans
SCENARIOS_STRUCTURELS ou SCENARIOS_DIFFERES (un test verrouille l'union avec la banque importee).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: Outcomes sans commentaire en V2.1 (voir regle 1).
OUTCOMES_NON_COMMENTES = frozenset({"poteau", "barre"})

_BUT_PAR_GABARIT = {
    "coup_franc": "COUP_FRANC",
    "construction_placee": "CONSTRUCTION",
    "corner": "CORNER",
}
_OCCASION_PAR_OUTCOME = {
    "hors_cadre": "TIR_NON_CADRE",
    "tacle": "DEFENSE",
    "degagement": "DEFENSE",
}
_CARTON_PAR_OUTCOME = {
    "yellow": "CARTON_JAUNE",
    "direct": "CARTON_ROUGE",
    "second_yellow": "CARTON_ROUGE",
}

#: Scenarios que `event_to_scenario` peut renvoyer (verrouille par un test qui enumere tout le domaine).
SCENARIOS_ATTEIGNABLES = frozenset(
    {
        "BUT", "COUP_FRANC", "CONSTRUCTION", "CORNER",
        "ARRET_GARDIEN", "PENALTY_RATE", "TIR_NON_CADRE", "DEFENSE",
        "CARTON_JAUNE", "CARTON_ROUGE", "REMPLACEMENT",
    }
)  # fmt: skip

#: STRUCTUREL : par nature pas lie a un evenement de match discret (contexte, trait de joueur) -- aucune
#: source n'est a attendre de la racine. Chaque entree : raison ; revue : jamais (conception).
SCENARIOS_STRUCTURELS: dict[str, str] = {
    "DEBUT_MATCH": "commentaire d'avant-match (contexte), pas un evenement du moteur",
    "SITUATION_MATCH": "commentaire de tendance du match (contexte), pas un evenement discret",
    "GESTE_SIGNATURE": "trait de joueur conditionne par preferred_moves, pas un evenement du moteur",
}

#: DIFFERE : evenements de match reels mais SANS source dans narrative.py ni MatchEvents (D13) ; pilotes
#: importes mais non branches. Revue en V2.2 (une source cote racine suffirait a les debloquer).
SCENARIOS_DIFFERES: dict[str, str] = {
    "FAUTE_SIMPLE": "D13 : aucune source d'evenement (V2.2) ; 8 phrases a reecrire ({adversaire} = personne)",
    "HORS_JEU": "D13 : aucune source d'evenement (V2.2)",
    "AMBIANCE": "D13 : aucune source d'evenement (V2.2)",
}


def event_to_scenario(event: Mapping[str, Any]) -> str | None:
    """Code du scenario de commentaire de `event` (un dict deja valide par event_contract), ou None si
    l'evenement n'est pas commente en V2.1 (outcome `poteau` / `barre`). Leve ValueError pour un
    `event_type` inconnu ou une combinaison hors du domaine du moteur (ex. penalty + tacle)."""
    type_evenement = event.get("event_type")
    if type_evenement == "carton":
        if event["outcome"] not in _CARTON_PAR_OUTCOME:
            raise ValueError(f"Carton hors domaine : outcome {event['outcome']!r}.")
        return _CARTON_PAR_OUTCOME[event["outcome"]]
    if type_evenement == "remplacement":
        return "REMPLACEMENT"
    if type_evenement == "but":
        return _BUT_PAR_GABARIT.get(event["gabarit"], "BUT")
    if type_evenement == "occasion":
        outcome, gabarit = event["outcome"], event["gabarit"]
        if outcome in OUTCOMES_NON_COMMENTES:
            return None
        if outcome == "arret":
            return "ARRET_GARDIEN"
        if gabarit == "penalty":
            if outcome != "hors_cadre":
                raise ValueError(f"Occasion hors domaine : gabarit penalty avec outcome {outcome!r}.")
            return "PENALTY_RATE"
        if outcome not in _OCCASION_PAR_OUTCOME:
            raise ValueError(f"Occasion hors domaine : outcome {outcome!r}.")
        return _OCCASION_PAR_OUTCOME[outcome]
    raise ValueError(f"event_type inconnu : {type_evenement!r}.")
