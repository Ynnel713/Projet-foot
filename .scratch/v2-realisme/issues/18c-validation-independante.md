# 18c: Validation indépendante sur 1 000 à 2 000 matchs

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (clôt le chantier après la calibration). **Catégorie :** validation.

**Constat vérifié :** voir 18b.

**What to build:** Exécuter la série réservée après les calibrations `v2-collectif/22a`, `22b` et `22c`, appliquer la règle de décision figée, publier le rapport. Un écart déclenche un ticket, jamais un réglage dans ce ticket.

**Attributs :** aucun

**Blocked by:** 18b (Protocole de validation indépendante); `v2-collectif/22c`.

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : temps machine de plusieurs heures.
Temps machine, non compté : suite complète (environ 40 min) ; série de 1 000 à 2 000 matchs.

## Tests

- **Statistiques (séries de matchs) :** 1 000 à 2 000 matchs sur graines réservées

## Acceptance criteria

- [ ] Rapport publié avec intervalles
- [ ] Écarts transformés en tickets
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
