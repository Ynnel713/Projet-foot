"""Smoke test ponctuel du pipeline de commentaire -- 30/09/2026.

CE SCRIPT N'EST PAS LE MOTEUR. Deux blocages reels empechent le pipeline
"narrative.py -> engine/models -> phrase_selector -> template_filler" tel que
demande de tourner aujourd'hui :

1. engine/narrative.py (racine du projet Simulafoot, PAS simulafoot_nlg) ne
   genere que des NarrativeEvent de type BUT (buts/penalties), pour piloter
   l'animation canvas (gabarit -> template visuel, voir
   src/ligue1sim/animation/templates.py). Aucun generateur d'evenement
   n'existe nulle part dans le projet pour CARTON_ROUGE, ARRET_GARDIEN,
   COUP_FRANC, CONSTRUCTION, SITUATION_MATCH, DEBUT_MATCH ou
   GESTE_SIGNATURE -- pas seulement "pas encore branche a simulafoot_nlg",
   litteralement absent. Verifie par recherche exhaustive dans engine/ et
   src/ a la racine du projet.
2. phrase_selector.select, template_filler.render et post_process.apply
   restent des squelettes NotImplementedError (contrainte explicite de ce
   tour : "ne pas toucher au squelette engine/").

Ce script contourne (1) en fabriquant a la main une chronologie d'evenements
PLAUSIBLE (20 evenements, proportions realistes) plutot que de brancher un
generateur qui n'existe pas -- et contourne (2) en reimplementant, ICI
SEULEMENT (jamais dans engine/), une version minimale de la selection et de
la substitution, sur le modele de l'algorithme deja documente dans les
docstrings de phrase_selector.py/template_filler.py. Objectif unique :
donner un signal concret sur ce qui manque, pas produire un moteur.

Simplifications assumees et ANNONCEES (pas cachees) :
    - Pas de cooldown/anti-repetition (anti_repeat.py non implemente,
      hors-scope ce tour) -- une meme phrase PEUT ressortir plusieurs fois
      dans les 20 evenements, c'est attendu et note dans la sortie.
    - Substitution de slots simplifiee (pas d'elision post_process) --
      memes limites que scripts/audit_editorial_banque.py::
      substituer_slots_dans_audit, documentees dans l'audit du meme jour.
    - Chronologie et joueurs choisis a la main pour etre plausibles, pas
      generes par narrative.py (qui ne couvre pas ces scenarios).
"""

from __future__ import annotations

import random
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conditions import evaluate_condition  # noqa: E402
from engine.models import MatchContext, Phrase, Player  # noqa: E402
from engine.profile_engine import normalize_player  # noqa: E402
from engine.scenario_engine import load_phrases, load_scenario, load_variants  # noqa: E402

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "simulafoot.db"

# Chronologie fabriquee a la main (voir avertissement module) -- proportions
# calquees sur les frequences reelles approximatives d'un match (beaucoup de
# CONSTRUCTION/SITUATION_MATCH, peu de CARTON_ROUGE), PAS un tirage
# stochastique d'un moteur de simulation.
CHRONOLOGIE = [
    (1, "DEBUT_MATCH"),
    (4, "SITUATION_MATCH"),
    (7, "CONSTRUCTION"),
    (11, "COUP_FRANC"),
    (14, "CONSTRUCTION"),
    (18, "ARRET_GARDIEN"),
    (23, "GESTE_SIGNATURE"),
    (27, "SITUATION_MATCH"),
    (31, "BUT"),
    (34, "CONSTRUCTION"),
    (38, "PENALTY_RATE"),
    (45, "SITUATION_MATCH"),
    (52, "CARTON_ROUGE"),
    (58, "ARRET_GARDIEN"),
    (63, "COUP_FRANC"),
    (67, "GESTE_SIGNATURE"),
    (74, "CONSTRUCTION"),
    (79, "BUT"),
    (85, "ARRET_GARDIEN"),
    (90, "SITUATION_MATCH"),
]
assert len(CHRONOLOGIE) == 20

CLUB = "Lyon"
ADVERSAIRE = "Marseille"


def _random_players(conn: sqlite3.Connection, n: int, rng: random.Random) -> list[Player]:
    # Bug trouve en re-smoke-testant (01/10/2026) : "ORDER BY RANDOM()" est le
    # generateur SQLite, PAS `rng` -- deux executions avec le meme seed Python
    # tiraient des joueurs differents, rendant le smoke test non reproductible.
    # Corrige : la selection complete se fait cote Python avec `rng`.
    all_ids = [r[0] for r in conn.execute("SELECT id FROM players").fetchall()]
    rng.shuffle(all_ids)
    picked = all_ids[:n]
    players = []
    for pid in picked:
        row = conn.execute(
            "SELECT * FROM players WHERE id = ?", (pid,)
        ).fetchone()
        attrs = {
            r["attribute"]: r["value"]
            for r in conn.execute(
                "SELECT attribute, value FROM player_attributes WHERE player_id = ?", (pid,)
            ).fetchall()
        }
        d = dict(row)
        d["attributes"] = attrs
        players.append(normalize_player(d))
    return players


