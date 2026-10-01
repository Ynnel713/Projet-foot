"""engine/selectivity.py : couverture des phrases sur les joueurs de champ, seuil de 70 % (B2)."""

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


class TestSeuilDe70Pourcent:
    @pytest.mark.parametrize(
        ("seuil_pace", "couverture", "specifique"),
        [
            (4, 0.7, True),  # 7 joueurs sur 10 : exactement 70 % -> specifique (borne incluse)
            (3, 0.8, False),  # 8 sur 10 : 80 % -> trop large
            (8, 0.3, True),
            (11, 0.0, True),  # ne matche personne : "specifique" (la rarete est l'affaire de l'audit)
        ],
    )
    def test_frontiere_a_70_pour_cent(self, seuil_pace, couverture, specifique):
        phrase = _phrase(_cond("Pace", ">=", str(seuil_pace)))
        selectivite = Selectivite(_population(10))
        assert selectivite.couverture(phrase) == pytest.approx(couverture)
        assert selectivite.est_specifique(phrase) is specifique

    def test_la_frontiere_se_juge_en_entiers_sans_arrondi_flottant(self):
        # 21 joueurs sur 30 = 70 % exactement (21/30 pourrait s'ecrire 0.7000000000000001 selon le calcul).
        phrase = _phrase(_cond("Pace", ">=", "10"))
        selectivite = Selectivite(_population(30))  # Pace >= 10 : 21 joueurs
        assert selectivite.est_specifique(phrase) is True

    def test_phrase_sans_condition_est_generique(self):
        selectivite = Selectivite(_population())
        assert selectivite.couverture(_phrase()) is None
        assert selectivite.est_specifique(_phrase()) is False

    def test_les_conditions_de_contexte_ne_comptent_pas(self):
        phrase = _phrase(_cond("minute", ">=", "85"), _cond("score_context", "==", '"egalisation"'), _cond("gabarit", "==", '"penalty"'))
        selectivite = Selectivite(_population())
        assert selectivite.couverture(phrase) is None
        assert selectivite.est_specifique(phrase) is False

    def test_condition_de_contexte_et_condition_joueur_seule_la_derniere_compte(self):
        phrase = _phrase(_cond("minute", ">=", "85"), _cond("Pace", ">=", "8"))
        assert Selectivite(_population()).couverture(phrase) == pytest.approx(0.3)

    def test_les_conditions_joueur_s_intersectent(self):
        # Pace >= 4 : 7 joueurs (4..10) ; Strength >= 93 : Strength = 100 - i >= 93 -> i <= 7 (7 joueurs).
        # Chacune vise 70 % ; l'intersection (i dans 4..7) vise 40 %.
        phrase = _phrase(_cond("Pace", ">=", "4"), _cond("Strength", ">=", "93"))
        assert Selectivite(_population()).couverture(phrase) == pytest.approx(0.4)

    def test_une_condition_non_mandatory_n_est_pas_un_ciblage(self):
        phrase = _phrase(_cond("Pace", ">=", "8", mandatory=False))
        assert Selectivite(_population()).est_specifique(phrase) is False

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
        selectivite.est_specifique(phrase)
        selectivite.couverture(phrase)
        selectivite.est_specifique(phrase)
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
        # Pace >= 50 : joueurs 2 et 3 sur 3 -> 66,7 % : specifique.
        phrase = _phrase(_cond("Pace", ">=", "50"))
        assert selectivite.couverture(phrase) == pytest.approx(2 / 3)
        assert selectivite.est_specifique(phrase) is True
