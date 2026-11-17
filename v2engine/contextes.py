"""Registre des contextes d'attributs (ADR 0002, ticket v2-attributs-contextes/01).

Un **contexte** est une situation de jeu qui combine plusieurs attributs avec des poids sommant à 1 ; il appartient à
un temps du cerveau (perception, décision, exécution, ADR 0001). Les poids sont des constantes produit, validées par le
propriétaire, et ne s'écrivent qu'ici : un module du moteur qui veut une note composée appelle
`contextual_rating(joueur, CONTEXTE)`, qui lit chaque note par la façade `condition.effective_rating` (règle R6 : la
condition du joueur s'applique une fois, partout). Chaque contexte est documenté dans la section « Contextes » de
`docs/CARTE_ATTRIBUTS_V2.md`.

Au ticket 01, le registre reprend à l'identique les deux cumuls existants (mêmes poids, mêmes valeurs, mêmes empreintes
à graine fixée). Les cumuls d'une autre forme restent hors du registre, listés dans la carte : ballon dur à orienter
(First Touch x Technique, un produit, A17), temps d'arrivée Pace + Acceleration (capacités en secondes, R5), note du
gardien (A8, jusqu'au ticket v2-attributs-restants/03b).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType

from v2engine.condition import effective_rating

PERCEPTION, DECISION, EXECUTION = "perception", "décision", "exécution"
TEMPS = (PERCEPTION, DECISION, EXECUTION)


@dataclass(frozen=True)
class Contexte:
    """Situation de jeu : nom, temps du cerveau, (attribut, poids) dans l'ordre de calcul, ticket qui l'a branchée, et
    effet calculé, identifié par la fonction qui le porte (« module.fonction ») : un effet n'a qu'un contexte (R1)."""

    nom: str
    temps: str
    poids: tuple[tuple[str, float], ...]
    ticket: str
    effet: str

    def __post_init__(self) -> None:
        if self.temps not in TEMPS:
            raise ValueError(f"contexte {self.nom!r} : temps inconnu {self.temps!r}")
        attributes = [attribute for attribute, _ in self.poids]
        if len(attributes) < 2 or len(set(attributes)) != len(attributes):
            raise ValueError(f"contexte {self.nom!r} : au moins deux attributs, chacun une fois")
        if any(weight <= 0.0 for _, weight in self.poids) or not math.isclose(sum(w for _, w in self.poids), 1.0):
            raise ValueError(f"contexte {self.nom!r} : poids positifs sommant à 1")

    @property
    def attributs(self) -> tuple[str, ...]:
        return tuple(attribute for attribute, _ in self.poids)


# Porteur tête haute (ticket v2-realisme/08c, A15) : plus il est à l'aise balle au pied, moins il regarde le ballon,
# donc plus il peut scanner (`scan.head_up_share`). Poids validés le 13/11/2026 ; source : non trouvé.
PORTEUR_TETE_HAUTE = Contexte("porteur tête haute", PERCEPTION, (("Dribbling", 0.6), ("Technique", 0.4)),
                              "v2-realisme/08c", "scan.head_up_share")
# Idée de jouer de première (ticket v2-collectif/31a, A16) : le receveur y pense d'autant plus qu'il a le contrôle et la
# technique du geste (`decision.one_touch_idea_probability`). Moyenne validée le 13/11/2026 ; source : non trouvé.
IDEE_DE_PREMIERE = Contexte("idée de jouer de première", DECISION, (("First Touch", 0.5), ("Technique", 0.5)),
                            "v2-collectif/31a", "decision.one_touch_idea_probability")

# Lecture du pressing (ticket v2-collectif/15b1) : en construction sous pressing, le porteur lit la structure du
# pressing et repère un coéquipier libre derrière la première ligne, accessible par une remise (troisième homme)
# (`decision.reads_third_man_probability`). Poids validés le 17/11/2026 ; source : non trouvé.
LECTURE_DU_PRESSING = Contexte("lecture du pressing", PERCEPTION,
                               (("Vision", 0.5), ("Anticipation", 0.3), ("Decisions", 0.2)), "v2-collectif/15b1",
                               "decision.reads_third_man_probability")

# Repli après la perte (ticket v2-attributs-contextes/03, réduit le 17/11/2026) : devant le ballon à la perte, le
# joueur revient dans le bloc d'autant plus vite qu'il a l'envie de l'effort (Work Rate) et la discipline de reprendre
# sa place (Teamwork) (`defense.retreat_intensity`, courbe du presseur inchangée). Poids validés le 17/11/2026 ;
# source : non trouvé.
REPLI_APRES_LA_PERTE = Contexte("repli après la perte", DECISION, (("Work Rate", 0.7), ("Teamwork", 0.3)),
                                "v2-attributs-contextes/03", "defense.retreat_intensity")

# Lecture seule : un contexte ne s'ajoute qu'ici, par une déclaration revue (réserve A1 de l'expert, ticket 01).
CONTEXTES = MappingProxyType({c.nom: c for c in (PORTEUR_TETE_HAUTE, IDEE_DE_PREMIERE, LECTURE_DU_PRESSING,
                                                  REPLI_APRES_LA_PERTE)})


def contextual_rating(player, contexte: Contexte | str) -> float:
    """Note composée de `player` dans `contexte` (objet du registre ou son nom) : somme pondérée des notes exprimées,
    lues par la façade. Bornée par construction entre la plus basse et la plus haute des notes lues."""
    if isinstance(contexte, str):
        contexte = CONTEXTES[contexte]
    note = 0.0
    for attribute, weight in contexte.poids:
        note += weight * effective_rating(player, attribute)
    return note
