"""Convertit le classeur Excel de commentaire (colonnes : Code scenario,
Libelle scenario, Variante, Phrase, Condition, Poids, Tags -- voir
l'onglet "Instructions" du classeur) en YAML consommable par
scripts/import_seed.py.

Ce que ce script fait :
    1. Lit l'onglet "Phrases", ignore les lignes vides ou "d'exemple"
       (heuristique : texte contenant "exemple", ou tout slot {ex_...}).
    2. Valide chaque slot {xxx} utilise contre SLOTS_AUTORISES (mesure sur
       le vrai classeur du 29/09/2026 -- PAS une liste devinee, voir
       docstring de SLOTS_AUTORISES). Echec -> ValueError avec le numero de
       ligne Excel exact.
    3. Decoupe chaque condition en atomes structures (engine.conditions.
       parse_condition_atoms) -- le YAML final porte une LISTE de
       conditions par phrase, jamais la chaine brute "X et Y".
    4. Groupe les lignes par (scenario, variante) ; une scenario sans ligne
       a variante vide se voit attribuer sa variante existante comme
       defaut (voir _group_variants) plutot que d'echouer l'import pour
       une contrainte que le classeur ne peut pas exprimer nativement.
    4bis. Attribue DEFAULT_COOLDOWN_MATCHES a chaque phrase (aucune colonne
       "Cooldown" dans le classeur du 29/09/2026 -- voir la constante pour
       l'arbitrage complet). Jamais NULL en sortie : import_seed.py refuse
       tout scenario portant une phrase sans cooldown_matches (regle
       "cooldown obligatoire" du README), donc ce script ne doit jamais en
       produire une.
    5. Ecrit le YAML dans scenarios_path (defaut data/seed/scenarios.yml).

Ce que ce script ne fait PAS : il n'ecrit rien en SQLite -- c'est le role
de scripts/import_seed.py, qu'on ne duplique pas (decision du brief
"commentaire live quali", D4). Rejouable : chaque execution regenere le
YAML en entier a partir du classeur, pas de fusion incrementale.

Tracabilite (decision du 30/09/2026) : le classeur est la source de verite
EDITORIALE, versionne dans data/seed_source/ (pas juste sur le poste de son
auteur). `data/seed_source/CHECKSUM.txt` porte son SHA256 (format
`sha256sum`, verifiable par `sha256sum -c CHECKSUM.txt`) -- chaque
conversion logue le SHA256 REEL du fichier lu, et un WARNING explicite s'il
ne correspond pas a CHECKSUM.txt (classeur modifie sans regenerer le
checksum) ou si CHECKSUM.txt est absent. Objectif : six mois plus tard,
savoir quelle version du classeur a produit le scenarios.yml en base."""

from __future__ import annotations

import hashlib
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.conditions import parse_condition_atoms  # noqa: E402

logger = logging.getLogger(__name__)

_NLG_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX_PATH = _NLG_ROOT / "data" / "seed_source" / "banque_de_phrases_simulafoot.xlsx"
DEFAULT_CHECKSUM_PATH = _NLG_ROOT / "data" / "seed_source" / "CHECKSUM.txt"
DEFAULT_YAML_PATH = _NLG_ROOT / "data" / "seed" / "scenarios.yml"

_SLOT_RE = re.compile(r"\{(\w+)\}")

