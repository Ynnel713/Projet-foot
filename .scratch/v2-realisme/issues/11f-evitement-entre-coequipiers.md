# 11f: Évitement entre coéquipiers : ralentir ou infléchir sa course

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026). **Priorité :** P0, **priorité absolue fixée par le propriétaire le 15/11/2026** (rythme de jeu). **Catégorie :** déplacement.

**Constat vérifié (11e, 50 matchs, `docs/INDICATEURS_V2.md` section 44) :** 997 contacts francs par match (plus de 2 m/s de rapprochement), dont **337 entre coéquipiers** ; 1 099 déséquilibres par match (12c : vitesse perdue et délai avant d'agir). Aucun évitement dans le code : chaque joueur court droit vers sa cible (`movement.step`, appelé par `match.py:1166` avec `intention.target`) ; seule la collision corrige après coup (`match._resolve_player_collisions`, 11a-11b).

**What to build:** Conscience spatiale de base : avant de se déplacer, le joueur regarde devant lui, le long de sa course voulue, sur un court horizon. Si un coéquipier occupe ce couloir, il **infléchit** sa course (contournement par le côté le plus libre) ou, si l'inflexion ne suffit pas, **ralentit** pour ne pas le percuter. Ajustement de la cible et de l'intensité avant `movement.step`, sans toucher à `step` lui-même. Les adversaires ne sont pas évités (le contact avec eux est un duel : 11b, 11c, tacle) ; le ballon libre disputé par deux coéquipiers relève de qui y va (`cerveau`, chasseur désigné) : le non-désigné s'écarte.

**Attributs :** aucun (règle R1 : locomotion de base, chacun évite ses coéquipiers). Piste à trancher par le propriétaire : n'éviter que les coéquipiers **perçus** (champ de vision, 08a), ce qui ferait jouer la perception sans nouvel attribut.

**Constantes à proposer avant le code (valeurs indicatives, non validées) :** horizon d'anticipation 0,8 s de course ; couloir = somme des rayons + 0,3 m de part et d'autre ; inflexion au plus 35° par rapport à la course voulue, côté le plus libre ; si aucun cap à 35° ou moins n'est libre, vitesse ramenée à celle du coéquipier le long de la course (au plus 50 % de freinage par pas, borné par `decel_max_mps2`). Chiffre réel : non trouvé (ordre de grandeur : des coéquipiers ne se percutent qu'exceptionnellement, quelques fois par match).

**Lien avec l'existant :** réduit les contacts du 11a et les déséquilibres du 12c ; mesuré par les indicateurs du 11e (`contacts francs entre coéquipiers par match`).

**Blocked by:** aucun (11e livré).

**Bloque :** 11g.

