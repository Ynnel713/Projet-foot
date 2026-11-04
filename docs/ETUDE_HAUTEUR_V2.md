# Étude — hauteur du ballon et caméra inclinée (2.5D) dans la V2

Étude seule, aucun code modifié (03/11/2026). Décisions prises avec le propriétaire en séance de questions ; les
constantes chiffrées ci-dessous sont des **propositions à valider** avant tout code (règle du projet).

## 1. Recommandation en bref

Le meilleur compromis : **le moteur V2 calcule la hauteur du ballon** (chute libre plus rebonds, formules simples, pas
de moteur 3D) et **l'écran V2 passe en caméra fixe légèrement inclinée, sans perspective**, qui projette chaque point
(x, y, hauteur) par une seule formule. Les joueurs restent à plat dans le moteur ; un saut est un événement que l'écran
dessine.

Pourquoi ce compromis :
- **Réalisme physique** : la hauteur décide qui peut toucher le ballon (pied, tête, mains), ce qui donne enfin un sens
  aux centres, lobes, dégagements et duels aériens. Sans hauteur dans le moteur, l'écran montrerait un ballon à 3 m
  qu'un joueur intercepte du pied.
- **Réalisme visuel** : avec la caméra inclinée, la hauteur se voit d'elle-même (le ballon monte à l'écran, son ombre
  reste au sol, la barre transversale est visible) sans coefficient de « remontée » choisi à la main.
- **Complexité** : trois formules (chute, rebond, projection), un champ de plus dans la trace, aucune physique verticale
  des joueurs, aucune bibliothèque 3D.
- **Performances** : 23 éléments à trier et à ombrer par image, négligeable ; la trace grossit seulement pendant les
  vols (mesure à faire, section 7).

## 2. Audit de l'existant

### V1 : la hauteur existe déjà
- `src/ligue1sim/animation/types.py` : `BallState` porte `z` (mètres au-dessus du sol) et `vz` (m/s).
- `src/ligue1sim/animation/ball.py` : passes lobées, tirs, centres, coups francs en cloche ; rebonds au sol et sur les
  montants, restitution 0,70 (49 % de la hauteur gardée), 15 % de vitesse horizontale perdue par rebond.
- `render/canvas.html` (~l. 717) : ballon remonté de `min(z, 4) × 0,5` m à l'écran, rayon × `1 + min(0,5 ; 0,15 z)`,
  ombre décalée de taille fixe.
- Fichiers protégés : **la V1 n'est pas concernée par l'étude**, elle sert de référence (lois de rebond).

### V2 : à plat par décision (D-V03)
- `docs/TRD_V2.md` D-V03 : « physique continue à plat (x/y), pas de hauteur de ballon pour l'instant ; duels aériens
  résolus par tirage pondéré », révisable.
