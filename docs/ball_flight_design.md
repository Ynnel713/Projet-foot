# Design — vol du ballon après la frappe (`ball_flight`)

Document uniquement, aucun code. Suite de l'audit de réalisme (commit
`bb6fcaa`) : sur 12/12 gabarits, la dernière keyframe a `ball_owner="scorer"`
— le ballon ne quitte jamais le pied du tireur, aucune trajectoire vers la
cage n'est modélisée. Ce document spécifie le concept qui corrige ça.

## 1.1 — Le concept `ball_flight`

Un `ball_flight` est le segment qui **suit immédiatement** le dernier
segment portant un `ball_owner` non-`None` (aujourd'hui : le segment tagué
`"shot"`, `"deflect"` pour `corner`, ou l'équivalent header/frappe de chaque
gabarit). Pendant ce segment :

- **Position explicite, pas dérivée d'un porteur.** Contrairement à tous les
  segments actuels (où la position du ballon = position d'un rôle tant qu'un
  `ball_owner` est défini), le `ball_flight` a sa propre trajectoire
  `(x, y, z)` indépendante de tout joueur. `ball_owner=None` sur sa keyframe
  de départ (personne ne "possède" un ballon en vol) et sur son arrivée
  (personne ne possède un ballon dans les filets/hors du terrain), **sauf**
  pour l'issue "arrêt", où l'arrivée est possédée par le gardien (voir 1.4 —
  nécessite que le gardien soit identifiable, ce qui n'est pas garanti
  aujourd'hui, voir section Escalade).
- **Durée propre**, distincte des durées fixes des autres segments d'un
  gabarit. Elle ne peut PAS être une constante statique par gabarit comme
  les segments existants (`Template.duration` fixe) : elle dépend de la
  distance réelle entre le point de départ (position du tireur à l'instant
  de la frappe) et le point cible (dérivé de l'issue, donc de l'`event`
  précis, pas du gabarit seul) — deux occasions du même gabarit avec des
  `zone`/`outcome` différents ont des distances de vol différentes.
  `duration_flight = distance_m / vitesse_cible_m_s`, avec
  `vitesse_cible_m_s` tirée dans l'intervalle réaliste `[15, 35]` m/s (Tâche
  2.7 du brief), déterministe (seedée par `event_ref`, même principe que
  `ball._deterministic_unit`).
- **Position de départ** : là où se trouve le tireur à l'instant de la
  frappe — c'est-à-dire exactement l'ANCIEN point d'arrivée du segment
  `"shot"` actuel (`event.zone`, la position de tir). Aucun changement à ce
  point : il devient le point de DÉPART du vol plutôt que le point final de
  la séquence.
- **Position d'arrivée** : dérivée de l'issue (voir 1.2).
- **Courbure** : si `spin ≠ 0` sur la keyframe de départ du vol, la courbure
  de Magnus déjà implémentée dans `ball._behavior_shot` s'applique TELLE
  QUELLE (même formule, `a = _MAGNUS_K · spin · v`) — le vol réutilise le
  comportement `"shot"` existant, pas un nouveau modèle physique. Seul
  `decalage_enroulee` pose aujourd'hui un `spin` non nul (50 rad/s) ; les 11
  autres gabarits produisent un vol rectiligne, comme leur segment "shot"
  actuel.

**Ce n'est PAS un nouveau comportement physique dans `ball.py`** — voir 1.3 :
`_behavior_shot` gère déjà exactement ce cas de figure (ligne droite +
Magnus + hauteur croissante avec la distance) ; il suffit de lui donner le
bon `start`/`end`/`duration` via une keyframe supplémentaire.

## 1.2 — Points cibles par issue

Référentiel : `x, y` normalisés `[0, 1]` (`PITCH_LENGTH_M=105`,
`PITCH_WIDTH_M=68`, voir `pitch_geometry.py`), `z` en MÈTRES (convention
`BallState.z` existante). But adverse : ligne à `x=1.0`, centré `y=0.5`,
largeur réglementaire 7,32 m (`±3,66m` → `y ∈ [0.4462, 0.5538]`), hauteur
réglementaire 2,44 m.

