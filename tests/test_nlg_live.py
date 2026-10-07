"""api/nlg_live.py : fil live raconte par le NLG (marquage des noms, repli si le NLG est indisponible)."""

import pytest
from ligue1sim.events import GoalEvent, MatchEvents
from ligue1sim.schedule import Match

import api.nlg_live as nlg_live
import api.serializers as serializers


def test_marquer_joueurs_noms_les_plus_longs_d_abord_sans_casse():
    parts = nlg_live._marquer_joueurs("Kylian Mbappé sert Mbappé Junior, puis kylian mbappé conclut.", {"Kylian Mbappé", "Mbappé Junior"})
    assert [p for p, est_joueur in parts if est_joueur] == ["Kylian Mbappé", "Mbappé Junior", "kylian mbappé"]
    assert "".join(t for t, _ in parts) == "Kylian Mbappé sert Mbappé Junior, puis kylian mbappé conclut."


def test_marquer_joueurs_sans_nom_un_seul_morceau():
    assert nlg_live._marquer_joueurs("Le mitrailleur tire de partout !", set()) == (("Le mitrailleur tire de partout !", False),)
    assert nlg_live._marquer_joueurs("Texte", {None, ""}) == (("Texte", False),)


def test_venv_du_nlg_absent_leve_nlg_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(nlg_live, "NLG_DIR", tmp_path)
    with pytest.raises(nlg_live.NlgUnavailable, match="venv du NLG"):
        nlg_live._nlg_python()


def test_le_fil_retombe_sur_les_gabarits_si_le_nlg_echoue(monkeypatch):
    def echec(*args, **kwargs):
        raise nlg_live.NlgUnavailable("pas de venv")

    monkeypatch.setattr(serializers, "generate_nlg_feed", echec)
    events = MatchEvents(
        home_formation="4-4-2", away_formation="4-3-3", home_lineup=[], away_lineup=[],
        goals=[GoalEvent(club_name="Nice", scorer="G. Laborde", assist=None, minute=23)],
    )
    match = Match(home="Le Mans", away="Nice", home_goals=0, away_goals=1, events=events)
    feed = serializers._live_feed(match, None, None, "j1")
    assert [e.kind for e in feed] == ["start", "goal", "end"]


class TestCompleterProtagonistes:
    @staticmethod
    def _texte(parts):
        return "".join(t for t, _ in parts)

    def test_arret_sans_tireur_dans_le_texte_ajoute_le_tireur(self):
        parts = nlg_live._marquer_joueurs("Sur cette frappe enroulée, Lukas Hradecky s'envole !", {"Lukas Hradecky", "Folarin Balogun"})
        out = nlg_live.completer_protagonistes("save", parts, "Lukas Hradecky", tireur="Folarin Balogun")
        assert self._texte(out) == "Sur cette frappe enroulée, Lukas Hradecky s'envole ! Frappe de Folarin Balogun."
        assert [t for t, est in out if est] == ["Lukas Hradecky", "Folarin Balogun"]

    def test_phrase_a_surnom_recoit_le_nom_de_l_acteur_en_tete(self):
        out = nlg_live.completer_protagonistes("shot_off", (("Le mitrailleur tire de partout !", False),), "Clément Akpa")
        assert self._texte(out) == "Clément Akpa — Le mitrailleur tire de partout !" and out[0] == ("Clément Akpa", True)

    def test_un_nom_deja_present_n_est_pas_repete(self):
        parts = nlg_live._marquer_joueurs("Kévin Danois frappe !", {"Kévin Danois"})
        assert nlg_live.completer_protagonistes("shot_off", parts, "Kévin Danois") == parts

    def test_defense_et_remplacement(self):
        d = nlg_live.completer_protagonistes("defense", (("Il dégage.", False),), "Défenseur X", tireur="Attaquant Y")
        assert self._texte(d).endswith("Tir de Attaquant Y.") and self._texte(d).startswith("Il dégage.")
        s = nlg_live.completer_protagonistes("sub", (("La pépite fait son entrée pour Z.", False),), "Entrant E", entrant="Entrant E")
        assert self._texte(s) == "La pépite fait son entrée pour Z. Entrant : Entrant E."

    def test_sans_nom_connu_le_texte_est_inchange(self):
        parts = (("Texte.", False),)
        assert nlg_live.completer_protagonistes("save", parts, None, tireur=None) == parts