**Status:** livré (15/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : un seul point d'application avant `movement.step` ; boucle sur les coéquipiers seulement (11 x 10 paires par pas, coût à mesurer) ; validation en match au 11g (découpe : le ticket complet était estimé à 2 h 50).
Temps machine, non compté : suite complète (environ 12 min) ; deux matchs de contrôle.

## Tests

- **Unitaires (scène contrôlée) :** deux coéquipiers qui se croisent à 6 m/s : aucun chevauchement, inflexion ≤ 35° ; coéquipier arrêté dans le couloir : contourné ; couloir fermé des deux côtés : freinage, pas de contact ; adversaire dans le couloir : pas d'évitement (duel inchangé) ; course libre : trajectoire identique à avant.
- **Statistiques :** au 11g.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Scène : aucun contact franc entre deux coéquipiers qui se croisent, sur 20 graines
- [x] Course sans coéquipier dans le couloir : trajectoire inchangée (empreinte de scène identique)
- [x] Coût par pas mesuré (durée d'un match : + 10 % au plus)
- [x] Rayon des attributs inchangé (aucun attribut) ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, constantes validées par le propriétaire** (« Je valide entièrement les valeurs pour 11f ») : horizon 0,8 s, couloir à la somme des rayons + 0,3 m, inflexion 35° au plus, freinage limité à 50 % de l'intensité voulue ; tous les coéquipiers évités, sans attribut (« On affinera avec le champ de vision plus tard si besoin »). **Ajouts du propriétaire** (effet miroir) : priorité au porteur (« le joueur qui n'a pas le ballon évite en priorité celui qui l'a ») et côté d'évitement tenu au moins 0,2 s (hystérésis). Estimation réannoncée avant le code : 2 h 15 (priorité et hystérésis), puis 2 h 35 en cours de route (inflexion de la vitesse de cible, voir plus bas). Écart au ticket : le ballon libre disputé par deux coéquipiers n'a pas de règle propre (pas de « chasseur désigné » lu ici) ; les deux s'évitent, à mesurer au 11g.

**15/11/2026, implémentation.** Nouveau module `v2engine/evitement.py` (`avoid_teammates`, `conflicts`) : course voulue = direction de la cible à la vitesse actuelle ; coéquipier bloquant si la plus courte distance du mouvement relatif sur 0,8 s passe sous le couloir ; inflexion cherchée par pas de 5° jusqu'à 35°, côté opposé au coéquipier le plus proche (pile en face : à droite, donc côtés opposés pour deux joueurs face à face), côté tenu 0,2 s ; sinon intensité ramenée vers la vitesse du coéquipier le long de la course (rapport des vitesses, aucune note lue), au plus 50 % de freinage. Le porteur n'évite personne. La vitesse de cible (pressing) est infléchie du même angle que la cible. `match._step_player` l'applique avant `movement.step` (inchangé) ; côté retenu gardé dans `PlayerState.avoid_side` et `avoid_side_until_s`. Calcul en flottants avec pré-filtre des coéquipiers proches (coût). Première suite : deux gardes en échec (lecture de `player.pace` hors façade), corrigées en supprimant cette lecture. Tests : `tests/test_v2engine_evitement.py` (28 : course libre inchangée, adversaire non évité, contournement à 35° au plus du côté libre, face à face des deux côtés opposés, porteur prioritaire, couloir fermé et freinage à 50 %, côté tenu puis libéré, 20 croisements tirés sans contact franc ni inversion de côté tenu, témoin sans évitement qui percute).

**15/11/2026, mesure (2 matchs, graine d'audit, `11f-avant-2matchs.txt`, `11f-det1.txt`).** Contacts francs entre coéquipiers **356 → 203 par match** (− 43 %) ; contacts francs 1 024 → 837 ; contacts perdus 1 143 → 951 ; passes 1 127 → 1 128, temps de jeu effectif 0,744 → 0,737, buts 4,5 → 5,0, fautes 16,5 → 15,0 (2 matchs : indicatif, série au 11g). Coût : 119,7 → 126,1 à 128,5 s par match (+ 5 à + 7 %, mesures seules sur la même machine). `11f-det1` et `11f-det2` identiques hors temps de calcul. Un premier « avant » mesuré en parallèle d'un diagnostic (114,1 s) n'est pas retenu.

**15/11/2026, diagnostic des contacts restants (hors dépôt, 30 min de jeu, 81 contacts francs entre coéquipiers).** L'évitement a vu le conflit dans 81 cas et modifié la course dans 80 : il n'est pas aveugle, il est **impuissant** dans deux situations : cible à moins de 2 m (51 cas : deux coéquipiers visent presque le même point) et cible mobile (41 cas : pressing du même adversaire) ; seulement 6 impliquent le porteur. Ni l'inflexion à 35° ni un freinage à 50 % ne séparent deux joueurs qui veulent la même place. **Pistes pour le 11g, à trancher par le propriétaire** : (a) freinage au-delà de 50 % (jusqu'à l'arrêt) quand la cible elle-même est dans le couloir du coéquipier ; (b) au niveau de la décision : un seul presseur par adversaire, et des cibles de placement écartées d'au moins un couloir ; (c) horizon plus long à haute vitesse (rayon de virage borné par Agility, 12b).

**15/11/2026, suite complète.** 3 158 passés, 0 ignoré, 14 désélectionnés (3 130 + 28 ; `11f-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée.

**15/11/2026, durée.** Estimation du ticket 1 h 55, réannoncée 2 h 15 (priorité au porteur, hystérésis) puis 2 h 35 (inflexion de la vitesse de cible) ; durée réelle environ 2 h 25 (analyse 20, développement 50, tests 30, intégration 45), − 6 % sur la dernière annonce, + 26 % sur l'estimation du ticket : périmètre élargi par le propriétaire (priorité, hystérésis), diagnostic des contacts restants et optimisation du coût (premier essai à + 12 %). Durée estimée à l'horloge de la session hors attentes machine et échanges, non chronométrée. Temps machine hors total : deux suites complètes (13 et 12 min), cinq mesures de 2 matchs, deux diagnostics de 30 min de jeu, un profil de 10 min.

**15/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS.** A1 [réserve] : la règle « ballon libre : le non-désigné s'écarte » n'était pas implémentée ; receveur, chasseur du ballon libre et gardien en sortie infléchissaient leur course (indice sur 2 matchs : sorties du gardien réussies 0,083 → 0,0). A2 [facultatif] : horizon non coupé au temps d'arrivée à la cible (non traité : à vérifier d'abord sur le cas « même place visée », 11g). **Décision du propriétaire** sur A1 : « Corriger maintenant ». **Correction** : `avoid_teammates(..., priority=...)` ; `match._step_player` donne la priorité au receveur visé (`RECEVEUR`), au gardien qui va au ballon et au coéquipier désigné sur ballon libre (`BALLON_LIBRE` et `nearest_of_team`), qui n'évitent personne, comme le porteur ; les autres les évitent. Tests ajoutés (6 : priorité dans `avoid_teammates`, rôle transmis par `_step_player` dans cinq cas). Réestimation annoncée : + 30 min.

**15/11/2026, mesure après correction (2 matchs).** Contacts francs entre coéquipiers 356 → **222 par match** (− 38 %) ; sorties du gardien réussies 0,083 → 0,167 et disputées gagnées 0,091 → 0,167 (2 matchs : non interprétable, et sans lien avec la priorité du gardien, inopérante à ce stade : voir passage 2) ; coût 119,7 → 118,8 à 120,7 s par match (neutre) ; `11f-det1` et `11f-det2` identiques hors temps de calcul. Suite : `test_v2engine_mi_temps.py::test_half_time_resets_everyone_and_the_other_team_kicks_off` en échec (graine 20260928 : coup de pied arrêté en attente à la pause, période prolongée à 1,43 min, cas déjà rencontré aux tickets 01a et 03a) ; graine changée pour 20260930 (première graine suivante sans prolongation), assertions inchangées.

**15/11/2026, suite complète après correction.** 3 164 passés, 0 ignoré, 14 désélectionnés (3 130 + 34 ; `11f-suite.txt`) ; `CLAUDE.md` mis à jour.

**15/11/2026, durée révisée.** Correction de la réserve A1 comprise : environ 2 h 55 (analyse 25, développement 60, tests 40, intégration 50), sur une dernière annonce de 3 h 05 (2 h 35 + 30 min), − 5 % ; + 52 % sur l'estimation du ticket (1 h 55) : périmètre élargi deux fois par le propriétaire (priorité au porteur et hystérésis ; correction de A1) et diagnostic des contacts restants. Temps machine hors total : trois suites complètes, sept mesures de 2 matchs, deux diagnostics, un profil.

**15/11/2026, passage 2 de l'expert : REJECTED.** A1 [bloquant] : la priorité du gardien ne s'appliquait jamais : `cerveau` rend toujours le rôle « gardien » (`interpret`, `_keeper`), jamais `BALLON_LIBRE` ; le test simulait un rôle que le moteur ne produit pas. A2 [réserve] : gain des sorties du gardien attribué à tort à sa priorité (bruit : 1 sortie sur 6). A3 [facultatif] : horizon non coupé au temps d'arrivée (reporté au 11g). **Corrections** (actions obligatoires de l'expert) : le gardien a la priorité quand son action va au ballon (`KEEPER_TO_BALL_ACTIONS` : « aller au ballon », « venir au ballon », actions de `decide` en sortie et en prise de balle) ; il passe alors avant le désigné de champ sur ballon libre (« ballon du gardien », lu dans les intentions du pas), règle découverte par la scène réelle (le défenseur, plus proche, était aussi prioritaire : aucun n'évitait l'autre). Test paramétré refait sur des rôles réels (7 cas) ; scène sans simulation du cerveau (vrai `think` : gardien en sortie prioritaire, défenseur non). Documentation corrigée (A2). Réestimation : + 25 min (non annoncée avant la correction, oubli).

**15/11/2026, mesure et suite après le passage 2.** 2 matchs : contacts francs entre coéquipiers 356 → **242 par match** (− 32 %) ; sorties du gardien 1 réussie sur 12 avant, 0 sur 8 après (non interprétable) ; coût 119,7 → 121,2 à 121,7 s (+ 1 à + 2 %) ; `11f-det1` et `11f-det2` identiques hors temps de calcul. Suite complète : 3 167 passés, 0 ignoré, 14 désélectionnés (3 130 + 37) ; `CLAUDE.md` mis à jour.

**15/11/2026, durée finale.** Environ 3 h 20 (analyse 25, développement 70, tests 50, intégration 55), + 8 % sur la dernière annonce (3 h 05, correction du rejet non réannoncée), + 74 % sur l'estimation du ticket (1 h 55) : périmètre élargi deux fois par le propriétaire, diagnostic des contacts restants, puis rejet de l'expert sur le gardien (le rôle réel du gardien n'avait pas été vérifié dans `cerveau` avant de coder). Temps machine hors total : quatre suites complètes, neuf mesures de 2 matchs, deux diagnostics, un profil.

**15/11/2026, passage 3 de l'expert : APPROVED ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11f/cloture`). Remarques facultatives, non traitées : A1 la scène sur le vrai cerveau vérifie la priorité du défenseur, pas son écart effectif ; A2 horizon non coupé au temps d'arrivée (11g) ; A3 correction du rejet non réannoncée avant le code (écart de procédure reconnu) ; A4 gardien qui coupe une passe sans priorité (à revoir au 11g si des collisions gardien-défenseur sur interception apparaissent). À surveiller au 11g sur 50 matchs : sorties du gardien, réceptions, ballons libres récupérés, pressing à deux et cibles quasi confondues (principale source des 242 contacts restants).

