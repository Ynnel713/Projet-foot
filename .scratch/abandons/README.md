# Travaux abandonnés, archivés en patch

| Patch | Date d'abandon | Raison | Pour le reprendre |
|---|---|---|---|
| `animation-prechauffage-cache.patch` | 05/11/2026 | Préchauffage en tâche de fond de l'animation V1 après une journée simulée (`api/routers/competitions.py`, `tests/test_api_animation.py`). Refusé deux fois par le contrôle qualité (journal, 23/10/2026, sous-étape `animation-prechauffage-cache`) ; l'animation 2D V1 est désactivée depuis le 24/10/2026 (`70ca9d1`) : le calcul n'aurait servi à rien. Décision du propriétaire. | `git apply .scratch/abandons/animation-prechauffage-cache.patch` (contre `6ee5724`), puis nouvelle revue QC. |

## Tickets V1 en sommeil, supprimés

Supprimés le 27/11/2026 (décision du propriétaire : « Supprime les tickets en attente de la v1 ») : 11 tickets « en sommeil (04/11/2026) », mis en attente quand l'animation V1 a été désactivée (`70ca9d1`). Ils formaient à eux seuls 7 chantiers :
- `blessure-temps-fort` (01) ;
- `but-contre-son-camp` (01, 02) ;
- `but-refuse` (01, 02) ;
- `carton-rouge-autonome` (01, 02) ;
- `celebration-but` (01) ;
- `seance-tirs-au-but` (01, 02) ;
- `var-intervention-favorable` (01, 02).

Les mentions de ces chantiers ailleurs (`docs/PRD_PRODUIT.md`, `docs/AUDIT_ROADMAP_V2.md`, tickets V2 `21g`, `33`, spec `v2-mise-en-scene`) restent comme historique.

Pour les reprendre : `git checkout 8512f20 -- .scratch/<chantier>`.
