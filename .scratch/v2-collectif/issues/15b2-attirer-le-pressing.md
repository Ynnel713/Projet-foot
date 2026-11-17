# 15b2: Attirer le pressing en construction

**Découpé du ticket 15b le 17/11/2026** (décision du propriétaire : « je valide »). **Chantier :** `v2-collectif`. **Priorité :** P1. **Catégorie :** décision.

**Constat avant le code (17/11/2026) :** aucun mécanisme ne retarde la passe du porteur pour fixer un presseur ; le porteur réévalue ses options toutes les 0,5 s (`DECISION_INTERVAL_S`).

**What to build:** en construction (`bloc.builds_up`), quand un presseur arrive sur lui et que la passe qui suivrait son départ (l'espace qu'il libère) vaut plus que la meilleure passe actuelle, le porteur garde le ballon un court instant (fixation), puis joue l'espace libéré. Le risque de perdre le ballon pendant la fixation est celui de la conduite au contact (`keep_ball_probability`), amorti par Composure sous pression seulement (R3). La lecture du presseur à fixer réutilise le contexte « lecture du pressing » du 15b1, sans le recalculer (un effet, un calcul : à vérifier à l'ouverture, sinon un second contexte distinct).

**Hors de ce ticket :** le troisième homme (15b1) ; conduite nouvelle (la fixation est un délai de décision).

**Attributs (ADR 0002) :** contexte « lecture du pressing » (15b1) pour voir le presseur à fixer ; Composure, modulateur sous pression (R3) ; Dribbling garde la chance de garder le ballon au contact (inchangé). Poids et constantes à proposer à l'ouverture.

**Blocked by:** 15b1.

**Status:** clos sans objet (17/11/2026, décision du propriétaire : « Clore sans objet ») — suite au ticket `15b3-lecture-du-pressing-et-delai-apres-controle.md`

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

## Constantes validées puis mécanisme abandonné (17/11/2026)

Constantes validées par le propriétaire (« feu vert ») : même lecture que le 15b1 (un tirage) ; presseur à fixer = adversaire de champ le plus proche, entre 3 et 10 m, qui se rapproche à plus de 1 m/s ; fixer si la meilleure passe projetée (presseur engagé, retiré des lignes de passe) vaut au moins 1,25 fois la meilleure passe actuelle ; un intervalle de décision (0,5 s) au plus deux fois de suite ; pendant la fixation, sa meilleure conduite ; Composure non relue (choix du propriétaire : elle module déjà la lucidité sous pression, ticket 33).

Pendant le code : une première projection (presseur arrêté à 1 m, puis à 3 m sur sa course) ne libérait jamais la ligne, puisqu'un presseur qui court droit sur le porteur reste sur la ligne qu'il couvrait. Elle a été remplacée par « presseur retiré des lignes de passe ». La scène de test fixait alors comme prévu (9 tests écrits).

## Constat qui clôt le ticket (17/11/2026)

Sur un match de 90 min, 55 décisions du porteur en construction sous pressing : adversaire le plus proche à moins de 1,5 m dans 27 cas, entre 1,5 et 3 m dans 17, entre 3 et 10 m dans 11 seulement. Le presseur se rapprochait à plus de 1 m/s dans 2 cas, sans gain suffisant : **0 fixation** (0 aussi sur un essai de 20 min). Cause : après un contrôle, le porteur attend avant sa première décision (`possession.reception_delay_s`, ticket 31b : 2,3 s en moyenne, 1,84 à 2,76 s selon First Touch, au moins 3,5 s pour un gardien), et le presseur arrive pendant ce temps. Le moteur fait donc déjà attendre le porteur jusqu'à l'arrivée du presseur, mais toujours, sans choix ni lecture.

Décision du propriétaire (17/11/2026) : clore sans objet ; code retiré (dépôt revenu à l'état du commit `bd09fcc`), rien commité du mécanisme ; variante ouverte au ticket `15b3` : brancher la lecture du pressing sur le délai après contrôle.

## Durée

Estimée 2 h 10 ; passée environ 1 h 15 (analyse et proposition 25 min, code et tests 35 min, diagnostic et constat 15 min), mécanisme abandonné. Temps machine : un match de 90 min et un de 20 min de diagnostic.
