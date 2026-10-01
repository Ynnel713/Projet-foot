"""YAML (data/seed/scenarios.yml, data/seed/slots.yml) -> SQLite.

Algorithme :
    1. Charger les deux YAML (erreur explicite si fichier absent/invalide).
    2. VALIDER integralement avant la moindre ecriture : chaque scenario a
       au moins une variante is_default=1 (contrainte du brief -- import
       refuse tout le fichier si un seul scenario y deroge, pas d'import
       partiel). Les references de dictionary_key vers slots.yml absentes
       sont loguees en avertissement (pas bloquant : un dictionnaire peut
       etre complete apres coup, ce n'est pas une erreur de structure).
    3. Inserer scenarios -> variants -> phrases -> phrase_conditions ->
       phrase_slots, puis slot_dictionaries, dans UNE SEULE transaction
       (voir engine.db.sqlite_transaction) : tout ou rien.
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import Any

import yaml

from engine.conditions import NOMS_CONDITIONNABLES
from engine.db import get_sqlite, sqlite_transaction

logger = logging.getLogger(__name__)

DEFAULT_SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "scenarios.yml"
DEFAULT_SLOTS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "slots.yml"


class SeedValidationError(ValueError):
    """Le YAML est bien forme mais viole une regle metier (ex. scenario sans
    variante par defaut) -- distinct d'une erreur de parsing YAML."""


@dataclass(frozen=True)
class SeedStats:
    scenarios: int
    variants: int
    phrases: int
    dictionaries: int


def _load_yaml(path: Path, expected_type: type) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Fichier seed introuvable : {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = expected_type()
    if not isinstance(data, expected_type):
        raise SeedValidationError(
            f"{path} : attendu un {expected_type.__name__} au niveau racine, trouvé {type(data).__name__}"
        )
    return data


def _validate_scenarios(scenarios: list[dict[str, Any]], known_slot_keys: set[str]) -> None:
    for scenario in scenarios:
        code = scenario.get("code", "<sans code>")
        variants = scenario.get("variants", [])
        if not any(v.get("is_default") for v in variants):
            raise SeedValidationError(
                f'Scénario "{code}" : aucune variante is_default=true -- import refusé '
                "(règle du brief : toujours une variante par défaut)."
            )
        for variant in variants:
            for phrase in variant.get("phrases", []):
                # Cooldown obligatoire (règle du README, confirmée par
                # l'audit éditorial du 30/09/2026, section cooldown) : une
                # phrase sans cooldown_matches explicite laisserait
                # phrase_cooldowns.cooldown_matches à NULL, et
                # phrase_selector (une fois implémenté) doit alors REFUSER la
                # phrase -- autant échouer l'import maintenant, tant qu'on
                # peut encore corriger la source (le classeur/le YAML),
                # plutôt que découvrir en production qu'une phrase ne sort
                # jamais faute de cooldown défini. Pas de valeur par défaut
                # silencieuse ici : le défaut (3 matchs) est appliqué en
                # AMONT, à la conversion (voir
                # scripts/convert_commentary_xlsx_to_yaml.DEFAULT_COOLDOWN_MATCHES),
                # jamais côté import.
                if phrase.get("cooldown_matches") is None:
                    raise SeedValidationError(
                        f'Scénario "{code}" : la phrase {phrase.get("text", "<sans texte>")!r} '
                        "n'a pas de cooldown_matches -- import refusé (règle \"cooldown "
                        "obligatoire\" du README, voir AUDIT_EDITORIAL_2026-09-30.md)."
                    )
                for condition in phrase.get("conditions", []):
                    # D16-fine : un nom d'attribut inconnu est une faute de frappe,
                    # a refuser ICI (la phrase serait sinon importee, puis ferait
                    # lever ValueError a la premiere selection). Un attribut FM26
                    # connu mais absent chez certains joueurs reste valide : il
                    # est ecarte a l'execution (D16), pas a l'import.
                    attribute = condition.get("attribute")
                    if attribute not in NOMS_CONDITIONNABLES:
                        proches = difflib.get_close_matches(str(attribute), sorted(NOMS_CONDITIONNABLES), n=1)
                        suggestion = f" Vouliez-vous dire {proches[0]!r} ?" if proches else ""
                        raise SeedValidationError(
                            f'Scénario "{code}" : la phrase {phrase.get("text", "<sans texte>")!r} '
                            f"conditionne sur {attribute!r}, inconnu (ni champ Player, ni "
                            f"MatchContext, ni attribut FM26, ni preferred_moves).{suggestion}"
                        )
                for slot in phrase.get("slots", []):
                    key = slot.get("dictionary_key")
                    if key is not None and key not in known_slot_keys:
                        logger.warning(
                            'Scénario "%s" : le slot "%s" référence le dictionnaire "%s", '
                            "absent de slots.yml (à compléter plus tard, import poursuivi).",
                            code,
                            slot.get("slot_name"),
                            key,
                        )


def _insert_scenarios(conn: Connection, scenarios: list[dict[str, Any]]) -> tuple[int, int, int]:
    n_scenarios = n_variants = n_phrases = 0
    for scenario in scenarios:
        cur = conn.execute(
            "INSERT INTO scenarios (code, label, description, is_active) VALUES (?, ?, ?, ?)",
            (
                scenario["code"],
                scenario["label"],
                scenario.get("description"),
                int(scenario.get("is_active", True)),
            ),
        )
        scenario_id = cur.lastrowid
        n_scenarios += 1

        for variant in scenario.get("variants", []):
            cur = conn.execute(
                """INSERT INTO variants (scenario_id, code, label, is_default, weight, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    scenario_id,
                    variant["code"],
                    variant["label"],
                    int(variant.get("is_default", False)),
                    variant.get("weight", 1.0),
                    int(variant.get("is_active", True)),
                ),
            )
            variant_id = cur.lastrowid
            n_variants += 1

            for phrase in variant.get("phrases", []):
                phrase_is_active = int(phrase.get("is_active", True))
                cur = conn.execute(
                    "INSERT INTO phrases (variant_id, text, weight, is_active) VALUES (?, ?, ?, ?)",
                    (variant_id, phrase["text"], phrase.get("weight", 1.0), phrase_is_active),
                )
                phrase_id = cur.lastrowid
                n_phrases += 1

                # cooldown_matches deja valide non-NULL par _validate_scenarios
                # (regle "cooldown obligatoire") -- une ligne par phrase, PK
                # phrase_id (voir data/schema.sql : le cooldown est une
                # propriete de la PHRASE, pas du couple phrase x joueur, qui
                # lui vit dans phrase_history).
                conn.execute(
                    "INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, ?)",
                    (phrase_id, int(phrase["cooldown_matches"])),
                )

                for condition in phrase.get("conditions", []):
                    conn.execute(
                        """INSERT INTO phrase_conditions (phrase_id, attribute, operator, value, mandatory)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            phrase_id,
                            condition["attribute"],
                            condition["operator"],
                            str(condition["value"]),
                            int(condition.get("mandatory", True)),
                        ),
                    )
                for slot in phrase.get("slots", []):
                    conn.execute(
                        """INSERT INTO phrase_slots (phrase_id, slot_name, dictionary_key, expression)
                           VALUES (?, ?, ?, ?)""",
                        (phrase_id, slot["slot_name"], slot.get("dictionary_key"), slot.get("expression")),
                    )
    return n_scenarios, n_variants, n_phrases