# Slots reellement utilises dans le classeur du 29/09/2026 (281 phrases,
# mesure exacte par scenario -- PAS une liste devinee a l'avance, voir
# l'echange "commentaire live quali" : la premiere version de cette table
# contenait des noms (buteur, tireur, gardien...) qui n'apparaissent nulle
# part dans le vrai fichier). A completer si la banque grandit avec de
# nouveaux scenarios -- l'echec sera explicite (voir valider_slots) le jour
# ou un slot non couvert ici apparait.
SLOTS_AUTORISES: dict[str, frozenset[str]] = {
    "ARRET_GARDIEN": frozenset({"adversaire", "club", "joueur"}),
    "BUT": frozenset({"adversaire", "club", "joueur"}),
    "CARTON_ROUGE": frozenset({"adversaire", "club", "joueur", "minute"}),
    "CONSTRUCTION": frozenset({"adversaire", "club", "joueur", "passeur", "receveur"}),
    "COUP_FRANC": frozenset({"adversaire", "passeur", "receveur"}),
    "DEBUT_MATCH": frozenset({"adversaire", "club", "joueur"}),
    "GESTE_SIGNATURE": frozenset({"adversaire", "club", "joueur"}),
    "PENALTY_RATE": frozenset({"adversaire", "joueur"}),
    "SITUATION_MATCH": frozenset({"adversaire", "club"}),
}

# Expression template_filler pour chaque slot "connu automatiquement" (voir
# l'onglet Instructions du classeur : "{joueur}, {club}, {adversaire},
# {minute} sont deja connus automatiquement"), etendue a {passeur}/
# {receveur} (D1). Mini-interpreteur a points restreint (voir
# engine/template_filler.py) : chaque expression doit rester un chemin
# d'attributs simple, jamais de logique conditionnelle inline -- c'est pour
# ca que MatchContext.opponent_team existe comme property plutot que de
# forcer "is_home ? away_team : home_team" ici.
SLOT_EXPRESSIONS: dict[str, str] = {
    "joueur": "player.full_name",
    "club": "context.player_team",
    "adversaire": "context.opponent_team",
    "minute": "context.minute",
    "passeur": "context.passeur.full_name",
    "receveur": "context.receveur.full_name",
}

_JUNK_MARKERS = ("exemple", "ex_")

