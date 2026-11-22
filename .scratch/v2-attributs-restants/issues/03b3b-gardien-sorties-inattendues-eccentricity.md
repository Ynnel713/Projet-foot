# 03b3b: Gardien : sorties inattendues (Eccentricity)

**Découpé du ticket `03b3` le 22/11/2026.** Référence : Eccentricity 40, médiane des 50 gardiens notés de Ligue 1 de la base (de 25 à 85).

**What to build:** Eccentricity (tendance : goût du risque) donne au gardien des sorties inattendues : sur un ballon libre qu'il ne devrait pas disputer d'après la course (`gardien.race`), un gardien excentrique tente parfois sa chance, une fois par action (mémoire du « coup de tête » à créer, pour ne pas tirer à chaque tick ni changer d'avis aussitôt). Imprévisible : peut sauver ou couler son équipe ; le niveau moyen ne change pas. Dribbles du gardien dans sa surface : au `10b`.

**Attributs :** Eccentricity.

**Blocked by:** `03b3a`.

**Bloque :** `10b` ; `v2-coach-et-gestion-de-match/04`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 40 min |
| Tests | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (mécanisme à créer). Temps machine, non compté : suite complète ; 50 matchs appariés.

## Acceptance criteria

- [ ] Constantes proposées au propriétaire avant le code
- [ ] Eccentricity élevée : plus de sorties inattendues (scène et matchs), sans changer le niveau moyen
- [ ] Une décision par action : pas de tirage à chaque tick, pas d'aller-retour
- [ ] Test de rayon et carte à jour
- [ ] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée
