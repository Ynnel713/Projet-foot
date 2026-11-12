# 05: Tests NLG exécutables sous Linux (session cloud)

**What to build:** Les tests NLG cherchent l'interpréteur du sous-projet à un chemin Windows en dur (`simulafoot_nlg/.venv/Scripts/python.exe` : `tests/test_nlg_end_to_end.py:27`, `scripts/sample_nlg_output.py:36`). Sous Linux le venv donne `.venv/bin/python`, donc 5 tests sont toujours ignorés et la suite complète ne peut jamais atteindre le compte attendu. Le propriétaire ne code plus que dans les sessions cloud Linux (12/11/2026). `api/nlg_live.py:88` résout déjà les deux formes (`Scripts/python.exe`, puis `bin/python`) : aligner tests et script sur cette résolution (par l'API publique si elle existe, ticket 19), installer le venv NLG (`uv sync` dans `simulafoot_nlg/`, base `cli.py init-db / import-players / import-seed` si nécessaire) et l'ajouter au setup script de l'environnement `projet-foot`.

**Blocked by:** 04.

**Status:** livré (12/11/2026), validé expert + QC

## Critères d'acceptation

- [x] Plus aucun chemin `Scripts/python.exe` seul en dur dans `tests/` et `scripts/` : `NLG_PYTHON` essaie `Scripts/python.exe` puis `bin/python`, même ordre qu'`api/nlg_live.py:88` (fonction privée, non importée : ticket 19). Si aucun n'existe, le chemin retourné n'existe pas et les `skipif` s'appliquent comme avant.
- [x] Session cloud : suite complète 2 754 passés, 0 ignoré, 14 désélectionnés (12/11/2026, 9 min 21 ; avant : 2 749 passés, 5 ignorés).
- [x] Setup script de `projet-foot` : `uv sync` dans `simulafoot_nlg/` ajouté, commande testée dans cette session depuis le répertoire de départ du script. Confirmation dans une session neuve : à faire (point à vérifier).
- [x] `tests/test_nlg_end_to_end.py` + `tests/test_export_match_to_nlg.py` : 8 passés, 0 ignoré (avant : 5 ignorés). Arbre git inchangé après exécution (aucun fichier écrit dans le dépôt).

Hors critères : `tests/test_nlg_echantillon.py` (marqueur `integration`, désélectionné par défaut) exige aussi la base réelle `simulafoot_nlg/data/simulafoot.db`, absente du dépôt ; non traité ici.

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

**12/11/2026, passage 1.** Expert : APPROVED. QC : VALIDÉ. Clôture : VALIDÉ.
- A1 [facultatif] : la docstring de `scripts/export_match_to_nlg.py:5` donne encore l'exemple Windows `.venv/Scripts/python cli.py narrate ...` (documentation, pas un chemin exécuté).
- Point à vérifier : dans une session cloud neuve, le setup script doit installer le venv NLG ; sans lui, les 5 tests NLG redeviennent ignorés (2 749 passés).

**Durée.** Estimée 1 h, réelle environ 45 min (− 25 %, non chronométrée) : `api/nlg_live.py` résolvait déjà les deux chemins, la base NLG n'était pas nécessaire aux tests par défaut.
