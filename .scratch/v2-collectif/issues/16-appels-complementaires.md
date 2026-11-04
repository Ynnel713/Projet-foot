# 16: Déplacements offensifs complémentaires

**What to build:** Les attaquants ne convergent pas tous vers le ballon : appels **non redondants** (pas deux joueurs sur la même profondeur), décrochage pour **libérer une zone** même sans recevoir, **appels leurres**, permutations (l'ailier rentre, le milieu occupe la zone libérée). L'appel dépend de la capacité du porteur à l'exploiter : avec un excellent Off the Ball mais un porteur sans Vision ni qualité de passe, l'appel est ignoré ou avorté. Comprend le dernier tiers hors centres (les centres arrivent en phase 7).

**Attributs :** Off the Ball, Teamwork, Anticipation ; Vision et Passing du porteur.

**Blocked by:** 06, 13.

**Status:** livré (03/11/2026), validé expert + QC (clôture groupée 10-14-16, réserves acceptées par délégation, voir Comments)

**Point de vigilance :** Off the Ball mesuré à l'envers le 26/10 (784 appels vers l'avant à 99 contre 946 à 11) : à expliquer ici.

- [x] Off the Ball 99 contre 11 : plus d'appels, et plus intenses (le sens est inversé dans la mesure du 26/10)
- [x] Pas deux appels sur la même zone au même moment (test)
- [x] Reprend le critère en match reporté du ticket cerveau 03 (espace des coéquipiers du porteur) : mesuré, passé en indicateur par décision du propriétaire
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Comments

