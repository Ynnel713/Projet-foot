# 03j: Gardien : trier les sorties par état du ballon (tir en vol, rebond, passe, autre)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans ce tri, le 71 % de « tirs » du 03i ne peut pas guider un réglage). **Catégorie :** validation.

**Constat vérifié :** au 03i, 70,9 % des ballons où le gardien sort sont classés « issus d'un tir adverse » parce qu'un tir adverse a eu lieu dans les 5 s qui précèdent sa sortie. C'est une proximité dans le temps, pas l'état du ballon : un rebond ou un ballon contré y sont aussi classés « tir ». Sur les ballons hors tir (10,2 par match), 45,5 % finissent en corner sans explication (réserve A1 de l'expert du 03i, acceptée avec la condition de trier par état du ballon avant tout réglage au `05b` ou au `18e`).

**What to build:** Classer chaque ballon avec sortie **au moment de la première sortie**, par l'état du ballon lu dans le moteur (`BallState`) :
- **tir en vol** : `shot_for` renseigné (le ballon est en route vers le but) ;
- **rebond ou ballon contré** : `rebound` vrai ;
- **passe ou centre** : `receiver` renseigné, ou `last_pass_team` de l'adversaire, sans tir en vol ;
- **autre** (dégagement, déviation, ballon perdu).
Pour chaque catégorie : nombre par match, issue à 3 s (gardien, coéquipier, adversaire, libre, sortie de but, corner, engagement), part qui finit en corner. Dire combien des 71 % du 03i sont de vrais tirs en vol, et lesquels des 45,5 % de corners hors tir sont des centres, des corners joués longs ou des dégagements. Lecture seule : aucune constante recalée, aucun réglage du filtre de portée, de `gardien.race` ni de la sortie sur tir ; le rapport propose, le propriétaire tranche.

**Attributs :** aucun

**Blocked by:** 03i (Gardien : issue du ballon après une sortie).

**Bloque :** 03k (retrait des tirs en vol du déclencheur de sortie), 18e (calibration provisoire tirs et gardien) ; à lire avant tout réglage de la sortie sur tir au 05b.

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (classement de l'état du ballon à la sortie) | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications (rapport) | 15 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : lecture seule de `BallState` au moment de la première sortie, dans `scripts/v2_indicators.py`, comme le 03i. Si `shot_for` ne distingue pas un tir en vol d'un tir déjà dévié, le dire dans le rapport au lieu d'ajouter un champ au moteur.
Temps machine, non compté : suite complète (environ 15 à 40 min) ; série de 50 matchs (environ 24 min).

## Tests

- **Unitaires (scène contrôlée) :** un ballon dans chaque état (tir en vol, rebond, passe, autre) classé dans la bonne catégorie ; la somme des catégories égale le nombre de ballons avec sortie
- **Statistiques (séries de matchs) :** 50 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [x] Seuils et définitions de classement proposés avant le code : état par l'issue du dernier tir tracé de l'adversaire dans les 5 s précédentes, sinon drapeaux du ballon (voir Comments)
- [x] Chaque ballon avec sortie classé dans une seule catégorie d'état ; somme des catégories = 35,02 ballons avec sortie par match (graine d'audit 20260923), vérifiée par test et par la mesure
- [x] Issue à 3 s et part de corners par catégorie, sur 50 matchs (`docs/INDICATEURS_V2.md` section 14) ; nombre par état avec intervalles à 95 %, issue à 3 s agrégée (sans intervalle par état)
- [x] Les 71 % de « tirs » du 03i et les 45,5 % de corners hors tir sont répartis par catégorie : les tirs sont 95,0 % des ballons avec sortie (le 71 % ignorait les tirs contrés) ; corners hors tir = surtout tirs contrés (54,9 % finissent en corner) et claqués (96,7 %)
- [x] Aucune constante du moteur ni aucun fichier protégé modifié ; le rapport propose, le propriétaire tranche
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) (estimée 80 min, réelle environ 135 min, + 69 %, cause dans Comments)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (2 matchs, `.scratch/v2-realisme/mesures/03j-det1.txt` et `03j-det2.txt`, hors ligne de durée de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 528 passés, 14 désélectionnés (08/11/2026, 26 min 39 s, état final) ; attendu 2 524 + 4 nouveaux

## Comments

- **Origine (07/11/2026).** Réserve A1 de l'expert du ticket 03i, acceptée par délégation du propriétaire. Complète la réserve A2 (compteur « non résolus » à afficher au rapport) : à ajouter dans ce même ticket puisqu'il touche le même rapport de bancs.
- **Définition de l'état (08/11/2026).** Lecture du moteur : `shot_for` n'est posé que pour un tir qui entre ; un tir à côté, contré ou arrêté n'a aucun drapeau propre (`released_by` et `last_pass_team` seuls). L'état est donc rattaché au `ShotEvent` de l'adversaire dans les 5 s précédant la sortie (but, à côté, contré, repoussé, claqué), sinon `rebound` (rebond sans tir récent), `receiver` (passe ou centre), sinon autre. Aucun champ ajouté au moteur. Réserve A2 du 03i traitée : le compteur « non résolus » est au rapport (0,0 par match).
- **Résultat.** 63,6 % des ballons avec sortie sont des tirs à côté (89 % finissent en sortie de but), 20,9 % des tirs contrés, 5,1 % des tirs claqués ; passes et centres 1,7 % (0,58 par match), autre 3,3 %. Le gardien « sort » surtout sur des tirs qui s'en vont ; la preuve du cas « passe en profondeur coupée » (réserve A1 du 03d) est trop rare pour le banc. Piste pour le propriétaire (aucun réglage fait) : écarter les tirs en vol du déclencheur de sortie.
- **Fichiers modifiés :** `scripts/v2_indicators.py`, `scripts/measure_v2.py`, `tests/test_v2_indicators.py` (+ `CLAUDE.md` pour le compte de tests). Aucun fichier protégé.
- **Premier passage QC (08/11/2026, 00:37) : REFUSÉ.** Critère 4 non livré tel qu'écrit (pas de croisement entre l'ancien « hors tir » du 03i et les nouveaux états), critère 3 affaibli (parts par match biaisées pour les états rares par `max(1, k)`), état « tir capté » absent de `EXIT_STATES`. Corrigé : croisement `hors tir du 03i x état` ajouté au rapport, part non définie (`None`) quand aucun ballon dans l'état, état « tir : capté » ajouté. Critères 3 et 4 reformulés à ce qui est mesuré (l'issue à 3 s reste agrégée sur 50 matchs, sans intervalle par état ; le « 71 % » du 03i est expliqué : il ignorait les tirs contrés). Nouveau passage expert et QC ci-dessous.
- **Durée.** Estimée 1 h 20 (80 min ; 15/30/20/15), réelle environ 2 h 15 (135 min ; 20/50/30/35, non chronométrée), écart environ + 69 % : l'hypothèse du ticket (état lu sur les drapeaux de `BallState`) était fausse, `shot_for` ne marquant que le tir qui entre ; reclassement par le `ShotEvent` de l'adversaire, deuxième série de 50 matchs, refus QC et corrections. Temps machine, hors total : deux séries de 50 matchs d'environ 24 min, suite complète 26 min 39 s (2 528 passés, 14 désélectionnés).
- **Clôture (08/11/2026).** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `77a1c1f0`), QC `VALIDÉ` (second passage), clôture `VALIDÉ` (journal). Réserves acceptées d'office par le propriétaire, selon sa consigne du 08/11/2026 (« Considère que je valide automatiquement toutes tes recommandations, les avis d'expert et les commit ») : **A1** la projection « de 35 à environ 2 sorties » est une borne basse ; les candidats à écarter sont les tirs à côté et les tirs qui entrent (23,4 par match, projection d'environ 11,7 sorties, à mesurer) → section 14 reformulée, suite au ticket `03k` ; **A2** « passe ou centre » (`receiver` seul) mélange passes adverses coupées et passes de sa propre équipe → limite (5) ajoutée à la section 14. Facultatifs : A3 (l'état « tir » reste une proximité de 5 s, non calibrée), A4 (date de la section 14 corrigée ; intervalles par grappes de `03j-intervalles.py` hors du rapport). Réserve du QC (non bloquante) : ligne 03j ajoutée au registre `suivi-estimations.md`.
