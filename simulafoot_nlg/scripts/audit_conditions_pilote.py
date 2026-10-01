"""Audit de JOUABILITE des conditions d'un pilote V2 contre la vraie base
joueurs (data/simulafoot.db). Module reutilisable, PAS un module moteur.

Pourquoi : un pilote bien ecrit peut etre injouable (condition qui ne matche
presque personne : "fantome") ou dominante (condition qui matche la moitie
de la base : elle ecrase le tirage). GESTE_SIGNATURE l'a montre (32 SURNOM/
DEFAUT sur 37 injouables sur 95 % des joueurs).

Regles d'evaluation (miroir simplifie de engine/conditions.py) :
    - attribut FM26 (Finishing, Pace...) : table player_attributes ;
    - colonne joueur (age, fm_rating, height_cm, preferred_moves...) : players ;
    - "minute" / "score_context" : contexte de match, pas une propriete du
      joueur -> la condition est ignoree (la phrase est mesuree sur ses
      seules conditions joueur) et signalee ;
    - valeur absente (None) => la condition echoue (pas de faux match) ;
    - "contient" : sous-chaine dans preferred_moves ;
    - "in" : appartenance a une liste separee par des virgules (position).
Population de reference : joueurs de champ (hors GK) ET base complete.

Deux mesures a ne JAMAIS confondre (table `table_attributs`) :
    - COUVERTURE : part des joueurs ayant une valeur non NULL pour l'attribut
      (ex. Aggression 93,0 %) -- dit si l'attribut est exploitable ;
    - SELECTIVITE DU SEUIL : part des joueurs de champ qui MATCHENT la
      condition reellement utilisee (ex. Aggression >= 60 : 57 %) -- dit
      combien la condition filtre. Un attribut couvert a 93 % avec un seuil
      qui matche 57 % ne "concerne pas tous les joueurs" : il en filtre 43 %.

Usage : uv run python -m scripts.audit_conditions_pilote tir_non_cadre
        uv run python -m scripts.audit_conditions_pilote --attributs
"""

from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"
SEUIL_DOMINANCE = 0.50  # a signaler (information)
# REGLE UNIVERSELLE (decision du 01/10/2026) : alerte quand 3 phrases d'un pilote
# depassent 70 % des joueurs de champ (donc tolere : 2). Sous 70 %, une phrase
# qui matche la moitie des joueurs est un signal, pas un defaut -- la
# distribution compte plus que le compte (FAUTE_SIMPLE : 12 phrases a 50-76 %,
# aucune a 80 %+, 2 entre 70 et 80 %).
SEUIL_TRES_DOMINANTE = 0.70
MAX_TRES_DOMINANTES = 2
SEUIL_FANTOME = 20
CHAMPS_CONTEXTE = {"minute", "score_context", "score_diff", "is_home"}
COLONNES_JOUEUR = {"age", "fm_rating", "height_cm", "weak_foot", "average_rating", "preferred_moves", "foot", "position"}

Condition = tuple[str, str, str]


def charger_joueurs(chemin: Path = BASE) -> list[dict]:
    """Un dict par joueur : colonnes players + attributs FM26 a plat."""
    with sqlite3.connect(chemin) as conn:
        conn.row_factory = sqlite3.Row
        joueurs = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM players")}
        for ligne in conn.execute("SELECT player_id, attribute, value FROM player_attributes"):
            joueurs[ligne["player_id"]][ligne["attribute"]] = ligne["value"]
    return list(joueurs.values())


def _valeur(joueur: dict, attribut: str) -> Optional[object]:
    return joueur.get(attribut)


def condition_vraie(joueur: dict, condition: Condition) -> bool:
    attribut, operateur, valeur = condition
    observee = _valeur(joueur, attribut)
    if observee is None:
        return False
    if operateur == "contient":
        return valeur.lower() in str(observee).lower()
    if operateur == "in":
        # Meme semantique que engine.conditions : comparaison texte, valeurs
        # separees par des virgules (ex. position in [BU, AG] -> "BU, AG").
        return str(observee) in [v.strip().strip('"') for v in valeur.split(",")]
    seuil = float(valeur)
    return observee >= seuil if operateur == ">=" else observee <= seuil