**Important — pas de `Zone` (grille `GRID_COLUMNS×GRID_ROWS`)** : une case
de la grille existante fait ~8,75 m de large (105/12) — plus large que le
but entier (7,32 m). La grille `Zone` est trop grossière pour ce besoin ; le
point cible doit être un `(x, y, z)` flottant direct, pas une `Zone`.

| Issue | x | y | z (m) | Commentaire |
|---|---|---|---|---|
| `but` | `[1.00, 1.02]` | `[0.4462, 0.5538]` | `[0.0, 2.40]` | Dans la cage, légèrement derrière la ligne (profondeur de filet ≈1-2m) — volontairement hors `[0,1]`, le filet est physiquement hors du terrain. Marge de 4cm sous la barre (2,44m) pour rester "clairement" un but à l'œil. |
| `arret` | `[0.98, 1.00]` | `[0.47, 0.53]` | `[0.0, 2.0]` | Ballon stoppé AVANT la ligne (jamais au-delà), bande centrale resserrée ("position médiane" du gardien, brief). Hauteur large : un arrêt peut être bas ou haut. |
| `poteau` | `x=1.00±0.005` | `0.4462±0.005` OU `0.5538±0.005` (gauche/droite, déterministe par `event_ref`) | `[0.0, 2.2]` | Exactement sur le montant, un des deux poteaux tiré déterministe. |
| `barre` | `x=1.00±0.005` | `[0.4462, 0.5538]` | `[2.35, 2.44]` | Sur la barre transversale, n'importe où sur la largeur du but. |
| `hors_cadre` | `[0.97, 1.03]` | `y < 0.40 ou y > 0.60` | `[0.0, 3.5]` | Nettement à côté (marge 0,03 au-delà des poteaux) ou au-dessus (z jusqu'à 3,5m, "envoyé dans les tribunes"). |
| `tacle` / `degagement` | — | — | — | **Pas de `ball_flight`** — l'action est interrompue AVANT le tir (le défenseur intervient avant/pendant la frappe), voir 1.4. |

`poteau`/`barre` : narrative.py distingue déjà ces deux issues
(`_MISSED_PENALTY_OUTCOMES` contient les deux, `_NON_GOAL_OUTCOMES` ne
contient que `"poteau"` — pas de `"barre"` hors penalty aujourd'hui, à
confirmer si un futur brief l'ajoute aux occasions génériques).

**Zone d'ombre du brief, signalée plutôt que tranchée arbitrairement** : les
puces "Corner → point de chute dans la surface" et "Centre → point de chute
dans la surface" du brief ne sont pas des ISSUES au sens de
`NarrativeEvent.outcome` (qui vaut `but`/`arret`/`hors_cadre`/`tacle`/
`degagement`/`poteau`/`barre`) — ce sont des types de LIVRAISON
(corner/centre) déjà modélisés par le comportement `cross`/`deflect`
existant dans `ball.py`, indépendant du `ball_flight` final. Interprétation
retenue ici : ces deux puces décrivent la phase de CENTRE/CORNER déjà
existante (`corner`, `debordement_centre_tete`), pas un cas à part du
`ball_flight` — le `ball_flight` de ces deux gabarits suit la MÊME table
issue→cible ci-dessus (le header final reste un tir vers le but, avec la
même issue `but`/`arret`/`poteau`/`hors_cadre`). **À confirmer avec le
propriétaire** si cette lecture n'est pas celle voulue.

## 1.3 — Impact sur `Template`/`Keyframe`

**Aucun nouveau champ sur `Keyframe`/`BallState`** (`animation/types.py`
inchangé) : `BallState` a déjà `x`/`y`/`z`/`spin`/`owner_id` — un point
cible calculé est juste une nouvelle valeur pour des champs qui existent
déjà. Le `ball_flight` est une keyframe ORDINAIRE ajoutée à la fin de la
séquence, avec `physics_tag="shot"` explicite (pour forcer le comportement
`_behavior_shot`/Magnus, voir plus bas) et un nouveau `t` calculé.

**`Template` a besoin d'un nouveau champ** (le seul changement de schéma
proposé) :
```python
has_ball_flight: bool = False  # ce gabarit se termine par un tir/tête vers le but
```
Suffit à distinguer les gabarits concernés (1.4) sans dupliquer la logique
de calcul du vol (qui est GÉNÉRIQUE, dans `build_from_template`, pas
répétée par gabarit) — pas besoin d'un champ par issue : la cible dépend de
l'ÉVÉNEMENT (issue), pas du gabarit, donc elle est calculée dans
`build_from_template` à partir de l'issue transmise (voir Escalade), pas
stockée dans `Template`.

**`Sequence.duration`** : aujourd'hui `template.duration` fixe, deviendrait
`template.duration + duration_flight` (calculée dynamiquement, voir 1.1) —
changement de VALEUR dans `build_from_template`, pas de schéma
(`Sequence.duration` reste un simple `float`).

**Pourquoi pas un nouveau type de keyframe dédié** : `Keyframe` porte déjà
`physics_tag` pour distinguer le COMPORTEMENT d'un segment (`shot`/
`pass_ground`/`cross`/`deflect`) — c'est exactement le mécanisme existant
pour "ce segment se comporte différemment", pas besoin d'un concept
parallèle. Un `ball_flight` est un segment `physics_tag="shot"` comme un
autre, juste positionné après la fin actuelle du gabarit plutôt qu'avant.

