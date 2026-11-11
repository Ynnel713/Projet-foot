# 18a: Point d'étape après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (vérifier la cohérence des mécanismes avant tout réglage). **Catégorie :** validation.

**Constat vérifié :** les repères de l'audit sont loin (37,6 tirs par équipe, conversion 5,7 %, 54,7 % des buts dans la surface, mesure 28b) ; plusieurs causes possibles se recouvrent.

**What to build:** Série exploratoire de 50 matchs une fois les P0 livrés : rapport complet (structure, gardien, conduite, tirs, xG, physique), écarts aux repères du 01c attribués à un mécanisme ou à la calibration ; liste des tickets P1 à avancer ou à créer. Aucun réglage.

**Attributs :** aucun

**Blocked by:** 02h (Validation de la structure : côtés, rôles, appels, distances); 03g (Validation du placement et des sorties du gardien); 04c (Validation : risque annoncé, probabilité calculée, résultat observé); 05g (Validation des tirs : trajectoire, cadrage, contres, arrêts); 06b (Indicateurs : occasion, exécution, gardien, par attribut); 17a (Carte des attributs : état réel de branchement); 19a (Performance momentanée : façade des notes); 19b (Journal des événements et chaîne de causes); 19c (Garde probabiliste); 19d (Banc : rendement selon la minute) (ajouté le 10/11/2026, audit de la roadmap); 19e (Origine des buts) ; 19f (Banc : tranches au temps joué et contrôles par tentative) (ajouté le 11/11/2026, réserves de l'expert sur le 19d).

**Bloque :** 18d.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : rapport écrit, aucun code.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport complet

## Acceptance criteria

- [ ] Rapport publié dans `docs/INDICATEURS_V2.md`
- [ ] Chaque écart attribué (mécanisme ou calibration)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Ajouts au point d'étape, sans réglage : (1) section « condition physique » : ce que la fatigue change et ne change pas aujourd'hui (19d) ; (2) section « garde probabiliste » : résolutions hors garde (19c) et leur ticket ; (3) section « causalité » : part des buts par origine de chaîne (19b) ; (4) confirmation de l'ordre recommandé ensuite : 12d → 12e → 18d → 18e.

- [ ] Rapport complété des trois sections ci-dessus