- `v2engine/geometry.py` : géométrie 2D en mètres, sans hauteur.
- `v2engine/ball_state.py` : `mode` (`"sol"` / `"aérien"`) et `aerial_left_m` (distance encore à parcourir en l'air),
  ajoutés par le ticket `v2-collectif/29` (non commité à ce jour).
- `v2engine/match.py` :
  - l. ~198 : une passe jugée aérienne (`restart.is_aerial`) passe en mode aérien jusqu'à
    `AERIAL_LANDING_M = 3,0` m de sa cible ;
  - l. ~360 : tant que `aerial_left_m > 0`, **personne ne touche le ballon** ; ensuite retour au sol ;
  - freinage horizontal `BALL_FRICTION_PER_S = 0,6` (par seconde, exponentiel, `v2engine/possession.py`) ;
  - tir : l'issue est tirée au départ (`shooting.attempt_shot`), le but ne compte qu'à l'arrivée sur la ligne
    (`ball.shot_for`).
- `v2engine/trace.py` : `BallSnapshot(position, holder, mode, dead)` ; pas de tick moteur 0,1 s, **un enregistrement par
  seconde** (`record_every = 10`, `api/routers/v2.py` `_RECORD_EVERY`).
- Écran `ui/src/routes/V2Match.jsx` : SVG dont le viewBox est en mètres réels ; `interpolatedTick` interpole x/y en ligne
  droite entre deux enregistrements ; retournement du terrain par `<g transform="… scale(-1 1)">`.

### Constats de l'audit
1. **Échantillonnage trop grossier pour un vol** : un centre de 1,5 s n'a que deux points enregistrés ; interpolée en
   ligne droite, sa hauteur dessinerait un triangle.
2. **Affichage du mode aérien** : traité par le ticket `v2-correctifs-ecran/02` (en cours dans l'arbre de travail :
   ombre, ballon grossi et décalé de 1 m, mode gardé par l'interpolation). Pendant la séance, `V2Match.jsx` est
   momentanément revenu à l'état du dernier commit puis a retrouvé ces modifications : travail d'une autre session sur
   le même fichier, pas de perte constatée.
3. Le mode aérien actuel est un **interrupteur** (intouchable puis touchable) : il ne distingue ni hauteur de tête, ni
   ballon qui passe au-dessus d'un défenseur puis redescend, ni rebond.

## 3. Composants concernés

| Composant | Changement | Ticket |
|---|---|---|
| `ui/src/routes/V2Match.jsx` (terrain, joueurs, ballon, noms, flèches d'intention) | projection unique, ombres, tri par profondeur, buts en hauteur | 01 |
| `v2engine/ball_state.py` | `z`, `vz` ; `aerial_left_m` remplacé | 02 |
| `v2engine/match.py` (`_step_ball`, départ de passe et de tir) | chute libre, rebonds, mode calculé depuis `z` | 02 |
| `v2engine/restart.py` (`is_aerial`, `AERIAL_LANDING_M`) | choix de la vitesse verticale au départ | 02 |
| `v2engine/trace.py`, `api/serializers.py`, `api/schemas.py` | `z` dans `BallSnapshot`, points intermédiaires pendant un vol | 02 |
| `v2engine/match.py` (contact sur le trajet, réception) | tranches de hauteur par joueur | 03 |
| duel aérien, saut | joueurs éligibles par hauteur et temps, événement « saut » | `v2-attributs-restants/01` (complété) |
| `docs/TRD_V2.md`, `docs/PLAN_V2.md` | révision de D-V03 | à la validation de l'étude |

Hors du champ : V1 (moteur, `render/canvas.html`), `PitchField.jsx` (écrans V1), Streamlit.

## 4. Faisabilité et difficultés

Faisable sans changer d'architecture : le moteur reste à 0,1 s, la trace reste « calculée puis rejouée » (D-V04).

Difficultés identifiées :
- **Lier la hauteur au freinage horizontal.** Pour qu'une passe lobée retombe au bon endroit, la durée de vol `T` se
  déduit de la distance `d` et de la vitesse `v0` avec le freinage exponentiel (λ = −ln 0,6) :
  `T = −ln(1 − d·λ / v0) / λ` (impossible si `d·λ ≥ v0` : la passe n'arrive pas, à traiter), puis `vz0 = g·T / 2`.
- **Pas de temps de 0,1 s** : une intégration explicite simple sous-estime légèrement le point le plus haut. Utiliser la
  forme exacte sur le pas (`z += vz·dt − g·dt²/2`, `vz −= g·dt`), exacte pour la gravité seule.
- **Rebond en cours de pas** : couper le pas à l'instant d'impact (racine de l'équation du second degré) pour ne pas
  rater un rebond ou faire passer le ballon sous le sol.
- **Tir et barre** : la trajectoire doit respecter l'issue déjà tirée par le calcul de tir (cadré, à côté, au-dessus) :
  choisir `vz0` pour que la hauteur à la ligne de but soit sous 2,44 m (cadré) ou au-dessus (« au-dessus »).
- **Écran** : tout ce qui est posé sur le terrain doit passer par la projection (noms, flèches, sélection au clic) ; un
  oubli donne un élément décalé.

## 5. Architecture cible

### Moteur (source unique de la hauteur)
- `BallState` : `z` (m), `vz` (m/s). Au départ d'un ballon aérien, le moteur fixe `vz0` (section 4).
- `_step_ball` : x/y comme aujourd'hui ; z en chute libre exacte ; à l'impact, `vz ← −e·vz` (e = 0,70) et vitesse
  horizontale × 0,85 (valeurs V1) ; sous un seuil de `vz` le ballon roule (`z = 0`).
- `mode` **calculé** : `"aérien"` si `z` dépasse la hauteur du pied (seuil à proposer), `"sol"` sinon. Garde le format
  de l'API et du ticket 29.
- Interception (ticket 03) : un joueur peut jouer le ballon s'il l'atteint dans une tranche de hauteur qui dépend de sa
  taille : pied, corps (contrôle), tête (jusqu'à taille + détente selon Jumping Reach), mains (gardien dans sa surface).
- Joueurs : toujours à plat. Un duel aérien émet un événement « saut » (joueur, instant, hauteur de pointe) ; le
  tirage pondéré du ticket `v2-attributs-restants/01` ne réunit que les joueurs éligibles.

### Trace
- `BallSnapshot.z` à chaque enregistrement.
- Pendant un vol, le ballon est aussi enregistré à chaque tick moteur (0,1 s) : liste de points `(x, y, z)` attachée à
  l'enregistrement d'une seconde ; l'écran interpole entre ces points. Aucun calcul physique refait dans le navigateur.

### Écran V2
- Une fonction `project(x, y, z)` : `sx = x`, `sy = y·cos α − z·sin α` (caméra inclinée vers la tribune opposée, sans
  perspective). Le retournement du terrain (miroir horizontal) reste compatible.
- Ordre de dessin : pelouse et lignes → ombres → joueurs triés par `y` (fond d'abord) → buts (poteaux, barre en hauteur)
  → ballon → joueurs en saut → noms.
- Joueurs : vrais cercles (pas d'ovales), ombre ovale au sol ; en saut, rond remonté de `h·sin α`, ombre au sol.
- Ballon : position projetée ; rayon × `1 + min(k_max, k·z)` ; ombre au point `(x, y, 0)`, plus petite et plus pâle
  quand `z` monte.

### Constantes à valider (propositions)
| Constante | Proposition | Justification |
|---|---|---|
| Angle de caméra α (depuis la verticale) | 25° | terrain écrasé de 9 % (cos 25° ≈ 0,91), un ballon à 10 m monte de 4,2 m à l'écran |
| Grossissement du ballon | +5 % par mètre, plafond +40 % | lisible sans paraître « près de la caméra » |
| Ombre du ballon | rayon × `max(0,5 ; 1 − 0,05 z)`, opacité 0,30 → 0,10 à 10 m | repère de hauteur visible |
| Restitution, freinage par rebond | 0,70 ; 15 % | repris de la V1, déjà validés |
| g | 9,81 m/s² | physique |
| Hauteur de barre | 2,44 m | Lois du jeu |
| Tranches de hauteur (pied, corps, tête, mains) | à proposer au ticket 03, en fonction de la taille | à sourcer |

## 6. Risques de régression

| Risque | Gravité | Parade |
|---|---|---|
| Les interceptions changent (plus ou moins de ballons coupés) → possession, buts, passes réussies bougent | forte | ticket 03 séparé du 02 ; mesure sur 50 matchs avant/après ; tout avant la calibration 22 |
| Passe lobée qui ne retombe pas au bon endroit (freinage) | moyenne | test : point de chute à ± 1 m de la cible |
| Ballon sous le sol ou rebond raté au pas de 0,1 s | moyenne | test : `z ≥ 0` sur tous les ticks de 50 matchs |
| Tir annoncé cadré qui passe au-dessus à l'écran | moyenne | test de cohérence issue ↔ hauteur à la ligne |
| Trace plus lourde, rejeu en direct ralenti | faible à moyenne | mesure du poids par match ; points intermédiaires seulement en vol |
| Écran : élément non projeté (nom, flèche, clic) décalé | faible | une seule fonction de projection, revue de tous les éléments du SVG |
| Lisibilité tactique réduite par l'inclinaison | faible | pas de perspective, angle modéré réglable, contrôle à l'écran par le propriétaire |
| Déterminisme | faible | aucun hasard ajouté : `vz0` se déduit de la passe |
| V1 touchée | nulle | aucun fichier V1 dans le périmètre |

## 7. Tickets proposés (brouillons, chantier `.scratch/v2-hauteur-ballon/`)

Ordre : **01 tout de suite** (écran seul, sans effet sur les résultats) ; **02 puis 03 juste avant `v2-collectif/32`**
(types de passes) ; `v2-attributs-restants/01` complété ensuite ; tout avant la calibration 22.

### 01 — Caméra inclinée (écran V2)
Projection unique, terrain et lignes, buts en hauteur, ombre et tri par profondeur des joueurs ; ballon projeté avec son
mode actuel. Moteur non touché.
- [ ] Angle validé par le propriétaire ; terrain entier visible en largeur téléphone (375 px) et bureau
- [ ] Joueurs dessinés en cercles, triés par profondeur (le plus proche recouvre)
- [ ] Noms, flèches d'intention et sélection au clic alignés sur les joueurs, terrain retourné compris
- [ ] Fluidité inchangée (images par seconde mesurées avant/après sur téléphone)
- [ ] Suite V2 verte ; `npm run build` et `npm run lint` sans nouvelle erreur ; V1 inchangée

### 02 — Hauteur du ballon dans le moteur
`z`/`vz`, chute libre exacte, rebonds V1, `vz0` calculé pour retomber à la cible, tirs conformes à leur issue, mode
calculé depuis `z`, points intermédiaires pendant les vols ; affichage du ballon (taille, ombre). Révision de D-V03
écrite.
- [ ] Point le plus haut = `vz0² / 2g` (écart < 2 %), durée de vol = `2·vz0 / g` (écart < 1 tick)
- [ ] Point de chute d'une passe lobée à ± 1 m de la cible
- [ ] Rebond : hauteur suivante = 0,49 × la précédente (± 5 %)
- [ ] `z ≥ 0` sur tous les ticks de 50 matchs
- [ ] Tir cadré : hauteur à la ligne < 2,44 m ; « au-dessus » : > 2,44 m (100 % des tirs de 50 matchs)
- [ ] Mode affiché cohérent avec `z` à chaque enregistrement
- [ ] Ordres de grandeur réels (dégagement, centre, lob) dans les fourchettes sourcées, ou « non trouvé » noté
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée
- [ ] Poids de trace par match mesuré, avant/après
- [ ] Comportement sportif inchangé à ± bruit (les règles d'interception ne changent qu'au ticket 03)

### 03 — Interception selon la hauteur
Tranches pied / corps / tête / mains par joueur selon sa taille, à la place des deux règles fondées sur le mode.
- [ ] Constantes des tranches proposées et validées avant le code
- [ ] Scènes fixes : un ballon à 2,5 m passe au-dessus d'un défenseur de 1,70 m et est repris par un joueur de 1,90 m
  sauteur ; un gardien le capte dans sa surface
- [ ] Mesure sur 50 matchs avant/après (interceptions, possession, passes réussies, buts), écarts expliqués
- [ ] Suite V2 verte ; V1 inchangée

### `v2-attributs-restants/01` complété
Duel aérien entre les seuls joueurs capables d'atteindre le ballon à temps (hauteur et instant) ; événement « saut »
dans la trace, dessiné à l'écran (rond remonté, ombre au sol). Le reste du ticket inchangé.

## 8. Tests de validation du réalisme

- **Mathématiques** : point le plus haut, durée de vol, chute exacte sur un pas, rebond (rapport 0,49), arrêt du rebond,
  point de chute avec freinage. Tests unitaires purs, sans match.
- **Ordres de grandeur réels**, à sourcer (mention « non trouvé » sinon, jamais de chiffre inventé) :
  - hauteur et durée de vol d'un dégagement de gardien ;
  - hauteur et durée d'un centre, d'une passe lobée, d'un lob sur le gardien ;
  - hauteur de contact d'une tête selon la taille et la détente ;
  - portée d'un gardien bras levés et en extension.
- **Cohérence moteur ↔ écran** : mode calculé depuis `z`, issue de tir ↔ hauteur à la ligne, point de chute ↔
  interception.
- **Déterminisme** : empreintes identiques sur deux exécutions à graine fixée.
- **Non-régression** : suite complète (`PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider`), compte comparé à
  l'attendu ; V1 inchangée ; `scripts/measure_v2.py` et `scripts/v2_indicators.py` avant/après sur 50 matchs.
- **Performance** : images par seconde de l'écran V2 sur téléphone, poids de la trace par match, durée de calcul d'un
  match.
- **Contrôle à l'écran** (propriétaire, grille `docs/GRILLE_RELECTURE_V2.md`) : lisibilité tactique, centres et
  dégagements qui « se voient », tirs au-dessus de la barre.

## 9. Hors périmètre (réexaminable)

Perspective avec effet de fuite, caméra mobile ou zoom, effet qui fait dévier le ballon, vent, rotation visible du
ballon, variations de taille des joueurs, postures ou animations expressives, physique verticale des joueurs, toute
modification de la V1.
