"""Garde-fous PERMANENTS sur tous les pilotes V2 (pilotes_v2/*.py). La liste
des pilotes est decouverte automatiquement : un nouveau scenario (CARTON_JAUNE,
Tier 2...) est couvert des qu'il est ajoute, sans toucher a ce fichier.

Plafond de collisions de 4 mots : 2 par pilote. CORNER en porte 2 reelles,
acceptees comme vocabulaire naturel ("le gardien de {adversaire}", "tout le
monde et") ; tout autre pilote est a 0. Une 3e collision fait echouer le test
au lieu d'etre acceptee par habitude."""

from __future__ import annotations

import importlib
import pkgutil
import re
from collections import defaultdict
from types import ModuleType

import pytest

import pilotes_v2

PLAFOND_COLLISIONS_4_MOTS = 2


def _pilotes() -> list[ModuleType]:
    return [
        importlib.import_module(f"pilotes_v2.{info.name}")
        for info in pkgutil.iter_modules(pilotes_v2.__path__)
    ]


def _collisions_de_quatre_mots(phrases: list[str]) -> dict[str, list[int]]:
    positions: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for numero, texte in enumerate(phrases, 1):
        mots = re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))
        for debut in range(len(mots) - 3):
            positions[tuple(mots[debut:debut + 4])].append(numero)
    return {" ".join(g): n for g, n in positions.items() if len(n) > 1}


def test_les_pilotes_sont_bien_decouverts():
    noms = {m.__name__.rsplit(".", 1)[-1] for m in _pilotes()}
    assert {"defense", "faute_simple", "corner", "tir_non_cadre", "remplacement"} <= noms


@pytest.mark.parametrize("pilote", _pilotes(), ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_collisions_de_quatre_mots_sous_le_plafond(pilote):
    phrases = [texte for texte, _ in pilote.DEFAUT + pilote.SURNOM]
    collisions = _collisions_de_quatre_mots(phrases)
    assert len(collisions) <= PLAFOND_COLLISIONS_4_MOTS, collisions


def test_le_detecteur_voit_une_collision_et_ignore_les_phrases_distinctes():
    deux_phrases_jumelles = ["Il frappe de toute sa force !", "Soudain il frappe de toute sa rage !"]
    collisions = _collisions_de_quatre_mots(deux_phrases_jumelles)
    assert collisions["frappe de toute sa"] == [1, 2]
    assert collisions["il frappe de toute"] == [1, 2]
    assert len(collisions) == 2
    assert _collisions_de_quatre_mots(["Il frappe fort !", "Elle cadre à ras de terre !"]) == {}


@pytest.mark.parametrize("pilote", _pilotes(), ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_chaque_attribut_conditionne_est_resolvable_par_l_evaluateur(pilote):
    """Un attribut hors PLAYER_FIELDS / MATCH_CONTEXT_FIELDS / FM26 / preferred_moves
    leve ValueError dans engine.conditions._resolve a l'execution (cas reel :
    fm_rating avant le 01/10/2026). Ce test l'attrape a l'ecriture du pilote."""
    from engine.conditions import NOMS_CONDITIONNABLES

    resolvables = NOMS_CONDITIONNABLES
    for texte, conditions in pilote.DEFAUT + pilote.SURNOM:
        for attribut, _, _ in conditions:
            assert attribut in resolvables, (attribut, texte)


@pytest.fixture(scope="module")
def base_joueurs():
    from scripts.audit_conditions_pilote import BASE, charger_joueurs

    if not BASE.exists():
        pytest.skip("base locale absente")
    return charger_joueurs()


@pytest.mark.parametrize("pilote", _pilotes(), ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_regle_universelle_au_plus_deux_phrases_au_dessus_de_70_pourcent(pilote, base_joueurs):
    """Regle du 01/10/2026 : l'alerte de domination se declenche a 3 phrases
    dont la selectivite (joueurs de champ) depasse 70 %. FAUTE_SIMPLE en a 2
    (#15 a 75,6 %, #16 a 74,8 % -- minute ignoree par l'outil, donc sur-estimee)."""
    from scripts.audit_conditions_pilote import MAX_TRES_DOMINANTES, audit as audit_jouabilite

    rapport = audit_jouabilite(pilote.__name__, pilote.DEFAUT + pilote.SURNOM, base_joueurs)
    assert len(rapport["tres_dominantes"]) <= MAX_TRES_DOMINANTES, rapport["tres_dominantes"]


POOL_MOYEN_MIN = 2.5
PART_POOL_FAIBLE_MAX = 0.10  # joueurs dont le pool < 3 phrases


@pytest.mark.parametrize("pilote", _pilotes(), ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_prerequis_alpha_pool_par_joueur_dimensionne(pilote, base_joueurs):
    """Prerequis de l'option alpha (SPEC_ANTI_REPEAT.md, section 6) : un joueur de champ
    doit disposer en moyenne d'au moins 2,5 phrases DEFAUT (conditions matchees + repli
    sans condition), et moins de 10 % des joueurs d'un pool < 3. DEFENSE (74 % de
    joueurs sans phrase specifique) et CORNER (72 %) ont ete portes a 5 et 8 phrases
    sans condition le 01/10/2026 pour passer ce test."""
    from scripts.audit_conditions_pilote import pool_par_joueur

    pools = pool_par_joueur(pilote.DEFAUT, base_joueurs)
    assert sum(pools) / len(pools) >= POOL_MOYEN_MIN
    assert sum(p < 3 for p in pools) / len(pools) <= PART_POOL_FAIBLE_MAX