def joueurs_matchant(joueurs: list[dict], conditions: list[Condition]) -> list[dict]:
    conditions_joueur = [c for c in conditions if c[0] not in CHAMPS_CONTEXTE]
    return [j for j in joueurs if all(condition_vraie(j, c) for c in conditions_joueur)]


def audit(nom_pilote: str, phrases: list[tuple[str, list[Condition]]], joueurs: list[dict]) -> dict:
    """Imprime le rapport et retourne les listes de phrases a retravailler."""
    champ = [j for j in joueurs if j.get("position") != "GK"]
    dominantes, tres_dominantes, fantomes = [], [], []
    print(f"=== {nom_pilote} : {len(phrases)} phrases, base {len(joueurs)} joueurs ({len(champ)} de champ) ===")
    for i, (texte, conditions) in enumerate(phrases, 1):
        matchs_base = joueurs_matchant(joueurs, conditions)
        matchs_champ = joueurs_matchant(champ, conditions)
        part = len(matchs_champ) / len(champ)
        contexte = [c[0] for c in conditions if c[0] in CHAMPS_CONTEXTE]
        drapeau = ""
        conditions_joueur = [c for c in conditions if c[0] not in CHAMPS_CONTEXTE]
        if conditions_joueur and part > SEUIL_DOMINANCE:
            # Une phrase dont les SEULES conditions sont contextuelles (minute)
            # matche 100 % des joueurs par construction : ce n'est pas une
            # dominance joueur, elle est donc exclue de ce drapeau.
            dominantes.append(i)
            if part > SEUIL_TRES_DOMINANTE:
                tres_dominantes.append(i)
            drapeau = "  << DOMINANTE"
        if conditions_joueur and len(matchs_base) < SEUIL_FANTOME:
            fantomes.append(i)
            drapeau = "  << FANTOME"
        resume = ", ".join(f"{a} {o} {v}" for a, o, v in conditions) or "(aucune)"
        note = f" [+contexte {contexte}]" if contexte else ""
        print(f"#{i:>2} base={len(matchs_base):>4} champ={part:6.1%}  {resume}{note}{drapeau}")
    print(f"dominantes (>{SEUIL_DOMINANCE:.0%} des joueurs de champ) : {dominantes}")
    print(f"tres dominantes (>{SEUIL_TRES_DOMINANTE:.0%}, alerte a {MAX_TRES_DOMINANTES + 1}) : {tres_dominantes}")
    print(f"fantomes (<{SEUIL_FANTOME} joueurs) : {fantomes}")
    sans_condition = [i for i, (_, c) in enumerate(phrases, 1) if not c]
    print(f"sans condition (matchent 100 %) : {len(sans_condition)} phrases")
    return {
        "dominantes": dominantes,
        "tres_dominantes": tres_dominantes,
        "fantomes": fantomes,
        "sans_condition": sans_condition,
    }


def pool_par_joueur(phrases_defaut: list[tuple[str, list[Condition]]], joueurs: list[dict]) -> list[int]:
    """Nombre de phrases DEFAUT utilisables par chaque joueur de champ : phrases a
    conditions joueur qui matchent + phrases sans condition joueur (le repli alpha).
    Les conditions de contexte (minute, is_home) sont ignorees : elles dependent de
    l'evenement, pas du joueur. Sert au dimensionnement (SPEC_ANTI_REPEAT.md, section 6)."""
    champ = [j for j in joueurs if j.get("position") != "GK"]
    resultat = []
    for joueur in champ:
        utilisables = 0
        for _, conditions in phrases_defaut:
            conditions_joueur = [c for c in conditions if c[0] not in CHAMPS_CONTEXTE]
            if all(condition_vraie(joueur, c) for c in conditions_joueur):
                utilisables += 1
        resultat.append(utilisables)
    return resultat


