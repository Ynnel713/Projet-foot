# 11e: Validation des contacts physiques

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle de cohérence Strength / Balance / Agility). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur de contact hors tacles et fautes.

**What to build:** Indicateurs : collisions par match, duels d'épaule gagnés par écart de Strength, actions poursuivies après contact par Balance (12c). Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 11c (Duel épaule contre épaule à la course); 11d (Le tacle selon l'angle d'approche et la vitesse relative); 12c (Balance : rester debout et continuer après un contact).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Indicateurs définis et ajoutés
- [ ] Chaque attribut agit sur son seul effet (règle R1 vérifiée)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
