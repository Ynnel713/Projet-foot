# 05: Tests NLG exécutables sous Linux (session cloud)

**What to build:** Les tests NLG cherchent l'interpréteur du sous-projet à un chemin Windows en dur (`simulafoot_nlg/.venv/Scripts/python.exe` : `tests/test_nlg_end_to_end.py:27`, `scripts/sample_nlg_output.py:36`). Sous Linux le venv donne `.venv/bin/python`, donc 5 tests sont toujours ignorés et la suite complète ne peut jamais atteindre le compte attendu. Le propriétaire ne code plus que dans les sessions cloud Linux (12/11/2026). `api/nlg_live.py:88` résout déjà les deux formes (`Scripts/python.exe`, puis `bin/python`) : aligner tests et script sur cette résolution (par l'API publique si elle existe, ticket 19), installer le venv NLG (`uv sync` dans `simulafoot_nlg/`, base `cli.py init-db / import-players / import-seed` si nécessaire) et l'ajouter au setup script de l'environnement `projet-foot`.

**Blocked by:** 04.

**Status:** à faire

## Critères d'acceptation

- [ ] Plus aucun chemin `Scripts/python.exe` en dur dans `tests/` et `scripts/` ; résolution identique à `api/nlg_live.py` (Windows et Linux).
- [ ] Session cloud : suite complète 2 754 passés, 0 ignoré, 14 désélectionnés.
- [ ] Setup script de `projet-foot` : venv NLG installé (commandes testées dans une session, puis confirmées dans une session neuve).

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 15 min |
| Tests | 15 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h** |

Temps machine, hors total : suite complète ~10 min en cloud.

Confiance : moyenne. Hypothèses : le NLG s'installe avec `uv sync` sans hôte réseau supplémentaire ; sa base de données se construit depuis les fichiers du dépôt.

## Comments
