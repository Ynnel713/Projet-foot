# 06c: Contrôle de calibration de l'xG neutre sur 500 matchs

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'xG neutre doit prédire les buts des tireurs moyens). **Catégorie :** validation.

**Constat vérifié :** la formule de l'xG (`shooting._XG_LOGIT`) est ajustée sur une table cible ; aucune vérification sur les tirs du moteur.

**What to build:** Sur 500 matchs (01e), courbe de calibration : taux de buts observé par tranche d'xG neutre, pour les tireurs de note moyenne. Écarts rapportés et cause identifiée (exécution, gardien, contre) ; aucun réglage dans ce ticket.

**Attributs :** aucun

**Blocked by:** 06b (Indicateurs : occasion, exécution, gardien, par attribut); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 05e (La valeur du tir dans la décision suit la résolution physique).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : 500 matchs disponibles en temps machine.
Temps machine, non compté : suite complète (environ 40 min) ; série de 500 matchs.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs : courbe de calibration avec intervalles

## Acceptance criteria

- [ ] Courbe publiée avec intervalles de confiance
- [ ] Écarts expliqués par étage
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
