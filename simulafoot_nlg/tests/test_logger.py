"""logger.log_usage est un SQUELETTE (voir engine/logger.py) -- même
raisonnement que test_phrase_selector.py. Absent de l'arborescence tests/ du
brief, mais requis par la règle "chaque fonction publique a un test" (pas de
code mort) : logger.log_usage est une fonction publique, elle en a une."""

from __future__ import annotations

import pytest

from engine.logger import log_usage


def test_log_usage_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        log_usage(sqlite_conn, phrase_id=1, player_id=1, match_id="m1", rendered_text="Quel but !")


def test_log_usage_error_message_names_the_module(sqlite_conn):
    with pytest.raises(NotImplementedError, match="logger.log_usage"):
        log_usage(sqlite_conn, phrase_id=1, player_id=None, match_id="m1", rendered_text="Quel but !")
