"""Audit de couverture des donnees Player sur les 7563 joueurs importes --
30/09/2026. Script d'audit ponctuel, PAS un module moteur.

Pour chaque attribut reference par au moins une des 153 conditions
existantes : % de joueurs avec valeur non-nulle, distribution, nombre de
phrases concernees. Puis, pour chacune des phrases a conditions, taux de
declenchement THEORIQUE reel (utilise engine.conditions.evaluate_condition,
pas une approximation) sur les 7563 joueurs -- seules les conditions
portant sur un attribut JOUEUR sont evaluees ici (minute/score_context sont
des conditions de CONTEXTE DE MATCH, toujours disponibles au runtime, hors
perimetre de cet audit donnees-joueur).
"""

from __future__ import annotations

import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conditions import evaluate_condition  # noqa: E402
from engine.models import MatchContext, PhraseCondition, Player  # noqa: E402
from engine.profile_engine import normalize_player  # noqa: E402

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "simulafoot.db"

_MATCH_CONTEXT_ATTRS = {"minute", "score_context"}


def load_all_players(conn: sqlite3.Connection) -> list[Player]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM players").fetchall()
    attrs_by_player: dict[int, dict[str, int]] = {}
    for r in conn.execute("SELECT player_id, attribute, value FROM player_attributes"):
        attrs_by_player.setdefault(r[0], {})[r[1]] = r[2]
    players = []
    for row in rows:
        d = dict(row)
        d["attributes"] = attrs_by_player.get(d["id"], {})
        players.append(normalize_player(d))
    return players


def section1_attributs(conn: sqlite3.Connection, players: list[Player]) -> None:
    total = len(players)
    print(f"=== SECTION 1 -- couverture par attribut (sur {total} joueurs) ===\n")

    rows = conn.execute(
        "SELECT attribute, COUNT(DISTINCT phrase_id) FROM phrase_conditions GROUP BY attribute"
    ).fetchall()
    n_phrases_par_attr = {r[0]: r[1] for r in rows}

    # Champs directs sur players (hors EAV)
    champs_directs = ["foot", "weak_foot", "height_cm", "age", "preferred_moves"]
    for col in champs_directs:
        if col == "preferred_moves":
            n = sum(1 for p in players if p.preferred_moves)
        else:
            n = sum(1 for p in players if getattr(p, col) is not None)
        pct = 100 * n / total
        n_phrases = n_phrases_par_attr.get(col, 0)
        if col == "preferred_moves":
            verdict = "QUASI-VIDE"
        elif pct >= 80:
            verdict = "VIABLE"
        elif pct >= 40:
            verdict = "PARTIEL"
        else:
            verdict = "QUASI-VIDE"
        print(f"{col:18s} {n:5d}/{total} = {pct:5.1f}%   {n_phrases:3d} phrase(s)   [{verdict}]")
        if col == "preferred_moves":
            from collections import Counter
            tous_moves: Counter[str] = Counter()
            for p in players:
                for m in p.preferred_moves:
                    tous_moves[m] += 1
            print("    top 5 preferred_moves (parmi les 362 joueurs renseignes) :", tous_moves.most_common(5))
        elif col in ("weak_foot", "height_cm", "age"):
            vals = [getattr(p, col) for p in players if getattr(p, col) is not None]
            if vals:
                print(f"    min={min(vals)} med={statistics.median(vals)} max={max(vals)}")
        elif col == "foot":
            from collections import Counter
            c = Counter(p.foot for p in players if p.foot)
            print("    valeurs :", c.most_common())
    print()

    # Attributs FM26 (EAV)
    fm_attrs = [a for a in n_phrases_par_attr if a not in champs_directs and a not in _MATCH_CONTEXT_ATTRS]
    for attr in sorted(fm_attrs, key=lambda a: -n_phrases_par_attr[a]):
        vals = [p.attributes[attr] for p in players if attr in p.attributes]
        n = len(vals)
        pct = 100 * n / total
        n_phrases = n_phrases_par_attr.get(attr, 0)
        verdict = "VIABLE" if pct >= 80 else ("PARTIEL" if pct >= 40 else "QUASI-VIDE")
        if vals:
            print(f"{attr:18s} {n:5d}/{total} = {pct:5.1f}%   {n_phrases:3d} phrase(s)   "
                  f"min={min(vals)} med={statistics.median(vals)} max={max(vals)}   [{verdict}]")
        else:
            print(f"{attr:18s} {n:5d}/{total} = {pct:5.1f}%   {n_phrases:3d} phrase(s)   [{verdict}]")

    # Attributs de contexte de match (hors perimetre donnees-joueur)
    print()
    for attr in _MATCH_CONTEXT_ATTRS:
        if attr in n_phrases_par_attr:
            print(f"{attr:18s} -- attribut de CONTEXTE DE MATCH (toujours disponible au runtime, "
                  f"hors perimetre donnees-joueur)   {n_phrases_par_attr[attr]} phrase(s)")


