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

## 9. B3 — Rotation visible : diagnostic (08/10/2026)

**Diagnostic seul : aucune ligne de code modifiée** (`canvas.html`, `ball.py`, `templates.py`, `narrative.py`, `narrative_player.py`, moteur sportif, Poisson et 3c intacts). Les mesures viennent de scripts jetables hors dépôt (`PYTHONHASHSEED=0`, graines 1 à 100) et d'une planche d'essai de rendu hors dépôt (mêmes constantes de ballon que `canvas.html`).

### 9.1 Rotation actuelle : un champ `spin` posé par les gabarits, lu uniquement pour la courbure

- **Précision sur le périmètre de `ball.py`.** `ball.py` **ne calcule pas** `spin` : il le **consomme**. La valeur est posée par `templates.py` (`build_decalage_enroulee`, constante `_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S = 50.0`) sur les keyframes dont le tag est `shot` ou `ball_flight`. `ball.py` ne l'utilise que dans `_behavior_shot` (et `_behavior_ball_flight`, qui appelle `_behavior_shot`) pour la courbure de Magnus.
- **Formule.** `a_lat = _MAGNUS_K · spin · v_base` (`_MAGNUS_K = 0,003`, sans unité, `v_base = distance / durée`), `crête = ½ · a_lat · (durée/2)²`, décalage perpendiculaire en `crête · 4s(1−s)`, nul aux extrémités. **Dépendance** : linéaire en `spin` et en `v_base` (quadratique en durée) ; **aucune courbure sous 11 m** (`_SHOT_STRAIGHT_MAX_DIST_M`) ; pas de dépendance à l'angle de frappe. Le signe de la courbure suit le signe de `spin`.
- **Type de frappe.** Un seul gabarit a un spin non nul : `decalage_enroulee`. Tous les autres (passes au sol, centres, déviations, penalty, coup franc…) ont `spin = 0,0` : les segments `pass_ground`, `cross`, `deflect`, `bounce` et les segments sans tag renvoient toujours `spin = 0,0` (`ball.py`).
- **Mesure sur les séquences moteur** (6 séquences par gabarit, échantillonnage à 0,05 s) :

| Gabarit | Échantillons | `spin` ≠ 0 | Valeurs |
|---|---|---|---|
| `decalage_enroulee` | 835 | 541 (64,8 %) | 0 ou **+50 rad/s** (jamais négatif) |
| 11 autres gabarits (but_gag, construction_placee, contre_attaque, corner, coup_franc, debordement_centre_tete, penalty, percee_individuelle, profondeur_1v1, recuperation_haute, une_deux) | 0 non nul sur 9 657 | 0 % | 0,0 |

`decalage_enroulee` représente **163 événements sur 1 586** (10,3 %) sur les 100 matchs de référence.
- **Plage.** 50 rad/s ≈ **8 tours/s**, constante, posée en marche d'escalier (0 → 50 → 0, sans montée ni descente) ; jamais lente, jamais variable. À 30 images/s (`_FPS = 30`), cela fait **95,5° par image du payload** ; à 60 Hz d'affichage, 47,7°.
- **Courbure effective** (écart maximal à la corde, par segment, 6 séquences `decalage_enroulee` contre 6 séquences de gabarits sans spin) :

| Segment | `decalage_enroulee` (spin 50) | Gabarits sans spin |
|---|---|---|
| `shot` (conduite, 3,6 s, 10 à 52 m, 3 à 15 m/s) | 0,00 à **3,46 m** (0 m à 10,6 m ; 0,89 m à 13,5 m ; 2,3 à 3,5 m de 34 à 52 m) | **0,00 m** (profondeur_1v1, penalty, coup_franc) |
| `ball_flight` (0,9 à 2,1 s, 16 à 31 m/s) | **0,36 à 1,32 m** (4 à 14 px) | **0,00 m** |

Sur ces séquences, la courbure sépare donc **sans ambiguïté** une frappe enroulée (> 0) d'une frappe tendue (= 0) ; l'écart vient pour l'essentiel de la **conduite** (`shot`, lente), pas du vol rapide (déjà signalé §1.2 et la note « Hors liste » de la synthèse).
- **Clip témoin** (graine 2, `decalage_enroulee`, issue `poteau`) : 304 images, `spin` ≠ 0 sur **142 images** (t = 2,40 à 7,10 s), écart à la corde 1,08 m (11,8 px) sur 31,7 m. Pour comparaison, les clips sans spin ont des écarts de 1,6 à 6,8 m **à la corde sur une fenêtre de 3 s** (conduite, passes) : la courbure du ballon seule n'est donc pas lisible dans le flux de jeu, ce que l'architecte a constaté.

| Clip témoin (graine 2) | Issue | `spin` ≠ 0 | Écart à la corde (fenêtre) | Vitesse moyenne |
|---|---|---|---|---|
| frappe enroulée (`decalage_enroulee`) | poteau | 142 / 304 | 1,08 m (2,40–7,10 s) | 6,8 m/s |
| frappe tendue (`profondeur_1v1`) | but | 0 / 196 | 4,80 m (3,0 s) : conduite, pas frappe | 11,4 m/s |
| passe au sol (`construction_placee`) | but | 0 / 448 | 4,91 m (3,0 s) | 14,1 m/s |
| centre (`debordement_centre_tete`) | poteau | 0 / 281 | 1,62 m (3,0 s) | 12,6 m/s |
| déviation (`percee_individuelle` ; segments `deflect` dans `corner` et `recuperation_haute`) | tacle | 0 / 211 | 0,00 m | 6,2 m/s |

- **Transmission dans le payload.** Oui : `frames[i].ball.spin`, un **flottant scalaire** (rad/s, signé), arrondi à 4 décimales (`_round_frame_payload`), valeurs observées 0,0 et 50,0. Image de balle complète : `{"owner": "1523", "spin": 0.0, "x": 0.18, "y": 0.32, "z": 0.0}` (62 octets). **Ni axe, ni angle intégré, ni vitesse angulaire vectorielle.** Pas de rampe : la valeur change d'un coup à la frontière des segments.
- **Conséquence sur le rendu.** L'angle de rotation n'existe nulle part ; il faudrait l'intégrer côté lecteur (`angle(t) = ∫ spin dt`), sans changer le payload. Une rotation du ballon vue de dessus autour de l'axe vertical correspond bien à l'effet latéral (Magnus) : un motif dessiné sur le disque tourne dans le plan de l'écran, ce qui est physiquement cohérent ; un roulement (axe horizontal) n'est pas modélisé.

### 9.2 Rendu actuel du ballon dans `canvas.html`

