"""Convention : chaque fichier source `X.py` a son fichier de tests
`test_X.py`. Les tests d'une fonction définie dans `A.py` vivent dans
`test_A.py`, même si la fonction est utilisée ailleurs (brief "Trois manques
a combler avant cloture", 24/09/2026, Tâche 1 -- convention déjà appliquée
de fait dans ce dépôt, jamais écrite avant ce fichier).

Run par défaut : `pytest` -- exclut les tests `integration` (~5 s). Run
complet : `pytest -m integration` (~30 min, 100 matchs simulés), à lancer
avant tout commit touchant `narrative_player.py`, `sequence_generator.py`,
`ball.py`, `templates.py`, ou le moteur de résultats (brief "mark
narrative_player integration tests", 24/09/2026, voir le marqueur
`integration` déclaré dans pyproject.toml)."""

import pytest

from v2engine.flux import seed_streams


@pytest.fixture(autouse=True)
def _flux_v2_ressemes() -> None:
    """Flux aléatoires du moteur V2 (ticket v2-realisme/01a) ressemés avant chaque test : un test ne dépend pas de
    l'ordre d'exécution ni des tirages des tests précédents (un test qui sème `random` sème aussi les flux s'il en
    a besoin, voir `tests/scenes.seed_scene`)."""
    seed_streams(0)
