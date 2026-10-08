# Phase 6, Bloc B — Audit de la physique du ballon

Document de référence du **08/10/2026**, sur `HEAD` = `e63d6f0`. **Audit seulement : aucune ligne de code n'a été modifiée.** Les mesures viennent de scripts jetables, hors dépôt, qui appellent `ball_state_at` sur les 12 gabarits réels (helpers déterministes de `tests/test_narrative_player.py`, compo fixe) pour les issues `but`, `arret`, `poteau`, `barre`, `hors_cadre`, `tacle` et `degagement`.

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