def _insert_slot_dictionaries(conn: Connection, dictionaries: dict[str, list[dict[str, Any]]]) -> int:
    n = 0
    for dictionary_key, entries in dictionaries.items():
        for entry in entries:
            conn.execute(
                "INSERT INTO slot_dictionaries (dictionary_key, value, weight) VALUES (?, ?, ?)",
                (dictionary_key, entry["value"], entry.get("weight", 1.0)),
            )
            n += 1
    return n


def import_seed(
    sqlite_path: str | Path,
    scenarios_path: str | Path = DEFAULT_SCENARIOS_PATH,
    slots_path: str | Path = DEFAULT_SLOTS_PATH,
) -> SeedStats:
    scenarios = _load_yaml(Path(scenarios_path), list)
    dictionaries = _load_yaml(Path(slots_path), dict)

    _validate_scenarios(scenarios, known_slot_keys=set(dictionaries))

    conn = get_sqlite(sqlite_path)
    try:
        with sqlite_transaction(conn):
            n_scenarios, n_variants, n_phrases = _insert_scenarios(conn, scenarios)
            n_dictionaries = _insert_slot_dictionaries(conn, dictionaries)
    finally:
        conn.close()

    stats = SeedStats(
        scenarios=n_scenarios, variants=n_variants, phrases=n_phrases, dictionaries=n_dictionaries
    )
    logger.info(
        "%d scénarios, %d variantes, %d phrases, %d entrées de dictionnaire importés",
        stats.scenarios,
        stats.variants,
        stats.phrases,
        stats.dictionaries,
    )
    return stats
