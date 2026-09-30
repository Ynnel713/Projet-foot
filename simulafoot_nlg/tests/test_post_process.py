"""post_process.apply est un SQUELETTE (voir engine/post_process.py) --
même raisonnement que test_phrase_selector.py : les 4 cas du brief (élision,
majuscule, ponctuation, double espace) décrivent l'algorithme FUTUR. Seul le
contrat "échoue explicitement" est vérifié ici, un test par cas pour que
l'implémentation future les remplace un par un sans devoir redécouvrir la
liste."""

from __future__ import annotations

import pytest

from engine.post_process import apply


def test_apply_raises_not_implemented_error_on_plain_text():
    with pytest.raises(NotImplementedError):
        apply("quelle frappe")


def test_apply_raises_not_implemented_error_on_elision_case():
    # Futur : "le Ailier" -> "l'Ailier"
    with pytest.raises(NotImplementedError):
        apply("le Ailier a marqué")


def test_apply_raises_not_implemented_error_on_capitalisation_case():
    # Futur : "mbappé marque" -> "Mbappé marque"
    with pytest.raises(NotImplementedError):
        apply("mbappé marque")


def test_apply_raises_not_implemented_error_on_punctuation_case():
    # Futur : "Quel but !." -> "Quel but !"
    with pytest.raises(NotImplementedError):
        apply("Quel but !.")


def test_apply_raises_not_implemented_error_on_double_space_case():
    # Futur : "Quel  but" -> "Quel but"
    with pytest.raises(NotImplementedError):
        apply("Quel  but")
