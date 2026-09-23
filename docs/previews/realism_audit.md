# Audit de réalisme — rendu des clips (23/09/2026)

Diagnostic uniquement, aucun code modifié. Mesures produites par un script
de lecture seule (scratch, non versionné) qui construit, pour chacun des
12 gabarits, une `Sequence` via le pipeline RÉEL de production (`BUILDERS`,
`enrich_with_background`, `motion.interpolate`, `ball.ball_state_at`, FPS=30
identique à `narrative_player._build_clip_frames`) — zones (`event.zone`/
`event.assist_zone`) reprises des constantes réelles de `engine/narrative.py`
(`_GABARIT_BASE_ZONE`/`_GABARIT_ASSIST_BASE_ZONE`), pas des valeurs
inventées. Scorer/lineup synthétiques (4-3-3 standard, 11+11 joueurs) mais
mêmes mécaniques de placement que la production (`pitch_layout.place_starting_xi`).

**Convention "figurant"** : un joueur dont `RosterEntry.role is None` —
recouvre à la fois les coéquipiers du buteur non scriptés par le gabarit
(convertis en `background` par `enrich_with_background`) et la totalité des
11 adversaires (background eux aussi, gardien compris). "Actif" = un rôle
nommé du gabarit (`scorer`/`assist`/`support1`/`support2`). Référence de
déplacement "joueur actif" = le **scorer** (protagoniste présent dans les 12
gabarits).

## Tâche 1 — Figurants

| Gabarit | Figurants | Déplacement scorer (m) | Déplacement figurant médian (m) | Ratio médian | Figurants immobiles (<0,5m) | Verdict |
|---|---:|---:|---:|---:|---:|---|
| contre_attaque | 19 | 39,26 | 1,34 | 0,034 | 5/19 | quasi-immobiles |
| construction_placee | 19 | 39,26 | 1,34 | 0,034 | 5/19 | quasi-immobiles |
| debordement_centre_tete | 20 | 49,45 | 2,46 | 0,050 | 4/20 | quasi-immobiles |
| percee_individuelle | 21 | 39,26 | 2,43 | 0,062 | 5/21 | mobiles |
| une_deux | 20 | 47,97 | 1,90 | 0,040 | 5/20 | quasi-immobiles |
| coup_franc* | 21 | 4,39 | 2,43 | 0,554 | 5/21 | mobiles* |
| corner | 19 | 52,29 | 2,43 | 0,047 | 4/19 | quasi-immobiles |
| profondeur_1v1 | 20 | 47,97 | 1,90 | 0,040 | 5/20 | quasi-immobiles |
| recuperation_haute | 19 | 47,97 | 2,48 | 0,052 | 4/19 | mobiles |
| decalage_enroulee | 20 | 41,06 | 2,46 | 0,060 | 4/20 | mobiles |
| penalty* | 19 | 7,20 | 2,43 | 0,338 | 4/19 | mobiles* |
| but_gag | 19 | 56,70 | 2,49 | 0,044 | 4/19 | quasi-immobiles |

\* `coup_franc`/`penalty` : le tireur est déjà positionné près du ballon dès
t=0 (`starts_at_restart=True`), donc son propre déplacement de référence est
très faible (4,4m/7,2m contre 39-57m pour les autres gabarits) — le ratio
médian en est mécaniquement gonflé, **pas** parce que les figurants bougent
plus que dans les autres gabarits (leurs déplacements absolus, 2,43m
médian, sont comparables aux autres). Signalé plutôt que corrigé/dissimulé.

**Aucun gabarit n'atteint le verdict "immobiles" strict** (aucun avec 100%
des figurants < 0,5m) : les 4-5 figurants les plus statiques de chaque clip
sont bornés à 0,5m, mais jamais à 0m exactement — hypothèse initiale du
brief ("figurants immobiles") donc partiellement invalidée : ils ne sont
jamais totalement figés, mais 12/12 gabarits ont au moins 4 figurants sur
19-21 en dessous de 0,5m sur toute la durée du clip, et le déplacement
médian ne dépasse jamais 6% de celui du protagoniste hors coup_franc/penalty.

## Tâche 2 — Ballon

