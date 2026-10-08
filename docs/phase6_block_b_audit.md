# Phase 6, Bloc B — Audit de la physique du ballon

Document de référence du **08/10/2026**, sur `HEAD` = `e63d6f0`. **Audit seulement : aucune ligne de code n'a été modifiée.** *Mise à jour du 08/10/2026 : **B2 (rebonds) est terminé**, voir le §5, puis **B1 (décélération)**, voir le §6, puis **B4 (événements du ballon et parades)**, voir le §7, puis **B4-bis (consommation des événements)**, voir le §8 ; les §0 à §4 décrivent l'état avant B2.* Les mesures viennent de scripts jetables, hors dépôt, qui appellent `ball_state_at` sur les 12 gabarits réels (helpers déterministes de `tests/test_narrative_player.py`, compo fixe) pour les issues `but`, `arret`, `poteau`, `barre`, `hors_cadre`, `tacle` et `degagement`.

## 0. Méthode et limites

- **Chemin** : la physique du ballon est dans `src/ligue1sim/animation/ball.py` (517 lignes), pas `src/ligue1sim/ball.py`.
- **Lecture** : `ball.py`, `templates.py` (tags, `_flight_target`), `types.py` (`BallState`), `render/canvas.html` (dessin du ballon, détection du but), `docs/ball_flight_design.md`, `docs/simulation_physique_archi.md`.
- **Mesures** : échantillonnage de `ball_state_at` (60 points par segment ; 1/60 s par segment pour la détection de rebond). Une compo et un `event_ref` fixes : les valeurs tirées par hachage (vitesse du vol, hauteur du centre) sont donc celles de cette fixture, pas une moyenne.
- **Hors périmètre** : le temps de rendu côté navigateur, la perception réelle (pas de test utilisateur : les notes d'impact du §2 sont une appréciation, pas une mesure).
- **Contrainte de la phase** : `render/canvas.html` ne peut pas être modifié dans cette étape. Les leviers qui en dépendent sont signalés (§3).

## 1. Audit factuel de `ball.py`

### 1.1 Les comportements (6 tags, pas 5)

Le dispatch (`ball_state_at`) connaît **six** tags : `pass_ground`, `pass_lob`, `shot`, `cross`, `deflect` et `ball_flight` (ajouté le 24/09/2026 pour le vol après la frappe). Le tag d'un segment est celui de la keyframe de départ ; à défaut : porteur absent → `deflect`, dernier segment → `shot`, sinon `pass_ground`. Toute position est **exacte à la keyframe d'arrivée** (garantie du moteur) ; la durée de chaque segment vient du gabarit (`Template.duration`).

| Tag | Formule | Paramètres | Bornes | Mesuré (12 gabarits) |
|---|---|---|---|---|
| `pass_ground` | progression `p(s) = (1+k)s − k s²`, `k = (1−0,95)/(1+0,95) = 0,0256` ; ligne droite, `z = 0` | freinage final = 5 % de la vitesse initiale | arrivée exacte ; aucun plafond de vitesse | 0,56 à 18,95 m/s ; rapport v fin / v début = **0,95** partout |
| `pass_lob` | ligne droite au sol, `z = h·4s(1−s)` | `h` linéaire : 0,25 m à 10 m, 1,20 m à 30 m (distance bornée à [10, 30]) | `h` ∈ [0,25 ; 1,20] m | **non déclenché par aucun gabarit** (testé unitairement seulement) |
| `shot` | ligne droite + décalage latéral `c·4s(1−s)`, `c = ½·a·(T/2)²`, `a = 0,003·spin·(d/T)` ; `z = h·4s(1−s)` | `_MAGNUS_K = 0,003` ; `spin` en rad/s | pas de courbure sous 11 m ; `h = 0` sous 16 m puis rampe jusqu'à 0,8 m à 40 m | `z` max 0 à 0,75 m ; vitesse 1,5 à 17,2 m/s |
| `ball_flight` | x/y de `shot` (donc Magnus), `z = z_cible·s` (**rampe linéaire**) | durée = distance 3D / vitesse ; vitesse tirée par hachage dans [15 ; 35] m/s | cible : `but` z ∈ [0 ; 2,40], `arret` [0 ; 2,0], `poteau` [0 ; 2,2], `barre` [2,35 ; 2,44], `hors_cadre` [0 ; 3,5] m | durée 0,37 à 0,88 s ; vitesse 33,4 à 34,3 m/s |
| `cross` | Bézier quadratique latérale (point de contrôle décalé de ±12 % de la distance, signe par hachage) ; `z = h·4s(1−s)` | `h` ∈ [2,0 ; 2,5] m par hachage | arrivée exacte | corner : 41,2 m en 2,1 s (20,7 m/s), `z` max 2,48 m |
| `deflect` | ligne droite à vitesse constante + une bosse latérale lisse (cosinus surélevé) sur les 15 % finaux ; `z = 0` | amplitude 8 % de la distance, signe par hachage | revient à 0 exactement à s = 1 | 2,6 à 15,1 m/s |

**Observation de fond.** Dans les 12 gabarits, le tag `shot` ne désigne **pas** la frappe : c'est le segment d'approche (conduite, 1,5 à 17 m/s, `z` ≤ 0,75 m). La vraie frappe est le segment `ball_flight` qui suit (0,4 à 0,9 s à ~34 m/s).

### 1.2 Effet Magnus

- **Formule** : accélération latérale `a = 0,003 · spin · v_base`, `v_base = distance / durée`, déviation au pic `c = ½·a·(T/2)²`, appliquée comme décalage perpendiculaire en parabole (`4s(1−s)`), nul aux extrémités. `_MAGNUS_K` est un ordre de grandeur physique (`C_L·ρ·A·r/m`), pas une valeur mesurée sur ce moteur.
- **Paramètre** : seul `decalage_enroulee` a un spin non nul, **50 rad/s**, posé sur ses segments `shot` et `ball_flight` (`templates.py`, `_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S`).
- **Déviation mesurée** (écart maximal à la ligne droite, ce gabarit) :

| Issue | Segment `shot` (approche) | Segment `ball_flight` |
|---|---|---|
| but | 1,08 m (16,05 m, 3,6 s, 4,46 m/s) | 0,12 m |
| arret / poteau / barre | 1,08 m | 0,09 à 0,10 m |
| hors_cadre | 1,08 m | 0,49 m (vol de 0,88 s) |
| tacle / degagement | 1,08 m | pas de vol |

  La mesure coïncide avec la formule à deux décimales. La plage « 0,23 à 0,98 m » du rapport antérieur n'est pas reproductible ici : 0,98 m est le chiffre de calibrage du commentaire (géométrie 14,6 m / 3,6 s), 1,08 m est celui de cette fixture, et le minimum observé est 0,09 m.
- **Angle** : l'angle initial de déviation est d'environ **15°** sur l'approche (1,2 m/s latéral pour 4,46 m/s) mais de **1,8°** seulement sur le vol (1,1 m/s latéral pour 33,8 m/s).
- **Constat** : la courbure visible se produit sur le segment lent (la conduite), pas sur la frappe rapide, où elle vaut 0,1 m, soit environ 1 px à l'écran. C'est inversé par rapport à une vraie frappe enroulée. Dette connue, non corrigée : résidu de vitesse 3D > 35 m/s sur 2,8 % des vols (commentaire de tête de `ball.py`).

### 1.3 Rebond

**Aucun modèle de rebond.** Il n'y a ni coefficient de restitution, ni friction au contact, ni angle de réflexion. `z` vaut 0 sur les segments au sol et suit une parabole `4s(1−s)` ou une rampe linéaire sinon ; il ne remonte jamais après un contact.

Mesure : sur 84 combinaisons gabarit × issue, 5 retours à `z ≈ 0` et 3 « remontées » ensuite ; ce ne sont **pas** des rebonds : c'est l'atterrissage d'un centre (`corner`) suivi du vol de la tête, qui repart de 0. Amplitude de rebond sur un tir : **0**.

Conséquence visible : pour les issues `poteau` et `barre`, le ballon arrive à 33,9 m/s sur la cible (z = 0,88 m et 2,39 m) et **le clip s'arrête là**, sans retour. Pour `arret`, il s'arrête à 33,8 m/s au niveau du gardien.

### 1.4 Friction de l'air et du sol

**Pas de friction de l'air.** Le seul freinage est celui de `pass_ground` : **5 % de perte de vitesse sur tout le segment** (décélération constante, très faible). Ni `shot`, ni `ball_flight`, ni `cross`, ni `deflect` ne ralentissent.

Mesure d'une passe au sol (`construction_placee`, segment 0, 5,06 m en 4,2 s) : vitesse de 1,23 m/s à 1,17 m/s, puis **5,29 m/s** au début du segment suivant. La vitesse n'est pas continue d'un segment à l'autre (documenté dans `ball.py` : « PAS garantie d'un segment à l'autre »).

### 1.5 Rotation du ballon

- **Modélisée ?** Partiellement : `BallState.spin` est un **scalaire** (rad/s) porté par les keyframes. Pas d'axe, pas de vitesse angulaire vectorielle, pas d'angle intégré. Il ne sert qu'à calculer le Magnus.
- **Transmise ?** Oui : `ball.spin` est sérialisé dans chaque image du payload.
- **Rendue ?** **Non.** `render/canvas.html` contient **0 occurrence** de `spin`. Le ballon est un disque blanc uni de 6 px de diamètre avec un contour (`BALL_DIAMETER_SCREEN_PX = 6`) : même tourné, il serait identique. En l'air, il est surélevé à l'écran (`lift = min(z, 4)·SCALE·0,5`), son rayon grossit jusqu'à ×1,5 et son ombre reste au sol.

### 1.6 Sorties du ballon

**Pas de détection explicite dans `ball.py`.** Aucune notion de ligne de touche, de ligne de but ou de sortie.
- Le ballon ne « sort » que parce que la cible du vol a des coordonnées hors terrain : `but` x ∈ [1,00 ; 1,02], `hors_cadre` x ∈ [0,97 ; 1,03] avec y hors des poteaux, `poteau` et `barre` x ≈ 1,00. Mesure : fin de clip à x = 1,012 (but), 1,001 (poteau, barre), 1,006 (hors cadre), 0,992 (arrêt).
- **Aucun événement n'en découle** : pas de corner, de touche, de dégagement ou de remise en jeu ; le clip s'arrête à la fin du vol. `tacle` et `degagement` n'ont pas de vol (fin à x = 0,875, 4,4 m/s).
- La détection du **but** est faite côté navigateur, dans `render/canvas.html` (`goalEvents`) : première image où `x ≥ 1` (ou `≤ 0`) avec `|y − 0,5|` dans les poteaux, pour les clips d'issue `but`. Ce n'est pas une information du moteur.

### 1.7 Tag ambigu cross / deflect sur corner

**Plus d'actualité dans le code.** Le conflit a été tranché le 23/09/2026 (brief « corner tags decision ») : `templates.py` pose `physics_tags=((0.0, "pass_ground"), (0.3, "cross"), (0.6, "deflect"))`, soit centre en vol (0,3 → 0,6) puis ballon disputé au contact (0,6 → 1,0). Mesure : `cross` 41,2 m, 2,1 s, `z` max 2,48 m ; `deflect` 7,2 m, 2,8 s, 2,6 m/s, au sol.

**Documentation périmée** : `docs/simulation_physique_archi.md` (ligne 12) parle encore d'un « point non résolu ». Reste un défaut de **vocabulaire** : `shot` nomme une conduite, et `deflect` un ballon au sol qui roule lentement après un centre à 20 m/s.

## 2. Comparaison avec un rendu Football Manager 2D classique

Les notes d'impact (faible / moyen / fort) sont une **appréciation** à partir des mesures du §1, pas un test utilisateur.

| Attendu en FM | Aujourd'hui | Écart | Impact |
|---|---|---|---|
| **Cloche lisible** : sommet, descente, rebond | Aucun lob (`pass_lob` jamais déclenché). Le centre de corner a un sommet à 2,5 m et une descente nette ; les frappes montent en rampe linéaire jusqu'à la cible ; **pas de rebond** après l'atterrissage | Cloche : seulement via le centre de corner ; pas de rebond | **Moyen** |
| **Passe qui ralentit progressivement** | Perte de 5 % sur tout le segment (1,23 → 1,17 m/s), puis saut de vitesse (→ 5,29 m/s) au segment suivant. La passe paraît à vitesse constante, puis le ballon change brutalement de rythme | Pas de décélération lisible, discontinuité entre segments | **Moyen** (proche de la dette du ticket 12 pour les joueurs) |
| **Frappe enroulée à courbure visible, rotation lisible** | Courbure : 1,08 m (≈ 10 px) sur la conduite lente, 0,1 m (≈ 1 px) sur la frappe rapide. Rotation : `spin` calculé mais **jamais lu** par le rendu ; ballon uni de 6 px | Courbure presque invisible sur la frappe ; rotation invisible | **Moyen** |
| **Rebond crédible** : hauteur décroissante, contact court | Aucun. Sur poteau et barre, le ballon arrive à ~34 m/s et le clip s'arrête net ; sur arrêt, de même | Rebond absent précisément là où il est le plus attendu | **Fort** |
| **Ballon sorti → réaction logique** (corner, touche, dégagement) | Aucune : le clip finit à la fin du vol ; le but est détecté par le navigateur | Pas de suite logique après une frappe non cadrée | **Moyen** (les clips sont des temps forts isolés, pas un match continu) |

**Écart transversal, noté « moyen »** : les durées longues des gabarits (jusqu'à 4,2 s pour 5 m) donnent des passes à 0,6-1,2 m/s, très en dessous d'une vraie passe, alors que le vol de la frappe est à 34 m/s. Le contraste de vitesse entre approche et frappe est très marqué.

## 3. Leviers proposés (aucune implémentation)

Les numéros B1 à B6 sont ceux de ce document.

| # | Levier | Gain perceptible (estimation) | Risque | Complexité | Dépendances |
|---|---|---|---|---|---|
| **B1** | **Décélération réaliste (friction de l'air et du sol)** : remplacer le freinage de 5 % par une décélération marquée sur les passes et un ralentissement sur le vol, par reparamétrage du temps (la position d'arrivée reste exacte) ; frottement quadratique pour le ballon en l'air | Moyen : passes qui s'éteignent, frappes qui perdent un peu de vitesse | Faible à moyen : `test_ball.py` fige le rapport 0,95 ; la discontinuité entre segments reste | Faible | Aucune ; la discontinuité entre segments est un sujet voisin (ticket 12) |
| **B2** | **Rebond au sol, sur poteau, barre et arrêt** : segment supplémentaire après le vol ; restitution verticale 0,5 à 0,7 (selon la surface), friction horizontale, 2 à 3 rebonds à hauteur décroissante ; poteau et barre renvoient le ballon vers le jeu | **Fort** : l'écart le plus visible, sur les issues les plus spectaculaires | Moyen : la durée du clip s'allonge (0,5 à 1,5 s, soit environ +10 % de poids), la détection du but du navigateur doit continuer à ne voir que le premier franchissement | Moyenne | Demande `templates.py` (ajout du segment après `ball_flight`) ; B4 s'appuie sur lui |
| **B3** | **Rotation visible** : intégrer un angle de rotation (axe perpendiculaire à la trajectoire, vitesse liée à la vitesse du ballon) ; champ additionnel dans le payload ; marqueur visible sur le ballon (point sombre ou pentagone qui tourne), idéalement avec un ballon un peu plus grand que 6 px | Moyen : seul un ballon assez grand rend la rotation lisible | Faible côté moteur ; **demande `canvas.html`** (aujourd'hui gelé) ; champ additif au protocole `version` 1 | Moyenne | `canvas.html` (autorisation requise) ; mieux perçu avec B1 |
| **B4** | **Sorties et événements du ballon explicites** : le moteur émet, avec leur instant, les événements `franchissement de ligne de but`, `poteau`, `barre`, `arrêt`, `sortie` (but, corner, touche, dégagement) dans les métadonnées du clip ; le navigateur n'a plus à les deviner | Moyen : fiabilise le but, ouvre la voie à une suite logique après la frappe | Faible à moyen : touche le payload et la narration (`engine/`) ; deux sources de vérité tant que `canvas.html` garde son heuristique | Moyenne | B2 (poteau et barre naissent avec les rebonds) ; `canvas.html` pour consommer les événements |
| **B5** | **Vocabulaire des tags** : renommer `shot` en `carry` (conduite) quand il s'agit d'une approche, clarifier `deflect`, mettre à jour la documentation périmée ; permettre de régler friction et courbure par type de geste | Faible en soi (cohérence), mais **débloque** B1 et B3 sans ambiguïté | Faible à moyen : `physics_tags` des 12 gabarits (`templates.py`) et de nombreux tests | Faible à moyenne | Aucune ; facilite B1 |
| **B6** | **Micro-variations encadrées** (variabilité acceptée en Phase 6) : angle et vitesse de sortie de frappe, cible du vol, restitution des rebonds, ±5 à 10 % autour de la valeur du gabarit ; score, buts et cartons restent déterministes | Moyen : deux visionnages du même match ne sont plus identiques au pixel | Moyen : le cache HTTP et la reproductibilité (ticket 16) ; il faut un identifiant de variante (graine de rendu) dans la clé de cache ou un petit nombre de variantes pré-calculées | Moyenne | Mieux après B1 et B2 (il faut des grandeurs à faire varier) ; indépendant du résultat sportif |

**Hors liste, à noter** : (a) la courbure Magnus est portée par la conduite lente plutôt que par la frappe rapide (§1.2) : à corriger avec B1 ou B3 ; (b) le résidu de vitesse > 35 m/s sur 2,8 % des vols de `decalage_enroulee` (dette connue).

## 4. Ordre de traitement proposé

La consigne suggérait B2 (rebonds), B3 (rotation), B4 (sorties), B5 (tag). L'audit conduit à un ordre légèrement différent, **à valider** :

1. **B2 — rebonds.** C'est l'écart le plus visible (fort) et il ne dépend d'aucun autre levier. Il demande une modification de `templates.py` à autoriser.
2. **B1 — décélération.** Complexité faible, gain moyen, indépendant ; utile avant B3, car un ballon qui ne ralentit pas rend la rotation incohérente.
3. **B4 — événements du ballon.** Il consomme les poteaux, barres et arrêts de B2 ; il demande un accord sur la modification du payload (et, pour être consommé, de `canvas.html`).
4. **B5 — vocabulaire des tags.** Peu visible, mais à faire **avant** B3 et avant toute différenciation fine de B1 ; peut aussi passer en tête s'il est préférable de nettoyer d'abord.
5. **B3 — rotation visible.** Dépend de `canvas.html` (gelé) ; moins perceptible avec un ballon de 6 px ; à regrouper avec d'éventuels autres changements de rendu.
6. **B6 — micro-variations.** En dernier : il faut des grandeurs stables à faire varier, et il touche le cache et la reproductibilité.

**Décisions attendues de l'architecte** : (1) autorisation de modifier `templates.py` pour B2, B4, B5 ; (2) levée du gel de `canvas.html` pour B3 et pour consommer B4 ; (3) choix du mécanisme de variantes pour B6 (graine de rendu dans la clé de cache, ou nombre fixe de variantes).


## 5. B2 — Rebonds (terminé le 08/10/2026)

### 5.1 Périmètre, et écart à la consigne

Périmètre autorisé par l'architecte (option A) : `src/ligue1sim/animation/ball.py`, `src/ligue1sim/animation/templates.py` et `engine/narrative_player.py`. **Fichiers réellement modifiés : `ball.py` et `narrative_player.py`. `templates.py` n'est pas modifié.**

La consigne demandait de prolonger la **durée de la `Sequence`** dans `templates.py`. Mesure faite avant d'écrire du code : allonger `Sequence.duration` décale presque toutes les images **avant** le contact, parce que `motion` s'en sert pour la dérive des joueurs de fond (`_background_position_at`) et pour le décalage de réaction des joueurs sans rôle (`_start_offset`).

| Gabarit (issue `barre`, +2 s) | Images avant contact | Images modifiées | Écart maximal d'un joueur |
|---|---|---|---|
| `corner` | 222 | 221 | 0,85 m |
| `decalage_enroulee` | 192 | 191 | 0,96 m |
| `une_deux` | 132 | 131 | 1,30 m |

Cela contredit « la trajectoire existante ne change pas » et « seul l'ajout du segment final ». Les images du rebond sont donc ajoutées **après** la séquence, dans `narrative_player._extend_with_rebound`, avec la physique de `ball.py` (`rebound_after_flight`) ; les joueurs restent figés sur leurs dernières positions, comme pendant le vol. Les images existantes sont strictement identiques (vérifié, §5.4). Conséquence : les tests `test_ball_reaches_target_on_shot` et `test_poteau_on_post_not_between` ne sont **pas** cassés (la séquence s'arrête toujours à la cible du vol) et restent en place ; `tests/test_templates.py` n'a pas besoin d'être adapté.

**Durée du rebond.** La consigne parlait d'une prolongation de 0,3 s. Elle ne suffit pas : un ballon qui quitte la barre à 2,4 m met 0,2 s à retomber, et trois à cinq rebonds en demandent 2 à 3. La durée est donc **physique, plafonnée à 3 s** (`REBOUND_MAX_DURATION_S`), le clip s'arrête au dernier contact avec le sol qui tient dans ce plafond.

### 5.2 Ce qui est livré

- **`ball.py`** : tag `bounce` ; `rebound_trajectory`, `rebound_exit_velocity`, `rebound_after_flight` (poteau, barre) ; `ReboundTrajectory.state_at(tau)` ; rebond de la hauteur d'un ballon qui retombe d'un centre (`cross` puis `deflect`, donc le corner), la trajectoire x/y du `deflect` étant inchangée.
- **`narrative_player.py`** : `_extend_with_rebound`, appelé après la contrainte d'accélération, uniquement pour les issues `poteau` et `barre`.
- **Issues inchangées** : `but`, `arret`, `hors_cadre`, `tacle`, `degagement` n'ont aucun rebond. Un ballon qui franchit la ligne n'est donc jamais dévié ; la détection du but (`canvas.html`) n'est pas touchée.

### 5.3 Paramètres retenus

| Paramètre | Valeur | Justification |
|---|---|---|
| Restitution au sol | **0,70** | la hauteur d'un rebond vaut e² de la précédente, soit 0,49 : perte de 51 %, dans la cible « rebond mou » de FM (40 à 50 %). À 0,8, la perte tombe à 36 % (balle de tennis) |
| Friction horizontale au sol | **−15 % par rebond** | milieu de la fourchette 10-20 % |
| Arrêt des rebonds | sommet < 5 cm, puis roulement à 2,5 m/s² | herbe sèche (1,5 à 3 m/s²) |
| Poteau | restitution **0,70** | réflexion horizontale, `vz` conservé ; angle de contact de 0 (plein centre) à 35° selon l'écart du point d'impact au centre du montant |
| Barre | restitution **0,70**, normale inclinée de **5 à 15°** sous l'horizontale côté terrain | le ballon repart vers le bas et vers le terrain, jamais derrière la ligne. Avec 10 à 30°, le premier rebond au sol montait à 3,19 m en moyenne (10,5 m au maximum) ; avec 5 à 15° : 1,46 m (2,71 m au maximum) |
| Aléa de direction (D8) | **±10°** sur l'azimut de sortie | calculé à partir de la géométrie, puis perturbé par un hachage déterministe de `event_ref` (borné, vérifié par test) |
| Garde-fous | vitesse de sortie vers le terrain ≥ 1 m/s ; vers le bas ≥ 1 m/s (barre) ; ballon arrêté à 3 m des lignes (planches) | jamais derrière la ligne : 0 cas sur 1 440 rebonds simulés |

### 5.4 Mesures avant / après

**Déterminisme** (graines 1 à 100, `random.seed` et `np.random.seed`, `PYTHONHASHSEED=0`, Ligue 1 réelle, HEAD contre arbre modifié) : **100 matchs sur 100** avec scores, buts, cartons, remplacements, blessures et notes identiques ; scores identiques 100/100. L'animation est en aval du moteur sportif.

**Clips** (les mêmes 100 matchs, tous les clips d'issue `poteau` ou `barre` : 40 clips, tous des poteaux ; aucune barre n'apparaît dans cet échantillon) :
- images existantes strictement identiques : **39 clips sur 40**. Le 40e est un `corner` : joueurs, x, y et t identiques sur les 271 images ; seule la hauteur du ballon change (47 images, jusqu'à 0,48 m, au lieu de 0), ce qui est le rebond du centre qui retombe (voulu) ;
- rebonds au sol (min / moy / max) : **1 / 3,58 / 5** ; sommet du 1er rebond : 0,0 / 0,72 / 4,78 m ;
- prolongation du clip : 2,09 / 2,92 / 3,03 s, soit 63 à 91 images ajoutées (+19 à +60 % d'images, 40 % en moyenne, pour ces clips seulement : `poteau` et `barre`) ;
- arrêt à 19,6 / 36,9 / 58,0 m du point de contact, et à 7,9 / 40,4 / 62,4 m du point de tir.

**5 clips témoins** (avant : le clip s'arrête au contact, ballon à ~34 m/s, `z` = hauteur du contact ; après : rebond jusqu'à un contact au sol) :

| Clip | Gabarit | Rebonds | Sommet du 1er rebond | Prolongation | Arrêt / contact | Arrêt / point de tir | Avant : durée du clip |
|---|---|---|---|---|---|---|---|
| 1:8 | `une_deux` | 4 | 0,34 m | 3,03 s | 22,2 m | 19,7 m | 5,37 s |
| 1:11 | `recuperation_haute` | 3 | 1,17 m | 2,59 s | 56,3 m | 45,2 m | 6,00 s |
| 2:0 | `decalage_enroulee` | 1 | 0,0 m | 3,03 s | 25,1 m | 15,8 m | 7,10 s |
| 2:1 | `debordement_centre_tete` | 5 | 0,76 m | 3,03 s | 55,0 m | 58,4 m | 6,60 s |
| 3:1 | `decalage_enroulee` | 2 | 0,06 m | 3,01 s | 40,4 m | 53,5 m | 6,87 s |

**Écart perceptible** : avant, le ballon s'arrêtait net sur le poteau ; après, il repart vers le terrain, rebondit 1 à 5 fois et finit au sol, en 2 à 3 s de plus. En revanche, il va **loin** (36,9 m en moyenne depuis le contact, jusqu'à 58 m) parce que le moteur n'a pas encore de frottement de l'air.

**Sur 720 rebonds de barre simulés** (12 gabarits × 60 événements) : 3 à 4 rebonds, sommet du 1er rebond 1,21 à 2,71 m (moyenne 1,46 m), arrêt à 22,8 à 59,0 m du contact, durée 2,41 à 3,0 s.

### 5.5 Corrections factuelles (vérifiées contre les mesures de l'audit, §1)

| Point | État vérifié |
|---|---|
| Effet Magnus | La conduite `shot` dévie de **1,08 m** (spin 50 rad/s, 16,05 m, 3,6 s, mesuré) ; le vol rapide `ball_flight` de **0,09 à 0,49 m** (0,49 m pour un `hors_cadre` de **0,88 s**). Le « 0,75 m » est la hauteur `z` maximale d'une conduite, pas la déviation ; le « 0,15 s » et le « 0,49 s » ne correspondent à aucune durée de segment mesurée |
| Friction de l'air | **Elle n'existe pas** dans `ball.py` : seul `pass_ground` perd 5 % de vitesse, sur la **totalité du segment**. Le « 5 % par seconde partout » n'est donc pas l'état du code ; c'est une valeur à implémenter, au levier B1 |
| Tag cross / deflect | Résolu depuis le 23/09/2026 (`templates.py` : `cross` puis `deflect` pour le corner). La mention « non résolu » de `docs/simulation_physique_archi.md` (ligne 12) est périmée. Le périmètre de B5 se réduit à la variété des types de frappe et au vocabulaire |

### 5.6 Limites connues

- **Le ballon n'est pas à l'arrêt à 3 s** : sans frottement de l'air, l'arrêt complet demande 6 à 7 s et 45 à 57 m (mesuré avec un plafond de 60 s). Le clip est coupé au dernier contact avec le sol avant 3 s. Le levier B1 doit résoudre cela.
- **Planches** : environ 16 % des rebonds (229 sur 1 440) finissent contre la limite de 3 m derrière les lignes ; le ballon y est arrêté.
- **Barre** : aucune issue `barre` dans l'échantillon de 100 matchs (rare dans la narration) ; couverte par les tests unitaires et les 720 rebonds simulés.
- **Joueurs figés** pendant le rebond (2 à 3 s) ; aucun joueur ne réagit au ballon. À revoir avec le Bloc A.
- `arret`, `hors_cadre` et `but` sont inchangés : un tir qui finit dans le filet ou dans le gardien s'arrête toujours net.

### 5.7 Statut

**B2 terminé.** Prochaine étape de la séquence : B1 (décélération, friction de l'air).


## 6. B1 — Décélération (friction de l'air), terminé le 08/10/2026

**Pourquoi B1.** B2 a mesuré que, sans friction de l'air, le ballon n'était pas à l'arrêt à 3 s après un impact (il lui fallait 6 à 7 s et 45 à 57 m). B1 ajoute la friction de l'air à toute la physique du ballon. Fichiers modifiés : `ball.py` et `tests/test_ball.py` ; `templates.py`, `canvas.html`, le moteur sportif et 3c sont intacts.

### 6.1 Formule retenue

Friction proportionnelle au carré de la vitesse : `dv/dt = −c·v²`, soit `v(d) = v0·exp(−c·d)` à la distance `d` parcourue.

| Paramètre | Valeur | Justification |
|---|---|---|
| `AIR_DRAG_PER_M` (c) | **0,05 / 15 = 0,0033 /m** | 5 % de perte de vitesse par seconde à 15 m/s (valeur de l'architecte) ; la perte relative `c·v` vaut ~1 %/s à 3 m/s et ~11 %/s à 34 m/s : jamais nulle, plus forte quand le ballon va vite |
| `AIR_DRAG_MAX_RATE_PER_S` | 0,30 | borne : la perte relative initiale d'un vol ne dépasse jamais 30 %/s |
| `AIR_DRAG_MIN_SPEED_RATIO` | 0,50 | borne : un segment ne perd jamais plus de la moitié de sa vitesse |

**Application.** Les trajectoires de `ball.py` sont cinématiques (positions imposées aux keyframes, durée fixée par le gabarit). La friction y est un **reparamétrage du temps** le long de la trajectoire, `p(s) = ln(1 + (e^{cD} − 1)·s) / (cD)`, qui garde `p(0) = 0` et `p(1) = 1` (arrivée exacte) : le ballon part plus vite qu'il n'arrive (rapport `e^{−cD}`). La vitesse initiale n'est pas réduite : `v0 = v_moyenne · cD / (1 − e^{−cD})`, un peu au-dessus de la moyenne. Elle s'applique à `pass_ground` (qui remplace l'ancien freinage fixe de 5 %), `pass_lob`, `shot` (la conduite), `cross`, `deflect` et `ball_flight`. Dans les rebonds, les vols balistiques sont freinés horizontalement (`h(τ) = h0 / (1 + c·h0·τ)`) ; la composante verticale ne subit que la gravité.

### 6.2 Ce que la friction de l'air seule ne règle pas (écarts à la consigne)

L'objectif « arrêt en 3 à 4 s après le premier rebond » **n'est pas atteignable par la friction seule** : la durée est portée par la série de rebonds **verticaux** (restitution 0,70), que la friction horizontale ne freine pas. Mesure (12 gabarits × 40 événements, poteau et barre, sans plafond de durée) :

| Réglage | Arrêt après le 1er rebond (poteau / barre, moyenne) |
|---|---|
| B2, sans friction de l'air | 5,42 / 5,60 s |
| friction de l'architecte (c = 0,0033) | 4,97 / 5,18 s (−8 %) |
| friction physique réelle (c = 0,0133, ~27 %/s à 20 m/s) | 4,19 / 4,44 s |
| friction de l'architecte + roulement 4 m/s² | 3,80 / 4,35 s |
| + seuil de rebond 15 cm | 3,91 / 4,34 s, rebonds 3,4 / 4,5 en moyenne |

Trois réglages **non validés par l'architecte** ont donc été changés dans `ball.py`, pour approcher l'objectif ; chacun se revient d'une constante :

| Constante | B2 | B1 | Raison |
|---|---|---|---|
| `ROLL_DECEL_M_S2` | 2,5 | **4,0** | seul levier restant sur la phase de roulement (valeur de jeu, plus forte que le roulement réel de l'herbe) |
| `REBOUND_MIN_APEX_M` | 0,05 | **0,15** | sans cela la barre fait 6 à 7 rebonds (objectif 2 à 5) ; un rebond de moins de 15 cm lève le ballon de moins d'1 px à l'écran. La durée n'en dépend presque pas (mesuré : 4,35 → 4,34 s) |
| `REBOUND_MAX_DURATION_S` | 3,0 | **5,0** | à 3 s, le ballon était encore en mouvement dans 131 clips sur 131 ; à 5 s, 88 sur 131 sont à l'arrêt |

Le seuil de 5 cm de l'architecte (B2) et l'objectif « 2 à 5 rebonds » se contredisent dès que le ballon va loin ; B1 retient l'objectif mesurable.

### 6.3 Mesures avant / après (graines 1 à 100, 131 clips d'issue `poteau`)

| Mesure | Avant (état B2) | Après (B1) |
|---|---|---|
| Arrêt après le 1er rebond (moyenne / médiane / p90 / max) | 2,26 / 2,36 / 2,74 / 2,96 s (**clip coupé à 3 s**, ballon en mouvement dans 131 clips sur 131) | **3,76 / 3,88 / 4,38 / 4,96 s** (clip coupé à 5 s, ballon en mouvement dans 43 clips sur 131) |
| Rebonds au sol (min / moy / max) | 1 / 3,8 / 5 | 1 / 3,1 / 5 |
| Durée totale du rebond | 2,91 s | 4,41 s |
| Sommet moyen du 1er rebond | 0,68 m | 0,67 m |
| Arrêt à (depuis le contact) | 38,4 m | 39,5 m |

**Les chiffres « avant » ne sont pas comparables tels quels** : le plafond de 3 s de B2 coupait le rebond avant son arrêt naturel (mesuré sans plafond : 5,4 à 5,6 s). La comparaison à plafond égal est celle du tableau du §6.2.

**5 clips témoins** (avant → après) :

| Clip | Gabarit | Arrêt après le 1er rebond | Rebonds | Durée totale | Vitesse à la fin |
|---|---|---|---|---|---|
| 1:8 | `une_deux` | 2,58 → 2,61 s | 4 → 3 | 3,00 → 3,04 s | 2,8 → 0,0 m/s |
| 1:11 | `recuperation_haute` | 1,66 → 4,08 s | 3 → 4 | 2,58 → 5,00 s | 18,1 → 2,6 m/s |
| 2:0 | `decalage_enroulee` | 2,85 → 2,79 s | 1 → 1 | 3,00 → 2,94 s | 4,5 → 0,0 m/s |
| 2:1 | `debordement_centre_tete` | 2,22 → 4,22 s | 5 → 4 | 3,00 → 5,00 s | 8,0 → 1,4 m/s |
| 3:1 | `decalage_enroulee` | 2,82 → 4,82 s | 2 → 1 | 3,00 → 5,00 s | 0,5 → 0,0 m/s |

**Passe au sol** (vitesse départ / mi-course / arrivée, m/s ; avant → après) :

| Clip | Passe | Avant | Après | Arrivée / départ |
|---|---|---|---|---|
| 1:0 | 33,6 m en 3,60 s | 9,56 / 9,32 / 9,08 | 9,86 / 9,31 / 8,82 | 0,89 |
| 1:1 | 28,1 m en 3,20 s | 9,02 / 8,79 / 8,57 | 9,22 / 8,79 / 8,39 | 0,91 |
| 1:3 | 34,6 m en 1,50 s | 23,64 / 23,05 / 22,46 | 24,42 / 23,02 / 21,77 | 0,89 |

La décélération est continue (vérifiée à 1/60 s par test : aucun pas ne perd plus de 2 % de la vitesse initiale) ; le ballon arrive à 89-94 % de sa vitesse de départ, ni mort ni trop vif. La vitesse moyenne n'a pas changé (la mi-course reste la même) : la durée et les positions imposées sont conservées.

**Tir** (`ball_flight`, vitesse départ / mi-course / arrivée au but, m/s) :

| Clip | Vol | Avant | Après |
|---|---|---|---|
| 1:3 | 15,0 m en 0,44 s | 34,60 / 34,60 / 34,60 | 35,47 / 34,60 / 33,77 |
| 1:4 | 13,7 m en 0,63 s | 21,64 / 21,64 / 21,64 | 22,14 / 21,63 / 21,15 |
| 1:9 | 31,8 m en 1,52 s | 20,99 / 20,99 / 20,99 | 22,14 / 20,97 / 19,92 |

Le tir arrive à 94-96 % de sa vitesse de départ. La trajectoire reste lisible : la position à 10 % du vol diffère de moins de 1 % de la distance de celle sans friction (testé). **Point d'attention** : la vitesse de départ est environ 2,5 % au-dessus de la vitesse moyenne tirée (35,47 m/s pour 34,6 m/s), donc un tir tiré près de 35 m/s dépasse légèrement cette borne au départ (résidu de la même nature que la dette Magnus du §1.2).

### 6.4 Déterminisme

**100 matchs sur 100** avec scores, buts, cartons, remplacements, blessures et notes identiques entre l'état B2 (HEAD) et B1 (graines 1 à 100, `random.seed`, `np.random.seed`, `PYTHONHASHSEED=0`). La friction n'agit que sur l'animation, en aval du moteur sportif.

### 6.5 Limites connues

- L'effet de la loi en `v²` est **faible aux basses vitesses** (une passe de 1,2 m/s perd moins de 2 % sur son segment), conformément à la loi ; un frottement de roulement sur les passes lentes serait un autre réglage.
- La friction physique réelle (c ≈ 0,013, quatre fois la valeur retenue) rapprocherait l'arrêt de l'objectif ; elle changerait aussi la vitesse d'arrivée des tirs (94-96 % → environ 82 %).
- La barre n'apparaît pas dans l'échantillon de 100 matchs (rare) : couverte par les tests et les balayages de 720 rebonds.
- Le clip de rebond dure jusqu'à 5 s (contre 3 s en B2) : environ +1,5 s en moyenne (une quarantaine d'images de plus) pour les clips `poteau` et `barre` seulement.

### 6.6 Statut

**B1 terminé** ; objectif « arrêt en 3 à 4 s après le premier rebond » atteint en moyenne (3,76 s), pas pour tous les clips (p90 4,38 s, max 4,96 s). Prochaine étape de la séquence : B4 (événements du ballon).


## 7. B4 — Événements du ballon et parades (terminé le 08/10/2026)

Fichiers : `engine/ball_events.py` (nouveau), `engine/narrative_player.py`, `tests/test_ball_events.py` (nouveau), `tests/test_narrative_player.py`. **Intacts** : `ball.py`, `templates.py`, `render/canvas.html`, `tests/test_canvas_html.py`, le moteur sportif, 3c.

### 7.1 Principe

**Une parade est l'issue visuelle d'un non-but ; le score est décidé en amont par le moteur de Poisson et rien dans B4 ne le modifie.** Aucune portée de gardien n'est calculée : un `arret` (issue déjà tirée par la narration) est mis en images comme une parade, un `but` ne produit jamais de parade. Le moteur produit désormais explicitement les événements du ballon ; `canvas.html` garde sa propre détection du but (`goalEvents`) et ignore le nouveau champ, qui est **optionnel** (`metadata.events_ball`, absent quand un clip n'a pas d'événement).

### 7.2 Écarts à la consigne (à connaître)

- **Le choix de l'issue avec biais selon le gardien n'est pas implémenté.** L'issue d'un non-but est tirée dans `engine/narrative.py` (poids 0,40 / 0,25 / 0,15 / 0,10 / 0,10 pour `arret`, `hors_cadre`, `tacle`, `degagement`, `poteau` ; menu des penaltys manqués avec `barre`), et le commentaire texte (`nlg_ingestion`, `nlg_live`) s'appuie sur cette même issue. La retirer dans `narrative_player` ferait afficher une parade pendant que le texte dit « poteau ». Un biais selon le gardien demande de toucher `narrative.py` (et sa distribution testée, côté NLG aussi) : hors périmètre ; le test « deux gardiens de qualité différente » n'est donc pas fait.
- **Menu réellement disponible** : parade (`arret`), à côté (`hors_cadre`), poteau, bloc / dégagement (`tacle`, `degagement`). **« Au-dessus » est absent** (les cibles `hors_cadre` de `templates.py` sont toujours à côté des poteaux) et **`barre` n'est jamais produite par la narration** (0 sur 100 matchs ; seulement 7,5 % des penaltys manqués) : elle n'est couverte que par les tests.
- **Champs** : la consigne donnait `t_minute` ; il vaut la minute du match. J'ai ajouté `t`, l'instant dans le clip (s), indispensable pour dater l'événement ; il est borné à la durée du clip.
- **Référence de la parade** : l'angle `a = 60° · u` utilise `u` = décalage latéral du tir ramené à **0,03** (demi-largeur de la cible `arret` de `templates.py`, y ∈ [0,47 ; 0,53]). Cette référence n'était pas dans les constantes validées ; sans elle l'angle ne dépasserait jamais 34°.
- **`_build_clip_frames`** garde sa signature `(frames, roster)` ; `_build_clip` renvoie en plus les événements.

### 7.3 Événements produits

| Issue visuelle | Événements | Dernier toucheur |
|---|---|---|
| `but` | `but` (franchissement de la ligne entre les poteaux) | attaquant |
| `arret` | `parade`, puis `corner` ou `touche` si le ballon sort | défenseur (gardien) |
| `poteau` / `barre` | `poteau` / `barre`, puis `touche` ou `sortie_but` si le ballon sort (rebond de B2) | attaquant |
| `hors_cadre` | `sortie_but` | attaquant |
| `tacle`, `degagement` | `degagement` (position du ballon en fin de clip, joueur inconnu) | défenseur |

Structure : `{type, t_minute, t, x, y, joueur, direction_deg, last_toucher, event_ref}` (`direction_deg` : cap de sortie, 0° = vers le but attaqué, 90° = vers +y).

**Règles de sortie** (`classify_line_exit`) : entre les poteaux et sous la barre → `but` ; hors des poteaux ou au-dessus de la barre, dernier toucheur défenseur → `corner`, attaquant → `sortie_but` ; ligne de touche → `touche`.

### 7.4 Constantes appliquées (validées par l'architecte)

| Constante | Valeur |
|---|---|
| Angle maximal de la parade (`a_max`) | 60° |
| Garde-fou « jamais un but sur une parade » | 40° (puis, en dernier recours, retour vers le terrain) |
| Restitution de la parade | tirée par hachage de `event_ref` dans [0,5 ; 0,7] (un tir à 30 m/s repart à 15-21 m/s) |
| Aléa de direction (D8) | ±10° sur l'azimut, déterministe |
| Coupe du clip | 1,0 s après le franchissement d'une ligne (plafond de sécurité conservé : 5 s) |

### 7.5 Mesures (graines 1 à 100, 1 586 clips)

| Événement | Total | Par match (moy / min / max) |
|---|---|---|
| `parade` | 515 | 5,15 / 0 / 13 |
| `poteau` | 131 | 1,31 / 0 / 5 |
| `barre` | 0 | — |
| `corner` | 119 | 1,19 / 0 / 4 |
| `sortie_but` | 317 | 3,17 / 0 / 8 |
| `touche` | 104 (50 après une parade, 54 après un poteau) | 1,04 / 0 / 3 |
| `degagement` | 328 (188 tacles + 140 dégagements) | 3,28 / 0 / 11 |
| `but` | 295 | 2,95 / 0 / 11 |

**Issues de non-but** (1 291 clips) : parade 39,9 %, à côté 24,6 %, bloc (tacle) 14,6 %, dégagement 10,8 %, poteau 10,1 %, barre 0 % ; au-dessus : sans objet (voir §7.2). **Après une parade** : le ballon reste en jeu dans 346 cas sur 515 (67 %), sort en corner dans 119 (23 %), par la touche dans 50 (10 %) ; aucune parade ne produit de but (garde-fou vérifié sur 780 tirs de test, dont 300 tirs extrêmes). **Directions de sortie des parades** : les tranches de 30° de −180° à −90° et de 60° à 150° sont toutes bien représentées (52 à 75 parades chacune) ; les caps proches de 0° (ballon renvoyé vers le but) sont rares ou absents (5 et 12 parades dans les deux tranches voisines, 0 dans les deux tranches centrales) ; cap moyen 3°, écart-type 126°.

**Cinq clips avec tir au but** (match 1, sauf mention) :

| Clip | Gabarit | Issue | Événements | Prolongation |
|---|---|---|---|---|
| 2 | `percee_individuelle` | but | `but` (t = 8,80 s, 0°) | — |
| 3 | `recuperation_haute` | arrêt | `parade` (t = 5,44 s, −154°) | 5,0 s |
| 4 | `debordement_centre_tete` | arrêt | `parade` (t = 6,63 s, −128°) | 2,89 s |
| 8 | `une_deux` | poteau | `poteau` (t = 5,39 s, 129°) | 3,04 s |
| 10 | `profondeur_1v1` | hors cadre | `sortie_but` (t = 6,83 s, 0°) | — |

Les clips 1, 5, 7 de ce match sont des tacles : un `degagement` chacun, sans trajectoire.

### 7.6 Déterminisme

**100 matchs sur 100** avec scores, buts, cartons, remplacements, blessures et notes identiques entre HEAD et l'arbre modifié ; les événements du ballon sont **identiques sur deux exécutions** (mêmes graines, `PYTHONHASHSEED=0`). Tout vient d'un hachage sha256 de `event_ref`.

### 7.7 Impact sur le poids et la latence

646 clips sur 1 586 (41 %) sont maintenant prolongés (parades : 515, poteaux : 131), de 3,26 s en moyenne (5,0 s au maximum), soit environ 100 images de plus chacun. C'est un coût de poids et de sérialisation (ticket 4, non corrigé), très inférieur à celui du calcul des clips (les images ajoutées sont des copies de la dernière image avec un ballon différent, sans `interpolate`).

### 7.8 Statut

**B4 terminé.** `canvas.html` n'est pas modifié : une sous-étape ultérieure consommera `metadata.events_ball`. Rappel de B1 : l'objectif « arrêt en 3-4 s après le premier rebond » a été accepté à 3,76-4,96 s (4-5 s est crédible pour Football Manager ; descendre plus bas demanderait de revoir la restitution de B2, refusé).


## 8. B4-bis — Consommation des événements visuels (terminé le 08/10/2026)

Fichiers : `engine/narrative.py` (biais gardien), `render/canvas.html` (consommation de `events_ball`), `tests/test_ball_events.py`, `tests/test_canvas_html.py`, `docs/previews/phase6/b4_bis/` (12 captures). `engine/narrative_player.py` n'est **pas** modifié dans cette étape. **Intacts** : `ball.py`, `templates.py`, le moteur sportif, 3c, le contrat d'injection standalone et le protocole embarqué.

### 8.1 Biais gardien

- **Où.** La consigne demandait `narrative_player.py`. L'issue d'un non-but est tirée dans `engine/narrative.py` et le commentaire texte (`nlg_ingestion`, `nlg_live`) lit la même issue : appliquer le biais ailleurs ferait afficher une parade pendant que le texte dit « poteau ». Le biais est donc dans `narrative.py` (hunk limité : deux fonctions et deux appels), ce qui garde l'animation et le texte cohérents sans toucher au NLG. **Écart de périmètre à valider.**
- **Facteur** (formule d'origine, remplacée par la formule recentrée du §8.7) : `0,5 + note/100` appliqué au poids de l'issue `arret` ; `rng.choices` normalise, les autres issues se répartissent proportionnellement. Note 50 → 1,0 ; 90 → 1,4 ; 20 → 0,7 ; gardien introuvable ou note inconnue (0,0) → 1,0. Le nombre de tirages du générateur ne change pas : minutes, gabarits, équipes et tireurs sont identiques, seule l'issue peut changer. Appliqué aussi au menu des penaltys manqués.
- **Mesure sur 1 000 non-buts** (gardien 90 contre gardien 20) : 49,0 % de parades (252 / 514) contre 29,2 % (142 / 486), soit **+68 %** en relatif (théorie : 48,3 % et 31,8 %). Deux gardiens à 50 : 41,6 % et 38,7 % (théorie : 40 %).
- **Effet réel sur les données** : les gardiens titulaires de Ligue 1 ont une note de 68 à 81 (moyenne 74,7), donc un facteur de 1,18 à 1,31 : **tous sont au-dessus du « rating 50 » neutre**. Conséquence mesurée sur 100 matchs : la part des arrêts passe de **39,9 % à 45,4 %** (+5,5 points), `hors_cadre` 24,6 → 22,3 %, `tacle` 14,6 → 13,1 %, `degagement` 10,8 → 9,9 %, `poteau` 10,1 → 9,3 % ; 147 clips sur 1 586 (9,3 %) changent d'issue visuelle. Entre le meilleur et le moins bon gardien réels (81 contre 68), l'écart de facteur n'est que de 11 %. **Si la distribution globale doit rester inchangée, il faut recentrer le facteur sur la moyenne de la ligue** (par exemple `1 + (note − 74,7) / 100`) ; non fait, car c'est une constante produit.
- **Score** : **100 matchs sur 100** identiques (scores, buts, cartons, remplacements, blessures, notes) entre HEAD et l'arbre modifié ; 295 buts avant et après ; test sur 60 matchs avec trois couples de notes de gardiens (90 / 20, 20 / 90, 50 / 50) : mêmes buts, mêmes minutes, mêmes tireurs.
- **NLG** : les tests du sous-projet (`simulafoot_nlg`, environnement propre) passent (environ 897 tests, couverture 99,77 %) ; aucun test n'a eu besoin d'être adapté. Les 203 tests du projet principal qui lisent la narration et l'ingestion NLG passent aussi.

### 8.2 Consommation des événements dans `canvas.html`

`metadata.events_ball` est lu comme **champ optionnel** (absent : rien n'est dessiné). Les types retenus sont `parade`, `poteau`, `barre`, `corner`, `sortie_but` ; `but`, `touche` et `degagement` sont ignorés (le but reste détecté par `goalEvents`, **inchangé**). Chaque effet dure 0,5 s (`NET_ANIM_S`) et l'étiquette 1,0 s (`GOAL_FLASH_S`), couleur or du joueur actif ; aucune autre constante produit n'a été ajoutée :

| Événement | Rendu |
|---|---|
| `parade` | anneau or autour du ballon qui s'élargit, flèche dans le cap de sortie (`direction_deg`), étiquette « Parade » |
| `poteau` | disque blanc et anneau or sur le point de contact (discret, sans texte) |
| `barre` | éclair blanc sur la ligne de but, sur la largeur du but (discret, sans texte) |
| `corner` | éclair or sur la ligne de but au point de sortie, anneau blanc sur le poteau de corner, étiquette « Corner » |
| `sortie_but` | éclair or sur la ligne de but au point de sortie, étiquette « Sortie de but » |

`playEnd` garde le maintien du but (`GOAL_HOLD_S`) et ajoute, en `max`, la fin de l'effet d'un événement de fin de clip : les clips `hors_cadre` (l'événement est daté à la toute fin) durent 0,5 s de plus pour que « Sortie de but » soit visible avant la carte de titre.

### 8.3 Captures (`docs/previews/phase6/b4_bis/`, canvas 1200 × 780, match de la graine 3, même instant avant / après)

| Cas | Avant | Après | Description factuelle de l'écart |
|---|---|---|---|
| Parade, clip 0 (t = 6,98 s) | `avant_clip0_parade_6s98.png` | `apres_clip0_parade_6s98.png` | anneau or autour du ballon au but de droite, flèche vers le bas (cap −99°), étiquette « Parade » |
| Parade, clip 1 (t = 6,71 s) | `avant_clip1_parade_6s71.png` | `apres_clip1_parade_6s71.png` | idem, cap +87° (vers le haut) |
| Corner, clip 1 (t = 7,73 s) | `avant_clip1_corner_7s73.png` | `apres_clip1_corner_7s73.png` | éclair or sur la ligne de but (y = 0,71), anneau blanc sur le poteau de corner supérieur droit, étiquette « Corner » ; le ballon est déjà hors du terrain dans les deux images |
| Poteau, clip 2 (t = 7,00 s) | `avant_clip2_poteau_7s00.png` | `apres_clip2_poteau_7s00.png` | disque blanc et anneau or sur le poteau inférieur du but de droite |
| Sortie de but, clip 3 (t = 8,09 s) | `avant_clip3_sortie_but_8s09.png` | `apres_clip3_sortie_but_8s09.png` | éclair or sur la ligne de but, étiquette « Sortie de but » |
| But, clip 4 (t = 15,55 s) (contrôle) | `avant_clip4_but_15s55.png` | `apres_clip4_but_15s55.png` | **images identiques octet pour octet** : le but n'est pas touché |

Méthode : un serveur local jetable (hors dépôt) sert l'ancien et le nouveau `canvas.html` avec le même payload, lecture figée à l'instant voulu ; le canvas est enregistré depuis le navigateur intégré. Un premier lot a produit cinq images identiques de 21 374 octets (onglet en arrière-plan, canevas non redessiné) : ces fichiers ont été refaits après avoir forcé le rendu, et les tailles ont été contrôlées.

### 8.4 Déterminisme

Scores, buts, cartons, remplacements : **100 / 100** identiques (§8.1). Issues visuelles et événements du ballon : **identiques sur deux exécutions** (mêmes graines, `PYTHONHASHSEED=0`).

### 8.5 Limites

- Le biais décale la distribution globale (§8.1) ; recentrage à décider.
- Les 12 captures sont celles d'un seul match ; l'animation en mouvement (effet qui s'éteint en 0,5 s) n'est vérifiée que par ses instants figés et par les tests statiques.
- `touche` et `degagement` ne sont pas dessinés (voir ticket 20).

### 8.6 Statut

**B4-bis terminé.** Tickets ouverts à cette occasion : 18, 19 et 20 (`docs/known_issues.md`).

### 8.7 B4-bis — Formule de biais gardien (recentrée) (08/10/2026)

Fichiers : `engine/narrative.py` (formule), `tests/test_ball_events.py` (tests). `render/canvas.html`, `ball.py`, `templates.py`, `narrative_player.py`, le moteur sportif, Poisson et 3c sont **intacts**.

- **Ancienne formule** (§8.1) : `0,5 + note/100`. Les gardiens titulaires réels (notes 68 à 81, moyenne 74,7) étaient tous au-dessus du neutre 50 : la part des arrêts passait de **39,9 % à 45,4 %** (+5,5 points) et 147 clips sur 1 586 changeaient d'issue visuelle.
- **Nouvelle formule** : `1 + (note − 74,7)/100`, appliquée au poids de l'issue `arret` (les autres issues se renormalisent). Justification : recentrée sur la moyenne des gardiens titulaires (74,7), elle préserve la distribution globale tout en différenciant les gardiens extrêmes. **Décision propriétaire B4-bis.** Constante : `_KEEPER_RATING_MEAN = 74.7`. Gardien introuvable ou note inconnue : 1,0.
- **Facteurs** : note 74,7 → 1,000 ; 90 → 1,153 ; 20 → 0,453 ; titulaires réels (68 à 81) → 0,933 à 1,063.

**Part de parades sur des non-buts** (valeur attendue : `0,40·f / (0,40·f + 0,60)`) :

| Gardien | Facteur | 1 000 non-buts | 8 000 non-buts | Théorie |
|---|---|---|---|---|
| 74,7 | 1,000 | 387 (38,7 %) | 3 181 (39,8 %) | 40,0 % |
| 90 | 1,153 | 419 (41,9 %) | 3 447 (43,1 %) | 43,5 % |
| 20 | 0,453 | 205 (20,5 %) | 1 873 (23,4 %) | 23,2 % |

**Écart avec les ordres de grandeur annoncés** : la consigne attendait « environ 45-46 % » (note 90) et « environ 18-20 % » (note 20). La formule validée donne mathématiquement 43,5 % et 23,2 % : seul le poids de l'arrêt (0,40) est multiplié, puis renormalisé, ce qui amortit l'effet. La formule a été appliquée telle quelle ; atteindre 45-46 % et 18-20 % demanderait un facteur plus ample (environ 1,25 et 0,35), à décider par l'architecte.

**Distribution globale (100 matchs, graines 1 à 100, 1 291 non-buts)** :

| Issue | Avant B4-bis | B4-bis (0,5 + note/100) | Recentrée |
|---|---|---|---|
| arrêt | 515 (39,9 %) | 586 (45,4 %) | **512 (39,7 %)** |
| hors cadre | 317 (24,6 %) | 288 (22,3 %) | 321 (24,9 %) |
| tacle | 188 (14,6 %) | 169 (13,1 %) | 187 (14,5 %) |
| dégagement | 140 (10,8 %) | 128 (9,9 %) | 140 (10,8 %) |
| poteau | 131 (10,1 %) | 120 (9,3 %) | 131 (10,1 %) |

La distribution globale est préservée (39,7 % contre 39,9 % : −3 arrêts sur 1 291). **Clips dont l'issue change par rapport à avant B4-bis : 14 sur 1 586** (147 avec l'ancienne formule). Aucun n'est dû à un gardien exceptionnel (note < 60 ou > 85) : il n'y en a pas dans les données (68 à 81). Les 14 changements viennent de l'écart résiduel de la note à 74,7 (facteur 0,93 à 1,06, notes 69 à 77 pour ces clips) ; un facteur continu ne peut pas laisser **tous** les clips inchangés tant que la note diffère de 74,7. Sens : 5 arrêts devenus autre chose, 2 l'inverse, 7 autre issue vers autre issue.

- **Score** : 100 matchs sur 100 identiques (scores, buts, cartons, remplacements, blessures, notes) entre avant B4-bis, B4-bis et l'arbre recentré ; 295 buts dans les trois cas ; mêmes minutes, équipes, gabarits et types d'événement.
- **Cohérence texte / animation** (100 matchs) : 1 586 clips vérifiés, 0 incohérence — arrêt ⇒ premier événement `parade` ; poteau ⇒ `poteau` sans parade ni barre ; barre ⇒ `barre` ; but ⇒ `but` ; toute autre issue ⇒ aucun événement parade / poteau / barre. L'ingestion NLG (`timeline_to_events`) restitue la même issue que le `NarrativeEvent` pour 1 287 occasions, 0 écart.
- **Statut** : formule validée par décision propriétaire.
