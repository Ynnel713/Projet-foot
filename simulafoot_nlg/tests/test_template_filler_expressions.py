"""Mini-interpreteur d'expressions de slot (template_filler.resolve_expression)."""

from __future__ import annotations

import pytest

from engine.models import MatchContext, Player
from engine.template_filler import SlotResolutionError, resolve_expression


def _joueur(prenom: str = "Kylian", nom: str = "Mbappé") -> Player:
    return Player(id=1, first_name=prenom, last_name=nom, age=26)


def _contexte(**surcharges) -> MatchContext:
    base = dict(
        match_id="m1",
        minute=67,
        home_team="Lyon",
        away_team="Marseille",
        is_home=True,
        player_team="Lyon",
        passeur=_joueur("Alexandre", "Lacazette"),
    )
    base.update(surcharges)
    return MatchContext(**base)


@pytest.mark.parametrize(
    ("expression", "attendu"),
    [
        ("player.full_name", "Kylian Mbappé"),  # property
        ("context.opponent_team", "Marseille"),  # property derivee
        ("context.passeur.full_name", "Alexandre Lacazette"),  # chemin a trois segments
        ("player.last_name", "Mbappé"),  # champ de dataclass
        ("context.player_team", "Lyon"),
        ("context.minute", "67"),  # int -> texte
        ("player.age", "26"),
    ],
)
def test_resolution_des_chemins_d_attributs(expression, attendu):
    assert resolve_expression(expression, _joueur(), _contexte()) == attendu


def test_un_nom_a_apostrophe_est_rendu_tel_quel():
    assert resolve_expression("player.full_name", _joueur("Jake", "O'Brien"), _contexte()) == "Jake O'Brien"


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "player",  # pas de segment
        "joueur.full_name",  # racine inconnue
        "Player.full_name",  # casse
        "player..full_name",
        "player.full_name.",
        "player.full_name()",  # appel
        "player.__class__",  # attribut prive
        "player._x",
        "player.full_name + 'x'",  # operateur
        "player.full_name ",  # espace
        "__import__('os')",
        "player.first_name[0]",  # indexation
        "player.1",
    ],
)
def test_une_expression_hors_grammaire_est_refusee(expression):
    with pytest.raises(SlotResolutionError, match="invalide"):
        resolve_expression(expression, _joueur(), _contexte())


def test_une_expression_non_textuelle_est_refusee():
    with pytest.raises(SlotResolutionError, match="invalide"):
        resolve_expression(None, _joueur(), _contexte())  # type: ignore[arg-type]


def test_un_attribut_inexistant_est_refuse_en_nommant_le_chemin():
    with pytest.raises(SlotResolutionError, match=r"player\.nope|'nope'"):
        resolve_expression("player.nope", _joueur(), _contexte())
    with pytest.raises(SlotResolutionError, match="passeur"):
        resolve_expression("context.passeur.nope", _joueur(), _contexte())


def test_une_methode_n_est_jamais_appelee():
    with pytest.raises(SlotResolutionError, match="methode"):
        resolve_expression("player.full_name.title", _joueur(), _contexte())
    with pytest.raises(SlotResolutionError, match="methode"):
        resolve_expression("context.opponent_team.upper", _joueur(), _contexte())


@pytest.mark.parametrize(
    ("expression", "contexte"),
    [
        ("context.passeur.full_name", _contexte(passeur=None)),  # intermediaire absent
        ("context.receveur.full_name", _contexte()),
        ("player.nationality", _contexte()),  # feuille absente
        ("context.opponent_team", _contexte(home_team=None)),  # property qui vaut None
    ],
)
def test_une_valeur_absente_n_est_jamais_rendue_en_none(expression, contexte):
    with pytest.raises(SlotResolutionError, match="None|absente"):
        resolve_expression(expression, _joueur(), contexte)