- **Dessin** (`drawFrame`) : disque blanc `#ffffff` de **6 px écran** de diamètre (`BALL_DIAMETER_SCREEN_PX = 6`, rayon 3 px × `pxPerScreenPx`), contour noir `rgba(0, 0, 0, 0.85)` de 0,8 px, surface intérieure ≈ 21 px² ; **ombre** ellipse `rgba(0, 0, 0, 0.28)` décalée de 0,6 r, de rayons r × 0,8 r ; **hauteur** : le disque est relevé de `min(z, 4)·SCALE·0,5` px et son rayon grossit de `min(0,5, z·0,15)` (jusqu'à +50 %) ; position interpolée linéairement entre deux images (`lerp`). Échelle du terrain : 10,88 px par mètre (canvas 1200 × 780).
- **Marqueur sur le ballon** : aucun (pas de point, de ligne, de motif). **Traînée** : aucune. **Rotation visible** : non ; `canvas.html` contient **0 occurrence** de `spin`.
- **Contraintes qui pèsent sur toute option** : l'or `#ffd700` est déjà utilisé par le contour du joueur actif et par les effets B4-bis (parade, corner, sortie de but) ; le ballon est dessiné après les joueurs et avant `drawBallEvents` ; ordre de dessin et constantes sont protégés par des tests statiques (`tests/test_canvas_html.py`).
- **Captures existantes** (`docs/previews/phase5/sous_etape_2/zoom_ballon_en_vol_avant_apres.png`) : le ballon de 6 px est un disque blanc net avec son ombre ; à cette taille, un motif interne de plus de 1 à 2 px prend une part sensible de la surface (21 px²).

### 9.3 Options évaluées à 6 px

Planche d'essai jetable (hors dépôt) : le ballon de 6 px est rendu avec chaque option, 6 images successives à 60 Hz (47,7° par image) sur la pelouse, à taille réelle et agrandi (pixels nets). **Limite** : seules des images fixes ont été examinées ; la perception en mouvement n'a pas été testée.

| Option | Faisabilité | Perceptibilité | Risque | Complexité | `canvas.html` | Observation sur la planche |
|---|---|---|---|---|---|---|
| **A.** 1 point noir (Ø 1,2 px) | Oui | **Faible à moyenne** | Le ballon paraît « sale » ; à 8 tours/s le point saute de 48° par image : lu comme un scintillement, **le sens de rotation n'est pas lisible**. Distingue « tourne / ne tourne pas » seulement par la présence d'une marque qui bouge | Faible | Oui | Une tache sombre de 1 à 2 px changeant de place ; sans sens |
| **B.** 3 points noirs à 120° | Oui | **Faible** | Les trois points forment un damier de 6 px qui **se lit comme une texture**. À 30 images/s (95,5° par image) la période de 120° provoque un repliement (la rotation semble **reculer** de 24,5° par image) ; à 60 Hz (47,7°) il reste lisible mais sans direction | Faible à moyenne | Oui | Texture grise, plus lourde qu'en A |
| **C.** Arc de rotation (queue de 70° au bord, 1,2 px) | Oui | **Moyenne à forte** (présence nette ; sens porté par la queue de l'arc, à confirmer en mouvement) | Collision de couleur si l'arc est or (déjà utilisé) ; nuit à la lisibilité des étiquettes B4-bis si trop long | Moyenne | Oui | Arc jaune bien visible autour du disque ; il se déplace de 48° par image ; le ballon blanc reste intact |
| **D.** Ballon à 8 px + point | Oui | **Moyenne** | **Lève une décision Phase 5** (6 px) ; le disque passe de 28 à 50 px² (+ 78 %) ; ne règle pas la lecture du sens ; modifie les captures de référence de la Phase 5 | Faible | Oui | Le point est un peu plus net, le ballon paraît plus massif |
| **E.** Flèche courbe externe fixe | Oui | **Forte** pour le sens, **sans rotation réelle** | Indicateur d'interface plus que rotation ; ≈ 15 px de large autour d'un ballon de 6 px, surcharge si les deux équipes enchaînent des frappes enroulées ; ne se distingue pas des flèches de B4-bis (parade) | Moyenne | Oui | Très lisible, mais statique et plus grosse que le ballon |
| **F.** A + C | Oui | **Moyenne à forte** | Cumule les risques de A (tache) et de C ; deux éléments pour une information | Moyenne à forte | Oui | Plus chargé que C seul, sans gain de sens |

- **Coût en pixels** (aire de la marque, ballon de 6 px) : A ≈ 1,1 px² (5 % de la surface) ; B ≈ 3 px² ; C ≈ 1,2 px de large sur un arc d'environ 5,5 px de long, **hors du disque** (surface blanche intacte) ; D +22 px² sur le ballon ; E ≈ 20 px² ; F ≈ A + C.
- **Impact sur les captures de référence.** Toute option modifie le rendu du ballon uniquement **pendant les clips `decalage_enroulee` avec `spin ≠ 0`** (10,3 % des clips) ; les captures de B4-bis dont le gabarit n'a pas de spin (parade `profondeur_1v1`, corner `debordement_centre_tete`, sortie de but `coup_franc`, but `construction_placee`) resteraient identiques avec C ou E ; **la capture « poteau » de B4-bis est un `decalage_enroulee` en plein spin (t = 7,00 s, spin ≠ 0 de 2,40 à 7,10 s) : elle changerait**, comme tout clip `decalage_enroulee` des captures de la Phase 5 (gabarits non relus dans cette étape : à vérifier) ; A, B, D et F changeraient aussi le ballon des captures sans spin si le marqueur est dessiné en permanence (A, B, D) : à éviter, un marqueur ne devrait apparaître que pour `spin ≠ 0`.
- **Traînée de trajectoire** (variante de C, hors liste) : testée à 8 points (≈ 27 px, 0,12 s à 20 m/s). **Inefficace** : la flèche de courbure d'une parabole de 1 m sur 560 px n'est que de **0,03 px** sur 27 px et de **0,4 px** sur 110 px (0,5 s). Seul un **tracé long** (≥ 2 à 3 s, la conduite entière) rendrait la courbure visible, au prix d'un trait persistant sur le terrain ; non recommandé en première intention.

### 9.4 Points durs révélés par le diagnostic

1. **Le spin s'applique aussi à la conduite.** `decalage_enroulee` porte `spin = 50` sur son segment `shot` (conduite lente de 3,6 s, 3 à 15 m/s) **avant** la frappe. Un rendu fondé sur `spin ≠ 0` ferait **tourner le ballon pendant la conduite**, et donc avant le tir. C'est le défaut déjà noté §1.2 et la note « Hors liste » de la synthèse : la courbure est portée par la conduite plutôt que par la frappe. Deux manières de le traiter (à décider) : (a) côté rendu, n'afficher la rotation que lorsque le ballon est en vol (par exemple `z > 0` ou vitesse supérieure à un seuil), **avec une constante produit à fixer**, car les vitesses de conduite (jusqu'à 14,6 m/s) et de vol (16 à 31 m/s) se chevauchent peu mais se touchent ; (b) côté moteur, ne poser `spin` que sur `ball_flight` (modification de `templates.py`), ce qui **supprimerait aussi la courbure de la conduite** (jusqu'à 3,5 m, soit 38 px) et ramènerait la courbure visible à 0,4 à 1,3 m (4 à 14 px).
2. **Crénelage temporel.** À 50 rad/s et 30 images/s, un motif à symétrie multiple (B) apparaît tournant à l'envers. Tout motif doit être orienté par `angle = spin · (t − t0)` calculé **à partir de la tête de lecture** (60 Hz), jamais par image du payload, et se limiter à une marque unique (A ou C).
3. **Sens de rotation.** Le signe de `spin` est constant (+) dans les données actuelles : un sens « gauche / droite » n'est pas distingué selon le côté de l'attaque. Le sens affiché sera donc toujours le même ; le lien avec le côté de la courbure est à vérifier avant d'afficher un sens.
4. **Déterminisme.** Tout angle calculé à partir de `spin` et de la tête de lecture est une fonction pure du payload : même graine, même payload, même rendu. Aucun aléa à ajouter, aucune modification du payload nécessaire (le champ `ball.spin` existe déjà).

### 9.5 Recommandation

- **Option recommandée : C (arc de rotation), sans agrandir le ballon, avec rotation limitée aux phases de vol.** Elle est la seule à (1) rendre visible la différence entre une frappe enroulée (arc présent) et une frappe tendue (rien), (2) laisser le disque blanc de 6 px intact (l'arc est à l'extérieur), (3) ne rien changer au payload, (4) rester déterministe, (5) ne rien dessiner pour les 89,7 % de clips sans spin.
- **Ce qu'elle ne garantit pas** : la lecture du **sens** de rotation (non vérifiée en mouvement) ; l'arc peut être pris pour un effet de B4-bis s'il reste or. Il faut un choix de couleur distinct.
- **Pourquoi pas les autres.** A et B : à 6 px, une marque noire se lit comme une tache ou une texture, avec un risque de repliement temporel pour B ; D : lève la décision Phase 5 sans résoudre la lecture du sens ; E : lisible mais ne montre pas une rotation et ajoute un pictogramme volumineux ; F : charge sans gain.
- **Aucune option ne rend la rotation « réelle » lisible à 6 px.** La rotation d'un disque blanc de 6 px à 8 tours/s est, en pratique, **invisible** sans marque ; ce que l'on peut obtenir est un **indicateur de rotation** (arc), pas la rotation du ballon. Si l'architecte exige la rotation d'un motif sur le ballon lui-même, **l'agrandissement (D) est le seul moyen d'y parvenir, et il lève la décision Phase 5** (décision à lui).

### 9.6 Décisions attendues de l'architecte

1. **Cible** : accepter un **indicateur de rotation** (option C) à la place de la rotation d'un motif sur le ballon, ou lever la décision Phase 5 (ballon de 8 px, option D).
2. **Phase d'affichage** : afficher l'arc seulement en vol (règle de rendu à seuil, constante à fixer) ou corriger le moteur pour que `spin` ne soit posé que sur `ball_flight` (`templates.py`, courbure de la conduite supprimée) — voir §9.4 point 1.
3. **Couleur de l'arc** (différente de l'or `#ffd700` du joueur actif et de B4-bis) et **longueur / épaisseur** (propositions : 70°, 1,2 px, rayon + 1,6 px ; à valider avant toute modification).
4. **Périmètre** : levée du gel de `canvas.html` pour B3 (une fonction de dessin après `drawBallEvents`, tests statiques, captures avant / après), sans toucher au payload.

### 9.7 Statut

**B3 : diagnostic terminé, implémentation en attente des décisions du §9.6.** Rien n'a été modifié dans le code.

## 10. B3 — Rotation visible : implémentation (08/10/2026)

Fichiers : `render/canvas.html` (traînée), `tests/test_canvas_html.py` (5 tests), `docs/previews/phase6/b3/` (24 captures avant / après et une comparaison de longueurs), `docs/known_issues.md` (ticket 21). **Intacts** : `templates.py`, `ball.py`, `narrative.py`, `narrative_player.py`, le payload, le moteur sportif, Poisson et 3c.

### 10.1 Décisions de l'architecte appliquées

- **Option C** : traînée suivant les positions réelles du ballon, sans les modifier.
- **Activation** : `|spin| > 5 rad/s` (`BALL_TRAIL_MIN_SPIN_RAD_S`). Mesure : le spin ne prend que les valeurs 0 et 50 (373 456 images, 0 image entre 0 et 5 rad/s) ; le seuil de 5 ne coupe donc aucun cas réel.
- **Longueur** : `BALL_TRAIL_POINTS = 12` positions, une par image du payload (`fps_target`, 30), soit (12 − 1) / 30 = **0,37 s**.
- **Style** : blanc cassé `rgba(245, 241, 230)`, opacité 0,6 à la tête et 0 à la queue, épaisseur 2 px à la tête et 0,4 px à la queue (px écran), extrémités arrondies.
- **Ballon** : maintenu à **6 px** (`BALL_DIAMETER_SCREEN_PX = 6`, décision Phase 5 inchangée).

### 10.2 Implémentation

- `drawBallTrail(clipData, t)`, appelée dans `drawFrame` après les joueurs et **avant** le ballon et ses effets (B4-bis).
- **Calcul sans état** à partir de l'instant `t` : les 12 positions sont lues dans le payload à `t − k/30` (`findSegment`, interpolation linéaire comme le ballon), avec le même relevage que le ballon en hauteur. Pas de tampon circulaire : un tampon survivrait mal à une pause, un saut ou un rejeu, et le rendu ne serait plus une fonction de l'instant. L'effet est celui d'un tampon de 12 positions, sans état à invalider.
- La traînée s'arrête à la première position **sans spin** (le début d'un spin n'est pas prolongé en arrière) ; aucune traînée si moins de 2 positions ou si la longueur totale est inférieure à 2 px écran (ballon immobile).
- Aucune lecture hors du payload, aucun hasard, aucune horloge ; le contrat standalone (`/*__SEQUENCE_JSON__*/null`), le protocole embarqué et l'interdiction d'accès réseau sont inchangés.

### 10.3 Longueur retenue (12) : justification visuelle

`docs/previews/phase6/b3/comparaison_longueurs_N10_N12_N15.png` : même instant, 10 / 12 / 15 positions, agrandi ×3. À 10 positions le tracé est net mais court ; à 15 positions il remonte jusqu'à la conduite avant le tir et fait apparaître un **coude** (changement de direction, pas de la courbure) sur le clip 3 ; 12 positions donne un tracé net, sans coude, de 4 à 12 m selon la vitesse. La queue est très fine dans les trois cas (0,4 px).

### 10.4 Résultats

- **Clips avec traînée** : **163 sur 1 586 (10,3 %)**, tous `decalage_enroulee` (la consigne annonçait ~9,7 %). Images à spin non nul : 21 546 sur 373 456 (5,8 %).
- **Captures** (`docs/previews/phase6/b3/`, canvas 1 200 × 780, graines 1 à 5, instants figés, avant = HEAD, après = arbre modifié) :

| Clip | Gabarit | Instant | Phase | Pixels modifiés | Longueur de la traînée |
|---|---|---|---|---|---|
| 0 | `decalage_enroulee` (poteau) | 6,40 s | vol | 172 | 7,2 m (79 px) |
| 1 | `decalage_enroulee` (poteau) | 6,37 s | vol | 260 | 10,0 m (109 px) |
| 2 | `decalage_enroulee` (dégagement) | 2,83 s | conduite | 120 | 4,9 m (54 px) |
| 3 | `decalage_enroulee` (hors cadre) | 6,37 s | vol | 315 | 11,8 m (128 px) |
| 4 | `decalage_enroulee` (dégagement) | 2,73 s | conduite | 67 | 4,0 m (43 px) |
| 0 | `decalage_enroulee` | 3,90 s | conduite lente (3 m/s) | 18 | 1,1 m (12 px) |
| 3 | `decalage_enroulee` | 3,90 s | conduite | 137 | 5,6 m (61 px) |
| 5 à 9 | `une_deux` (5 clips) | vitesse maximale | vol | **0** (images identiques octet pour octet) | aucune |

  Noms : `avant_clip<i>_<gabarit>_<phase>_<instant>.png` / `apres_...`.
- **Suit la courbure réelle ?** Les points de la traînée sont les positions du payload (vérifié par test). Mais la traînée de 0,37 s est **presque rectiligne** : flèche de courbure de 0,06 à 0,82 px sur les clips de vol, 2,47 px au plus (clip 4, conduite). Elle signale qu'**une frappe est enroulée** (présence), elle ne rend **pas la courbure lisible** (cf. §9.3 : il faudrait un tracé de 2 à 3 s).
- **Phase d'affichage.** La règle est `|spin| > seuil` : la traînée apparaît donc aussi pendant la **conduite** du gabarit (82,5 % des images à spin non nul, 17,5 % en vol), avant la frappe. Le point 2 du §9.6 (afficher en vol seulement, ou corriger `templates.py`) n'est pas tranché par la consigne ; il est reporté au ticket 21 / B5.

### 10.5 Déterminisme

- **Moteur** : 100 matchs sur 100 (graines 1 à 100) identiques entre HEAD et l'arbre modifié (scores, buts, cartons, remplacements, blessures, notes : 295 buts ; événements narratifs identiques), puisqu'aucun fichier Python n'est modifié.
- **Pixels** : trois rendus indépendants du même instant (clip 3, 6,367 s ; deux rechargements de page) donnent la **même empreinte SHA-256** ; test comportemental : deux appels de `drawBallTrail` produisent exactement les mêmes tracés.

### 10.6 Tests (`tests/test_canvas_html.py`)

Cinq tests : seuil strict (|spin| > 5, sens indifférent), longueur 10 à 15 positions avec épaisseur et opacité décroissantes, positions identiques à celles du payload sur une trajectoire non rectiligne et déterminisme, aucune traînée pour un ballon qui roule sans spin, au repos ou lent, et ordre de dessin / ballon à 6 px / contrat standalone. Les tests comportementaux exécutent les fonctions extraites de `canvas.html` sous Node avec un contexte 2D factice (ignorés si Node est absent).

### 10.7 Limites et suites

- Seuls **10,3 % des clips** montrent une traînée (spin binaire, ticket 21) : B5 élargira.
- Perception en mouvement non testée (captures figées) ; la lecture du sens de rotation n'est pas visée par cette option.
- Ticket 21 ouvert (`docs/known_issues.md`).

### 10.8 Statut

**B3 terminé** (traînée de rotation, ballon à 6 px, payload inchangé).

## 11. B5 — Variétés de frappe : diagnostic (08/10/2026)

**Diagnostic seul : aucune ligne de code modifiée** (`canvas.html`, `templates.py`, `ball.py`, `narrative.py`, `narrative_player.py`, moteur sportif, Poisson et 3c intacts). Mesures par scripts jetables hors dépôt (`PYTHONHASHSEED=0`, graines 1 à 100, 1 586 clips, séquences construites par `templates.BUILDERS`). Les nombres de la typologie (§11.3 à §11.5) sont des **estimations** à partir de ces mesures, pas des constantes validées.

### 11.0 Corrections factuelles aux hypothèses de la consigne

| Hypothèse | Mesure |
|---|---|
| spin 50 pour `decalage_enroulee` **et** `debordement_centre_tete` | **Faux** : `debordement_centre_tete` a un spin de 0 sur ses 248 clips. Seul `decalage_enroulee` (163 clips) porte 50 rad/s |
| 163 clips à spin 50 et 657 à spin 0 | 163 à spin 50 et **1 423** à spin 0 (1 586 clips) |
| `shot` = frappe | `shot` est la **conduite** finale du ballon (2,4 à 5,6 s, 2,7 à 22 m/s en moyenne) ; la frappe réelle est le segment `ball_flight` (§11.1) |
| tendue = spin 5 à 10 | Incompatible avec le seuil de la traînée B3 (valeur absolue du spin > 5) : une frappe tendue à 6-10 rad/s afficherait la traînée (§11.6) |
| HEAD `b71592` | HEAD de départ : `f0f6383` (B3), précédé de `b715092` (diagnostic B3) |

### 11.1 Audit des types de frappe actuels (Tâche 1)

Chaque gabarit a un segment `shot` (conduite) suivi, pour 1 259 clips sur 1 586 (79,4 %), d'un segment `ball_flight` (la frappe) ; les issues `tacle` et `degagement` (327 clips) n'ont pas de vol. Fréquences sur 100 matchs ; distances, durées et vitesses : moyenne [minimum ; maximum].

| Gabarit | Frappe implicite (étiquette narrative finale) | Spin | Clips (par match) | Segment `shot` : distance, durée, vitesse | Vol `ball_flight` : nombre, distance, vitesse |
|---|---|---|---|---|---|
| `contre_attaque` | tir du pied (`tir`) après récupération et passe | 0 | 223 (2,23) | 53,1 m [13,7 ; 77,9], 4,8 s, 11,1 m/s | 166, 27,8 m, 24,7 m/s |
| `construction_placee` | tir du pied (`tir`) après circulation | 0 | 176 (1,76) | 53,0 m [20,4 ; 75,0], 5,6 s, 9,5 m/s | 142, 26,7 m, 25,7 m/s |
| `debordement_centre_tete` | **tête** (`tete`) après centre | 0 | 248 (2,48) | 27,1 m [0,3 ; 41,6], 2,4 s, 11,3 m/s | 205, 23,7 m, 24,8 m/s |
| `percee_individuelle` | tir après dribbles (`tir`) | 0 | 182 (1,82) | 15,2 m [1,4 ; 23,9], 1,8 s, 8,7 m/s | 137, 27,9 m, 24,9 m/s |
| `une_deux` | tir après remise (`tir`) | 0 | 107 (1,07) | 44,7 m [13,9 ; 82,7], 2,0 s, 22,3 m/s | 92, 17,1 m, 24,1 m/s |
| `coup_franc` | frappe de coup franc (`frappe`) | 0 | 46 (0,46) | 4,0 m [1,1 ; 6,1], 1,5 s, 2,7 m/s | 35, 44,3 m [30,1 ; 62,2], 23,8 m/s |
| `corner` | centre (`cross`) puis tête déviée (`deflect`, `tete`) ; pas de segment `shot` | 0 | 89 (0,89) | — | 70, 26,4 m, 24,2 m/s |
| `profondeur_1v1` | 1 contre 1 conclu au tir (`1v1`) | 0 | 118 (1,18) | 43,7 m [10,5 ; 59,8], 4,2 s, 10,4 m/s | 95, 18,3 m, 25,6 m/s |
| `recuperation_haute` | récupération haute, déviation (`deflect`) puis tir | 0 | 166 (1,66) | 40,2 m [8,9 ; 54,2], 2,2 s, 17,9 m/s | 134, 19,3 m, 24,6 m/s |
| `decalage_enroulee` | **frappe enroulée** (`enroulee`) après contrôle | **50** (conduite et vol) | 163 (1,63) | 37,7 m [9,3 ; 59,5], 3,6 s, 10,5 m/s | 122, 25,4 m, 25,5 m/s |
| `penalty` | tir de penalty (`tir`) | 0 | 34 (0,34) | 2,6 m [0,3 ; 3,8], 0,6 s, 4,4 m/s | 34, 21,8 m, 25,0 m/s |
| `but_gag` | déviation finale (`but`) | 0 | 34 (0,34) | 52,1 m [21,5 ; 67,8], 1,8 s, 29,8 m/s | 27, 16,3 m, 24,0 m/s |

Constats :
1. **Un seul type de frappe a un spin** (`decalage_enroulee`), et ce spin est posé sur la **conduite** (82,5 % des images à spin non nul) autant que sur le vol : la courbure de Magnus déplace donc le ballon hors des pieds de son porteur pendant la conduite (jusqu'à 3,46 m), défaut qui ne devrait pas être étendu à d'autres gabarits.
2. **La vitesse de la frappe ne dépend pas de son type** : elle est tirée par hachage de l'événement dans [15 ; 35] m/s pour tous les gabarits (moyennes de 23,8 à 25,7 m/s, y compris pour les têtes et les penaltys). Une tête vole aussi vite qu'un tir.
3. **La distance du vol dépend de l'issue**, pas du type : 4 à 63 m ; la courbure de Magnus n'agit qu'au-delà de 11 m.
4. Pas de frappe de volée, ni du pied extérieur, ni de tir enroulé léger dans le catalogue actuel.

### 11.2 Audit des tags (Tâche 2)

| Tag | Sens | Produit par | Consommé |
|---|---|---|---|
| `pass_ground` | passe au sol (cinématique) | `templates.py` (corner, t = 0,0) | `ball.py` (trajectoire) ; **ni payload ni canvas** |
| `pass_lob` | passe lobée | défini dans `ball.py`, **posé par aucun gabarit** | `ball.py` (utilisé pour le rebond après un centre) |
| `shot` | conduite finale (courbée par Magnus si spin ≠ 0, hauteur jusqu'à 0,8 m) | `templates.py` (11 gabarits) | `ball.py` ; ni payload ni canvas |
| `cross` | centre en cloche | `templates.py` (corner, t = 0,3) | `ball.py` ; ni payload ni canvas |
| `deflect` | déviation / perturbation latérale (hachage) | `templates.py` (corner t = 0,6 ; `recuperation_haute` t = 0,3) | `ball.py` ; ni payload ni canvas |
| `ball_flight` | vol de la frappe vers la cible de l'issue (ajouté en fin de séquence si l'issue a un vol, 79,4 % des clips) | `templates.py` (`build_from_template`) | `ball.py`, `engine/ball_events.py` (`keyframes[-2]`) ; ni payload ni canvas |
| `bounce` | rebond sur le sol, le poteau, la barre (B2) | défini dans `ball.py`, **posé par aucun gabarit** | `ball.py` (`ball_state_at`) ; ni payload ni canvas |
| `lob` | **n'existe pas** (le tag est `pass_lob`) | — | — |

- **Étiquettes narratives** (`Keyframe.tag` : `recuperation`, `progression`, `tir`, `tete`, `frappe`, `enroulee`, `1v1`, …) : produites par `templates.py`, jamais interprétées par le rendu, **absentes du payload**. Le payload d'un clip ne contient que, par image, la position du ballon (x, y, z), `spin`, `owner` et les joueurs.
- Ce que `canvas.html` consomme : `metadata.template` (titre, marqueur, libellé « Penalty raté »), `ball.spin` (traînée B3), `metadata.events_ball` (B4-bis), `ball.x`, `ball.y`, `ball.z`, `ball.owner`.
- `metadata.declinaison` vaut `"default"` pour les 1 586 clips (`narrative.py`) : champ prévu pour des variantes, non consommé par le canvas ; aucun lien avec les types de frappe aujourd'hui. Le NLG (`simulafoot_nlg`) lit le **gabarit** ; seuls les gabarits `decalage_enroulee` et quelques scénarios de coup franc emploient le mot « enroule ».

### 11.3 Typologie enrichie proposée (Tâche 3)

Six types, **tous réalisables en ne posant que spin et vitesse du vol dans `templates.py`** (post-traitement comme `build_decalage_enroulee`, déterministe par hachage de la référence de l'événement), sans toucher à `ball.py`. Courbure : `pic ≈ 0,5 · 0,003 · spin · v · (T/2)²` ; pour un vol typique (v = 25 m/s, T = 1,1 s) soit **≈ 0,0113 m par rad/s** (spin 25 : 0,28 m ≈ 3 px ; spin 80 : 0,90 m ≈ 10 px).

| Type | Spin (rad/s) | Vitesse du vol | Trajectoire | Contexte typique (gabarits) | Vols / 100 matchs (estim.) | Impact visuel | Complexité |
|---|---|---|---|---|---|---|---|
| `shot_tendu` | 0 (≤ 4 : sous le seuil de traînée) | 25 à 35 | droite | `percee_individuelle`, `profondeur_1v1`, `une_deux`, `penalty`, 40 % de `contre_attaque` et de `construction_placee` | ≈ 443 (35 %) | faible : référence sans traînée | très faible |
| `shot_enroule_leger` | 20 à 30 | 22 à 30 | courbe légère (0,2 à 0,35 m) | 50 % de `contre_attaque` et de `construction_placee` | ≈ 154 (12 %) | moyen sur la traînée (présente, discrète), faible sur la courbure | faible |
| `shot_enroule_fort` | 50 à 80 | 20 à 30 | courbe forte (0,6 à 0,9 m) | `decalage_enroulee`, `coup_franc` | ≈ 157 (12,5 %) | fort sur la traînée, moyen sur la courbure | faible |
| `shot_exterieur_pied` | −30 à −20 (sens inverse) | 22 à 30 | courbe légère inverse | 30 % de `percee_individuelle` et de `profondeur_1v1` | ≈ 69 (5,5 %) | faible (traînée identique, courbure opposée) | moyenne (le signe du spin dépend du côté, voir §11.6) |
| `reprise_volee` | 10 à 15 | 28 à 35 | quasi droite | `recuperation_haute`, `but_gag` (déviation puis tir) | ≈ 161 (12,8 %) | faible à moyen (traînée discrète) | faible |
| `tete` | 0 | 15 à 25 (plus lente) | droite, hauteur du vol | `debordement_centre_tete`, `corner` | ≈ 275 (21,8 %) | moyen sur la variété (vitesse), nul sur la traînée | faible (vitesse seule) |

Estimations par gabarit à partir des vols mesurés (§11.1) : somme 443 + 154 + 157 + 69 + 161 + 275 = **1 259 vols / 100 matchs**, soit 12,6 par match. Les parts 40 / 50 / 60 % sont des partages hachés par événement (déterministes) proposés, non validés.

**Contraintes de cohérence** : un clip `decalage_enroulee` doit toujours rester `shot_enroule_fort` (le NLG dit « enroule sa frappe ») ; le spin posé sur le **vol** seulement (pas sur la conduite) évite que le ballon quitte son porteur ; la hauteur et la cible de l'issue (B4, parades, poteaux) ne changent pas, car l'écart de Magnus est nul aux extrémités du segment.

### 11.4 Impact sur la distribution du spin (Tâche 4)

Aujourd'hui, sur 1 586 clips : **163 clips (10,3 %) à spin 50**, 1 423 à spin 0 ; 21 546 images sur 373 456 (5,8 %) ont un spin non nul, dont 82,5 % en conduite.

Avec la typologie (spin sur le vol seulement), par 100 matchs :

| Classe de spin (valeur absolue) | Types | Vols | Part des 1 259 vols |
|---|---|---|---|
| nul (0) | `shot_tendu`, `tete` | ≈ 718 | 57 % |
| faible (5 à 15) | `reprise_volee` | ≈ 161 | 12,8 % |
| moyen (20 à 30) | `shot_enroule_leger`, `shot_exterieur_pied` | ≈ 223 | 17,7 % |
| élevé (50 à 80) | `shot_enroule_fort` | ≈ 157 | 12,5 % |

- **Traînée visible (|spin| > 5)** : ≈ 541 vols sur 1 259 (43 %), soit ≈ 34 % des 1 586 clips (contre 10,3 % aujourd'hui), à raison d'une traînée d'environ 1 s seulement (le vol), contre 3,6 s aujourd'hui (la conduite). Images concernées : ≈ 16 000 à 18 000 (≈ 4,3 à 4,8 %), du même ordre qu'aujourd'hui (5,8 %).
- **Variété à l'écran** : avec la traînée actuelle (apparence identique dès que |spin| > 5), les classes faible, moyenne et élevée **ne se distinguent pas** : la variété ne ferait que passer de « 1 gabarit » à « 4 gabarits » présents. Pour qu'elle soit lisible il faut **moduler la traînée par |spin|** (opacité, épaisseur ou longueur), ce qui est un changement de `canvas.html` (décision D3 ci-dessous).
- **Courbure** : sur le vol, elle reste ≤ 10 px même à spin 80 (§11.3) : la limite d'échelle du ticket 22 demeure.

### 11.5 Ordre d'implémentation proposé (Tâche 5)

1. **`shot_tendu` contre `shot_enroule_fort`, spin déplacé de la conduite au vol** : gain visuel maximal (la traînée n'apparaît plus qu'à la frappe, 82,5 % des images à spin non nul disparaissent de la conduite), complexité très faible (un post-traitement, la constante existe déjà), et corrige le défaut de la conduite. Un seul gabarit change de comportement ; `coup_franc` peut être ajouté ici.
2. **`tete`** (vitesse seule) : indépendante, complexité faible (`_FLIGHT_MIN/MAX_SPEED_MPS` par type) ; aucune interaction avec le spin ; gain de variété sur 22 % des vols.
3. **`shot_enroule_leger`** : demande la modulation de la traînée par |spin| (D3) pour être visible ; dépend de l'étape 1.
4. **`reprise_volee`** : spin faible, dépend de la modulation de la traînée ; gabarits `recuperation_haute` et `but_gag`.
5. **`shot_exterieur_pied`** : en dernier, car il exige un spin **négatif** et donc la règle du côté (D4) ; gain visuel le plus faible.

À chaque étape : 100 matchs identiques pour le score, issues et événements du ballon (B4) inchangés, tests de signature par type, captures avant / après, NLG inchangé.

### 11.6 Points d'attention

- **Seuil de la traînée.** Un spin « tendu » de 5 à 10 rad/s dépasserait le seuil de 5 : soit la frappe tendue reste à 0 à 4, soit le seuil monte (par exemple à 15) ; décision D2.
- **Signe du spin.** Aujourd'hui toujours positif ; un signe négatif courbe de l'autre côté **par rapport au sens de la frappe**, sans notion de pied fort ou de côté d'attaque.
- **Spin sur la conduite.** Le déplacer vers le vol supprime la courbure de 0 à 3,46 m de la conduite (aujourd'hui peut-être perçue comme du dribble) ; c'est le choix de D1.

### 11.7 Décisions attendues de l'architecte

1. **D1 : spin sur le vol seulement** (recommandé) ou aussi sur la conduite (déconseillé, §11.1 constat 1).
2. **D2 : seuil de la traînée** : maintenir 5 rad/s (frappe tendue ≤ 4) ou relever le seuil (le tendu à 5 à 10).
3. **D3 : modulation de la traînée par |spin|** (opacité / épaisseur / longueur) : nécessaire pour que la variété de spin se voie ; modifie `canvas.html` (gel à lever).
4. **D4 : signe du spin** : règle du côté (pied fort, côté de l'attaque) ou sens fixe.
5. **D5 : vitesse par type de frappe** (tête plus lente) : autorisée à modifier `templates.py` (`_FLIGHT_*_SPEED_MPS`) ?
6. **D6 : périmètre** : types et pourcentages de la §11.3 à valider avant toute implémentation (constantes produit).

### 11.8 Statut

**B5 : diagnostic terminé, implémentation en attente des décisions du §11.7.** Rien n'a été modifié dans le code. Ticket 22 ouvert (`docs/known_issues.md`).

## 12. B5 — Variétés de frappe : implémentation (08/10/2026)

Fichiers : `src/ligue1sim/animation/templates.py` (types, spin, vitesse), `tests/test_templates.py` (nouveaux tests, empreinte de `decalage_enroulee` mise à jour), `tests/test_ball.py` (borne basse de vitesse du vol : 15 → 12 m/s), `tests/test_canvas_html.py` (tolérance d'une image sur le franchissement de la ligne, §12.7), `docs/previews/phase6/b5/` (captures), ce document. **Intacts** : `canvas.html`, `ball.py`, `narrative.py`, `narrative_player.py`, le moteur sportif, Poisson et 3c, le payload (aucun champ ajouté).

### 12.1 Principe

- Le **type** de frappe se tire par hachage déterministe de `event_ref` (`strike_type_for`, sha256 via `_flight_unit`, jamais `random`) parmi les types cohérents avec le gabarit (`_STRIKE_TYPE_WEIGHTS`). Le **spin** et la **vitesse** du vol sont tirés de la même manière dans la fourchette du type (`strike_spin_for`, `strike_speed_for`).
- Le spin est posé sur la keyframe qui **démarre le vol** (`ball_flight`), jamais sur la conduite `shot`, qui reste droite : le ballon ne quitte plus son porteur (hypothèse « D1 : vol seulement », recommandée au diagnostic §11.7, appliquée en l'absence d'indication contraire). Sans vol (issues `tacle`, `degagement`, ou séquence sans issue) : aucun spin.
- `build_decalage_enroulee` ne pose plus de spin constant (50 rad/s sur conduite et vol) : le gabarit passe par la même logique et produit toujours `shot_enroule_fort`.
- `ball.py` n'est pas modifié ; la cible, l'issue, la minute, le score et les événements du ballon (B4) ne dépendent pas du type (l'écart de Magnus est nul aux extrémités du vol).

### 12.2 Les six types

| Type | Spin (rad/s) | Vitesse du vol (m/s) | Cible de l'architecte | Observé (1 259 vols, 100 matchs) |
|---|---|---|---|---|
| `shot_tendu` | 0 | 30 à 35 | 35 % | 448 (35,6 %) |
| `shot_enroule_leger` | 20 à 30 | 20 à 28 | 12 % | 165 (13,1 %) |
| `shot_enroule_fort` | 50 à 80 | 20 à 28 | 9,7 % | 122 (9,7 %) |
| `shot_exterieur_pied` | −30 à −20 | 22 à 30 | 5,5 % | 88 (7,0 %) |
| `reprise_vollee` | 10 à 15 | 25 à 32 | 16 % | 193 (15,3 %) |
| `tete` | 0 | 12 à 18 | 21,8 % | 243 (19,3 %) |

Observé : spin minimum / moyen / maximum et vitesse minimum / moyenne / maximum (vitesse moyenne sur le vol, distance sur durée) :

| Type | Spin | Vitesse | Durée moyenne du vol | Clips avec traînée |
|---|---|---|---|---|
| `shot_tendu` | 0 / 0 / 0 | 30,0 / 32,4 / 35,0 | 0,76 s | 0 |
| `shot_enroule_leger` | 20,1 / 25,2 / 29,8 | 20,0 / 24,2 / 28,0 | 1,19 s | 165 |
| `shot_enroule_fort` | 50,1 / 65,4 / 80,0 | 20,0 / 24,2 / 28,0 | 1,06 s | 122 |
| `shot_exterieur_pied` | −30,0 / −25,2 / −20,0 | 22,1 / 26,3 / 30,0 | 0,94 s | 88 |
| `reprise_vollee` | 10,0 / 12,3 / 15,0 | 25,0 / 28,4 / 31,9 | 0,70 s | 193 |
| `tete` | 0 / 0 / 0 | 12,0 / 14,9 / 18,0 | 1,66 s | 0 |

### 12.3 Correspondance gabarit → type

Les six cibles ne peuvent pas être tenues à la fois avec les règles de cohérence de la consigne (voir 12.7) ; le mapping retenu s'appuie sur le diagnostic §11.3 et donne les écarts ci-dessus (au plus 2,5 points, après le recalibrage du pool pied du §12.11).

| Gabarit | Types (poids) | Observé (vols) |
|---|---|---|
| `decalage_enroulee` | `shot_enroule_fort` (100 %) | fort 122 |
| `debordement_centre_tete` | `tete` (90 %), `reprise_vollee` (10 %) | tête 182, volée 23 |
| `corner` | `tete` (90 %), `reprise_vollee` (10 %) | tête 61, volée 9 |
| `recuperation_haute`, `but_gag` | `reprise_vollee` (100 %) | volée 134 et 27 |
| `penalty` | `shot_tendu` (100 %) | tendu 34 |
| `coup_franc` | `shot_enroule_leger` (100 %) | léger 35 |
| `contre_attaque`, `construction_placee`, `percee_individuelle`, `profondeur_1v1`, `une_deux` | `shot_tendu` 64 %, `shot_enroule_leger` 22 %, `shot_exterieur_pied` 14 % | tendu 414, léger 130, extérieur 88 |

### 12.4 Distribution du spin (100 matchs, graines 1 à 100, 1 586 clips)

| Mesure | Avant B5 | Après B5 |
|---|---|---|
| Clips avec un spin en valeur absolue > 5 (traînée visible) | 163 (10,3 %) | **568 (35,8 %)**, soit 45,1 % des 1 259 vols |
| Images avec traînée | 21 546 / 373 456 (5,8 %), 82,5 % en conduite | 16 007 / 372 918 (4,3 %), toutes en vol |
| Spin nul | 1 423 clips | 1 018 clips (dont 327 sans vol) |
| Spin faible (5 à 15) | 0 | 193 |
| Spin moyen (20 à 30, valeur absolue) | 0 | 253 |
| Spin élevé (50 à 80) | 163 (spin 50) | 122 |

La traînée apparaît sur trois fois plus de clips, plus brièvement (une seconde de vol au lieu de 3,6 s de conduite). Elle est identique dès que le spin dépasse 5 en valeur absolue : la différence entre faible, moyen et élevé n'est pas visible tant que `canvas.html` ne module pas la traînée par le spin (décision D3 du diagnostic, non traitée ici).

### 12.5 Déterminisme

- **Moteur sportif** : 100 matchs sur 100 identiques entre HEAD et l'arbre modifié (scores, buts, cartons, remplacements, blessures, notes ; 295 buts ; événements narratifs identiques : minute, équipe, gabarit, issue).
- **Types** : deux exécutions indépendantes (graines 1 à 100, `PYTHONHASHSEED=0`) donnent les **mêmes** 1 586 lignes (type, spin, vitesse, distance, durée). Test : le tirage ne dépend pas de l'état du générateur global. Contrôle complémentaire après recalibrage (§12.11) : la trajectoire du ballon est identique à celle d'avant B5 sur les 286 clips sans vol hors `decalage_enroulee` et, pour les clips avec vol, **avant le début du vol** (1 137 clips sur 1 259) ; elle diffère pour les 122 `decalage_enroulee` (conduite redressée) et, par construction, après le début du vol (durée de chaque vol modifiée : 1 259 clips sur 1 259, 372 918 images contre 373 456).
- **Cohérence avec B4** : issues et événements du ballon inchangés ; durées de clip modifiées (la vitesse du vol dépend du type : durée moyenne d'un vol 1,01 s, tête 1,66 s, volée 0,70 s) ; durée moyenne d'un clip 7,81 s.

### 12.6 Cohérence NLG (100 matchs, textes réellement produits par le NLG)

Le NLG ne reçoit **ni le type de frappe ni le spin** : il choisit son scénario sur (type d'événement, gabarit, issue) et ses phrases dans des banques génériques (`narrative_adapter.py`) ; seul le gabarit `penalty` est lu dans le texte. Les textes sont donc **identiques avant et après B5** (mêmes entrées). Mesure sur 1 582 événements narratifs, dont 1 451 avec texte (poteau et barre ne sont pas commentés) :

| Mesure | Résultat |
|---|---|
| `decalage_enroulee` avec texte | 149 événements : **1 seul** texte contient « enroul » (148 sans) |
| Phrases qui nomment un type de frappe | « volée / reprise » 55, « enroulée » 20, « tête » (hors « tête froide ») 9, « frappe tendue / sèche » 3 |
| Contradictions texte / animation **avant B5** | 83 (volée 55, enroulée 19, tête 9) |
| Contradictions texte / animation **après B5** | **61** (volée 41, enroulée 13, tête 7) |

- La consigne attendait **0 incohérence** et que `decalage_enroulee` produise toujours un texte « enroulé » : **ce n'est pas le cas** et ce n'est pas atteignable sans modifier le NLG (la prémisse « le texte dit enroule sa frappe » n'existe pas dans les banques : seules quelques phrases génériques, conditionnées par les attributs du joueur, contiennent « enroule »). B5 **réduit** les contradictions de 27 % (83 → 61) sans les supprimer ; le texte n'est jamais ajusté par B5.
- Les 3 phrases « frappe tendue / sèche » tombent sur des clips sans traînée (penalty, `shot_tendu`) ; `shot_enroule_fort` n'est produit que par `decalage_enroulee`.
- Suite possible (hors périmètre, à décider) : transmettre le type de frappe au NLG, ou conditionner les phrases « volée », « enroulée », « tête » sur le type.

### 12.7 Écarts entre la consigne et les données

1. **Les six pourcentages ne se tiennent pas ensemble.** Avec « tête / volée pour les gabarits de tête » et « tendu / léger / extérieur pour les autres gabarits », la volée (16 %) ne peut venir que des gabarits de tête (275 vols, 21,8 %) : impossible de viser aussi la tête à 21,8 %. J'ai appliqué le mapping validé au diagnostic (`reprise_vollee` aussi pour `recuperation_haute` et `but_gag`, gabarits de déviation) ; écarts initiaux : tendu +4,4 points, tête −2,5, volée −0,7, léger −1,3 ; après recalibrage (§12.11) : tendu +0,6, léger +1,1, extérieur +1,5, tête −2,5, volée −0,7.
2. **`debordement_centre_tete` n'avait pas de spin** avant B5 (la consigne le disait à 50 rad/s) : seul `decalage_enroulee` en avait.
3. **Spin déplacé de la conduite au vol** : la conduite de `decalage_enroulee` est désormais droite (elle déviait jusqu'à 3,46 m du porteur) ; la courbure de Magnus ne s'applique plus qu'au vol (jusqu'à 2,9 m d'écart à la corde pour `shot_enroule_fort`).
4. **Vitesse instantanée > 35 m/s** : 125 vols sur 1 259 (9,9 %) après recalibrage (140 avant), tous `shot_tendu` (30 à 35 m/s de vitesse moyenne ; pic jusqu'à 38,1 m/s dû à la décélération de B1 : la vitesse initiale dépasse la moyenne). Même convention qu'avant B5 (vitesse moyenne dans la fourchette), mais plus fréquente puisque les tendus partent plus vite ; la dette notée au design doc (« résidu > 35 m/s ») s'étend donc aux frappes tendues.
5. **Tests existants adaptés** (conséquences directes des décisions) : l'empreinte de structure de `decalage_enroulee` (`tests/test_templates.py`, fixture sans issue, donc sans vol, donc plus de spin) ; la borne basse de vitesse moyenne du vol de `tests/test_ball.py` (15 → 12 m/s, la tête vole à 12-18 m/s). `tests/test_ball.py` n'était pas dans la liste du commit demandée : ajouté.
6. **Franchissement de la ligne par les clips de but.** `test_goal_clips_of_a_real_payload_cross_the_line_between_the_posts` (`tests/test_canvas_html.py`) a échoué sur l'export : un clip de but (volée de `debordement_centre_tete`, 23e minute) finit à 0,17 m de la ligne à la dernière image (échantillonnage à 30 images/s, vol plus rapide). Ce n'est pas un défaut nouveau : sans B5, **45 clips de but sur 295 (15,3 %)** n'ont déjà aucune image au-delà de la ligne (écart maximal 1,48 m) ; avec B5, **54 sur 295 (18,3 %)**, écart maximal 1,19 m. Le canvas prévoit ce cas (repli de `goalEvents` : l'événement but part à la dernière image), donc rien ne casse à l'écran ; le test d'origine réussissait par hasard sur son match d'essai. Il exige maintenant le franchissement **ou** une dernière image à moins de 1,5 m de la ligne, entre les poteaux. `tests/test_canvas_html.py` n'était pas dans la liste du commit : ajouté. Pas de ticket ouvert pour ce défaut d'échantillonnage (à décider).

### 12.8 Captures (`docs/previews/phase6/b5/`, canvas 1 200 × 780, 0,45 s après le début du vol, avant = HEAD, après = arbre modifié)

Un clip par type, mêmes événements des deux côtés (graines 1, 3 et 5).

| Clip | Type (gabarit, issue) | Avant (HEAD) | Après |
|---|---|---|---|
| 0 | `shot_tendu` (`percee_individuelle`, but) | pas de traînée, vol de 1,88 s | pas de traînée, vol de **1,05 s** (30,5 m/s) |
| 1 | `shot_enroule_leger` (`construction_placee`, arrêt) | pas de traînée | **traînée légère** (spin 20,6), vol de 1,14 s |
| 2 | `shot_enroule_fort` (`decalage_enroulee`, hors cadre) | traînée (spin 50, aussi sur la conduite) | **traînée bien visible** (spin 53,6), vol de 1,67 s, conduite droite |
| 3 | `reprise_vollee` (`recuperation_haute`, arrêt) | pas de traînée | **traînée courte** (spin 12,8), vol de 0,92 s |
| 4 | `tete` (`debordement_centre_tete`, arrêt) | pas de traînée, vol de 1,52 s | pas de traînée, ballon **plus lent** : vol de 2,31 s (13,8 m/s) |
| 5 | `shot_exterieur_pied` (`construction_placee`, but) | pas de traînée | **traînée** (spin −27,8), vol de 1,39 s |

Noms : `avant_clip<i>_<type>_<instant>.png` / `apres_...` ; `zoom_types_1_a_3.png` et `zoom_types_4_a_6.png` : même instant agrandi ×4 autour du ballon (avant à gauche, après à droite).

### 12.9 Tests

`tests/test_templates.py` : table des types conforme aux décisions, spin et vitesse attendus pour chacun des six types (300 tirages), spin posé sur le seul vol des 12 gabarits (60 séquences), `decalage_enroulee` toujours `shot_enroule_fort` (270 séquences, vitesse 20-28), cohérence gabarit → type, répartition sur 1 000 frappes (mélange réel de gabarits, tolérance 4,5 points, `shot_enroule_fort` à 9,7 % ± 0,6), déterminisme indépendant de l'état aléatoire global, absence de spin sans vol.

### 12.11 Revue de l'architecte du 08/10/2026 : recalibrage et alignements

**Point 1 : `shot_tendu` hors fourchette.** Constante produit modifiée, citée : poids du pool pied `_FOOT_POOL` (`contre_attaque`, `construction_placee`, `percee_individuelle`, `profondeur_1v1`, `une_deux`) **0,70 / 0,19 / 0,11 → 0,64 / 0,22 / 0,14** (tendu / enroulé léger / extérieur du pied). Les poids des gabarits spéciaux (`decalage_enroulee`, têtes, volées, penalty, coup franc) ne changent pas. Les poids ont été calés sur l'échantillon de 100 matchs (un seul réglage) ; 66 vols changent de type (48 tendu → léger, 18 léger → extérieur), le score et les issues ne changent pas.

| Type | Avant recalibrage | **Après** | Cible | Fourchette de l'architecte (cible ± 4) | Dans la fourchette |
|---|---|---|---|---|---|
| `shot_tendu` | 496 (39,4 %) | **448 (35,6 %)** | 35 % | 34-36 % demandé | oui |
| `shot_enroule_leger` | 135 (10,7 %) | 165 (13,1 %) | 12 % | 8 à 16 % | oui |
| `shot_enroule_fort` | 122 (9,7 %) | 122 (9,7 %) | 9,7 % | 5,7 à 13,7 % | oui |
| `shot_exterieur_pied` | 70 (5,6 %) | 88 (7,0 %) | 5,5 % | 1,5 à 9,5 % | oui |
| `reprise_vollee` | 193 (15,3 %) | 193 (15,3 %) | 16 % | 12 à 20 % | oui |
| `tete` | 243 (19,3 %) | 243 (19,3 %) | 21,8 % | 17,8 à 25,8 % | oui |

Échantillon identique : 1 259 vols, 100 matchs (graines 1 à 100). Le test de répartition (`tests/test_templates.py`) exige maintenant ± 4 points pour chaque type (au lieu de 4,5) et ± 2,5 points pour `shot_tendu` sur son échantillon synthétique de 1 000 frappes (bruit d'échantillonnage d'environ ± 1,5 point). Les captures de §12.8 restent valides : les six événements témoins gardent le même type.

**Point 2 : spin de `reprise_vollee`.** La cible produit reste **10 à 15 rad/s** et le code l'applique (`StrikeType("reprise_vollee", 10.0, 15.0, 25.0, 32.0)`, spin posé sur le vol) : spin mesuré 10,0 / 12,3 / 15,0 sur 193 vols, traînée sur les 193 (courte : durée moyenne du vol 0,70 s). La formule « spin fixé à 0 sur le vol » n'apparaît ni dans le code ni dans ce document (la table du §12.2 donnait déjà 10 à 15) ; seule la **conduite** est à spin 0 pour tous les types, et les types `shot_tendu` et `tete` sont à spin 0 sur le vol. Aucune constante modifiée sur ce point.

**Point 3 : NLG et type de frappe.** Ticket 23 ouvert dans `docs/known_issues.md` (priorité moyenne, résolution prévue après B5). Aucune correction dans B5.

**Points acceptés.** Pic de vitesse de `shot_tendu` (38,1 m/s) : accepté en l'état, à surveiller en B6. Le test adapté `tests/test_canvas_html.py` (franchissement de la ligne, §12.7 point 6) est présent dans l'export et passe.

**Déterminisme relancé** (graines 1 à 100, état avant B5 contre arbre recalibré) : scores, buts (295), cartons, remplacements, blessures, notes : 100 / 100 identiques ; 1 586 événements narratifs et 1 586 clips identiques (graine, rang, gabarit, issue) ; deux exécutions de l'arbre : types, spin, vitesses, durées et empreintes de la trajectoire du ballon identiques ; 372 918 images (373 456 avant B5, la durée des vols ayant changé). Les chiffres « 246 événements, 60 clips, 5 864 images » du message de revue ne correspondent à aucune mesure de cette série ; les valeurs ci-dessus sont celles mesurées.

### 12.10 Statut

**B5 terminé** : six types de frappe, spin et vitesse par type, score identique 100/100, traînée sur 35,8 % des clips. À décider : modulation de la traînée par spin (D3), mise en cohérence du NLG avec le type de frappe (§12.6), écarts de répartition (§12.7).

---

## 13. B6-c — Micro-variations clé par événement : récapitulatif de clôture (14/10/2026)

**Principe.** Les décalages de départ et les dérives des joueurs étaient clés sur `player_id` seul : un même joueur avait les mêmes décalages dans tous ses clips. Ils sont désormais clés sur `player_id|event_ref|sel` (sha256, jamais `hash()` ni `random`), avec les mêmes amplitudes pour le décalage de départ (0 à 0,3 × durée du clip). Le plancher des dérives, jusque-là fixe à 0,5 m, est tiré par couple (joueur, événement) dans **[0,2 ; 0,5] m** (sel `drift_floor_mag`). Fichier modifié : `src/ligue1sim/animation/sequence_generator.py` (la clé du décalage de départ est dans `motion.py`).

### 13.1 Résultats (100 matchs réels de Ligue 1, graines 1 à 100, 1 586 événements)

| Mesure | Avant B6-c | B6-c (`80f2bd0`) | A3 (`9965d63`, plancher 0,1 m) | Clôture (`1f562e9`, plancher 0,2 m) |
|---|---|---|---|---|
| Variété des dérives (paires joueur / événement différentes, 37 619 paires) | 16,5 % | 79,9 % | 99,9 % | **99,9 %** |
| Amplitude moyenne des dérives | — | 2,00 m | 1,97 m | **1,97 m** |
| Plancher des dérives | 0,5 m fixe | 0,5 m fixe | [0,1 ; 0,5] m continu | **[0,2 ; 0,5] m continu** |
| Variété des décalages de départ (41 247 paires) | 0 % | 99,8 % | 99,8 % | **99,8 %** (inchangée) |
| Décors dont la dérive est sous 0,36 m | 0 % | 0 % | 10,2 % | 8,4 % |

**Distribution des dérives à la clôture (m).** Minimum 0,20 ; percentiles 1 / 5 / 10 / 25 / 50 / 75 / 90 / 95 / 99 : 0,23 / 0,31 / 0,38 / 0,57 / 1,79 / 3,23 / 3,91 / 4,14 / 5,23 ; maximum 5,25. Seul le bas de la plage change entre B6-c et la clôture ; à partir du percentile 25, rien ne change.

**Pourquoi un plancher variable.** Avec le plancher fixe de 0,5 m, 22,1 % des dérives valaient exactement 0,5 m, d'où 20,1 % de paires identiques d'un événement à l'autre ; le seuil de 90 % de variété n'était pas atteignable sans modifier cette amplitude produit (décision du propriétaire : A3, puis relèvement de la borne basse de 0,1 à 0,2 m pour garder du mouvement aux décors les plus lents, option 1B).

### 13.2 Vérifications

| Vérification | Résultat |
|---|---|
| Déterminisme (7 empreintes sur 100 matchs : résultat moteur, 1 586 événements narratifs, durées, métadonnées, trajectoires du ballon, nombre d'images, positions des joueurs) | **100 / 100** entre l'état précédent et l'état modifié pour les six premières (seules les positions des joueurs changent, par construction) ; **100 / 100** entre deux exécutions de l'arbre pour les sept |
| `pytest tests --ignore=simulafoot_nlg` (archive propre de `1f562e9`, `PYTHONHASHSEED=0`) | **1 493 passés, 5 ignorés, 12 désélectionnés** |
| `npm run build` / `npm run lint` (même archive) | **OK** ; 0 erreur, 5 avertissements |
| Tests d'intégration (7 de `tests/test_narrative_player.py`, `-m integration`, archive propre de `80f2bd0`) | 7 passés ; restent exclus de la suite standard (décision du propriétaire, ticket 29) |
| Captures avant / après (graine 5, mêmes clips : offensif, défensif, transition) | Aucune différence visible entre plancher 0,1 m et 0,2 m ; décor le plus lent des clips : 0,22 → 0,23 m, 0,37 → 0,37 m, 0,27 → 0,34 m |

### 13.3 Tests et empreintes

Les 5 empreintes figées de `tests/test_narrative_player.py` (`_WITNESS_DIGESTS`) ont été recalculées **trois fois** : après B6-c, après A3, puis après le plancher à 0,2 m. À chaque fois, la cause unique est prouvée par aller-retour de la constante : avec l'ancienne valeur remise, le code redonne exactement les empreintes précédentes. Modification de ce fichier, hors du périmètre initial de B6-c, entérinée par le propriétaire (décision B1). Tests ajoutés : 7 à B6-c (3 dans `tests/test_motion.py`, variété du décalage de départ ; 4 dans `tests/test_sequence_generator.py`, variété des dérives) et 4 à A3 (`tests/test_sequence_generator.py`, variété et bornes du plancher), soit 1 482 → 1 489 → 1 493 tests passés.

### 13.4 Commits

| Commit | Contenu |
|---|---|
| `80f2bd0` | B6-c : décalages de départ et dérives clés par événement |
| `9965d63` | A3 : plancher des dérives tiré dans [0,1 ; 0,5] m |
| `1f562e9` | Plancher relevé : [0,2 ; 0,5] m (option 1B) |
| `6d50b07` | Ticket 29 : tests d'intégration exclus de la suite standard |
| `a9c6897` | Ticket 30 : cohérence joueur-ballon (exigence du propriétaire, Bloc A, A1.6) |

### 13.5 Limites connues

- 8,4 % des dérives restent sous 0,36 m (22,1 % sous 0,5 m) : décors proches du minimum, jugés conformes sur les captures de la graine 5 (images fixes, début et fin de clip, pas une lecture animée).
- Ticket 28 (adversaire décor à 1,5 m du départ du tireur de penalty) et ticket 27 (tireur qui dépasse le ballon) restent ouverts.

### 13.6 Statut

**B6-c clos.** Prochaine étape : B6-d (réaction du gardien).
