"""Charge scenarios/variantes/phrases (+ leurs conditions/slots) depuis
SQLite -- lecture seule, aucune ecriture ici (voir scripts/import_seed.py
pour le peuplement). Chaque `load_*` retourne des objets `engine.models`
types, jamais des sqlite3.Row bruts."""

from __future__ import annotations

from sqlite3 import Connection

from engine.models import Phrase, PhraseCondition, PhraseSlot, Scenario, Variant


def load_scenario(conn: Connection, code: str) -> Scenario | None:
    """Le Scenario dont le code est `code`, ou None s'il n'existe pas --
    pas d'exception : un scenario absent est un cas attendu (ex. code
    fourni par un CLI avant que la banque ne soit chargee), a l'appelant de
    decider quoi en faire."""
    row = conn.execute(
        "SELECT id, code, label, description, is_active FROM scenarios WHERE code = ?",
        (code,),
    ).fetchone()
    if row is None:
        return None
    return Scenario(
        id=row["id"],
        code=row["code"],
        label=row["label"],
        description=row["description"],
        is_active=bool(row["is_active"]),
    )


def load_variants(conn: Connection, scenario_id: int) -> list[Variant]:
    """Toutes les variantes actives ou non d'un scenario -- filtrer sur
    `is_active`/choisir la variante par defaut est la responsabilite de
    l'appelant (phrase_selector), pas de ce chargement."""
    rows = conn.execute(
        """SELECT id, scenario_id, code, label, is_default, weight, is_active
           FROM variants WHERE scenario_id = ?""",
        (scenario_id,),
    ).fetchall()
    return [
        Variant(
            id=row["id"],
            scenario_id=row["scenario_id"],
            code=row["code"],
            label=row["label"],
            is_default=bool(row["is_default"]),
            weight=row["weight"],
            is_active=bool(row["is_active"]),
        )
        for row in rows
    ]


def load_phrase_conditions(conn: Connection, phrase_id: int) -> list[PhraseCondition]:
    rows = conn.execute(
        "SELECT id, phrase_id, attribute, operator, value, mandatory "
        "FROM phrase_conditions WHERE phrase_id = ?",
        (phrase_id,),
    ).fetchall()
    return [
        PhraseCondition(
            id=row["id"],
            phrase_id=row["phrase_id"],
            attribute=row["attribute"],
            operator=row["operator"],
            value=row["value"],
            mandatory=bool(row["mandatory"]),
        )
        for row in rows
    ]


def load_phrase_slots(conn: Connection, phrase_id: int) -> list[PhraseSlot]:
    rows = conn.execute(
        "SELECT id, phrase_id, slot_name, dictionary_key, expression FROM phrase_slots WHERE phrase_id = ?",
        (phrase_id,),
    ).fetchall()
    return [
        PhraseSlot(
            id=row["id"],
            phrase_id=row["phrase_id"],
            slot_name=row["slot_name"],
            dictionary_key=row["dictionary_key"],
            expression=row["expression"],
        )
        for row in rows
    ]


def load_phrases(conn: Connection, variant_id: int) -> list[Phrase]:
    """Toutes les phrases d'une variante, conditions et slots deja attaches
    (voir load_phrase_conditions/load_phrase_slots) -- un Phrase retourne
    ici est complet, l'appelant n'a pas besoin de requeter davantage."""
    rows = conn.execute(
        "SELECT id, variant_id, text, weight, is_active FROM phrases WHERE variant_id = ?",
        (variant_id,),
    ).fetchall()
    return [
        Phrase(
            id=row["id"],
            variant_id=row["variant_id"],
            text=row["text"],
            weight=row["weight"],
            is_active=bool(row["is_active"]),
            conditions=tuple(load_phrase_conditions(conn, row["id"])),
            slots=tuple(load_phrase_slots(conn, row["id"])),
        )
        for row in rows
    ]
