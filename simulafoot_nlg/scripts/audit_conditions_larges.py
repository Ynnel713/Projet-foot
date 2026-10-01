"""Audit des conditions TROP LARGES sur un flux d'evenements reel (ticket « banque » : resserrer, pas ici).

Pour chaque phrase conditionnee de la banque, part des evenements de son scenario pour lesquels toutes ses
conditions `mandatory` sont satisfaites (joueur ET contexte de l'evenement, comme `phrase_selector.candidats`).
Une phrase eligible pour plus de 30 % des evenements de son scenario domine le tirage et repete le meme modele :
elle est signalee. Complete `scripts/audit_conditions_pilote.py`, qui mesure la couverture sur TOUTE la base de
joueurs : ici la mesure porte sur les acteurs reels des matchs (les joueurs des grands clubs sont plus forts que
la moyenne de la base : `fm_rating >= 80` couvre 5 % des joueurs de champ mais 28 % des entrants simules).

Usage : uv run python -m scripts.audit_conditions_larges --events ../data/nlg_samples/inbox [--seuil 0.30] [--out rapport.md]
        (--events : un fichier .jsonl ou un dossier de .jsonl)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from sqlite3 import Connection
from typing import Any

from engine.conditions import evaluate_condition
from engine.context_builder import dict_to_context
from engine.db import get_sqlite
from engine.event_contract import validate_event_stream
from engine.narrative_adapter import event_to_scenario
from engine.player_resolver import resolve
from engine.scenario_engine import load_phrases, load_scenario, load_variants

SEUIL_PAR_DEFAUT = 0.30
DB_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"


def conditions_larges(
    conn: Connection, evenements: Iterable[Mapping[str, Any]], *, seuil: float = SEUIL_PAR_DEFAUT
) -> list[dict[str, Any]]:
    """Phrases conditionnees eligibles pour plus de `seuil` des evenements de leur scenario, du plus large au moins
    large : `scenario`, `phrase_id`, `texte`, `conditions` ("attribut op valeur"), `evenements` (eligibles),
    `total` (evenements du scenario), `part`. Les evenements sans scenario (poteau, barre) sont ignores."""
    par_scenario: dict[str, list[tuple[Any, Any]]] = defaultdict(list)
    for evenement in validate_event_stream(evenements):
        scenario = event_to_scenario(evenement)
        if scenario is not None:
            par_scenario[scenario].append((resolve(evenement["player_id"], conn), dict_to_context(evenement, conn)))

    larges = []
    for code, acteurs in par_scenario.items():
        scenario = load_scenario(conn, code)
        if scenario is None:
            continue
        for variante in load_variants(conn, scenario.id):
            for phrase in load_phrases(conn, variante.id):
                conditions = [c for c in phrase.conditions if c.mandatory]
                if phrase.is_fallback or not phrase.is_active or not conditions:
                    continue
                eligibles = sum(all(evaluate_condition(c, joueur, contexte) for c in conditions) for joueur, contexte in acteurs)
                if eligibles > seuil * len(acteurs):
                    larges.append({
                        "scenario": code, "phrase_id": phrase.id, "texte": phrase.text,
                        "conditions": " & ".join(f"{c.attribute} {c.operator} {c.value}" for c in conditions),
                        "evenements": eligibles, "total": len(acteurs), "part": eligibles / len(acteurs),
                    })
    return sorted(larges, key=lambda ligne: (-ligne["part"], ligne["phrase_id"]))


def _lire(source: Path) -> list[dict[str, Any]]:
    fichiers = sorted(source.glob("*.jsonl")) if source.is_dir() else [source]
    return [json.loads(ligne) for f in fichiers for ligne in f.read_text(encoding="utf-8").splitlines() if ligne.strip()]


def tableau(larges: list[dict[str, Any]], seuil: float) -> str:
    lignes = [f"Conditions eligibles pour plus de {seuil:.0%} des evenements de leur scenario : {len(larges)} phrases.", "",
              "| Scenario | phrase_id | Part | Evenements | Conditions | Texte |", "|---|---|---|---|---|---|"]
    lignes += [
        f"| {g['scenario']} | {g['phrase_id']} | {g['part']:.0%} | {g['evenements']}/{g['total']} | {g['conditions']} | {g['texte'][:70]} |"
        for g in larges
    ]
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=str(DB_PAR_DEFAUT))
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--seuil", type=float, default=SEUIL_PAR_DEFAUT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    conn = get_sqlite(args.db)
    try:
        resultat = tableau(conditions_larges(conn, _lire(args.events), seuil=args.seuil), args.seuil)
    finally:
        conn.close()
    if args.out:
        args.out.write_text(resultat + "\n", encoding="utf-8")
    else:
        sys.stdout.buffer.write((resultat + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
