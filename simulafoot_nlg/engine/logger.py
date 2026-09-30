"""SQUELETTE -- journalisation d'un usage de phrase (ecriture dans
phrase_history). Aucune implementation dans cette session, bien que
l'operation elle-meme soit un simple INSERT SQL : classee squelette au meme
titre que les autres briques du brief pour que sa premiere implementation
tranche explicitement l'articulation avec anti_repeat.update_cooldown (qui a
aussi besoin d'ecrire une trace d'usage, voir engine/anti_repeat.py) --
eviter une double ecriture de phrase_history depuis deux modules differents.

Algorithme prevu :
    INSERT INTO phrase_history (phrase_id, player_id, match_id,
    rendered_text, used_at) -- `used_at` via `datetime('now')` cote SQLite
    (voir data/schema.sql), pas calcule en Python (source de temps unique).
    A l'implementation : decider si anti_repeat.update_cooldown APPELLE
    logger.log_usage (source unique d'ecriture) ou si c'est l'inverse --
    ne pas dupliquer l'ecriture dans les deux modules.
"""

from __future__ import annotations

from sqlite3 import Connection


def log_usage(
    conn: Connection, phrase_id: int, player_id: int | None, match_id: str, rendered_text: str
) -> None:
    """Enregistre l'usage de `phrase_id` pour `player_id` sur `match_id`,
    texte final `rendered_text` -- voir algorithme prevu en tete de module.
    Leve NotImplementedError tant que la banque de phrases n'est pas livree."""
    raise NotImplementedError(
        "logger.log_usage : squelette non implémenté -- voir la docstring "
        "de engine/logger.py pour l'algorithme prévu."
    )
