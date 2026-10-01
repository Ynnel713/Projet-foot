"""Selectivite des phrases (decisions D9, D9-pop, B2, revisees le 02/10/2026) : combien de joueurs une phrase vise-t-elle ?

La couverture d'une phrase est la part de la population de reference qui satisfait l'ensemble de ses conditions
JOUEUR (champ Player, attribut FM26, preferred_moves). Elle sert a PONDERER le tirage (`facteur_ciblage`), non plus
a ranger les phrases en deux paliers durs (specifique avant generique, ancien seuil 70 %) : une condition large
(`fm_rating >= 80` seul, `Flair >= 75`) servie en priorite a tout joueur qui la remplit repetait le meme modele
pour la moitie des changements ou des cartons. Les conditions de contexte (minute, score_context, is_home,
gabarit...) varient d'un evenement a l'autre, elles se jugent a l'execution, pas ici.

Population de reference : les JOUEURS DE CHAMP (`position != "GK"`, D9-pop), la meme que
scripts/audit_conditions_pilote.py. Cache MEMOIRE (D9) : la population est chargee UNE fois, a la
construction (au demarrage de l'application), et la couverture de chaque phrase est memoisee a son
premier calcul. Aucune invalidation a chaud : modifier les joueurs ou la banque prend effet au
redemarrage.
"""

from __future__ import annotations

from collections.abc import Sequence
from sqlite3 import Connection

from engine.conditions import MATCH_CONTEXT_FIELDS, evaluate_condition
from engine.models import MatchContext, Phrase, Player
from engine.profile_engine import normalize_player

#: Ciblage : une phrase dont les conditions joueur couvrent <= 20 % de la population est DISCRIMINANTE (poids 1.0) ;
#: au-dela de 30 % elle est LARGE (poids 0.4) ; entre les deux, interpolation lineaire. Sans condition joueur : 1.0.
COUVERTURE_DISCRIMINANTE = 0.20
COUVERTURE_LARGE = 0.30
POIDS_CIBLAGE_LARGE = 0.4


def charger_population_champ(conn: Connection) -> list[Player]:
    """Les joueurs de champ de la base (tous sauf `position == "GK"`), attributs FM26 attaches."""
    attributs: dict[int, dict[str, int]] = {}
    for ligne in conn.execute("SELECT player_id, attribute, value FROM player_attributes"):
        attributs.setdefault(ligne[0], {})[ligne[1]] = ligne[2]
    joueurs = []
    for ligne in conn.execute("SELECT * FROM players WHERE position IS NULL OR position != 'GK' ORDER BY id"):
        brut = dict(ligne)
        brut["attributes"] = attributs.get(brut["id"], {})
        joueurs.append(normalize_player(brut))
    return joueurs


class Selectivite:
    """Couverture memoisee des phrases sur une population de reference (voir module)."""

    def __init__(self, population: Sequence[Player]) -> None:
        if not population:
            raise ValueError("Selectivite : population de reference vide (couverture indefinie).")
        self._population = tuple(population)
        self._contexte_vide = MatchContext(match_id="selectivite")
        self._memo: dict[int, tuple[int, int] | None] = {}

    @classmethod
    def depuis_base(cls, conn: Connection) -> Selectivite:
        """Construit le cache depuis la base : population = joueurs de champ (D9-pop)."""
        return cls(charger_population_champ(conn))

    @property
    def taille_population(self) -> int:
        return len(self._population)

    def _comptes(self, phrase: Phrase) -> tuple[int, int] | None:
        """(joueurs satisfaisant TOUTES les conditions joueur de la phrase, population), ou None si
        la phrase n'a aucune condition joueur. Memoise par `phrase.id`."""
        if phrase.id in self._memo:
            return self._memo[phrase.id]
        conditions = [c for c in phrase.conditions if c.mandatory and c.attribute not in MATCH_CONTEXT_FIELDS]
        resultat: tuple[int, int] | None = None
        if conditions:
            satisfaits = sum(
                all(evaluate_condition(c, joueur, self._contexte_vide) for c in conditions)
                for joueur in self._population
            )
            resultat = (satisfaits, len(self._population))
        self._memo[phrase.id] = resultat
        return resultat

    def couverture(self, phrase: Phrase) -> float | None:
        """Part [0, 1] de la population qui satisfait les conditions joueur de `phrase` ; None si elle
        n'en a pas (phrase sans ciblage joueur)."""
        comptes = self._comptes(phrase)
        return None if comptes is None else comptes[0] / comptes[1]

    def facteur_ciblage(self, phrase: Phrase) -> float:
        """Facteur de poids [`POIDS_CIBLAGE_LARGE`, 1.0] selon la couverture : 1.0 sans condition joueur ou a
        couverture <= `COUVERTURE_DISCRIMINANTE` ; `POIDS_CIBLAGE_LARGE` a couverture >= `COUVERTURE_LARGE` ;
        lineaire entre les deux."""
        couverture = self.couverture(phrase)
        if couverture is None or couverture <= COUVERTURE_DISCRIMINANTE:
            return 1.0
        if couverture >= COUVERTURE_LARGE:
            return POIDS_CIBLAGE_LARGE
        part = (couverture - COUVERTURE_DISCRIMINANTE) / (COUVERTURE_LARGE - COUVERTURE_DISCRIMINANTE)
        return 1.0 - part * (1.0 - POIDS_CIBLAGE_LARGE)