def section2_phrases_a_risque(conn: sqlite3.Connection, players: list[Player]) -> None:
    print(
        "\n=== SECTION 2 -- taux de declenchement theorique par phrase "
        "(conditions JOUEUR uniquement) ===\n"
    )
    rows = conn.execute(
        """SELECT p.id, p.text, s.code, v.code
           FROM phrases p
           JOIN variants v ON v.id = p.variant_id
           JOIN scenarios s ON s.id = v.scenario_id
           WHERE EXISTS (SELECT 1 FROM phrase_conditions pc WHERE pc.phrase_id = p.id)"""
    ).fetchall()

    contexte_neutre = MatchContext(match_id="AUDIT", minute=45, score_context=None)
    resultats = []
    for phrase_id, text, sc_code, v_code in rows:
        conds_rows = conn.execute(
            "SELECT attribute, operator, value, mandatory FROM phrase_conditions WHERE phrase_id = ?",
            (phrase_id,),
        ).fetchall()
        conds_joueur = [
            PhraseCondition(
                id=0, phrase_id=phrase_id, attribute=a, operator=o, value=str(v), mandatory=bool(m)
            )
            for a, o, v, m in conds_rows
            if a not in _MATCH_CONTEXT_ATTRS
        ]
        if not conds_joueur:
            continue  # phrase conditionnee uniquement sur le contexte de match -- hors perimetre ici
        n_ok = 0
        for player in players:
            try:
                if all(evaluate_condition(c, player, contexte_neutre) for c in conds_joueur):
                    n_ok += 1
            except (ValueError, TypeError):
                # TypeError : attribut connu (dans PLAYER_FIELDS) mais valeur
                # None pour CE joueur (ex. height_cm non renseigne) --
                # evaluate_condition compare None a un entier et plante au
                # lieu de renvoyer False. Trouve par cet audit (30/09/2026) :
                # gap reel de conditions.py, non corrige ici (engine/, hors
                # perimetre de ce tour), signale dans le rapport.
                continue
        pct = 100 * n_ok / len(players)
        resultats.append((pct, sc_code, v_code, text, conds_joueur))

    resultats.sort(key=lambda r: r[0])
    sous_10 = [r for r in resultats if r[0] < 10.0]

    # Distinction capitale : un taux bas peut venir (a) d'un attribut RARE
    # PAR CONCEPTION sur une population bien couverte (Aggression >= 85 :
    # 93% des joueurs ONT une valeur, peu l'ont aussi haute -- c'est voulu,
    # "Le colosse" doit etre rare) ou (b) d'un attribut PEU RENSEIGNE
    # (preferred_moves 4,8%, height_cm 11,7%, foot 39,1% -- un joueur qui
    # aurait la valeur qualifiante ne peut meme pas etre teste). Seul (b)
    # est un probleme de DONNEES ; (a) est une selectivite narrative saine.
    attrs_peu_renseignes = {"preferred_moves", "height_cm", "foot"}
    limitees_donnees = [
        r for r in sous_10 if any(c.attribute in attrs_peu_renseignes for c in r[4])
    ]
    selectivite_design = [r for r in sous_10 if r not in limitees_donnees]

    print(f"Phrases a conditions JOUEUR evaluees : {len(resultats)}")
    print(f"Phrases sous 10% de taux de declenchement theorique : {len(sous_10)}")
    print(f"  dont LIMITEES PAR LA DONNEE (preferred_moves/height_cm/foot) : {len(limitees_donnees)}")
    print(f"  dont SELECTIVITE NARRATIVE SAINE (attribut bien renseigne, seuil elitiste voulu) : "
          f"{len(selectivite_design)}\n")

    print("--- Limitees par la donnee (le vrai probleme) ---")
    for pct, sc_code, v_code, text, conds in limitees_donnees:
        attrs = ", ".join(f"{c.attribute} {c.operator} {c.value}" for c in conds)
        print(f"  {pct:5.2f}%  {sc_code}/{v_code}  [{attrs}]")
        print(f"          {' '.join(text.split())[:110]}")

    print("\n--- Selectivite narrative saine (PAS un probleme, liste pour memoire) ---")
    for pct, sc_code, v_code, _text, conds in selectivite_design:
        attrs = ", ".join(f"{c.attribute} {c.operator} {c.value}" for c in conds)
        print(f"  {pct:5.2f}%  {sc_code}/{v_code}  [{attrs}]")
    print("\n--- Pour reference, les 10 phrases les MIEUX couvertes (conditions non triviales) ---")
    for pct, sc_code, v_code, _text, conds in resultats[-10:]:
        attrs = ", ".join(f"{c.attribute} {c.operator} {c.value}" for c in conds)
        print(f"  {pct:5.2f}%  {sc_code}/{v_code}  [{attrs}]")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    players = load_all_players(conn)
    section1_attributs(conn, players)
    section2_phrases_a_risque(conn, players)
    conn.close()
