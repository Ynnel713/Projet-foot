"""Journalisation d'un usage de phrase : ecriture dans phrase_history.

`log_usage` est l'ECRIVAIN UNIQUE de phrase_history (decision D17) :
anti_repeat.update_cooldown l'appelle -- logger = journalisation, anti_repeat = decision de
penalite -- et recupere l'id insere pour y rattacher la signature de similarite
(similarity_signatures.history_id). `used_at` est pose par SQLite (`datetime('now')`, voir
data/schema.sql), source de temps unique ; l'unite de l'anti-repetition est `match_sequence`
(le rang du match), jamais cette date.

Ne COMMITE pas : la transaction appartient a l'appelant (update_cooldown y groupe l'historique
et la signature pour que l'un ne survive jamais sans l'autre).
"""

from __future__ import annotations

from sqlite3 import Connection

from engine.profile_engine import validate_match_sequence


def log_usage(
    conn: Connection,
    phrase_id: int,
    player_id: int | None,
    match_id: str,
    rendered_text: str,
    *,
    match_sequence: int,
) -> int:
    """Enregistre l'usage de `phrase_id` pour `player_id` sur `match_id` (rang `match_sequence`),
    texte final `rendered_text`. Retourne l'id insere (`phrase_history.id`).

    Leve ValueError, sans rien ecrire, si `phrase_id` est inconnu ou designe une phrase de
    secours (D10 : un fallback n'est jamais inscrit dans phrase_history -- il ne doit pas
    alimenter l'anti-repetition) ; ValueError/TypeError si `match_sequence` est invalide
    (voir profile_engine.validate_match_sequence)."""
    rang = validate_match_sequence(match_sequence)
    phrase = conn.execute("SELECT is_fallback FROM phrases WHERE id = ?", (phrase_id,)).fetchone()
    if phrase is None:
        raise ValueError(f"log_usage : phrase_id {phrase_id} inconnu.")
    if phrase[0]:
        raise ValueError(
            f"log_usage : phrase_id {phrase_id} est une phrase de secours (is_fallback) -- "
            "jamais inscrite dans phrase_history."
        )
    cur = conn.execute(
        """INSERT INTO phrase_history (phrase_id, player_id, match_id, match_sequence, rendered_text)
           VALUES (?, ?, ?, ?, ?)""",
        (phrase_id, player_id, match_id, rang, rendered_text),
    )
    if cur.lastrowid is None:  # pragma: no cover -- un INSERT reussi renseigne toujours lastrowid
        raise RuntimeError("log_usage : INSERT sans lastrowid.")
    return cur.lastrowid
