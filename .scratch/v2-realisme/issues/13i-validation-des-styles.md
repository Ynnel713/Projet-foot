# 13i: Validation des styles : des équipes différentes, pas meilleures

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le style déplace le risque, il ne doit pas créer de niveau). **Catégorie :** validation.

**Constat vérifié :** critère du ticket `v2-coach-et-gestion-de-match/01` : différence de buts non systématiquement en faveur d'un style.

**What to build:** Série appariée : chaque style contre le même adversaire neutre, 200 matchs par style (01e) ; indicateurs de style et différence de buts avec intervalle de confiance. Adaptation au score : tickets `v2-collectif/21` et `v2-coach-et-gestion-de-match/02`, non dupliqués ici.

**Attributs :** aucun

**Blocked by:** 13b (Style Pressing); 13c (Style Défensif); 13d (Style Offensif); 13e (Style Contre-attaque); 13f (Style Possession et tempo); 13g (Consigne de largeur); 13h (Rôles cohérents avec la formation); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : temps machine important (1 000 matchs).
Temps machine, non compté : suite complète (environ 40 min) ; série de 1 000 matchs.

## Tests

- **Statistiques (séries de matchs) :** 1 000 matchs appariés : rapport par style

## Acceptance criteria

- [ ] Chaque style mesurablement différent
- [ ] Aucun style systématiquement gagnant (intervalle de confiance)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
