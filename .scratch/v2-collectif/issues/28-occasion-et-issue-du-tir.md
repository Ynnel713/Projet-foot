# 28: Danger, occasion et issue du tir

**What to build:** Le tir est aujourd'hui un pile ou face : but ou ballon au gardien, avec une réussite qui ignore les défenseurs, la pression et la position du gardien ; 7,8 % seulement des tirs partent de 16 m ou moins. Ce ticket rend le **danger**, l'**occasion** et l'**issue** réalistes, condition d'une variété cohérente des buts (le choix du geste de finition vient ensuite, `v2-attributs-restants/10`).

1. **Qualité de l'occasion, géométrique, pour chaque attaquant** : angle sous lequel le joueur voit le but entre les poteaux (et non plus l'écart latéral `abs(dy)/(d+1)`), défenseurs dans ce cône, position du gardien, distance. Le calcul répond à « s'il touchait le ballon ici, quelle serait sa chance de marquer ? », y compris pour un joueur qui ne tire pas.
2. **Danger de la situation** : à chaque instant de la possession, la meilleure occasion potentielle parmi les attaquants, pondérée par la probabilité que le ballon leur parvienne. Une **grosse occasion** est un pic de danger au-dessus d'un seuil, **quelle que soit l'issue** : un centre qui traverse la surface et laisse un attaquant à deux doigts de pousser le ballon dans le but vide, un face-à-face conclu par un tacle salvateur, comme un tir. Le seuil est proposé avec un nombre plausible de grosses occasions par match (modes « Moments clés » et « Résumé », `v2-mise-en-scene`).
3. **Tirer ou jouer encore** : le tireur décide sur la qualité **perçue** de l'occasion, comparée à la passe, dans le cadre du ticket 33 (meilleur choix factuel calculé avec ses capacités, puis perception déformée par Decisions, Composure sous pression et Anticipation). Ce ticket remplace seulement la chance de but du tir par la qualité de l'occasion.
4. **Fin de la dérogation A2** : Finishing seul règle la qualité d'exécution ; Composure réduit seulement la part de difficulté due à la pression sur le tireur (modèle de `possession.py`, règle R3). Nouvelle constante : pression sur le tir.
5. **Issues du tir** : but, à côté, contré, arrêté, repoussé. L'issue « arrêté » se décline selon la situation (force du tir, angle, hauteur, distance) : **capté** (le gardien bloque), **repoussé** (devant, sur le côté, en l'air : le ballon libre part à un endroit qui dépend de la direction et de la force du tir, seconds ballons), **claqué** en corner ou en sortie de but (ticket 29). Les notes du gardien restent au ticket `v2-attributs-restants/03` : une part neutre sans attribut en attendant (A8 n'est pas levée à moitié).
6. **Issue d'une séquence dangereuse sans tir** : tacle ou interception salvateur, dégagement, centre non repris, tracés avec le pic de danger.
7. **Événement dans la trace** : séquence dangereuse (pic de danger, issue), et pour un tir : tireur, position, qualité de l'occasion, issue, origine (passe au sol, passe en retrait, passe en profondeur, centre, dribble, rebond). Le rendu 2D rejoue l'issue enregistrée, sans en inventer.
8. **Frontière Finishing / Long Shots** tranchée ici, de préférence par une distance liée à la surface de réparation, sans zone où les deux comptent ; la frappe de loin (Long Shots) est résolue ici, par le même calcul (déplacée du ticket `v2-attributs-restants/01`).

**Attributs :** Finishing, Composure (pression seulement), Long Shots, Decisions ; gardien inchangé (note A8 jusqu'au ticket `v2-attributs-restants/03`).

**Blocked by:** 33 (cadre de la décision du porteur), 16, 29 (corners, sorties de but, ballon libre après un arrêt). À livrer avant 17, 19 et 22 : sinon la calibration réglerait les volumes de tirs et de buts sur une répartition fausse.

**Status:** découpé (04/11/2026, audit de granularité) en 28a (qualité de l'occasion, décision de tirer), 28b (issues du tir), 28c (danger et grosses occasions). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Origine (03/11/2026) :** consultation de l'expert demandée par le propriétaire (jeu divers et varié, réaliste, sans voir toujours les mêmes tirs ni les mêmes buts) ; définition de la grosse occasion corrigée par le propriétaire (situation dangereuse, pas forcément un tir) ; recommandations acceptées.

**Hors périmètre :** choix du geste de finition (placée, puissante, enroulée, lob, dribble du gardien, côté ouvert ou fermé : `v2-attributs-restants/10`) ; centres variés (`v2-attributs-restants/11`) et têtes (`01`, dont l'issue passe par le calcul de ce ticket) ; coups de pied arrêtés (`02`) ; notes et sorties du gardien (`03`).

**Point de vigilance :**
- Hérité du ticket 33 (04/11/2026) : tir contré minimal (défenseur à moins de 1 m de la ligne de tir vers le centre du but, 60 % pile dans la ligne) et chance de but divisée par deux tous les 5 m au-delà de 6 m, plancher 1 %, à remplacer par la qualité de l'occasion. Réserve acceptée : 33 tirs par équipe (réel environ 12), le tir restant souvent le vrai meilleur choix factuel : les équipes arrivent trop souvent à portée de tir.
- Pas de trajectoire 3D (D-V03) : le mode de ballon du ticket 29 distingue sol et aérien ; le contact sur le trajet (ticket 25) ne s'applique qu'aux tirs au sol.
- Chaque nouveau tirage décale la suite aléatoire : toutes les mesures de référence sont à refaire (comme après les tickets 25 et 26).
- Les chiffres réels ci-dessous viennent de la mémoire de l'expert (type Opta, StatsBomb, FBref) : **à sourcer** avant de devenir des critères, sinon « non trouvé ». La définition large de la grosse occasion n'a pas de chiffre réel.

## Acceptance criteria

- [ ] Repris du ticket 29 (réserve A2 acceptée le 03/11/2026) : corners 6 à 14 par match et touches 30 à 55 par match en match (50 matchs, graine d'audit) ; au ticket 29 : 0,84 corner et 22,7 touches, faute de contres, d'arrêts repoussés et de dégagements

- [ ] Constantes produit (pression sur le tir, part des parades repoussées, frontière Long Shots, perception de l'occasion, seuil de grosse occasion) et critères chiffrés, sourcés ou « non trouvé », validés par le propriétaire avant le code
- [ ] Scène contrôlée : à distance égale, un défenseur dans le cône ou un angle fermé baisse mesurablement la qualité de l'occasion ; un gardien avancé la change
- [ ] Scène contrôlée : un porteur à faibles Decisions tire plus souvent sur une occasion médiocre qu'un porteur à Decisions élevées, à situation égale
- [ ] Scène contrôlée : le centre qui traverse la surface et laisse un attaquant à deux doigts du but vide est une grosse occasion sans tir ; un face-à-face stoppé par un tacle salvateur aussi ; un tir de loin sans danger ne l'est pas
- [ ] A2 levée : Composure n'agit que sous pression (test) ; test de rayon des attributs et carte (`docs/CARTE_ATTRIBUTS_V2.md`) à jour, sans double comptage Finishing / Long Shots
- [ ] Les issues existent en match (but, à côté, contré, capté, repoussé, claqué) et les séquences dangereuses sans tir sont tracées, chacune avec son pic de danger et son origine
- [ ] Test de cohérence : l'arrêt claqué en corner est plus fréquent sur un tir puissant et excentré que sur un tir central faible, où le gardien capte ; la direction de la repoussée dépend de la direction du tir
- [ ] En match (50 matchs, graine d'audit), comparés aux indicateurs à sourcer : part des tirs dans la surface (ordre de grandeur cité : 55-65 %), part des buts dans la surface (80-90 %), qualité moyenne d'un tir hors penalty (0,09-0,11), tirs cadrés (30-35 %), tirs contrés (20-28 %), conversion (10-11 %) ; nombre de grosses occasions par match rapporté
- [ ] Indicateurs ajoutés au banc (`scripts/v2_indicators.py`) et définis dans `docs/INDICATEURS_V2.md`
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant le ticket 22
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
