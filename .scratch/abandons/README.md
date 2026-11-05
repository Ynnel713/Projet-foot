# Travaux abandonnés, archivés en patch

| Patch | Date d'abandon | Raison | Pour le reprendre |
|---|---|---|---|
| `animation-prechauffage-cache.patch` | 05/11/2026 | Préchauffage en tâche de fond de l'animation V1 après une journée simulée (`api/routers/competitions.py`, `tests/test_api_animation.py`). Refusé deux fois par le contrôle qualité (journal, 23/10/2026, sous-étape `animation-prechauffage-cache`) ; l'animation 2D V1 est désactivée depuis le 24/10/2026 (`70ca9d1`) : le calcul n'aurait servi à rien. Décision du propriétaire. | `git apply .scratch/abandons/animation-prechauffage-cache.patch` (contre `6ee5724`), puis nouvelle revue QC. |
