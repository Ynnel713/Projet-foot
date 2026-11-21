# 29c: Défenseur collé devant le receveur : il gagne trop peu le ballon

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (physique, réalisme).

**Constat vérifié (20/11/2026, `18o`) :** sur des matchs joués (graines 2400 à 2447 et 2500 à 2547), quand un adversaire est à moins de 1,5 m du receveur, entre le passeur et lui, la passe n'est pas perdue dans environ 61 % des cas ; sur la ligne et à moins de 0,5 m du bout du trajet, cet adversaire touche le ballon le premier dans environ 23 % des cas seulement (168 adversaires sur 96 matchs). Dans le cas statique du test `test_marked_receiver_at_contact_keeps_the_measured_engine_chance` (adversaire immobile 0,5 m devant le receveur, passe de 12 m), la chance évaluée vaut 0,72 : fidèle au moteur, sans doute irréaliste (un défenseur collé devant, entre le ballon et le receveur, devrait gagner le ballon le plus souvent). Réserve A2 de l'expert au `18n`.

**What to build :** mesurer d'abord, sur des situations construites (receveur et défenseur immobiles ou en mouvement, défenseur devant, à côté, derrière), qui touche le ballon le premier et pourquoi (portée de contrôle du receveur, `match.RECEIVER_REACH_M`, portée du défenseur, ordre de résolution des contacts, receveur qui vient au ballon). Chercher un ordre de grandeur réel (part des passes vers un joueur marqué de face interceptées). Corriger le seul facteur en cause ; puis remesurer la table de coupe et les facteurs du `18o` (la chance évaluée décrit le moteur). Toute constante nouvelle est proposée au propriétaire avant d'être codée.

**À la remesure de la table (clôture du `18p`, 20/11/2026) :** vérifier aussi les biais laissés en l'état par le `18p` : Passing < 50 (+ 3,8 ± 1,8), passes de moins de 8 m (+ 1,6, réserve A2 du `18o`), de 15 à 30 m (− 1,1, réserve A1 du `18o`) ; causes écartées au `18p` (`docs/INDICATEURS_V2.md` section 63).

**Critères d'acceptation** (posés après la mesure, recommandations validées par délégation du propriétaire le 20/11/2026 : « Je valide automatiquement tes recommandations et les conseils d'experts ») :
- [x] Mesure : situations construites (défenseur devant, décalé, à côté, derrière ; cap vers le ballon, vers le receveur, de profil) et matchs joués (48, graines 2400 à 2447) : part des ballons touchés le premier par le défenseur collé, par cause (lecteur, orientation, passe vue, distance) ; chiffre réel cherché.
- [x] Instant d'entrée dans la portée exact (géométrie de la droite du pas) dans `match._contacts`, sans constante nouvelle ; tests de géométrie et de scène.
- [x] Scène : défenseur 0,5 m devant le receveur et 0,5 m à côté de la ligne, tourné vers le ballon, passe de 12 m : il garde le ballon dans au moins 90 % des tirages (0 % avant) ; défenseur à côté du receveur : le receveur garde le ballon.
- [x] 50 matchs appariés (banc, graines 0 à 49) : réussite des passes de jeu au-dessus de 80 % ; buts, tirs, passes prises par l'adversaire : écart avec IC 95 %, tout écart significatif expliqué.
- [x] Contrôle de la chance évaluée sur 52 matchs joués (graines 2600 à 2651, script du `18o`) : critères du `18n` et du `18o` (pire tranche au plus 4 points, moyenne à 0,5 point, adversaire à moins de 1,5 m du receveur à moins de 4 points) ; biais laissés par le `18p` remesurés ; table réestimée seulement si un critère tombe.
- [x] Déterminisme : mêmes empreintes sur deux exécutions à graine fixée ; suite complète comparée à l'attendu.