**`ball.py` : aucun changement de code nécessaire.** `_behavior_shot` gère
déjà ligne droite + Magnus + hauteur croissante avec la distance — les
constantes existantes (`_SHOT_STRAIGHT_MAX_DIST_M=11`,
`_SHOT_AIRBORNE_MIN_DIST_M=16`, `_SHOT_HEIGHT_FAR_M=0.8` à 40m) restent
telles quelles, dans le même ordre de grandeur que les distances de vol
réelles (4 à 39m selon `_GABARIT_BASE_ZONE`, cohérent avec les cas déjà
couverts). `ball_state_at` n'a pas besoin d'un nouveau tag ni d'une nouvelle
branche : `physics_tag="shot"` explicite sur la keyframe de départ du vol
suffit (`_resolve_physics_tag` priorise déjà le tag explicite sur
l'inférence par `owner_id`/dernier-segment). **Signature de `ball_state_at`
inchangée.**

## 1.4 — Impact sur les 12 gabarits

| Gabarit | `ball_flight` | Justification |
|---|---|---|
| contre_attaque | présent | tir de conclusion |
| construction_placee | présent | tir de conclusion |
| debordement_centre_tete | présent | tête au but |
| percee_individuelle | présent | tir de conclusion |
| une_deux | présent | dernier tag = `"tir"`, `physics_tags=((0.5,"shot"))` — **contrairement à l'hypothèse du brief**, une_deux se conclut bien par un tir direct (vérifié dans `templates.py`, pas supposé) |
| coup_franc | présent | frappe directe |
| corner | présent | tête au but (le vol suit le header, pas le centre lui-même — le centre garde son comportement `cross`/`deflect` actuel) |
| profondeur_1v1 | présent | tir de conclusion du 1v1 |
| recuperation_haute | présent | tir de conclusion |
| decalage_enroulee | présent | tir enroulé — SEUL gabarit avec `spin≠0`, cas de test de la courbure Magnus conservée |
| penalty | présent | tir de penalty |
| but_gag | présent | déviation finale au but |

**Les 12/12 gabarits sont concernés** — aucun n'en est structurellement
dispensé (chacun se termine par un rôle qui frappe/dévie vers le but). La
distinction pertinente n'est pas gabarit-par-gabarit mais **issue-par-issue**
(voir 1.2) : `tacle`/`degagement` interrompent l'action avant le tir, donc
n'importe QUEL gabarit tiré avec cette issue n'a PAS de `ball_flight` — la
condition est sur `NarrativeEvent.outcome`, pas sur le nom du gabarit.

## 1.5 — Non inclus

- **Gardien** : ce brief ne rend PAS le gardien réactif au vol (pas de rôle
  scripté, pas de saut/plongeon) — l'audit de réalisme l'a identifié comme
  un problème séparé (#3), hors périmètre ici. Conséquence directe pour
  l'issue `arret` : la cible existe (voir 1.2), mais **aucun joueur ne s'y
  déplace pour "faire" l'arrêt** — le ballon s'arrête net à la cible, sans
  mouvement de gardien correspondant. Documenté comme limite connue, pas
  corrigé.
- **Figurants** : aucun changement à `_tactical_drift`/`enrich_with_background`.
- **Séquencement** : aucun changement aux durées/tags des segments EXISTANTS
  (approche, passe, centre...) — seul un nouveau segment est ajouté À LA
  SUITE, les 9/12 gabarits avec un segment "shot" > 1,5s (identifiés dans
  l'audit) ne sont pas raccourcis ici.
- **Rendu visuel** (`canvas.html`) : explicitement hors périmètre par le
  brief — un ballon qui sort de `[0,1]` en x (issue `but`) n'aura pas de
  traitement visuel dédié (il sortira simplement du cadre du canvas actuel,
  comportement par défaut de `toPx`, non vérifié ici).

## Escalade

**Un point bloquant, à valider avant toute Tâche 2.**

Le calcul de la cible (1.2) dépend de `NarrativeEvent.outcome`
(`but`/`arret`/`hors_cadre`/`tacle`/`degagement`/`poteau`/`barre`) — cette
donnée existe dans `engine/narrative.py` (`NarrativeEvent.outcome`, ligne
277) mais n'atteint JAMAIS `templates.build_from_template` aujourd'hui : la
`GoalEvent` construite et transmise par `narrative_player.py::_build_clip_frames`
(`ligue1sim.events.GoalEvent`, ligne 219) ne porte **aucun champ outcome** —
elle a été conçue pour représenter un but RÉEL (toujours "but" implicite
dans le moteur de résultats), jamais réutilisée avec un outcome différent.

Faire parvenir l'issue jusqu'à `build_from_template` nécessite l'une des
deux options suivantes, **toutes deux interdites explicitement par ce
brief** :

1. Ajouter un champ `outcome` à `ligue1sim.events.GoalEvent` — ce module
   est le moteur de résultats (génération réelle des buts/cartons/
   remplacements d'un match simulé), explicitement hors périmètre
   ("Aucun changement au moteur de résultats").
2. Modifier `narrative_player.py::_build_clip_frames` pour transmettre
   `event.outcome` (sous quelque forme que ce soit) au constructeur de
   `GoalEvent` ou à `BUILDERS[gabarit]` — explicitement interdit deux fois
   dans ce brief ("Aucun changement... à narrative_player.py").

Aucune des deux n'est un contournement mineur : la donnée dont ce brief a
absolument besoin (l'issue de l'action) n'a structurellement aucun chemin
pour atteindre le code qu'il autorise à modifier (`templates.py`, et
marginalement `ball.py`), sans toucher l'un des deux fichiers protégés.
Ceci dépasse à la fois le seuil "plus de 3 fichiers" (2 fichiers protégés +
`templates.py` + potentiellement `docs/`) et touche directement un fichier
nommément interdit — **remonté avant d'écrire la Tâche 2**, conformément à
la règle d'escalade du brief.

Aucune tentative de contournement silencieux n'a été faite (ex. encoder
l'issue dans `event.zone` par convention, ou deviner l'issue depuis
`event.involved_players`) — cela aurait été une correction masquée, pas une
solution.

## Dette connue

**Résidu Magnus sur les bords du segment `ball_flight`** (découvert le
24/09/2026, brief "ball_flight duration uses 3D distance") : la Tâche 1 de
ce brief a corrigé la durée du vol (distance 2D → 3D), mais un test plus
fin (échantillonnage 30fps sur 100 matchs simulés, 1251 vols) a révélé un
second problème distinct, non corrigé (hors périmètre de cette Tâche,
"rien d'autre") : `decalage_enroulee` (seul gabarit avec `spin != 0`) peut
dépasser 35 m/s en vitesse 3D **instantanée** près des bords du segment
(`_hat_derivative(s)`, la contribution de vitesse de la courbure Magnus
dans `_behavior_shot`, culmine à `s→0`/`s→1` et s'additionne à la vitesse
de base) — 35/1251 vols (2,8%), max observé 35,51 m/s (35,0 visé, écart
1,5%, invisible à l'œil). La vitesse **moyenne** du vol reste correcte
(`tests/test_ball.py::TestBallSpeedRealisticOnFlight`, vert). Documenté
aussi en tête de `ball.py`. Piste : amortir la composante Magnus en
entrée/sortie du segment `ball_flight`. À traiter dans le chantier des
déclinaisons multiples de `decalage_enroulee` prévu séparément.