_VOYELLES_ELISION = "aeiouyAEIOUYhéèêàâôûîïH"


def substituer_slots(text: str, valeurs: dict[str, str]) -> str:
    """Mecanique de substitution ISOLEE, identique a
    scripts/audit_editorial_banque.py::substituer_slots_dans_audit -- PAS
    template_filler.render (squelette non touche)."""
    result = text
    for slot_name, valeur in valeurs.items():
        pattern = re.compile(r"(\b(?:de|du|le|la|que)\s+)\{" + re.escape(slot_name) + r"\}")

        def repl(m: re.Match[str], valeur: str = valeur) -> str:
            mot_intro = m.group(1).strip().lower()
            if valeur and valeur[0] in _VOYELLES_ELISION:
                elisions = {"de": "d'", "du": "d'", "le": "l'", "la": "l'", "que": "qu'"}
                if mot_intro in elisions:
                    return f"{elisions[mot_intro]}{valeur}"
            return f"{m.group(1)}{valeur}"

        result = pattern.sub(repl, result)
        result = result.replace("{" + slot_name + "}", valeur)
    if result:
        result = result[0].upper() + result[1:]
    return result


def simuler_selection(
    conn: sqlite3.Connection,
    scenario_code: str,
    player: Player,
    context: MatchContext,
    rng: random.Random,
) -> Phrase | None:
    """Reimplementation MINIMALE de l'algorithme documente dans
    phrase_selector.py (etapes 1 a 6, SANS l'etape 5 anti_repeat -- non
    implemente). Filtre les conditions mandatory, tirage pondere parmi les
    survivantes. None si le scenario n'existe pas ou si 0 candidat."""
    scenario = load_scenario(conn, scenario_code)
    if scenario is None:
        return None
    variants = [v for v in load_variants(conn, scenario.id) if v.is_active]
    if not variants:
        return None
    default_variant = next((v for v in variants if v.is_default), variants[0])

    candidates = [p for p in load_phrases(conn, default_variant.id) if p.is_active]
    survivants = []
    for p in candidates:
        try:
            ok = all(
                evaluate_condition(c, player, context)
                for c in p.conditions
                if c.mandatory
            )
        except ValueError:
            ok = False  # attribut inconnu pour CE joueur/contexte -- phrase ecartee, pas de crash
        if ok:
            survivants.append(p)
    if not survivants:
        return None
    poids = [p.weight for p in survivants]
    return rng.choices(survivants, weights=poids, k=1)[0]


def main() -> None:
    rng = random.Random(42)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    joueurs = _random_players(conn, 20, rng)

    print("=== SMOKE TEST -- 20 premiers evenements d'un match simule (Lyon-Marseille) ===")
    print("AVERTISSEMENT : simulation scripts/, pas le moteur reel -- voir docstring du module.\n")

    phrases_vues: dict[int, int] = {}
    echecs = []
    for i, (minute, scenario_code) in enumerate(CHRONOLOGIE):
        player = joueurs[i]
        context = MatchContext(
            match_id="SMOKE-1", minute=minute, home_team=CLUB, away_team=ADVERSAIRE,
            player_team=CLUB, is_home=True, score_context="ouverture_score" if i == 8 else None,
        )
        phrase = simuler_selection(conn, scenario_code, player, context, rng)
        if phrase is None:
            echecs.append((minute, scenario_code))
            print(f"[{minute:2d}'] {scenario_code:16s} -> AUCUNE PHRASE SELECTIONNABLE")
            continue

        phrases_vues[phrase.id] = phrases_vues.get(phrase.id, 0) + 1
        rendu = substituer_slots(
            phrase.text,
            {
                "joueur": player.full_name,
                "club": CLUB,
                "adversaire": ADVERSAIRE,
                "minute": str(minute),
                "passeur": joueurs[(i + 1) % 20].full_name,
                "receveur": joueurs[(i + 2) % 20].full_name,
            },
        )
        redite = " [DEJA VU dans cette sequence]" if phrases_vues[phrase.id] > 1 else ""
        print(f"[{minute:2d}'] {scenario_code:16s} -> {rendu}{redite}")

    print(f"\nEchecs de selection (0 candidat) : {len(echecs)}/20")
    for minute, code in echecs:
        print(f"  {minute}' {code}")
    print(f"Phrases reutilisees dans les 20 evenements (normal, anti_repeat non implemente) : "
          f"{sum(1 for c in phrases_vues.values() if c > 1)}")

    conn.close()


if __name__ == "__main__":
    main()
