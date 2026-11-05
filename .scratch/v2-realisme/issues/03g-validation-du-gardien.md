# 03g: Validation du placement et des sorties du gardien

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la position doit être juste avant de calibrer les arrêts). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur sur la position du gardien (le banc ne mesure que les issues des arrêts, ticket 28b).

**What to build:** Indicateurs : écart à la bissectrice au moment des tirs, distance à sa ligne par zone du ballon, sorties par match et leur issue, distance maximale à son but. Scènes de référence rejouées et rapport sur 50 matchs ; aucune calibration du taux d'arrêt.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux); 03c (Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)); 03d (Gardien : sortie sur un ballon dans la profondeur); 03e (Gardien : fermer l'angle dans un face-à-face); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a, 18e.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture seule de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** indicateurs calculés sur trajectoires synthétiques
- **Statistiques (séries de matchs) :** 50 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Indicateurs définis par écrit et ajoutés au banc
- [ ] Rapport 50 matchs publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
