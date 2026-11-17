# 11k: Validation de l'évitement entre coéquipiers en match

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026). **Priorité :** P0 (suite du 11f, priorité absolue du propriétaire). **Catégorie :** validation.

**Constat vérifié :** voir 11f (337 contacts francs par match entre coéquipiers, 1 099 déséquilibres par match).

**What to build:** Série appariée de 50 matchs avant / après le 11f avec les indicateurs du 11e ; réglage des constantes du 11f si la cible n'est pas atteinte (nouvelle valeur proposée au propriétaire avant tout changement) ; vérifier que l'évitement ne casse ni le pressing à deux, ni les appels croisés, ni le soutien court (coéquipiers volontairement proches).

**Attributs :** aucun

**Blocked by:** 11f (Évitement entre coéquipiers, livré) ; 11g (Une seule décision par ballon) ; 11j (Cibles de placement écartées, sans objet le 15/11/2026 : abandonné, le 11g ayant déjà supprimé les cibles confondues).

**Bloque :** rien.

**Status:** livré (15/11/2026), validé expert (avec réserves acceptées) + QC (cible de 30 contacts non atteinte : constat clos sur décision du propriétaire, suites 11l et 11m)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : pas de réglage nécessaire ; un réglage ajoute environ 30 min et une série.
Temps machine, non compté : deux séries de 50 matchs (environ 35 min chacune sur 3 cœurs) ; suite complète.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs appariés : contacts francs entre coéquipiers, déséquilibres, rythme

## Acceptance criteria

- [ ] (non atteint : 106,5 ; constat clos par le propriétaire, suite au 11m) Contacts francs entre coéquipiers : de 337 à **30 par match au plus** (cible indicative à confirmer par le propriétaire avec les constantes du 11f)
- [x] Déséquilibres (contacts perdus) en baisse d'au moins 300 par match
- [x] (régression des pressings déclenchés − 29 ± 17 et de la récupération en 5 s après pressing 0,215 → 0,194, acceptée par le propriétaire le 15/11/2026 comme effet attendu du 11g, réserve A1 de l'expert) Sans régression significative sur : buts, tirs, passes réussies, pressings déclenchés, appels, distance entre les lignes ; écarts de rythme (passes, temps de jeu effectif, km) rapportés et expliqués
- [x] Contacts francs entre adversaires rapportés (attendu : peu changés)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, réserve A1 du 11g acceptée par le propriétaire** : mesurer ici les changements de chasseur désigné sur ballon libre en moins de 1 s ; si le taux est notable, désigner par le temps d'arrivée au point du ballon avec une marge de maintien.

**15/11/2026, découpage décidé par le propriétaire.** Après le diagnostic du 11f (contacts restants : deux coéquipiers sur le même ballon libre, deux presseurs sur le même porteur, cibles de placement quasi confondues), le propriétaire choisit d'agir sur la décision (« On ne corrige pas une erreur de décision par un patch physique ») : ancien 11g découpé en 11g (une seule décision par ballon), 11j (cibles écartées) et ce ticket, renuméroté 11k (validation sur 50 matchs). À mesurer en plus : sorties du gardien, réceptions réussies, ballons libres récupérés (condition de l'expert, 11f), et récupération sur ballon libre (risque du 11g).

**15/11/2026, démarrage.** Estimation réannoncée : **2 h** (analyse 15, développement 30, tests 25, intégration 50), confiance moyenne : deux indicateurs du banc à écrire (stabilité du chasseur, réserve A1 du 11g ; ballons libres récupérés, condition de l'expert au 11f) ; au seuil de découpage, non découpé (indicateurs propres à cette validation). Critères : ceux ci-dessous ; aucun réglage dans ce ticket sans valeur validée.

**15/11/2026, indicateurs.** `scripts/v2_indicators.py` : `Collector.on_free_ball_role` et `_free_ball_chase` (chasseurs par équipe et par pas, changements de chasseur et en moins de 1 s, épisodes de ballon libre disputé et leur issue), `CHASER_SWITCH_S` (seuil de mesure) ; `scripts/measure_v2.py` : branchement sur `match.think`, rapport `free_ball_report`. Tests : `tests/test_v2_indicators_ballon_libre.py` (4). Le banc observe sans changer le jeu (déterminisme ci-dessous).

**15/11/2026, séries (`docs/INDICATEURS_V2.md` section 47).** 50 matchs appariés, avant le 11f (`c84f77e`) contre maintenant : contacts francs entre coéquipiers **336,5 → 106,5 par match** (− 230 ± 12, cible de 30 non atteinte) ; contacts perdus − 420 ± 24 (critère atteint) ; entre adversaires 660 → 509 (moins de duels d'épaule) ; buts, tirs, appels, temps de jeu effectif, sorties du gardien sans écart significatif ; passes réussies + 1,9 point, receveur visé + 2,3 points, passes − 18 ; pressings déclenchés − 29, récupération en 5 s après pressing 0,215 → 0,194, km − 4 % environ (un seul presseur et un seul chasseur, 11g). Chasseur désigné : 21 % des désignations changent de joueur en moins de 1 s. Première série « avant » tuée par manque de mémoire (deux séries en parallèle), relancée seule.

**15/11/2026, décisions du propriétaire.** Cible : « Clore, suite en ticket (Recommandé) » : ticket **11m** (contacts restants, diagnostic d'abord). Chasseur et pressing : « Ticket chasseur stable (Recommandé) » : ticket **11l** ; recul du pressing et des km documenté comme effet attendu du 11g.

**15/11/2026, déterminisme et suite.** `measure_v2 2` avec le banc du 11k (`11k-det1.txt`) : identique à `11g-det1.txt` hors temps de calcul et nouvelles lignes du ballon libre (le banc observe sans changer le jeu ; même moteur). Suite complète : 3 176 passés, 0 ignoré, 14 désélectionnés (3 172 + 4) ; `CLAUDE.md` mis à jour. V1 inchangée.

**15/11/2026, durée.** Estimation du ticket 1 h 20, réannoncée 2 h au démarrage (indicateurs du banc) ; durée réelle environ 1 h 35 (analyse 15, développement 25, tests 10, intégration 45), − 21 % sur l'annonce, + 19 % sur l'estimation du ticket : indicateurs plus simples que prévu ; intégration allongée par la série « avant » tuée (mémoire) et relancée, la rédaction des tickets 11l et 11m. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : trois séries de 50 matchs (dont une tuée), une mesure de 2 matchs, suite complète (13 min).

**15/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11k/cloture`, réserves acceptées). A1 [réserve] : critère « sans régression significative » coché malgré le recul des pressings déclenchés (− 29 ± 17) ; critère annoté. A2 [réserve] : avant / après du ballon libre non comparable (définition d'épisode changée par le 11g) ; section 47 nuancée, référence du 11l : série « après » du 11k. A3 [réserve] : documentation hors du périmètre revu ; sans objet, le verrou admet le suivi documentaire (`docs/`, `.scratch/`). A4 [facultatif] : `min(names)` choisit le chasseur par le nom quand une équipe en a plusieurs (cas nul depuis le 11g), non traité. **Réserves acceptées par le propriétaire** : « Accepter A1, A2, A3 (Recommandé) ».