| Gabarit | Segment décisif (tag) | Durée (s) | Distance (m) | Vitesse moy. (m/s) | Vitesse max (m/s) | Vitesse hors segment (m/s) | Verdict |
|---|---|---:|---:|---:|---:|---:|---|
| contre_attaque | shot | 4,80 | 51,93 | 10,82 | 10,83 | 11,42 | correct |
| construction_placee | shot | 5,60 | 50,67 | 9,05 | 9,06 | 4,83 | correct |
| debordement_centre_tete | shot | 2,40 | 23,71 | 9,88 | 9,88 | 9,39 | correct |
| percee_individuelle | shot | 1,75 | 11,78 | 6,73 | 6,73 | 5,23 | **mou** |
| une_deux | shot | 2,00 | 42,07 | 21,04 | 21,07 | 3,84 | rapide |
| coup_franc | shot | 1,50 | 2,19 | 1,46 | 1,46 | 0,63 | **mou** |
| corner | deflect (pas de tag "shot") | 2,80 | 23,71 | 8,47 | 15,91 | 16,29 | correct |
| profondeur_1v1 | shot | 4,20 | 33,60 | 8,00 | 8,01 | 14,69 | correct |
| recuperation_haute | shot | 2,25 | 31,48 | 13,99 | 14,01 | 18,37 | correct |
| decalage_enroulee | shot | 3,60 | 29,09 | 8,08 | 8,59 | 9,08 | correct |
| penalty | shot | 0,60 | 2,40 | 4,00 | 4,00 | 1,41 | **mou** |
| but_gag | shot | 1,75 | 48,06 | 27,46 | 27,50 | 20,14 | rapide |

**3/12 gabarits "mou"** (percee_individuelle, coup_franc, penalty), **7/12
"correct"**, **2/12 "rapide"**. Référence réelle donnée par le brief : un
tir réel part à 25-30 m/s ; **aucun** des 12 gabarits n'atteint cette
fourchette sur son segment décisif (`but_gag` s'en approche à 27,5 m/s mais
c'est une coïncidence géométrique, voir Synthèse — pas une frappe modélisée
comme telle).