def detail_surnoms(nom: str, phrases: list[tuple[str, list[Condition]]], joueurs: list[dict], echantillon: int = 5) -> None:
    """Pour chaque SURNOM : effectif, clubs les plus representes, echantillon."""
    print(f"=== {nom} : detail des SURNOM ===")
    for i, (texte, conditions) in enumerate(phrases, 1):
        matchs = joueurs_matchant(joueurs, conditions)
        clubs: dict[str, int] = {}
        for j in matchs:
            clubs[j.get("club") or "?"] = clubs.get(j.get("club") or "?", 0) + 1
        top = sorted(clubs.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        noms = [f"{(j['first_name'] or '').strip()} {(j['last_name'] or '').strip()}".strip() for j in sorted(matchs, key=lambda j: j["id"])[:echantillon]]
        resume = ", ".join(f"{a} {o} {v}" for a, o, v in conditions)
        print(f"S{i}: {texte}")
        print(f"    condition : {resume}")
        print(f"    matchent : {len(matchs)}/{len(joueurs)}  | clubs : {top}")
        print(f"    echantillon : {noms}")


def table_attributs(pilotes: dict[str, list[tuple[str, list[Condition]]]], joueurs: list[dict]) -> list[dict]:
    """Une ligne par (attribut, operateur, seuil) utilise par au moins un
    pilote : couverture de l'attribut ET selectivite du seuil. `minute` est
    exclu (contexte de match, pas une propriete du joueur)."""
    champ = [j for j in joueurs if j.get("position") != "GK"]
    utilisations: dict[Condition, set[str]] = {}
    for nom, phrases in pilotes.items():
        for _, conditions in phrases:
            for condition in conditions:
                if condition[0] not in CHAMPS_CONTEXTE:
                    utilisations.setdefault(condition, set()).add(nom)
    lignes = []
    for condition, noms in sorted(utilisations.items()):
        attribut = condition[0]
        renseignes = [j for j in joueurs if j.get(attribut) not in (None, "", ())]
        matchs_base = [j for j in joueurs if condition_vraie(j, condition)]
        matchs_champ = [j for j in champ if condition_vraie(j, condition)]
        lignes.append({
            "attribut": attribut,
            "seuil": f"{condition[1]} {condition[2]}",
            "pilotes": sorted(noms),
            "couverture": len(renseignes) / len(joueurs),
            "selectivite_champ": len(matchs_champ) / len(champ),
            "matchent_base": len(matchs_base),
        })
    return lignes


def table_attributs_markdown(lignes: list[dict]) -> str:
    sortie = [
        "| Attribut | Seuil utilisé | Pilotes | Couverture attribut | Sélectivité du seuil (% joueurs de champ) | Matchent (base) |",
        "|---|---|---|---|---|---|",
    ]
    for ligne in lignes:
        sortie.append(
            f"| {ligne['attribut']} | `{ligne['seuil']}` | {', '.join(ligne['pilotes'])} | "
            f"{ligne['couverture']:.1%} | {ligne['selectivite_champ']:.1%} | {ligne['matchent_base']} |"
        )
    return chr(10).join(sortie)


if __name__ == "__main__" and sys.argv[1] == "--attributs":
    base = charger_joueurs()
    pilotes = {}
    for info in __import__("pkgutil").iter_modules(importlib.import_module("pilotes_v2").__path__):
        module = importlib.import_module(f"pilotes_v2.{info.name}")
        pilotes[info.name] = module.DEFAUT + module.SURNOM
    print(table_attributs_markdown(table_attributs(pilotes, base)))
elif __name__ == "__main__":
    nom_module = sys.argv[1]
    module = importlib.import_module(f"pilotes_v2.{nom_module}")
    base = charger_joueurs()
    audit(nom_module, module.DEFAUT + module.SURNOM, base)
    detail_surnoms(nom_module, module.SURNOM, base)