**Attributs :** à établir (portées, Anticipation, Positioning ; voir `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by :** aucun.

**Status:** livré (21/11/2026), validé expert + QC

## Résultat (21/11/2026)

Rapport : `docs/INDICATEURS_V2.md`, section 64 ; scripts et sorties `.scratch/v2-realisme/mesures/29c-*`.

- Mesure : le défenseur encore devant le receveur à l'arrivée du ballon touche le premier 77 % des fois en match (104 cas, 48 matchs) ; 58 % des adversaires collés au départ ne sont plus sur le trajet à l'arrivée (receveur démarqué). L'orientation ne pèse pas (1 %). Scène statique, défenseur 0,5 m devant tourné vers le ballon : 97 %.
- Cause corrigée : instant d'entrée du ballon dans la portée faux dans `match._contacts` quand le point le plus proche est rabattu sur la fin du pas (avantage au joueur de grande portée, le receveur). Calcul exact sur la droite du pas, sans constante. Scène décalée (0,5 m devant, 0,5 m à côté) : 0 % → 96 % (premier au contact : 100 %).
- Laissés en l'état : défenseur de profil ou dos au ballon sur la ligne (portée 0,41 m : le receveur, à 1 m de portée, joue le ballon à travers lui ; 1 cas sur 104 en match) ; temps de réaction de 0,25 s sur les passes très courtes (constante du 29b).
- Critères : [x] mesure ; [x] entrée exacte, 6 tests (`tests/test_v2engine_entree_contact.py`) ; [x] scène 96 % (au moins 90 %) ; [x] appariés : réussite 84,90 % (− 0,32 ± 0,25), passes prises + 5,1 ± 4,1 (expliqué), tirs et buts dans le bruit ; [x] contrôle de la chance évaluée : pire tranche 1,7, moyenne − 0,3, moins de 15 m + 0,8, adversaire à moins de 1,5 m + 3,2 ± 4,3, table non réestimée ; biais du 18p : + 3,1 / + 1,8 / − 1,1 ; [x] déterminisme : empreinte des comptes du match 3 `4301640c70ae2cc7` sur deux exécutions ; suite complète 3 473 passés (3 467 + 6), 0 ignoré, 14 désélectionnés.
- Test du receveur marqué (`test_marked_receiver_at_contact_keeps_the_measured_engine_chance`) : valeur inchangée (0,72), docstring mise à jour (moyenne sur les adversaires collés au départ).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code (résolution des contacts) | 30 min |
| Mesure sur situations construites, recherche d'un chiffre réel | 60 min |
| Développement | 45 min |
| Tests | 30 min |
| Intégration et vérifications (remesure de la coupe, matchs appariés) | 75 min |
| **Total (travail effectif)** | **4 h** |

Confiance : faible (cause physique non établie, remesure de la table du `18o` probable). Au-delà du seuil de 2 h : découpage proposé en mesure (1 h 30) puis correction et remesure, à confirmer avant le code. Temps machine, non compté : enregistrement et contrôle sur matchs joués, 50 appariés, suite complète.

## Comments

- 20/11/2026, création pendant le `18o` (décision du propriétaire : le test du receveur marqué fige la valeur du moteur, ticket de physique à part, « oui valide les 3 »).
- 20/11/2026, découpage proposé (mesure, puis correction) refusé par le propriétaire : « 1 seul ticket », estimation gardée à 4 h.
- 20/11/2026, critères posés après la mesure, validés par délégation (« Je valide automatiquement tes recommandations et les conseils d'experts. Finis donc ce ticket et enchaîne avec les 2 suivants »).

## Durée réelle

Environ 3 h 30 de travail effectif pour 4 h estimées (− 12 %) : analyse 30 min, mesure (situations construites, enregistrement de 48 matchs, recherche d'un chiffre réel) 70 min, développement 15 min, tests 25 min, intégration et vérifications 70 min (compte de l'ordre des contacts, appariés, contrôle de la chance évaluée, rapport). Correction plus simple que prévu (aucune constante, table non réestimée). Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée ; temps machine hors total : 48 matchs d'enregistrement (30 min), 24 matchs de comptage de l'ordre (relancés une fois), 2 x 50 matchs appariés (1 h 10), 52 matchs de contrôle (30 min), suite complète (16 min).
- 21/11/2026, passage 1 : expert APPROVED (empreinte 12031da7), QC VALIDÉ ; liste de fichiers incluant le ticket et `docs/PLAN_V2.md`, à mettre à jour à la clôture : revue refaite. Libellés du §64 corrigés (A1, A2).
- 21/11/2026, passage 2 : expert APPROVED (empreinte 406a567a), QC VALIDÉ, clôture VALIDÉ. Améliorations facultatives non faites : A1 (receveur qui joue le ballon à travers un défenseur de profil ou dos au ballon sur la ligne, 1 cas sur 104 ; correctif : portée du receveur seulement pour un ballon qui a franchi les adversaires sur la ligne), A2 (point d'impact du contre de tir, `_blocked`, encore calculé sur le point rabattu). À surveiller au `v2-collectif/22a` : adversaire sur la ligne à moins de 1,5 m (+ 5,3 ± 7,2), passes prises par l'adversaire.