**Constat structurel plus profond que "mou"/"rapide" (mesure, pas
hypothèse)** : sur les 12 gabarits, la dernière keyframe a
`ball_owner="scorer"` (vérifié directement dans `templates.py` — le
commentaire de `but_gag` le confirme explicitement : *"un ball_owner absent
retombe sur la dernière position connue... le ballon n'atteindrait jamais
event.zone"*). Le ballon **ne quitte donc jamais le pied du tireur pour
traverser la ligne de but** dans le modèle de données actuel — `event.zone`
est la position de FRAPPE (13 à 39m du but selon le gabarit, voir
`_GABARIT_BASE_ZONE`), pas le but lui-même. Le "segment décisif" mesuré
ci-dessus n'est donc pas la trajectoire d'un tir vers la cage : c'est la
distance parcourue par le porteur (souvent déjà le scorer) entre le début du
segment et sa position de frappe. La vitesse mesurée dépend uniquement de
cette distance et de la durée fixée par le gabarit — ce qui explique aussi
bien les verdicts "mou" (coup_franc/penalty : le tireur est déjà tout près
du ballon, distance quasi nulle) que "rapide" (but_gag : grande distance sur
segment court, sans rapport avec la vitesse réelle d'une frappe).

**Spin/courbure** : `build_from_template` pose `spin=0.0` par défaut pour
tous les gabarits — un seul (`decalage_enroulee`) reçoit une courbure de
Magnus non nulle (50 rad/s, post-traitement dédié dans `build_decalage_enroulee`).
Les 11 autres gabarits ont donc une trajectoire de tir rigoureusement
rectiligne (aucune courbure), y compris `coup_franc`.

## Tâche 3 — Gardien

Aucun des 12 gabarits ne porte de rôle `Role` nommé "gardien"/"keeper" (0
occurrence dans `templates.py`) — le gardien adverse est systématiquement
un joueur "décor" (`sequence.background`, `team_side="opponent"`), au même
titre que n'importe quel autre adversaire non impliqué dans l'occasion.

| Gabarit | Mouvement latéral documenté | Déplacement mesuré (m) | Plongeon documenté | Comportement dédié au tir | Verdict |
|---|---|---:|---|---|---|
| contre_attaque | oui (générique) | 1,32 | non | non | statique |
| construction_placee | oui (générique) | 1,32 | non | non | statique |
| debordement_centre_tete | oui (générique) | 1,32 | non | non | statique |
| percee_individuelle | oui (générique) | 1,32 | non | non | statique |
| une_deux | oui (générique) | 1,32 | non | non | statique |
| coup_franc | oui (générique) | 1,32 | non | non | statique |
| corner | oui (générique) | 1,32 | non | non | statique |
| profondeur_1v1 | oui (générique) | 1,32 | non | non | statique |
| recuperation_haute | oui (générique) | 1,32 | non | non | statique |
| decalage_enroulee | oui (générique) | 1,32 | non | non | statique |
| penalty | oui (générique) | 1,32 | non | non | statique |
| but_gag | oui (générique) | 1,32 | non | non | statique |

**Précision sur "mouvement latéral documenté" / verdict "statique"** :
`sequence_generator._tactical_drift` a bien une branche `poste == "GK"`
(micro-décalage latéral vers `ball_y`, plafonné à `_GK_Y_MAX=0,02` soit
~1,36m réels — cohérent avec le déplacement mesuré, 1,32m). Ce mouvement
**existe** au sens strict, mais c'est la MÊME formule générique que celle de
n'importe quel joueur "décor" à poste GK, à n'importe quel instant du match
— rien dans le code ne le lie à la direction du tir, à sa vitesse, à son
cadrage, ni au fait qu'un but soit marqué ou non. D'où le verdict
"statique" : aucun comportement RÉACTIF au tir, ni plongeon (aucun champ
vertical `z` n'existe pour un joueur — seul le ballon a un `z`), ni arrêt,
ni encaissement visible. Identique sur les 12/12 gabarits produisant un tir.
**Confirmé, non corrigé** (conforme à la consigne du brief).

## Tâche 4 — Séquencement

Durées et tags de chaque gabarit (lus directement dans `Template.tags`/
`duration`, pas simulés — donnée exacte).

**contre_attaque** (8,0s) : [0,00-3,20s] recuperation/pass_ground · [3,20-8,00s] progression/**shot (4,8s)**
**construction_placee** (14,0s) : [0,00-4,20s] recuperation/pass_ground · [4,20-8,40s] circulation/pass_ground · [8,40-14,00s] progression/**shot (5,6s)**
**debordement_centre_tete** (6,0s) : [0,00-3,60s] debordement/pass_ground · [3,60-6,00s] centre/**shot (2,4s)**
**percee_individuelle** (7,0s) : [0,00-2,80s] controle/pass_ground · [2,80-5,25s] dribble/pass_ground · [5,25-7,00s] dribble/**shot (1,75s)**
**une_deux** (4,0s) : [0,00-2,00s] passe/pass_ground · [2,00-4,00s] remise/**shot (2,0s)**
**coup_franc** (5,0s) : [0,00-3,50s] placement/pass_ground · [3,50-5,00s] elan/shot (1,5s, pas signalé — exactement au seuil)
**corner** (7,0s) : [0,00-2,10s] preparation/pass_ground · [2,10-4,20s] montee/cross · [4,20-7,00s] centre/deflect (2,8s, pas de tag "shot")
**profondeur_1v1** (6,0s) : [0,00-1,80s] appel/pass_ground · [1,80-6,00s] passe/**shot (4,2s)**
**recuperation_haute** (5,0s) : [0,00-1,50s] pressing/pass_ground · [1,50-2,75s] pressing/deflect · [2,75-5,00s] recuperation/**shot (2,25s)**
**decalage_enroulee** (6,0s) : [0,00-2,40s] decalage/pass_ground · [2,40-6,00s] controle/**shot (3,6s)**
**penalty** (4,0s) : [0,00-2,00s] placement/pass_ground · [2,00-3,40s] attente/pass_ground · [3,40-4,00s] elan/shot (0,6s)
**but_gag** (5,0s) : [0,00-1,75s] centre/pass_ground · [1,75-3,25s] premier_contact/pass_ground · [3,25-5,00s] rebond/**shot (1,75s)**

**Segments `shot` > 1,5s : 9/12 gabarits** (contre_attaque 4,8s,
construction_placee 5,6s, debordement_centre_tete 2,4s, percee_individuelle
1,75s, une_deux 2,0s, profondeur_1v1 4,2s, recuperation_haute 2,25s,
decalage_enroulee 3,6s, but_gag 1,75s) — jusqu'à **5,6 secondes** pour
construction_placee. `coup_franc` (1,5s pile) et `penalty` (0,6s) n'y
figurent pas.

**Transitions abrupdes / absence d'accélération progressive** : mesuré
précisément (pas estimé) en reproduisant la condition exacte de
`motion._interpolate_segment` — un segment bascule sur un repli LINÉAIRE
(vitesse constante dès le premier instant, aucune accélération/décélération
Bézier) dès que la vitesse moyenne exigée dépasse 55% de la vitesse max du
poste. **32 segments sur 9/12 gabarits** tombent dans ce cas (aucun sur
`construction_placee`, `coup_franc`, `penalty`) :

| Gabarit | Segments en repli linéaire (rôle, ratio de v_max) |
|---|---|
| contre_attaque | scorer 0,4→1,0 (0,59×) |
| debordement_centre_tete | assist 0,0→0,6 (1,17×), assist 0,6→1,0 (0,75×), scorer 0,0→0,6 (0,61×), scorer 0,6→1,0 (1,37×) |
| percee_individuelle | scorer 0,4→0,75 (0,62×), scorer 0,75→1,0 (0,75×) |
| une_deux | assist 0,0→0,5 (1,07×), scorer 0,0→0,5 (1,60×), scorer 0,5→1,0 (1,07×) |
| corner | assist ×2, support1 ×2, scorer ×2 (jusqu'à 2,40×) |
| profondeur_1v1 | assist 0,0→0,3, scorer ×2 |
| recuperation_haute | support1, support2, scorer ×3 |
| decalage_enroulee | scorer ×2 |
| but_gag | support1 ×2, support2, scorer ×3 |

Chaque occurrence produit exactement le symptôme décrit par le brief : une
vitesse instantanée non nulle dès `elapsed=0` (pas de rampe), puis un arrêt
net à la transition vers le segment suivant (ou la fin du clip).

## Tâche 5 — Comparaison factuelle (rendu réel, `render/canvas.html`)

Lu directement dans le code de rendu (fonction `drawFrame`) :
1. Chaque joueur = un simple cercle (rayon 13px actif/9px figurant), rempli
   de la couleur d'équipe, contour doré si actif.
2. Un numéro de maillot (texte) sous chaque cercle — aucune autre
   information affichée par joueur.
3. Aucune orientation/direction du corps du joueur (le cercle est
   symétrique, rien n'indique vers où le joueur "regarde" ou court).
4. Aucune ombre portée, aucun dégradé de profondeur.
5. Le ballon = un cercle blanc dont le rayon croît légèrement avec sa
   hauteur `z` — aucune traînée (trail), aucun flou de mouvement.
6. Aucune flèche/ligne de passe, aucune pastille de surbrillance sur le
   porteur du ballon au-delà du contour doré (partagé avec tout joueur actif,
   pas spécifique au porteur).
7. Aucune animation dédiée à un tir/une tête/un tacle — un tir est rendu
   par la même interpolation cercle-vers-cercle qu'une passe ou une marche.
8. Aucun texte/overlay contextuel pendant le jeu (le score/minute
   s'affichent en dehors du canvas de terrain, pas superposés au joueur).

Aucune solution proposée (hors périmètre de ce brief).

## Synthèse

Les 5 problèmes les plus graves, classés par impact visuel :

1. **Figurants quasi-immobiles sur toute la durée du clip (12/12 gabarits, 100% du temps).**
   Gabarits affectés : 12/12. Cause : `sequence_generator.py`
   (`_tactical_drift`, amplitude bornée à 5% du terrain max, souvent bien
   moins selon le poste) + `templates.py` (`build_from_template`, les
   coéquipiers non scriptés restent figés à `start_positions` avant même
   d'être convertis en background). Complexité : **moyen** (1-3 jours) —
   augmenter les bornes de `_tactical_drift` est un ajustement de
   constantes, mais un vrai mouvement continu (pas juste un point A vers un
   point B) demanderait plus de travail sur `BackgroundTrack`.

2. **Le tir ne modélise jamais la trajectoire du ballon vers le but.**
   Gabarits affectés : 12/12 (`ball_owner="scorer"` à la dernière keyframe
   dans les 12 gabarits). Cause : `templates.py` (conception de `Template`,
   `ANCHOR_SCORER` ancre sur la position de frappe `event.zone`, jamais sur
   le but) + `engine/narrative.py` (`event.zone` = position de tir, aucune
   donnée de trajectoire post-frappe). Complexité : **lourd** (>3 jours) —
   nécessite un nouveau concept (segment "ballon vers le but" après la
   frappe), potentiellement une extension du schéma `Template`/`Keyframe`.

3. **Gardien adverse jamais réactif au tir, sur 12/12 gabarits produisant un tir cadré.**
   Gabarits affectés : 12/12. Cause : `templates.py` (aucun rôle "gardien"
   dans les 12 `Template`) + `sequence_generator.py`
   (`enrich_with_background` traite le gardien comme n'importe quel
   adversaire "décor"). Directement lié au point 2 (sans trajectoire de tir
   vers le but, un gardien réactif n'a rien à quoi réagir). Complexité :
   **moyen** (1-3 jours) — ajouter un rôle "gardien" scripté suivrait le
   même patron que les rôles existants (`Role`/`RoleFrame`), sans changer le
   moteur générique.

4. **Vitesse de tir mesurée "mou" sur 3/12 gabarits (jusqu'à 1,46 m/s), durée du segment "tir" jusqu'à 5,6s sur 9/12.**
   Gabarits affectés : 3/12 directement "mou" (percee_individuelle,
   coup_franc, penalty), 9/12 avec un segment "shot" > 1,5s. Cause :
   `templates.py` (distances/durées de `Template`, symptôme mesurable direct
   du point 2 — sans lui, ces chiffres n'ont pas de sens physique de "tir").
   Complexité : **lourd** (>3 jours) — structurellement lié au point 2, pas
   isolément corrigeable sans le même travail de fond.

5. **32 transitions de vitesse sans rampe d'accélération (repli linéaire), sur 9/12 gabarits.**
   Gabarits affectés : 9/12 (tous sauf construction_placee, coup_franc,
   penalty). Cause : `animation/motion.py` (`_interpolate_segment`, repli
   quand la vitesse moyenne exigée dépasse 55% de `v_max`) — déclenché par
   les distances/durées définies dans `templates.py`. Complexité :
   **moyen** (1-3 jours) — le point de bascule est isolé dans `motion.py`,
   mais une correction durable implique aussi de retravailler les
   distances/durées des gabarits concernés (comme le point 4).

**Hypothèses du brief invalidées ou nuancées par la mesure :**
- "Figurants immobiles" (au sens strict, déplacement nul) : **faux** — le
  déplacement médian n'est jamais 0m, toujours borné par `_tactical_drift`
  (0,5-4,5m selon le poste/gabarit). "Quasi-immobiles" est le verdict
  correct sur 7/12 gabarits, jamais "immobiles" au sens strict.
- "Tirs mous" partout : **faux** — 2/12 gabarits (`une_deux`, `but_gag`)
  mesurent au contraire une vitesse "rapide" (21-27,5 m/s), par coïncidence
  géométrique (grande distance/segment court), pas par une frappe
  physiquement modélisée. Seuls 3/12 sont mesurablement "mou".
- "Gardien fantôme" : **confirmé et quantifié** — 0/12 gabarits n'ont de
  comportement de gardien dédié au tir, la cause racine se trouve autant
  dans l'absence de rôle "gardien" (templates.py) que dans l'absence de
  trajectoire de tir vers le but (point 2) à laquelle il pourrait réagir.