- 03/11/2026, clôture groupée v2-collectif/10-14-16 (tickets imbriqués dans `cerveau.py`, `measure_v2.py`, `test_v2engine_rayon_attributs.py`), base `704cae3`, empreinte `40a69fa0` : expert INCONCLUSIVE au passage 1 (suite complète absente), APPROVED_WITH_RESERVATIONS au passage 2 ; QC VALIDÉ ; clôture VALIDÉ. Suite complète : 2 305 passés, 13 désélectionnés, 0 échec. Réserves acceptées par délégation du propriétaire (« Considère que je valide automatiquement toutes les reco d'experts ») : documents dans le même commit ; priorité de l'appel dans le dos sur la relance du plan du 14, avec test du plan à rendre indépendant de la graine (ticket de suivi). A13 jugée conforme à R1 (Vision et Passing du porteur = contexte perçu par le coureur), reformulée dans la carte.
- 01/11/2026, diagnostic du hors-jeu après le ticket 26 (8 matchs, graine d'audit, `c379ba6` + correctif du 26) : l'arbitrage fonctionne (50 % des passes vers un receveur hors-jeu sont sifflées, 41 % avant le ticket 25), mais les attaquants ne jouent pas sur la ligne. L'attaquant le plus avancé est à 8,6 m derrière la ligne en médiane, à moins de 2 m lors de 5,5 % des passes seulement (12,6 % avant le 25) ; receveur hors-jeu : 15 passes en 8 matchs ; passes en profondeur : 0,2 % des passes ; hors-jeu : 0,6 à 0,75 par match (3 à 4 dans le football réel). Ce ticket (appels à l'épaule du dernier défenseur, profondeur non redondante) est l'un des leviers, avec les tickets 11 et 13 ; le propriétaire a écarté le 01/11/2026 une recalibration de la règle du hors-jeu, qui gonflerait le chiffre sans corriger le jeu. Détail : `.scratch/v2-collectif/diagnostic-hors-jeu-30-10-2026.md`.

## Proposition (02/11/2026), soumise à validation du propriétaire

**Inversion d'Off the Ball.** Elle n'apparaît plus : 2 matchs, profil 99 contre 11, 81 contre 67 appels par joueur, 12,5 contre 8,6 km de course intense (moteur `fe33bd2` avec le ticket 09 en cours). Le chiffre du 26/10 (784 contre 946) n'est pas documenté. Cause probable : avant le ticket 06, un grand rayon de recherche (15 m à 99) faisait viser plus loin, donc atteindre moins vite, donc relancer moins d'appels. Depuis le ticket 06, un joueur garde son espace jusqu'à l'atteindre ou jusqu'à 3 s. À confirmer sur 20 matchs.

**Ce qui manque.** Aujourd'hui, l'espace visé reste à 10 m au plus devant la place du joueur dans le bloc, puis il est ramené 1 m derrière la ligne. Le classement favorise les espaces où une passe passe déjà (≥ 70 %), ce qu'un appel dans le dos n'offre jamais au départ. Personne n'attaque donc la profondeur.

**Mécanismes (dans `off_ball.py`, avec un branchement minimal dans la partie « appel » de `cerveau.py`).**
1. **Appel dans le dos.** À chaque recherche d'espace, un joueur placé devant le ballon, dont la place dans le bloc est à `DEPTH_REACH_M` ou moins de la ligne du hors-jeu, tente un appel sur la ligne : à la largeur de sa place, 1 m derrière la ligne (`ONSIDE_MARGIN_M`, existant), et la règle du ticket 23 s'applique toujours. Probabilité = volonté du coureur (Off the Ball) × capacité du porteur à l'exploiter.
2. **Le porteur doit pouvoir l'exploiter.** Ce facteur est lu sur le porteur : moyenne de Vision et de Passing. Un porteur faible fait renoncer le coureur. L'appel est rejoué à chaque recherche (toutes les 1 à 3 s), donc il est aussi abandonné si un porteur faible reçoit le ballon. Ce n'est pas un double comptage avec le ticket 13 : là-bas, la Vision choisit la passe ; ici, le coureur décide de courir ou non.
3. **Profondeur non redondante.** Un seul appel dans le dos par couloir de `DEPTH_LANE_M` de large. Le deuxième joueur du même couloir garde la recherche d'espace habituelle (soutien ou décrochage), avec l'écart de 8 m déjà en place.
4. **Appels leurres** : effet induit, mesuré mais sans mécanisme propre. Le marqueur du ticket 07 suit l'attaquant dangereux qui part dans le dos, et libère ainsi la zone qu'il quitte.
5. **Permutations** (l'ailier rentre, le milieu occupe la zone libérée) : **renvoyées au ticket 17** (surcharges), qui en dépend déjà. Elles demandent une réaffectation des places dans le bloc, hors du périmètre d'un appel.
6. **Intensité** : pas de nouvelle constante. L'appel dans le dos garde l'intensité actuelle (vitesse maximale) ; le réglage de l'intensité selon le rôle reste au ticket 12. L'effet « plus intense » d'Off the Ball vient de la part plus grande d'appels dans le dos.

**Constantes proposées.**

| Constante | Valeur | Justification |
|---|---|---|
| `_DEPTH_RUN` (volonté, Off the Ball, courbe partagée) | 99 → 60 %, 55 → 35 %, 11 → 10 % par recherche d'espace | Le joueur moyen tente un appel dans le dos environ une recherche sur trois. Valeur réelle : 32 % des courses d'un avant-centre sont des appels dans le dos (SkillCorner) |
| `_EXPLOIT` (porteur, moyenne Vision et Passing) | 99 → 95 %, 55 → 70 %, 11 → 45 % | Même courbe que le choix du meilleur espace (`_BEST_SPACE`) ; jamais 0, jamais 1 |
| `DEPTH_REACH_M` | 20 m | La place dans le bloc des attaquants et des milieux offensifs, mais pas celle des défenseurs (bloc d'environ 30 à 40 m de long) |
| `DEPTH_LANE_M` | 15 m | Au plus 4 appels dans le dos sur 68 m de largeur |

**Critères chiffrés (20 matchs, graine d'audit, profils avec rôles inversés).**
- C1 Profil Off the Ball 99 contre 11 : au moins 10 % d'appels en plus par joueur, plus de course intense, et au moins 2 fois plus d'appels dans le dos. Nouvel indicateur du banc : un appel dans le dos est un appel qui finit à 2 m ou moins de la ligne du hors-jeu.
- C2 Redondance : test unitaire (deux joueurs dans le même couloir : un seul appel dans le dos) ; en match, la part d'appels redondants ne dépasse pas la valeur de référence.
- C3 Critère reporté du ticket cerveau 03 : en possession, la distance moyenne des coéquipiers du porteur à l'adversaire le plus proche est au moins 30 % plus grande à Off the Ball 99 qu'à 11. Le critère validé comparait 90 et 30 ; les profils du banc utilisent 99 et 11.
- C4 Jeu sur la ligne : l'attaquant le plus avancé est en médiane à 5 m ou moins de la ligne lors des passes (8,6 m aujourd'hui), et à moins de 2 m lors d'au moins 12 % des passes (5,5 %). Hors-jeu et passes en profondeur : indicateurs seulement (réel : 3 à 4 hors-jeu par match), pas d'objectif.
- C5 Porteur : test unitaire, même coureur à 99 ; un porteur à Vision et Passing 99 déclenche au moins 2 fois plus d'appels dans le dos qu'un porteur à 11.
- C6 Déterminisme, suite V2 verte, V1 inchangée ; carte des attributs et `test_v2engine_rayon_attributs.py` mis à jour (Vision et Passing lus dans `off_ball.py`).

Sources : CIES/SkillCorner, 15,1 appels par joueur sur 90 minutes ([football-observatory.com](https://football-observatory.com/Call-for-the-ball-runs-worldwide-analysis)) ; part des appels dans le dos chez les avant-centres ([Training Ground Guru](https://trainingground.guru/articles/skillcorner-analysing-centre-forwards-off-ball-runs)). Fréquence réelle par match des appels dans le dos : non trouvée.

## Mesures (02/11/2026, 20 matchs, graine d'audit ; « avant » = même code, appel dans le dos désactivé)

Proposition validée par le propriétaire le 02/11/2026. Ajustement imposé par la règle R2 : Vision et Passing en deux tirages distincts (produit), le porteur à 11 donne 47 % au lieu de 45 %. Les mesures incluent le travail en cours des tickets 09 et 14 (fichiers partagés).

| Critère | Avant | Après | Cible | Verdict |
|---|---|---|---|---|
| C1 appels par joueur, OtB 99 / 11 | 81,7 / 67,8 | 81,1 / 67,9 (+19 %) | ≥ +10 % | OK |
| C1 course intense, 99 / 11 (m) | 12 280 / 8 167 | 12 402 / 8 201 | plus à 99 | OK |
| C1 appels dans le dos par joueur, 99 / 11 | 3,60 / 1,24 | 3,69 / 1,51 (×2,4) | ≥ ×2 | OK |
| C2 appels redondants (part, standard) | 0,021 | 0,020 | ≤ avant | OK |
| C3 espace des coéquipiers du porteur, 99 / 11 (m) | 14,2 / 12,5 | 14,6 / 12,6 (+16 %) | ≥ +30 % | **NON** |
| C4 attaquant le plus avancé à 5 m ou moins (part, standard) | 0,242 | 0,274 | ≥ 0,50 | **NON** |
| C4 à 2 m ou moins (part, standard) | 0,120 | 0,154 | ≥ 0,12 | OK |
| Appels dans le dos par match (standard) | 53,5 | 58,9 | indicateur | +10 % |
| Hors-jeu par match (standard) | 1,0 | 1,6 | indicateur (réel 3 à 4) | |

Constat : l'inversion d'Off the Ball est confirmée disparue (C1 tenait déjà avant). Le mécanisme va dans le bon sens mais son effet est faible (+10 % d'appels dans le dos) : C3 et C4 (médiane) ne sont pas atteints. Piste à diagnostiquer avant toute retouche : part des recherches d'espace où `depth_run` est candidat (joueur devant le ballon, place à 20 m de la ligne) et part abandonnée ensuite (« plans abandonnés, ligne fermée » 0,457 → 0,484).

**Statut intermédiaire (02/11/2026, dépassé) :** en cours — critères C3 et C4 non atteints ; déterminisme, suite complète et revue non faits.

## Diagnostic (02/11/2026, matchs standard, graine d'audit, `depth_run` instrumenté hors dépôt)

**Où l'appel n'est pas candidat** (4 matchs, 121 500 recherches d'espace) : joueur derrière le ballon 40 %, ballon en l'air sans porteur 39 %, place dans le bloc à plus de 20 m de la ligne 14 % (écart le plus fréquent : 20 à 40 m), couloir déjà pris moins de 1 %. **Candidat : 6 %** (7 248), surtout BU (4 921), AG (1 293), AD (774), MOC (253) ; MC et MDC quasi jamais. Tirage réussi : 26 % des candidats, soit environ 470 appels dans le dos lancés par match.

**Ce que devient un appel lancé** (3 matchs, 1 321 appels) : au re-choix suivant, le joueur est à 3,1 m de sa cible en médiane (quartiles 2,1 / 3,1 / 12,3 m) après 2,7 s (1,6 / 2,7 / 4,8 s) ; 76 % n'ont pas atteint la cible (2 m). La ligne bouge pendant la course (−5,7 / −0,2 / +4,7 m).

**Cause principale.** L'appel est retiré au sort à chaque re-choix (au plus 3 s, `SPACE_HOLD_MAX_S`). Un joueur arrive presque sur la ligne, ses 3 s expirent, il perd le nouveau tirage (74 % à 55) et repart vers sa place dans le bloc, 10 à 20 m en arrière. Il fait donc des allers-retours au lieu de rester à l'épaule du dernier défenseur : 470 appels lancés par match, environ 60 qui finissent sur la ligne. Causes secondaires : la place dans le bloc des attaquants est souvent à plus de 20 m de la ligne, et aucun appel n'est décidé pendant une passe en l'air.

**Piste proposée (sans nouvelle constante, à valider par le propriétaire).** Un joueur qui a lancé un appel dans le dos le **tient** : au re-choix, tant qu'il reste candidat (devant le ballon, couloir libre, même porteur ou passe de son équipe en l'air), il vise de nouveau la ligne actuelle sans nouveau tirage. Il ne retire au sort qu'au changement de porteur ou quand il cesse d'être candidat. La probabilité validée reste celle de *décider* l'appel, pas celle de le *poursuivre* toutes les 3 s.

## Appel tenu (02/11/2026, validé par le propriétaire) et nouvelles mesures

Codé : un appel dans le dos lancé est tenu sans nouveau tirage tant que le joueur reste candidat et que le même porteur a le ballon (ou que la passe est en l'air). Un nouveau porteur fait retirer au sort. Pas de nouvelle constante. Tests : `test_a_launched_depth_run_is_held_without_a_new_draw` (off_ball), `test_a_depth_run_is_remembered_and_held_at_the_next_search` (cerveau).

20 matchs, graine d'audit ; « avant » = appel dans le dos désactivé, relancé sur l'arbre actuel.

| Critère | Avant | Tiré à chaque re-choix | Tenu | Cible | Verdict |
|---|---|---|---|---|---|
| C1 appels par joueur, OtB 99 / 11 | 81,7 / 67,8 | 81,1 / 67,9 | 81,8 / 67,2 (+22 %) | ≥ +10 % | OK |
| C1 course intense, 99 / 11 (m) | 12 280 / 8 167 | 12 402 / 8 201 | 12 409 / 8 197 | plus à 99 | OK |
| C1 appels dans le dos par joueur, 99 / 11 | 3,60 / 1,24 | 3,69 / 1,51 | 3,82 / 1,80 (×2,1) | ≥ ×2 | OK |
| C2 appels redondants (standard) | 0,021 | 0,020 | 0,023 | ≤ avant | limite (+0,002, bruit) |
| C3 espace des coéquipiers, 99 / 11 (m) | 14,2 / 12,5 | 14,6 / 12,6 | 14,5 / 12,5 (+16 %) | ≥ +30 % | **NON** |
| C4 attaquant à 5 m ou moins (standard) | 0,242 | 0,274 | 0,291 | ≥ 0,50 | **NON** |
| C4 attaquant à 2 m ou moins (standard) | 0,120 | 0,154 | 0,171 | ≥ 0,12 | OK |
| Appels dans le dos par match (standard) | 53,5 | 58,9 | 61,8 | indicateur | +16 % |
| Hors-jeu par match (standard) | 1,0 | 1,6 | 2,05 | indicateur (réel 3 à 4) | |

Déterminisme : les deux mesures « avant » (même graine, 02/11 à 10 h et à 18 h) donnent des indicateurs de match identiques ; seuls diffèrent le temps de calcul et les compteurs de plans du ticket 14, dont le code de mesure a changé entre-temps.

**Lecture.** L'appel tenu améliore le jeu sur la ligne (attaquant à 2 m ou moins : 12 % → 17 % des passes ; hors-jeu doublés), mais C3 et la médiane de C4 restent loin. Le goulot n'est plus l'appel lui-même : 94 % des recherches d'espace ne sont pas candidates (joueur derrière le ballon, passe en l'air, place dans le bloc à 20-40 m de la ligne). C3 mesure surtout la recherche d'espace classique (rayon Off the Ball), hors du mécanisme de ce ticket ; C4 dépend de la hauteur des attaquants dans le bloc (ticket 04) et de la calibration (ticket 22).

**Décision du propriétaire (03/11/2026).** C3 et la médiane de C4 passent en indicateurs sans cible : ils dépendent de la recherche d'espace classique (C3), de la hauteur des attaquants dans le bloc (ticket 04) et de la calibration générale (ticket 22). Pas de réglage de `DEPTH_REACH_M` pour les atteindre. Critères retenus pour la clôture : C1, C2, C4 (part à 2 m ou moins), C5, C6.

## Revue et mesures finales (03/11/2026)

Correctifs issus de la revue (`simulafoot-reviewer`) :
- un appel tenu ne survit pas à une perte de balle : la mémoire du porteur n'est reprise que si l'échéance de la dernière recherche d'espace (lancée + `SPACE_HOLD_MAX_S`) est dépassée de 3 s au plus, soit au plus 6 s après cette recherche ; au-delà, nouveau tirage ;
- un appel annulé par l'équilibre (joueur ramené au niveau du ballon) n'est pas mémorisé comme appel dans le dos.
Test ajouté : `test_a_held_depth_run_does_not_survive_a_loss_of_the_ball` (cerveau).

Quatre mesures lancées en même temps sur le même arbre (20 matchs, graine d'audit), l'autre session ayant modifié le moteur dans la matinée (les mesures du matin sur des arbres différents ne sont pas comparables) :

| Critère | Sans appel dans le dos | Tenu, avant correctifs | Tenu, avec correctifs | Cible | Verdict |
|---|---|---|---|---|---|
| C4 attaquant à 2 m ou moins (standard) | 0,113 | 0,168 | 0,171 | ≥ 0,12 | OK |
| C4 attaquant à 5 m ou moins (indicateur) | 0,231 | 0,282 | 0,290 | — | |
| C2 appels redondants (standard) | 0,022 | 0,021 | 0,020 | ≤ avant | OK |
| Appels dans le dos par match (standard) | 54,4 | 64,6 | 64,7 | indicateur | +19 % |
| Hors-jeu par match (standard) | 1,2 | 1,4 | 1,5 | indicateur (réel 3 à 4) | |

Profil Off the Ball, code final : appels par joueur 81,9 (99) / 70,5 (11), +16 % ; appels dans le dos par joueur 4,1 / 1,6 (×2,6) ; course intense 12 243 / 7 819 m ; espace des coéquipiers 14,7 / 12,8 m (C3, indicateur). C1 : OK.

Les correctifs de la revue ne dégradent pas le mécanisme (0,171 contre 0,168). C5 : `test_a_weak_holder_makes_the_runner_give_up` dans `test_v2engine_off_ball.py`. C6 : suite complète 2 291 passés, 13 désélectionnés (03/11/2026), puis 2 305 passés, 13 désélectionnés, 0 échec sur l'état commité (clôture groupée) ; carte des attributs et test de rayon mis à jour.
