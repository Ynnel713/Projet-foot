# 01c: Repères de calibration : sources, définitions, compatibilité avec le banc

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les repères de l'audit ne deviennent bloquants qu'une fois leurs définitions vérifiées). **Catégorie :** documentation.

**Constat vérifié :** l'audit propose 8-15 tirs par équipe, 10-11 % de conversion, 80-90 % de buts dans la surface, 9-14 km, 5-20 appels, 2-5 % au-dessus de 19,8 km/h et 15-17 passes par minute ; `docs/INDICATEURS_V2.md` cite certaines sources, mais la définition d'un « appel » du banc (plus de 0,7 s au-dessus de 15 km/h) n'est pas forcément celle de la source (PLOS One 2022) et « temps » ou « distance » au-dessus de 19,8 km/h ne sont pas distingués.

**What to build:** Pour chacun des 7 repères : source primaire, population (ligue, saison), définition exacte, unité, indicateur du banc qui le mesure et écart de définition. Conclure pour chacun : critère bloquant, indicatif ou à redéfinir. Consigner dans `docs/INDICATEURS_V2.md` (nouvelle section « Repères de calibration »). Aucun code.

**Hors de ce ticket :** modification des indicateurs (01d).

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 01d, 14a, 18b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 1 h |
| Tests unitaires et comportementaux | 0 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : sources accessibles en ligne ; un repère introuvable est noté « non trouvé ».
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Intégration :** relecture croisée : chaque repère renvoie à un indicateur existant du banc ou à un indicateur à créer

## Acceptance criteria

- [ ] 7 repères documentés : source, définition, unité, indicateur correspondant, statut (bloquant, indicatif, à redéfinir)
- [ ] Écarts de définition entre source et banc listés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