# Cooldown par defaut applique a TOUTE phrase issue de ce classeur (aucune
# colonne "Cooldown" dans l'onglet "Phrases" du 29/09/2026 -- voir
# AUDIT_EDITORIAL_2026-09-30.md, section cooldown, pour l'arbitrage complet).
#
# Decision (30/09/2026, audit editorial) sur l'unite et la portee -- non
# revisees ici, deja tranchees et confirmees par le 2e tour d'audit :
#   - unite = MATCHS (nom deja porte par phrase_cooldowns.cooldown_matches ;
#     un spectateur juge la repetition d'un match sur l'autre, pas a la
#     minute pres).
#   - portee = PAR PHRASE (phrase_cooldowns.phrase_id est la PRIMARY KEY).
#   - JAMAIS laisse a NULL (regle "cooldown obligatoire" du README) : c'est
#     ce qui rendrait toute la banque injouable une fois phrase_selector
#     implemente. import_seed.py refuse tout import si une phrase en manque.
#
# Revision (2e tour d'audit, 30/09/2026) : un chiffre unique (3) pour 281
# phrases de densites emotionnelles tres differentes etait sous-pense --
# corrige en configurable PAR SCENARIO. Chaque valeur est un arbitrage
# frequence x memorabilite (plus l'evenement est rare et marquant, plus le
# cooldown est long) ; PAS une mesure d'usage reel (aucune donnee de match
# jouee n'existe encore, voir SPEC_ANTI_REPEAT.md) -- place-holder assume, a
# affiner une fois l'anti-repetition mesurable en production.
DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO: dict[str, int] = {
    # Evenement rarissime (quelques cartons rouges par saison et par joueur)
    # et choquant a chaque fois -- doit rester un non-evenement en temps
    # normal, la memoire du spectateur y est la plus longue de tout le lot.
    "CARTON_ROUGE": 10,
    # Rare dans un match donne (0-3 penalties en moyenne, souvent 0), mais un
    # penalty rate (surtout manque) est un moment fort dont on se souvient
    # -- juste en dessous de CARTON_ROUGE, pas au meme niveau (moins choquant,
    # plus frequent sur une saison complete).
    "PENALTY_RATE": 6,
    # Trait de caractere d'UN joueur (pas un evenement de match) : le revoir
    # trop vite pour le MEME joueur casserait l'illusion de personnalite
    # ("il fait encore son numero"), mais le pool est deliberement large
    # (30-37 phrases/scenario) donc pas besoin d'un cooldown aussi long que
    # les evenements rares ci-dessus.
    "GESTE_SIGNATURE": 5,
    # Ne sort qu'UNE fois par match par construction (contexte d'avant-match),
    # mais les faits qu'il relaie (forme du moment, absences) restent vrais
    # sur plusieurs semaines pour la MEME equipe -- cooldown moyen pour eviter
    # de resservir la meme accroche a la rencontre suivante de ce club.
    "DEBUT_MATCH": 4,
    # Moment fort classique (~2-3 buts/match en moyenne) : memorable mais pas
    # rarissime, le pool (60 phrases, 3 variantes) est deja le plus large du
    # lot -- valeur de reference du 1er tour d'audit, conservee.
    "BUT": 3,
    "COUP_FRANC": 3,
    # Frequent (plusieurs arrets/relances par match) et individuellement peu
    # marquant hors gros arret -- valeur de reference du 1er tour d'audit,
    # conservee.
    "ARRET_GARDIEN": 2,
    # Phase de jeu la plus frequente d'un match (de tres nombreuses
    # constructions par mi-temps), jamais un "moment" en soi -- cooldown
    # court pour ne pas assecher le pool sur une seule rencontre.
    "CONSTRUCTION": 2,
    # Commentaire d'ambiance/tactique quasi continu, appele bien plus souvent
    # que tout autre scenario au fil d'un match -- le plus court du lot :
    # un cooldown plus long asseche le pool (30 phrases) avant la mi-temps.
    "SITUATION_MATCH": 1,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_checksum_file(checksum_path: Path, xlsx_name: str) -> str | None:
    """Hash attendu pour `xlsx_name` dans un fichier au format `sha256sum`
    (`<hash> *<nom>` ou `<hash>  <nom>`) -- None si le fichier de checksum
    est absent ou ne mentionne pas ce nom."""
    if not checksum_path.exists():
        return None
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected_hash, _, name = line.partition(" ")
        name = name.strip().lstrip("*")
        if name == xlsx_name:
            return expected_hash
    return None


def log_checksum(xlsx_path: Path, checksum_path: Path) -> str:
    """Calcule le SHA256 réel de `xlsx_path`, le logue toujours (traçabilité
    -- voir docstring du module), et logue un WARNING (n'interrompt pas la
    conversion) si `checksum_path` est absent ou ne correspond pas. Renvoie
    le hash réel."""
    actual = _sha256(xlsx_path)
    expected = _parse_checksum_file(checksum_path, xlsx_path.name)
    if expected is None:
        logger.warning(
            "Aucun CHECKSUM.txt pour %s (cherché : %s) -- SHA256 réel non vérifié : %s",
            xlsx_path.name,
            checksum_path,
            actual,
        )
    elif expected != actual:
        logger.warning(
            "CHECKSUM.txt ne correspond PAS à %s -- classeur modifié sans régénérer le checksum ? "
            "attendu=%s réel=%s",
            xlsx_path.name,
            expected,
            actual,
        )
    else:
        logger.info("Checksum vérifié pour %s : %s", xlsx_path.name, actual)
    return actual


class CommentaryConversionError(ValueError):
    """Le classeur est bien forme (pandas a pu le lire) mais viole une
    regle metier (slot non autorise, condition illisible...) -- distinct
    d'une erreur de lecture du fichier lui-meme."""


def _is_junk_row(phrase: str) -> bool:
    """Heuristique de detection d'une ligne d'exemple residuelle (bandeau
    jaune du classeur, voir onglet Instructions) : texte contenant
    "exemple" (insensible a la casse), ou un slot {ex_...} -- voir brief
    "commentaire live quali", point 4."""
    lowered = phrase.lower()
    if "exemple" in lowered:
        return True
    return any(slot.startswith("ex_") for slot in _SLOT_RE.findall(phrase))


def valider_slots(phrase: str, scenario: str, ligne_excel: int) -> None:
    """Verifie que tous les slots {xxx} de `phrase` sont autorises pour
    `scenario` (voir SLOTS_AUTORISES). Leve CommentaryConversionError avec
    le numero de ligne Excel si un slot est inconnu ou si le scenario
    lui-meme n'est pas dans la table -- correction immediate dans le
    fichier source, jamais un KeyError au runtime ni un "{passeur}"
    affiche tel quel a l'ecran."""
    if scenario not in SLOTS_AUTORISES:
        raise CommentaryConversionError(
            f"Ligne {ligne_excel} : scénario inconnu {scenario!r}. Connus : {sorted(SLOTS_AUTORISES)}"
        )
    autorises = SLOTS_AUTORISES[scenario]
    for slot in _SLOT_RE.findall(phrase):
        if slot not in autorises:
            raise CommentaryConversionError(
                f"Ligne {ligne_excel} : slot {{{slot}}} non autorisé pour le scénario {scenario!r}. "
                f"Autorisés : {sorted(autorises)}"
            )


def _slots_for_phrase(phrase: str) -> list[dict[str, Any]]:
    """PhraseSlot (forme YAML) pour chaque {xxx} du texte, expression tirée
    de SLOT_EXPRESSIONS -- tous les slots du classeur actuel sont "connus
    automatiquement" (aucun dictionary_key utilisé dans les 281 phrases
    réelles, voir l'analyse du 29/09/2026), donc aucune branche
    dictionary_key ici. À étendre le jour où une phrase pioche réellement
    dans "Dictionnaires de slots"."""
    slots = []
    for slot_name in _SLOT_RE.findall(phrase):
        expression = SLOT_EXPRESSIONS.get(slot_name)
        if expression is None:
            raise CommentaryConversionError(
                f"Slot {{{slot_name}}} autorisé mais sans expression connue -- complète SLOT_EXPRESSIONS."
            )
        slots.append({"slot_name": slot_name, "expression": expression})
    return slots


def _conditions_for_phrase(condition_brute: str, ligne_excel: int) -> list[dict[str, Any]]:
    try:
        atomes = parse_condition_atoms(condition_brute)
    except ValueError as exc:
        raise CommentaryConversionError(f"Ligne {ligne_excel} : condition invalide — {exc}") from exc
    return [
        {"attribute": a.attribute, "operator": a.operator, "value": a.value, "mandatory": True}
        for a in atomes
    ]


def _group_variants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Regroupe les lignes d'un scenario par variante (voir colonne
    "Variante (optionnel)") en respectant la contrainte de
    scripts/import_seed.py : au moins une variante is_default=true par
    scenario.

    Une ligne sans variante -> groupe "DEFAUT", marque is_default=true.
    Si AUCUNE ligne du scenario n'a de variante vide (ex. PENALTY_RATE,
    ou 100% des lignes portent la variante "PENALTY") -- il n'existe alors
    qu'un seul groupe : celui-ci devient implicitement le defaut (log
    warning, puisque le classeur n'exprime pas cette intention
    explicitement)."""
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        code = row["variant"] or "DEFAUT"
        by_variant[code].append(row)

    has_explicit_default = "DEFAUT" in by_variant
    variants = []
    for code, variant_rows in by_variant.items():
        is_default = code == "DEFAUT" if has_explicit_default else len(by_variant) == 1
        if not has_explicit_default and len(by_variant) > 1:
            # Plusieurs variantes nommées, aucune vide -- aucune ne peut
            # prétendre au défaut sans arbitraire : échec explicite plutôt
            # qu'un choix silencieux.
            raise CommentaryConversionError(
                f"Variantes {sorted(by_variant)} sans aucune ligne à variante vide : "
                "impossible de déterminer la variante par défaut, précise-en une."
            )
        if not has_explicit_default:
            logger.warning(
                'Variante "%s" prise comme défaut implicite (seule variante du scénario, '
                "aucune ligne à variante vide dans le classeur).",
                code,
            )
        variants.append(
            {
                "code": code,
                "label": "Variante par défaut" if code == "DEFAUT" else code.capitalize(),
                "is_default": is_default,
                "phrases": [
                    {
                        "text": r["phrase"],
                        "weight": r["weight"],
                        "cooldown_matches": r["cooldown_matches"],
                        "conditions": r["conditions"],
                        "slots": r["slots"],
                    }
                    for r in variant_rows
                ],
            }
        )
    return variants


def convertir(xlsx_path: Path, yml_path: Path, checksum_path: Path | None = None) -> int:
    log_checksum(xlsx_path, checksum_path if checksum_path is not None else xlsx_path.parent / "CHECKSUM.txt")

    df = pd.read_excel(xlsx_path, sheet_name="Phrases")
    df.columns = ["scenario_code", "scenario_label", "variant", "phrase", "condition", "weight", "tags"]

    rows_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    labels: dict[str, str] = {}
    skipped = 0

    for pos, (_, ligne) in enumerate(df.iterrows()):
        ligne_excel = pos + 2  # +1 (0-based -> 1-based) +1 (ligne d'en-tête)

        phrase = ligne["phrase"]
        scenario = ligne["scenario_code"]
        if pd.isna(phrase) or pd.isna(scenario):
            continue
        phrase = str(phrase).strip()
        scenario = str(scenario).strip()
        if _is_junk_row(phrase) or _is_junk_row(scenario):
            logger.warning(
                "Ligne %d ignorée (ligne d'exemple résiduelle détectée) : %r", ligne_excel, phrase[:60]
            )
            skipped += 1
            continue

        valider_slots(phrase, scenario, ligne_excel)

        condition_brute = ligne["condition"] if pd.notna(ligne["condition"]) else ""
        weight = float(ligne["weight"]) if pd.notna(ligne["weight"]) else 1.0
        variant = str(ligne["variant"]).strip() if pd.notna(ligne["variant"]) else None

        labels.setdefault(scenario, str(ligne["scenario_label"]).strip())
        if scenario not in DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO:
            # Echec explicite plutot qu'un defaut silencieux -- un nouveau
            # scenario sans cooldown arbitre serait sinon importe avec une
            # valeur au hasard (voir la discussion "cooldown obligatoire").
            raise CommentaryConversionError(
                f"Ligne {ligne_excel} : scénario {scenario!r} sans cooldown_matches arbitré dans "
                "DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO -- ajoute une valeur justifiée avant de convertir."
            )
        rows_by_scenario[scenario].append(
            {
                "phrase": phrase,
                "variant": variant,
                "weight": weight,
                "cooldown_matches": DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO[scenario],
                "conditions": _conditions_for_phrase(condition_brute, ligne_excel),
                "slots": _slots_for_phrase(phrase),
            }
        )

    scenarios_yaml = [
        {
            "code": code,
            "label": labels[code],
            "variants": _group_variants(rows),
        }
        for code, rows in rows_by_scenario.items()
    ]

    yml_path.parent.mkdir(parents=True, exist_ok=True)
    yml_path.write_text(yaml.safe_dump(scenarios_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")

    n_phrases = sum(len(r) for r in rows_by_scenario.values())
    logger.info(
        "%d scénarios, %d phrases écrits dans %s (%d ligne(s) ignorée(s))",
        len(scenarios_yaml),
        n_phrases,
        yml_path,
        skipped,
    )
    return n_phrases


def main(argv: list[str] | None = None) -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_YAML_PATH)
    args = parser.parse_args(argv)
    convertir(args.xlsx, args.out)


if __name__ == "__main__":
    main()
