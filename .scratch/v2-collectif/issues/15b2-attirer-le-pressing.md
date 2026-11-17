# 15b2: Attirer le pressing en construction

**Découpé du ticket 15b le 17/11/2026** (décision du propriétaire : « je valide »). **Chantier :** `v2-collectif`. **Priorité :** P1. **Catégorie :** décision.

**Constat avant le code (17/11/2026) :** aucun mécanisme ne retarde la passe du porteur pour fixer un presseur ; le porteur réévalue ses options toutes les 0,5 s (`DECISION_INTERVAL_S`).

**What to build:** en construction (`bloc.builds_up`), quand un presseur arrive sur lui et que la passe qui suivrait son départ (l'espace qu'il libère) vaut plus que la meilleure passe actuelle, le porteur garde le ballon un court instant (fixation), puis joue l'espace libéré. Le risque de perdre le ballon pendant la fixation est celui de la conduite au contact (`keep_ball_probability`), amorti par Composure sous pression seulement (R3). La lecture du presseur à fixer réutilise le contexte « lecture du pressing » du 15b1, sans le recalculer (un effet, un calcul : à vérifier à l'ouverture, sinon un second contexte distinct).

**Hors de ce ticket :** le troisième homme (15b1) ; conduite nouvelle (la fixation est un délai de décision).

**Attributs (ADR 0002) :** contexte « lecture du pressing » (15b1) pour voir le presseur à fixer ; Composure, modulateur sous pression (R3) ; Dribbling garde la chance de garder le ballon au contact (inchangé). Poids et constantes à proposer à l'ouverture.

**Blocked by:** 15b1.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible. Hypothèses : la fixation est un délai de décision dans `match._step_ball`, sans nouvelle action ; la valeur de « l'espace libéré » se calcule par les options existantes avec le presseur projeté sur le porteur. Au seuil de 2 h : indivisible (la fixation sans le jeu de l'espace libéré n'a pas d'effet mesurable).
Temps machine, non compté : séries de 50 matchs avant et après ; suite complète.

## Acceptance criteria

- [ ] Constantes produit validées par le propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [ ] Scène : un presseur fixé libère une solution que le porteur joue ; sans presseur, pas de fixation
- [ ] Statistiques (50 matchs, avant et après) : fixations par match, passes vers l'espace libéré, pertes dans son propre tiers
- [ ] Effet probabiliste, jamais binaire ; plafond d'écart 99 / 11 ; rayon conforme à la carte, test de rayon à jour
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md` ; durée réelle relevée
