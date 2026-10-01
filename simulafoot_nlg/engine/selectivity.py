"""Selectivite des phrases (decisions D9, D9-pop, B2) : combien de joueurs une phrase vise-t-elle ?

Une phrase est SPECIFIQUE si elle a au moins une condition JOUEUR et que l'ensemble de ses
conditions joueur (intersection) est satisfait par au plus 70 % de la population de reference
(`SEUIL_SPECIFIQUE`, decision B2 : au-dela, une condition large -- ex. `Aggression >= 45`, 80 % --
ne distingue personne et alpha n'apporte rien). Toute autre phrase est GENERIQUE : aucune
condition joueur, ou conditions trop larges. Seules les conditions JOUEUR comptent (champ Player,
attribut FM26, preferred_moves) ; les conditions de contexte (minute, score_context, is_home,
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

#: Une phrase est specifique si sa couverture est <= 70 % de la population (bornes incluses).
SEUIL_SPECIFIQUE_POURCENT = 70


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

    def est_specifique(self, phrase: Phrase) -> bool:
        """Au moins une condition joueur ET couverture <= 70 % (comparaison en entiers : pas
        d'arrondi flottant a la frontiere)."""
        comptes = self._comptes(phrase)
        return comptes is not None and comptes[0] * 100 <= SEUIL_SPECIFIQUE_POURCENT * comptes[1]
