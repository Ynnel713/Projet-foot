"""engine/selectivity.py : couverture des phrases sur les joueurs de champ et facteur de ciblage (poids du tirage)."""

from __future__ import annotations

import pytest

import engine.selectivity as module
from engine.models import Phrase, PhraseCondition, Player
from engine.selectivity import Selectivite, charger_population_champ


def _population(n: int = 10) -> list[Player]:
    """n joueurs dont Pace vaut 1..n (Pace >= k est satisfait par n - k + 1 joueurs)."""
    return [Player(id=i, first_name="J", last_name=str(i), attributes={"Pace": i, "Strength": 100 - i}) for i in range(1, n + 1)]


def _cond(attribute: str, operator: str, value: str, mandatory: bool = True) -> PhraseCondition:
    return PhraseCondition(id=1, phrase_id=1, attribute=attribute, operator=operator, value=value, mandatory=mandatory)


def _phrase(*conditions: PhraseCondition, identifiant: int = 1) -> Phrase:
    return Phrase(id=identifiant, variant_id=1, text="x", conditions=conditions)


class TestFacteurCiblage:
    @pytest.mark.parametrize(
        ("seuil_pace", "couverture", "facteur"),
        [
            (11, 0.0, 1.0),  # ne matche personne : discriminante
            (9, 0.2, 1.0),  # 20 % : borne incluse, discriminante
            (8, 0.3, 0.4),  # 30 % : borne incluse, large
            (1, 1.0, 0.4),
        ],
    )
    def test_bornes_de_la_couverture(self, seuil_pace, couverture, facteur):
        phrase = _phrase(_cond("Pace", ">=", str(seuil_pace)))
        selectivite = Selectivite(_population(10))
        assert selectivite.couverture(phrase) == pytest.approx(couverture)
        assert selectivite.facteur_ciblage(phrase) == pytest.approx(facteur)

    def test_entre_20_et_30_pour_cent_le_facteur_est_lineaire(self):
        # 25 joueurs sur 100 : mi-chemin entre 1.0 (20 %) et 0.4 (30 %)
        phrase = _phrase(_cond("Pace", ">=", "76"))
        assert Selectivite(_population(100)).facteur_ciblage(phrase) == pytest.approx(0.7)

    def test_le_facteur_decroit_avec_la_couverture(self):
        selectivite = Selectivite(_population(100))
        facteurs = [selectivite.facteur_ciblage(_phrase(_cond("Pace", ">=", str(seuil)))) for seuil in (90, 80, 77, 76, 75, 50)]
        assert facteurs == sorted(facteurs, reverse=True)

    def test_phrase_sans_condition_joueur_n_est_pas_ponderee(self):
        selectivite = Selectivite(_population())
        assert selectivite.couverture(_phrase()) is None
        assert selectivite.facteur_ciblage(_phrase()) == 1.0

    def test_les_conditions_de_contexte_ne_comptent_pas(self):
        phrase = _phrase(_cond("minute", ">=", "85"), _cond("score_context", "==", '"egalisation"'), _cond("gabarit", "==", '"penalty"'))
        selectivite = Selectivite(_population())
        assert selectivite.couverture(phrase) is None
        assert selectivite.facteur_ciblage(phrase) == 1.0

    def test_condition_de_contexte_et_condition_joueur_seule_la_derniere_compte(self):
        phrase = _phrase(_cond("minute", ">=", "85"), _cond("Pace", ">=", "8"))
        assert Selectivite(_population()).couverture(phrase) == pytest.approx(0.3)

    def test_les_conditions_joueur_s_intersectent(self):
        # Pace >= 4 : 7 joueurs (4..10) ; Strength >= 93 : Strength = 100 - i >= 93 -> i <= 7 (7 joueurs).
        # Chacune vise 70 % ; l'intersection (i dans 4..7) vise 40 %.
        phrase = _phrase(_cond("Pace", ">=", "4"), _cond("Strength", ">=", "93"))
        assert Selectivite(_population()).couverture(phrase) == pytest.approx(0.4)

    def test_une_condition_non_mandatory_n_est_pas_un_ciblage(self):
        phrase = _phrase(_cond("Pace", ">=", "1", mandatory=False))
        assert Selectivite(_population()).facteur_ciblage(phrase) == 1.0

    def test_un_attribut_absent_chez_certains_joueurs_ne_les_compte_pas(self):
        population = _population(10) + [Player(id=99, first_name="X", last_name="Sans attributs")]
        phrase = _phrase(_cond("Pace", ">=", "1"))
        assert Selectivite(population).couverture(phrase) == pytest.approx(10 / 11)


class TestCacheEnMemoire:
    def test_la_couverture_est_calculee_une_seule_fois_par_phrase(self, monkeypatch):
        appels = []
        original = module.evaluate_condition

        def espion(condition, joueur, contexte):
            appels.append(joueur.id)
            return original(condition, joueur, contexte)

        monkeypatch.setattr(module, "evaluate_condition", espion)
        selectivite = Selectivite(_population(10))
        phrase = _phrase(_cond("Pace", ">=", "4"))
        selectivite.facteur_ciblage(phrase)
        selectivite.couverture(phrase)
        selectivite.facteur_ciblage(phrase)
        assert len(appels) == 10  # une evaluation par joueur, une seule fois

    def test_une_population_vide_est_refusee(self):
        with pytest.raises(ValueError, match="vide"):
            Selectivite([])

    def test_taille_de_la_population(self):
        assert Selectivite(_population(7)).taille_population == 7


class TestPopulationDeReference:
    def test_depuis_la_base_les_gardiens_sont_exclus_et_les_attributs_attaches(self, sqlite_conn):
        sqlite_conn.executemany(
            "INSERT INTO players (id, first_name, last_name, position) VALUES (?, ?, ?, ?)",
            [(1, "A", "Gardien", "GK"), (2, "B", "Defenseur", "DC"), (3, "C", "Attaquant", "BU"), (4, "D", "Sans poste", None)],
        )
        sqlite_conn.executemany(
            "INSERT INTO player_attributes (player_id, attribute, category, value) VALUES (?, ?, ?, ?)",
            [(1, "Pace", "physique", 40), (2, "Pace", "physique", 60), (3, "Pace", "physique", 90)],
        )
        sqlite_conn.commit()

        population = charger_population_champ(sqlite_conn)

        assert [p.id for p in population] == [2, 3, 4]  # le gardien (id 1) est exclu, le joueur sans poste reste
        assert population[0].attributes == {"Pace": 60}
        assert population[2].attributes == {}
        selectivite = Selectivite.depuis_base(sqlite_conn)
        assert selectivite.taille_population == 3
        # Pace >= 50 : joueurs 2 et 3 sur 3 -> 66,7 % : condition large.
        phrase = _phrase(_cond("Pace", ">=", "50"))
        assert selectivite.couverture(phrase) == pytest.approx(2 / 3)
        assert selectivite.facteur_ciblage(phrase) == pytest.approx(0.4)
