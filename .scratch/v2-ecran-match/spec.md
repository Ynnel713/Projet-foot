# Chantier : refonte UX/UI de l'écran Match (V2, matchs amicaux)

**Status :** validé par le propriétaire (07/11/2026, « Ok ») ; recommandations du §4 retenues (bancs resserrés, analyse en tiroir, pression territoriale) ; constantes et définitions de statistiques proposées au début de chaque ticket. Tickets dans `issues/`.
Tickets créés le 07/11/2026 dans `issues/` (EM-D1 et EM-D2 = fichiers 17 et 18).

Écran concerné : `ui/src/routes/V2Match.jsx` (route `/v2`), seul écran qui porte à la fois vitesses x1 à x8, pause, momentum,
compositions et caméra 2.5D. L'écran V1 (`PitchView`, `render/canvas.html`, protégé) n'est pas concerné.

---

## 1. Audit de l'existant

### 1.1 Architecture frontend

- Un seul composant de 840 lignes (`V2Match.jsx`) mélange : choix des clubs, appels API et sondage (1 s), boucle de
  lecture (`requestAnimationFrame`), ralenti des buts, bandeau de mi-temps, calcul du score révélé, et tout le rendu
  (en-tête, compositions, momentum, terrain SVG, bancs, panneau d'intention).
- Chaque image (60 fois par seconde) appelle `setSeconds` : **tout** l'écran se redessine, y compris compositions et
  momentum, qui ne changent presque jamais. Aucun `memo`.
- Rendu du terrain : un SVG en mètres réels + `project(x, y, z)` (`utils/v2Projection.js`), caméra inclinée de 25°
  **sans perspective** (validée le 04/11/2026, ticket `v2-hauteur-ballon/01`). **Écart documenté du 09/11/2026** :
  à la réouverture du ticket `v2-hauteur-ballon/01`, l'angle est passé de 25° à **35°** (toujours sans point de fuite),
  écart accepté par le propriétaire par rapport à la décision du 07/11/2026 ; ce n'est pas une régression. Le propriétaire
  a ordonné de ne plus modifier l'angle. Les « points d'avant » des tests de projection (EM-05) sont ceux de 35°. Une seule projection pour le sol, les
  joueurs, le ballon, les bancs. Cette projection est le contrat avec le moteur et les évolutions 2.5D (`02b`, `03`) :
  on n'y touche pas.
- Système de design existant : `docs/DESIGN.md` + tokens `@theme` dans `ui/src/index.css` (direction « la loge de
  presse, de nuit », Barlow Condensed pour scores et titres, IBM Plex Sans pour le texte, plancher 11 px, rayons 8/12 px,
  une couleur = un sens). L'écran V2 l'applique à moitié : texte aux jetons, mais couleurs d'équipe en dur.
- Composants réutilisables : `ClubBadge` (écusson, repli sur initiales colorées), `ClubLogo` (petit écusson),
  156 logos dans `ui/public/logos/clubs/` (`clubSlug`), tokens CSS, `lucide-react`, `framer-motion`.
- Environnement : PWA, `orientation: landscape` dans le manifeste → l'écran se pense **en paysage** (téléphone 844×390,
  tablette 1024×768, portable 1366×768, 1920×1080). Aucun lanceur de tests JavaScript installé (seulement `npm run build`
  et `npm run lint`) ; Node 26 est présent (`node --test` utilisable sans dépendance).

### 1.2 Flux de données moteur → écran

`POST /api/v2/matches/start` lance le calcul en tâche de fond ; l'écran lit `GET /api/v2/matches/{id}?from_tick=N` chaque
seconde (images à 1 s de match d'écart, interpolées côté écran) et `GET /api/v2/lineup?club=…`. Le calcul avance plus
vite que la lecture : **l'écran reçoit toujours du futur** (buts, tirs…) et ne doit jamais l'afficher avant que la lecture
l'atteigne. Règle à garder partout : tout élément affiché est filtré sur `seen` (instant le plus avancé déjà vu).

| Donnée | Dans la trace du moteur | Envoyée à l'écran | Remarque |
|---|---|---|---|
| Positions joueurs, ballon (porteur, mode, mort) | oui | oui, en continu | |
| Buts (minute, équipe) | oui | oui, en continu | **pas de buteur** |
| Hors-jeux (minute, équipe, joueur) | oui | oui, en continu | |
| Situations d'équipe, mi-temps, temps additionnel | oui | oui | |
| Tirs (joueur, lieu, qualité, issue, origine) | oui (`trace.shots`) | **non** | remplie en direct comme les buts |
| Fautes (gravité, issue) | oui (`trace.fouls`) | **non** | |
| Remises en jeu dont corners | oui (`trace.restarts`) | **non** | |
| Cartons (jaune, rouge) | **non** : le ticket `v2-attributs-restants/09a` n'est pas fait | non | un carton rouge n'existe pas encore dans la V2 |
| Remplacements | non (ticket `v2-coach-et-gestion-de-match/05`) | non | la composition est fixe |
| Momentum | **aucun concept dans le moteur** | calculé côté écran | voir 1.3 |
| Couleurs des clubs | `ligue1sim/kits.py` (`primary`, `secondary`, motif) | **non** pour la V2 | `/api/clubs` ne les donne pas ; `RosterOut.color` existe côté V1 |

### 1.3 Momentum actuel : ce qu'il vaut

Calcul (`momentumByMinute`) : pour chaque image, `dx·|dx|` où `dx` est la position du ballon dans la longueur
(−1 à +1), plus ±0,15 à l'équipe qui tient le ballon ; moyenne par minute ; échelle recalculée sur les seules minutes déjà
jouées.

- Données **réelles** (positions du moteur), rien d'inventé : c'est une mesure de **pression territoriale + possession**.
- Limites : (1) ce n'est pas du « momentum » au sens des tirs et occasions (les tirs ne sont pas envoyés) ; (2) l'échelle
  s'auto-ajuste, donc les barres anciennes changent de hauteur quand une grosse minute arrive ; (3) la minute en cours
  moyenne des images reçues mais pas encore vues (réserve A1 du ticket `v2-correctifs-ecran/03`, correctif promis au
  ticket 02) ; (4) un ballon aérien ou mort (`holder` nul) ne compte que pour le territoire.
- Verdict : **fiable comme « pression territoriale »**, à condition de la nommer ainsi, de fixer l'échelle et de ne
  moyenner que les images vues. Pour un vrai momentum (danger créé), il faut les tirs → ticket de données D2.

### 1.4 Couleurs des clubs

Aujourd'hui : bleu `#4f8ef7` pour le domicile et or `#e0b84a` pour l'extérieur, **codés en dur à huit endroits** de
`V2Match.jsx` ; aucun lien avec les clubs. Les kits existent côté serveur (`primary`, `secondary`) pour environ 100 clubs ;
les autres tombent sur un gris `#6b7280`. Il n'existe aucune détection de couleurs proches.

### 1.5 Performance (mesure du 07/11/2026)

Serveur de développement Vite, panneau de 1024×768, x8 : **médiane 50 ms par image (20 images/s)**, 243 nœuds SVG. Mesure
faite en mode développement (React non optimisé, panneau possiblement bridé) : à refaire sur `npm run build` avant tout
chiffre définitif. Dès maintenant : le point de départ est déjà sous 60 i/s, donc la refonte ne peut rien coûter de plus ;
objectif du chantier = **ne pas régresser**, et mémoïser les parties qui ne bougent pas.

### 1.6 Diagnostic de l'écran actuel (capture : état « avant », AEK Athens – Al-Ahli, 1re période, x1)

1. **Le terrain n'est pas le héros.** Autour des lignes (105×68 m) il y a 6 m de bord + 2 m de piste rouge + 7 m de zone de
   bancs : 13 % de la hauteur du dessin ne sert pas au jeu. S'y ajoutent l'en-tête global de l'application, une ligne de
   texte à 4 niveaux, le momentum, le panneau d'intention : le terrain occupe environ 40 % de la hauteur d'un écran 1024×768.
2. **Épaisse bordure rouge `#9c4a3c`** (piste) et zone grise des bancs : le terrain ressemble à un rectangle posé sur un
   fond noir, exactement ce que vous voulez éviter.
3. **Pas de HUD de retransmission.** Score en 16 px gras, sur une ligne de texte ; pas d'écusson, pas de nom de club mis en
   valeur ; lignes techniques (« transition défensive », « calcul 10' », hors-jeu en texte) qui ressemblent à du débogage.
4. **Commandes** minuscules (boutons de 28 px), état actif peu visible, aucun bouton statistiques.
5. **Compositions** : listes de 11 px, **masquées sous 1024 px** (`hidden lg:flex`) donc invisibles sur tablette et
   téléphone en paysage ; numéro, poste et nom sans hiérarchie ; titulaires et remplaçants peu distingués.
6. **Momentum** : bande de 110 px au plus, au-dessus du terrain (loin du lecteur de score), 90 barres, emoji ⚽ pour les
   buts, aucune chronologie lisible, aucun nom de buteur, pas de cartons.
7. **Joueurs** : ronds corrects mais plats, numéro blanc illisible sur le jaune, couleurs sans rapport avec les clubs.
8. **États** : mi-temps = bandeau noir plein écran ; but = rien (juste le score qui change) ; fin = une ligne de texte.
9. **Code** : 840 lignes, rendu intégral à chaque image, constantes de couleur dupliquées : toute refonte visuelle
   commence par un découpage.

---

## 2. Conception de la cible

### 2.1 Architecture visuelle (trois zones)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ←   [écusson] PARIS SG   2 : 1   OLYMPIQUE MARSEILLE [écusson]   ▸ Stats │  HUD  (≈ 72 px)
│                  63'  ·  2e période  ·  EN DIRECT      x1 x1.5 x2 x4 x8 ⏯ │
├────────────┬───────────────────────────────────────────┬─────────────────┤
│ COMPOSITION│                                           │   COMPOSITION   │
│ PSG  4-3-3 │            T E R R A I N  (2.5D)          │   OM  4-2-3-1   │  zone
│ ▌1 GK  …   │          grand, centré, sans cadre        │   1 GK  …       │  centrale
│ ▌2 DC  …   │                                           │   2 DC  …       │
│ Remplaçants│                                           │   Remplaçants   │
├────────────┴───────────────────────────────────────────┴─────────────────┤
│  momentum ▲ domicile / ▼ extérieur   0'        15'       45'       75' 90'│  zone basse
│  ██▆▅▃▂ ─────────────────────────────────────── ⚽ ───── ▌                │  (≈ 150 px)
│  ▂▃▅▆                                                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

Proportions estimées par la géométrie (à **vérifier sur le rendu réel**, ticket 04) : en 1280×720, en masquant l'en-tête
global, en resserrant la marge du terrain et en sortant les bancs du dessin, le terrain passe d'environ 610×415 px à
**environ 770×465 px** (+ 50 % de surface). Colonnes de compositions : 200 à 230 px.

Trois solutions comparées :

| | A. Colonnes latérales (votre demande) | B. Compositions en bandeaux sous le terrain | C. Terrain plein cadre, compositions en tiroirs |
|---|---|---|---|
| Terrain | grand | le plus large, mais écrasé en hauteur | maximum |
| Accès aux compositions | immédiat | immédiat mais illisible (22 cartes en ligne) | un geste de plus |
| Symétrie des équipes | naturelle (gauche/droite) | moyenne | oui |
| Paysage téléphone | à adapter | mauvais | bon |

**Recommandation : A**, avec repli par taille d'écran (≥ 1280 px : cartes complètes ; 960 à 1279 px : cartes compactes
numéro + nom, poste en pastille ; < 960 px, paysage téléphone : compositions en tiroirs ouverts par une languette de
chaque côté, terrain pleine largeur). C'est ce que vous avez demandé, et seule A reste lisible sur desktop et tablette.

### 2.2 Direction artistique : « la retransmission, de nuit »

On prolonge le design system existant plutôt qu'en créer un second (cohérence avec les lots 1 à 7 de la refonte).

- **Fond** : `bg #0B0F14` ; HUD et colonnes sur `surface #121821` (filet `line #232D3A`), sans ombre portée. Le terrain
  n'a plus de cadre : un **sol sombre** (`#0E141B`) prolonge le fond et une vignette très légère (≤ 8 % de luminosité)
  assombrit les bords du terrain pour le fondre dans l'interface. Pas d'effet lumineux.
- **Gazon** : bandes de tonte sobres `#24603A` / `#2A6B3F` (aujourd'hui `#2f7d32` / `#3a8f3c`, trop vives), lignes
  `rgba(255,255,255,0.85)` à 0,12 m (aujourd'hui 0,15 m), but et filets conservés. Profondeur : un seul dégradé vertical
  fonctionnel (côté lointain 6 % plus sombre) ; la perspective reste celle de `project()` (inclinaison de 35° depuis le 09/11/2026, écart documenté ci-dessus, sans point
  de fuite) pour que joueurs et lignes coïncident. Un vrai effet trapèze est exclu : il imposerait de changer la
  projection du moteur d'affichage, ce que vous interdisez (et la liste « hors périmètre » du chantier hauteur-ballon).
- **Typographie** : Barlow Condensed 700 pour le score (56 à 72 px sur bureau) et les noms de club (20 à 22 px, majuscules,
  espacement +0,04 em) ; Barlow Condensed 600 pour la minute (24 px) et les numéros de joueurs ; IBM Plex Sans pour les
  cartes et la timeline (13 px, plancher 11 px).
- **Couleurs d'équipe** : variables CSS `--team-home` / `--team-away` (+ `--team-home-ink` / `--team-away-ink`, couleur
  de texte lisible dessus), posées une fois à la racine de l'écran et lues par HUD, cartes, joueurs, momentum, timeline,
  statistiques. Plus aucune couleur d'équipe en dur.
- **Accents** : `accent #2F6FE4` pour l'état actif des commandes (une couleur = une action), `gold` réservé au résultat
  final, `loss/ev-red` pour le carton rouge, `live #2DD4BF` pour le badge EN DIRECT.
- **Mouvement** : 150 à 250 ms, `ease-out`, uniquement pour marquer un changement (score qui tombe, bandeau de but,
  tiroir), `prefers-reduced-motion` respecté.

#### Règle de couleur des joueurs

1. Domicile : couleur principale du maillot (`kits.primary`). Extérieur : sa principale aussi.
2. Distance entre les deux couleurs en CIELAB (ΔE 2000). Si elle est **sous un seuil** (proposition : 25), l'extérieur
   prend sa couleur secondaire si celle-ci passe le seuil face à la principale du domicile (et face au gazon).
3. Sinon, on garde la teinte de l'extérieur et on décale sa clarté jusqu'à passer le seuil (préserve l'identité).
4. En dernier recours : blanc cassé ou noir selon ce qui s'oppose le mieux.
5. Chaque couleur est aussi comparée au **gazon** (un club vert) et au **ballon blanc** ; un anneau clair ou sombre, choisi
   selon la luminance, garantit la lisibilité (noir sur gazon sombre, blanc sur club noir).
6. Couleur du numéro : blanc ou `#0B0F14`, celle qui donne le contraste le plus élevé (≥ 4,5:1), avec un liseré de la
   couleur opposée de 0,2 m.
7. Seuils et amplitudes = constantes produit : proposées avant le code (règle du projet).

#### Joueurs et ballon

Cercles de rayon 1,3 m (inchangé), remplissage de la couleur d'équipe avec un très léger relief (éclaircissement de 10 % en
haut à gauche), anneau fin (0,12 m), ombre ovale au sol déjà en place (opacité 0,25 : on ne la change que si le propriétaire
le demande, c'est une valeur validée). Ballon blanc à contour sombre, légèrement plus grand que l'actuel (0,4 → 0,5 m
proposé, constante à valider). Joueur sélectionné : anneau blanc (comportement actuel).

#### Compositions (cartes)

Ligne-carte de 36 px : `[numéro 22 px, pastille aux couleurs du club]  [poste 28 px, gris]  [nom, une ligne]`, liseré
gauche de 3 px à la couleur de l'équipe. En-tête de colonne : écusson 28 px, nom du club, formation, entraîneur. Deux
sections : « Titulaires » (11 cartes) et « Remplaçants » (cartes à 60 % d'opacité de texte, plus petites). Équipe de droite
en miroir (liseré à droite, numéro à droite). Aucune note, aucun attribut, aucune statistique individuelle.

#### Momentum et timeline (une seule frise)

Histogramme symétrique, une barre par minute, domicile au-dessus de l'axe et extérieur en dessous, couleurs
`--team-home` / `--team-away`. Largeur pleine de la zone basse (≈ 10 px par barre), hauteur de 150 px. Axe central fin ;
repères 15', 30', 45' (trait de mi-temps), 60', 75', 90'. Curseur de lecture. **Zone future vide** (ligne de base seule :
rien n'est révélé). Marqueurs d'événements posés sur l'axe, du côté de leur équipe : but = pastille ballon à la couleur
de l'équipe avec la minute ; carton rouge = rectangle rouge (emplacement prévu, en attente du ticket 09a). Survol ou toucher :
info-bulle « 23' · Nom du buteur » (dès que la donnée existe). Échelle **fixe** (pas d'auto-ajustement) et nom honnête :
« Pression territoriale » tant que le moteur ne fournit pas le danger créé.

#### Statistiques (accès secondaire)

Bouton « Stats » dans le HUD → tiroir de 340 px qui recouvre la colonne de droite (le HUD, le terrain et la frise restent
visibles ; sur petit écran, feuille depuis le bas). Le match **continue** pendant l'ouverture (aucun changement de
comportement). Lignes symétriques : valeur domicile — barre — valeur extérieur, aux couleurs d'équipe. Contenu : possession,
tirs, tirs cadrés, corners, fautes, hors-jeu, cartons (quand 09a existera). Toutes les valeurs sont **filtrées sur le temps
lu** : jamais de futur.

#### Interactions

- Pause et reprise : bouton rond de 44 px, barre d'espace.
- Vitesses : groupe segmenté de 5 boutons (x1, x1.5, x2, x4, x8), actif plein `accent`, cible ≥ 40 px ; comportement
  inchangé (`SPEED_OPTIONS`, `DEFAULT_SPEED`).
- But : bandeau de 2 s sous le HUD « BUT · 23' · [équipe] » (buteur dès D1), score qui « tombe », puis ralenti existant
  signalé par un badge RALENTI à côté de la minute (le bouton « passer » conservé).
- Mi-temps : bandeau centré, plus discret (même durée 3 s), score, sans masque noir total.
- Fin : panneau de fin sur le terrain (score final, bouton « Statistiques », « Retour »).
- Toucher un joueur : conserve le comportement actuel (anneau) ; le panneau d'intention devient un tiroir « Analyse »
  (décision proposée, voir 4).

### 2.3 Composants à créer ou modifier

Nouveaux, dans `ui/src/components/match/` : `MatchHud`, `ScoreBlock`, `SpeedControls`, `ClubCrest` (ClubBadge + couleur
d'équipe), `LineupColumn` / `PlayerCard`, `PitchView2` (V2Pitch extrait), `PlayerMarker`, `MomentumTimeline`,
`EventMarker`, `StatsDrawer`, `MatchBanner` (but, mi-temps, fin), `AnalysisDrawer` ; utilitaires `utils/teamColors.js`
(règle de couleur), `utils/matchStats.js` (statistiques filtrées sur le temps lu), `utils/momentum.js` ; hook
`hooks/useMatchPlayback` (déplacement pur de la boucle existante, sans changer sa logique). À modifier : `V2Match.jsx`
(devient un assembleur), `AppShell.jsx` (masquer l'en-tête global sur `/v2`, comme sur la vue terrain), `index.css`
(ajout de jetons, aucune valeur existante modifiée), `api/routers/v2.py` (sérialisation seulement, voir 4).

### 2.4 Risques de régression

- Boucle de lecture, ralenti, mi-temps, score révélé : logique **déplacée mais jamais modifiée** (tickets 01 et suivants
  vérifient que le score, les minutes de but et la durée de lecture sont identiques avant/après sur une trace enregistrée).
- `AppShell` et `index.css` sont partagés par toute l'application : vérifier que les autres routes gardent leur en-tête.
- `project()` / `GROUND_MATRIX` : intouchables (contrat avec les tickets hauteur-ballon `02b` et `03`).
- Fluidité : mémoïsation à introduire sans changer le résultat ; mesure sur build de production avant/après.
- Aucun test JavaScript n'existe : les fonctions pures (couleurs, momentum, statistiques) sont testées avec `node --test`
  (natif, zéro dépendance) ; l'API avec `pytest` ; le visuel par captures reproductibles (ticket 00).

---

## 3. Backlog

Convention : estimation en travail effectif (analyse/développement/tests/intégration), temps machine à part ; confiance
entre parenthèses. Types : **V** refonte visuelle, **E** ergonomie, **S** structure sans effet visible, **D** données
(sérialisation de ce que la trace enregistre déjà, moteur non modifié). Identifiants provisoires `EM-NN` (écran match),
convertis en `NN-slug.md` après validation.

### EM-00 — Banc de rejeu d'une trace enregistrée (S, dev seulement) — 90 min (moyenne)
- **Objectif** : pouvoir atteindre n'importe quel état (but, mi-temps, fin, x8) en quelques secondes, de façon reproductible.
- **Problème** : un match demande environ 3 min de calcul et 11 min de lecture à x8 ; impossible de comparer avant/après ou
  de mesurer la fluidité proprement.
- **Résultat** : script qui enregistre une **vraie trace** du moteur (via l'API) dans `.scratch/v2-ecran-match/fixtures/`,
  et un mode de développement (`?fixture=<nom>`, absent du build de production) qui la rejoue à la place de l'API, avec un
  paramètre `?t=<minute>` pour partir d'un instant donné.
- **Périmètre** : lecture seule d'une trace réelle ; aucune donnée inventée ; aucune modification du moteur.
- **Composants** : `scripts/record_v2_trace.py`, `V2Match.jsx` (point d'entrée dev), `ui/src/dev/fixture.js`.
- **Critères** : 3 traces enregistrées (match avec 3 buts ou plus, match 0-0, match avec temps additionnel) ; build de
  production sans le mode ; départ à `t=44` affiche la mi-temps en moins de 5 s.
- **Tests** : script rejoué deux fois (mêmes octets à graine fixée) ; `npm run build` ; vérification que le mode est
  absent de `dist/`.
- **Dépendances** : aucune. **Risques** : traces volumineuses (taille du dépôt) → hors dépôt ou compressées.

### EM-01 — Découpage de `V2Match.jsx` et mémoïsation (S) — 120 min (moyenne)
- **Objectif** : un assembleur léger + composants dédiés ; l'écran de réglage (choix des clubs) séparé de l'écran de lecture.
- **Problème** : 840 lignes, redessin complet à chaque image.
- **Résultat** : aucun changement visible ; composants `React.memo` ; boucle de lecture déplacée telle quelle dans un hook.
- **Périmètre** : déplacement et mémoïsation seulement ; pas de style.
- **Composants** : `V2Match.jsx`, nouveaux fichiers de `components/match/`, `hooks/useMatchPlayback.js`.
- **Critères** : sur trace enregistrée, score, minutes de but, instants de ralenti et mi-temps **identiques** à l'ancien
  code ; médiane de durée d'image ≤ celle d'avant (build de production, x8) ; `npm run build` OK ; `npm run lint` : pas
  d'avertissement nouveau.
- **Tests** : comparaison des sorties (score, buts révélés) sur 3 traces ; mesure d'images par seconde avant/après ;
  capture avant/après identique.
- **Dépendances** : EM-00. **Risques** : boucle de lecture (fermetures sur les refs) → déplacement sans réécriture.

### EM-02 — Couleurs de maillot dans l'API (D) — 60 min (élevée)
- **Objectif** : fournir à l'écran `primary` et `secondary` de chaque club du match.
- **Problème** : la V2 n'a aucune couleur de club (`/api/v2/lineup` n'en donne pas).
- **Résultat** : `LineupOut` gagne `color` et `secondary` (via `kits.CLUB_KIT`, lecture seule) ; clubs sans kit : gris du kit
  par défaut, repéré par un indicateur `known_kit`.
- **Périmètre** : sérialisation ; ni moteur ni données joueurs.
- **Composants** : `api/routers/v2.py` (`LineupOut`, `numbered_lineup`), `tests/`.
- **Critères** : PSG renvoie ses deux couleurs ; club inconnu renvoie le défaut et `known_kit=false` ; route existante
  inchangée pour les autres champs.
- **Tests** : tests `pytest` de la route (club connu, club sans kit, 404).
- **Dépendances** : aucune. **Risques** : nul pour le moteur ; la suite complète dure environ 40 min (temps machine).

### EM-03 — Règle de couleurs d'équipe + jetons (V) — 120 min (moyenne)
- **Objectif** : couleurs d'équipe fidèles aux clubs, toujours distinctes, numéros lisibles ; variables CSS d'équipe.
- **Problème** : bleu et or codés en dur, sans lien avec les clubs.
- **Résultat** : `teamColors.js` applique la règle de 2.2 ; variables `--team-home|away` et `-ink` posées à la racine ;
  les huit couleurs en dur remplacées.
- **Périmètre** : couleurs seulement (aucune mise en page).
- **Composants** : `utils/teamColors.js`, `V2Match.jsx`, `index.css` (jetons ajoutés).
- **Critères** : ΔE ≥ seuil entre équipes dans 100 % des paires testées (toutes les paires d'un échantillon de ≥ 40 clubs
  dont blanc/blanc, rouge/rouge, club vert, club noir) ; contraste du numéro ≥ 4,5:1 ; domicile garde sa principale dans
  100 % des cas ; résultat identique à chaque appel (pas d'aléa).
- **Tests** : `node --test` sur la règle (paires pathologiques, déterminisme).
- **Dépendances** : EM-02. **Constantes à valider avant code** : seuil ΔE (25), pas de décalage de clarté, anneau.
- **Risques** : club à la couleur proche du gazon ; un seuil trop strict dénature les clubs.

### EM-04 — Mise en page en trois zones et responsive (E) — 120 min (moyenne)
- **Objectif** : HUD / centre / zone basse ; terrain dominant ; adaptation 844×390 à 1920×1080.
- **Problème** : terrain petit, compositions masquées sous 1024 px, en-tête global qui mange 56 px.
- **Résultat** : grille CSS à trois zones, en-tête global masqué sur `/v2`, colonnes de compositions à 200 à 230 px, repli
  tiroirs sous 960 px ; coquilles vides stylées pour les zones (contenu inchangé à ce stade).
- **Périmètre** : structure uniquement. **Composants** : `V2Match.jsx`, `AppShell.jsx`, `index.css`.
- **Critères** : captures aux 4 tailles (844×390, 1024×768, 1366×768, 1920×1080) ; surface du terrain ≥ +30 % à 1280×720
  (mesurée) ; aucun défilement de page ; autres routes gardent leur en-tête.
- **Tests** : captures avant/après ; contrôle manuel des autres routes ; build, lint.
- **Dépendances** : EM-01. **Risques** : `AppShell` partagé.

### EM-05 — Terrain : pelouse, marquages, suppression du cadre rouge (V) — 120 min (moyenne)
- **Objectif** : terrain qualitatif intégré à l'interface, sans bordure rouge.
- **Problème** : piste rouge épaisse, vert saturé, marges et zone de bancs qui rétrécissent le jeu.
- **Résultat** : nouvelles teintes et lignes de 2.2, marge réduite à 3 m, sol sombre, vignette, dégradé de profondeur
  unique ; coordonnées inchangées (`viewBox` recadré, `project` intact).
- **Périmètre** : dessin du terrain seulement (le dessin des bancs est le ticket EM-06).
- **Composants** : `PitchView2` (ex-V2Pitch), `index.css`.
- **Critères** : joueurs et ballon tombent exactement sur les mêmes points qu'avant (test de projection de 5 points :
  coins, centre, points de penalty) ; plus aucune zone rouge ; lignes visibles à 844×390 (≥ 1 px).
- **Tests** : test unitaire de `project` (inchangé) ; captures avant/après aux 4 tailles.
- **Dépendances** : EM-04. **Risques** : confusion lignes/gazon sur petit écran (épaisseur minimale).

### EM-06 — Bancs et bord de terrain (V) — 90 min (moyenne)
- **Objectif** : bancs compacts et cohérents avec le nouveau terrain (décision propriétaire en 4).
- **Problème** : zone de 7 m dessinée en gris, rustique, qui prend de la hauteur.
- **Résultat** : bancs resserrés à la ligne de touche (zone de 4,5 m proposée), sièges aux couleurs d'équipe, échauffement
  conservé (comportement et constantes `WARMING_UP`, `BENCH_GAP` inchangés).
- **Composants** : `Bench` (dans `PitchView2`). **Critères** : numéros lisibles ; échauffement dès la 2e période identique ;
  hauteur du dessin −6 % minimum.
- **Tests** : captures x1 en 1re et 2e période ; build, lint.
- **Dépendances** : EM-05, EM-03. **Risques** : constantes validées le 04/11 (modifier la zone demande leur accord).

### EM-07 — Marqueurs joueurs et ballon (V) — 120 min (moyenne)
- **Objectif** : cercles lisibles, relief subtil, équipes distinctes au premier coup d'œil.
- **Résultat** : `PlayerMarker` (couleur d'équipe, anneau, numéro à contraste garanti, relief 10 %), ballon plus visible.
- **Périmètre** : apparence ; rayon, ombre et sélection inchangés. **Composants** : `PlayerMarker`, `PitchView2`.
- **Critères** : numéro lisible à 1366×768 (capture zoomée) pour les 40 clubs de l'échantillon ; aucune équipe confondue
  avec l'autre sur les paires pathologiques ; fluidité ≥ EM-01.
- **Tests** : planche de rendu de toutes les couleurs du banc d'essai ; mesure d'images par seconde.
- **Dépendances** : EM-03, EM-05. **Risques** : coût de rendu des dégradés (utiliser un seul `<defs>` partagé).

### EM-08 — HUD supérieur : identité du match (V) — 120 min (moyenne)
- **Objectif** : écussons, noms, score central très visible, minute, période, état.
- **Résultat** : `MatchHud`/`ScoreBlock` aux jetons du design system ; écussons `ClubBadge` à 40 à 48 px ; lignes techniques
  (« transition défensive », « calcul… ») retirées de l'écran principal (hors-jeu : repris par la frise).
- **Composants** : `MatchHud`, `ScoreBlock`, `ClubCrest`. **Critères** : score lisible à 2 m (≥ 56 px à 1366×768) ; minute
  avec temps additionnel (45+2') identique à la logique `clock()` ; score jamais en avance sur la lecture (test sur trace).
- **Tests** : sortie de `clock()` comparée avant/après sur 3 traces ; captures des 6 états.
- **Dépendances** : EM-01, EM-03, EM-04. **Risques** : noms de clubs longs (troncature, tailles).

### EM-09 — Commandes de vitesse, pause, ralenti (E/V) — 90 min (élevée)
- **Objectif** : boutons élégants, état actif évident, cohérents avec le HUD ; comportement strictement inchangé.
- **Résultat** : groupe segmenté, bouton pause de 44 px, barre d'espace, badge RALENTI ; `SPEED_OPTIONS` et la boucle intacts.
- **Composants** : `SpeedControls`. **Critères** : chaque vitesse produit exactement la même durée de lecture qu'avant
  (chronométrage d'une minute de match par vitesse, écart < 2 %) ; pause/reprise inchangées ; cibles ≥ 40 px.
- **Tests** : mesure de lecture par vitesse ; test clavier ; captures.
- **Dépendances** : EM-08. **Risques** : raccourci clavier en conflit avec le navigateur.

### EM-10 — Compositions en cartes (V) — 165 min (moyenne) → découpé en 10a et 10b
- **10a** (90 min) : `LineupColumn`, `PlayerCard`, titulaires/remplaçants, symétrie, écrans ≥ 1280 px.
- **10b** (75 min) : compacts 960 à 1279 px et tiroirs < 960 px.
- **Problème** : listes de 11 px, invisibles sous 1024 px. **Résultat** : cartes de 2.2, sans note ni statistique.
- **Critères** : 11 titulaires et jusqu'à 9 remplaçants visibles sans défilement à 1366×768 ; gauche et droite symétriques ;
  noms longs tronqués proprement ; accessible sur 844×390 en un geste.
- **Tests** : captures aux 4 tailles ; contrôle des noms les plus longs de la base.
- **Dépendances** : EM-03, EM-04. **Risques** : entraîneur (conservé, discret) ; numéros des entrants (ticket coach/05).

### EM-11 — Momentum : histogramme symétrique (V) — 150 min (moyenne) → 11a rendu, 11b données
- **11a** (90 min) : `MomentumTimeline` : barres, axe, repères, curseur, zone future vide, couleurs d'équipe.
- **11b** (60 min) : `momentum.js` extrait, échelle fixe, minute en cours limitée aux images vues (correctif de la réserve A1),
  libellé « Pression territoriale ».
- **Problème** : 1.3. **Résultat** : frise de 150 px pleine largeur, ≈ 10 px par barre.
- **Critères** : aucune barre future ; barres déjà affichées **ne changent jamais de hauteur** quand le match avance ; mêmes
  valeurs que l'ancienne formule à l'échelle près ; pas de calcul par image (recalcul par seconde au plus) ; fluidité ≥ EM-01.
- **Tests** : `node --test` sur `momentum.js` (trace courte synthétique issue d'une vraie trace tronquée) ; mesure.
- **Dépendances** : EM-01, EM-03, EM-04. **Constantes à valider** : échelle fixe, largeur de barre, seuil visuel.
- **Risques** : amplitude trop faible → visuel plat (alors ticket de données EM-D2).

### EM-12 — Chronologie : buts et cartons sur la frise (V) — 90 min (moyenne)
- **Objectif** : buts (minute, équipe) et cartons rouges (emplacement) sur l'axe du momentum.
- **Résultat** : `EventMarker` ; info-bulle (« 23' · équipe », + buteur après EM-D1) ; plus d'emoji.
- **Critères** : marqueur n'apparaît qu'à sa minute de lecture ; nombre de marqueurs = buts révélés ; cartons : composant
  prêt, testé sur propriété simulée **dans les tests seulement**, rien d'affiché tant que 09a n'existe pas.
- **Tests** : trace enregistrée ; test du composant carton avec propriétés de test.
- **Dépendances** : EM-11. **Risques** : buts rapprochés (chevauchement) → décalage vertical.

### EM-13 — États du match : but, mi-temps, fin (E/V) — 120 min (moyenne)
- **Résultat** : `MatchBanner` pour but (2 s), mi-temps (3 s, durée actuelle), fin (panneau de fin, bouton Stats et Retour) ;
  badge RALENTI ; coup d'envoi.
- **Critères** : durées du bandeau de mi-temps et du ralenti **inchangées** ; le bandeau ne bloque ni la lecture ni la
  pause ; états vérifiés à x1 et x8.
- **Tests** : trace enregistrée à `t=44`, `t=goal-1`, `t=fin` ; captures des 6 états.
- **Dépendances** : EM-08, EM-12. **Risques** : bandeau qui masque l'action au x8 (durée en temps réel).

### EM-D1 — Buteur dans les buts (D) — 75 min (moyenne)
- **Objectif** : nom du buteur sur chaque but de la trace.
- **Problème** : `GoalEvent` = minute + équipe ; le buteur n'est pas envoyé.
- **Résultat** : `GoalEventOut.player` rempli côté API en appariant le but au dernier tir de l'équipe d'issue « but » (ou
  penalty) avant la minute du but ; moteur **inchangé**. Si l'appariement ne peut être garanti, ticket moteur séparé.
- **Critères** : sur 50 matchs, 100 % des buts ont un buteur de la bonne équipe ; aucun doublon ; si la règle échoue, le
  ticket s'arrête et ouvre le ticket moteur.
- **Tests** : `pytest` sur traces simulées ; vérification sur 50 matchs (temps machine).
- **Dépendances** : aucune. **Risques** : but contre son camp (aucun mécanisme dans la V2 à ce jour : à confirmer).

### EM-D2 — Tirs, fautes et corners dans le flux (D) — 90 min (moyenne)
- **Objectif** : envoyer à l'écran ce que la trace enregistre déjà.
- **Résultat** : listes `shots`, `fouls`, `restarts` (corners) dans `MatchProgressOut`, comme `goals` aujourd'hui (remplies
  pendant le calcul) ; moteur inchangé.
- **Critères** : réponse allégée (taille mesurée) ; tous les événements portent leur minute (filtrage sur le temps lu).
- **Tests** : `pytest` ; mesure de la charge utile (cible : < 2× la taille actuelle).
- **Dépendances** : aucune. **Risques** : poids de la réponse chaque seconde (n'envoyer que les nouveaux événements).

### EM-14 — Panneau de statistiques (V/E) — 150 min (moyenne) → 14a calculs, 14b panneau
- **14a** (60 min) : `matchStats.js` : tirs, tirs cadrés, corners, fautes, hors-jeu, possession ; tous filtrés sur le temps lu.
- **14b** (90 min) : `StatsDrawer` + bouton du HUD, lignes symétriques aux couleurs d'équipe ; le match continue.
- **Critères** : valeurs = somme des événements de la trace jusqu'à `seen` (test de cohérence, pas de futur) ; panneau
  ouvert, HUD et terrain visibles ; aucune valeur inventée (cartons : « — » tant que 09a n'existe pas).
- **Tests** : `node --test` ; captures avec panneau ouvert à x1 et x8.
- **Dépendances** : EM-D2, EM-08, EM-03. **À valider avant code** : définitions de « tir cadré » (issues but, capté, repoussé,
  claqué ; hors cadre : à côté, contré) et de la possession (équipe du dernier porteur).
- **Risques** : définitions discutables (c'est un calcul nouveau, donc soumis à votre accord, d'où la contrainte).

### EM-15 — Panneau « Analyse » du joueur sélectionné (E) — 60 min (élevée) — optionnel
- **Problème** : le panneau d'intention (décisions, options envisagées) est un outil technique qui encombre le bas de l'écran.
- **Résultat** : même contenu, dans un tiroir ouvert par un toucher sur un joueur ; bas de l'écran libéré.
- **Critères** : contenu identique ; fermé par défaut. **Dépendances** : EM-04, EM-10. **Décision propriétaire requise.**

### EM-16 — Finitions, accessibilité, performance, recette (V/E) — 120 min (moyenne)
- **Résultat** : animations (score qui tombe, tiroirs), `prefers-reduced-motion`, focus clavier, libellés ARIA, contrastes
  vérifiés ; mesure finale de fluidité x1 et x8 sur build de production (avant/après EM-01) ; recette sur les 8 états.
- **Critères** : tableau de captures (début, en cours, but, mi-temps, fin, x1, x8, stats ouvertes) à 4 tailles ; images par
  seconde ≥ mesure d'avant ; contraste ≥ 4,5:1 sur tout texte utile ; `npm run build` et `npm run lint` sans régression.
- **Dépendances** : tous. **Risques** : accumulation de petits écarts : recette à faire avec vos yeux (points à vérifier à l'écran).

### EM-19 — Sélecteur « Match complet / Temps forts » (E/V) — 90 min (moyenne) — ajouté le 07/11/2026
- Demande du propriétaire. Bouton segmenté du HUD ; le lecteur et les modes eux-mêmes sont ceux du chantier
  `v2-mise-en-scene` (tickets `01`, `02`, `03`). « Temps forts » = Résumé (recommandé) ou Moments clés, à confirmer ; la
  position est grisée tant que le mode n'est pas livré. Détail : `issues/19-selecteur-match-complet-temps-forts.md`.
- **Dépendances** : EM-08, EM-09 ; `v2-mise-en-scene/01` puis `03` (ou `02`).

### Hors chantier (à ouvrir si vous le voulez)
- **EM-X1** Carton rouge réel : dépend du ticket moteur `v2-attributs-restants/09a` ; l'écran est déjà prêt (EM-12).
- **EM-X2** Écran de réglage du match (choix des clubs) : aujourd'hui deux `<select>` ; hors de votre périmètre actuel.
- **EM-X3** Vraie perspective (point de fuite) : exige de changer le contrat de projection avec le moteur d'affichage ;
  exclu.
- **EM-X4** Vrai momentum « danger créé » (qualité des tirs, `quality` de `ShotEvent`) : après EM-D2 et validation du calcul.

---

## 4. Décisions à prendre par le propriétaire

1. **Écran visé** : `/v2` (V2Match). Confirmez que la V1 (`PitchView`) reste hors champ.
2. **Bancs** : recommandé = les garder, resserrés (4,5 m au lieu de 7 m). Alternatives : les retirer (terrain encore
   plus grand, mais on perd les remplaçants qui s'échauffent), ou ne rien changer.
3. **Panneau d'intention du joueur** (EM-15) : recommandé = le garder, en tiroir. C'est un outil d'analyse du moteur, pas
   un élément de retransmission.
4. **Momentum** : recommandé = livrer l'histogramme avec la pression territoriale réelle actuelle, nommée telle quelle, et
   rouvrir « danger créé » plus tard (EM-X4).
5. **Définitions des statistiques** (tir cadré, possession) avant EM-14.
6. **Constantes** : seuil de distance de couleur, échelle du momentum, tailles du HUD, opacité des anneaux : chacune sera
   proposée au début du ticket qui la porte (règle du projet).
7. **Cartons rouges** : n'existent pas dans la V2 ; l'écran réserve la place, sans en inventer.

## 5. Ordre d'exécution

Chaque ticket suit le workflow existant : critères chiffrés avant le code, tests, `/valider-ticket-simulafoot` (expert +
QC), commit des seuls hunks du ticket, puis ticket suivant.

| Rang | Ticket | Pourquoi à cette place | Estim. |
|---|---|---|---|
| 1 | EM-00 banc de rejeu | rend tout le reste vérifiable et mesurable | 90 min |
| 2 | EM-01 découpage + mémoïsation | débloque les refontes visuelles sans risque de fluidité | 120 min |
| 3 | EM-02 couleurs API | donnée de base, indépendante | 60 min |
| 4 | EM-03 règle de couleurs | alimente joueurs, cartes, momentum | 120 min |
| 5 | EM-04 mise en page 3 zones | plus gros gain visuel, impose les proportions | 120 min |
| 6 | EM-05 terrain | héros de l'écran | 120 min |
| 7 | EM-07 marqueurs joueurs | lisibilité de l'action | 120 min |
| 8 | EM-08 HUD identité | repère immédiat du score | 120 min |
| 9 | EM-10a, 10b compositions | accès aux équipes | 90 + 75 min |
| 10 | EM-11a, 11b momentum | élément fort de l'expérience | 90 + 60 min |
| 11 | EM-12 chronologie | s'appuie sur la frise | 90 min |
| 12 | EM-09 commandes | finition ergonomique du HUD | 90 min |
| 13 | EM-06 bancs | finition du terrain | 90 min |
| 14 | EM-13 états (but, mi-temps, fin) | cohérence des moments clés | 120 min |
| 15 | EM-D1 buteur, EM-D2 flux tirs/fautes/corners | données, indépendantes, parallélisables dès le rang 3 | 75 + 90 min |
| 16 | EM-14a, 14b statistiques | après D2 | 60 + 90 min |
| 17 | EM-15 analyse (optionnel) | après décision | 60 min |
| 17b | EM-19 sélecteur Match complet / Temps forts | après EM-08, EM-09 ; utile quand `v2-mise-en-scene/01` existe | 90 min |
| 18 | EM-16 finitions et recette | à la fin | 120 min |

Total estimé : **environ 36 h de travail effectif** (EM-00 à EM-16 et EM-19, EM-15 compris ; 32 h 15 sans EM-15 ni les deux tickets de données), temps machine en plus (suite complète
d'environ 40 min par ticket touchant l'API : EM-02, EM-D1, EM-D2 ; mesures de fluidité de quelques minutes). Chaque ticket
reste sous environ 2 h 30 ; ceux au-dessus de 2 h sont déjà découpés (10, 11, 14).

## 6. Besoins de données ou de moteur

| Besoin | Pourquoi | Ticket | Touche le moteur ? |
|---|---|---|---|
| Couleurs de maillot dans l'API V2 | couleurs fidèles aux clubs | EM-02 | non (sérialisation) |
| Buteur de chaque but | timeline et bandeau de but | EM-D1 (recoupe `v2-mise-en-scene/01`, point 1 : à faire une seule fois) | non si l'appariement tir→but est garanti, sinon ticket moteur séparé |
| Tirs, fautes, corners dans le flux | statistiques | EM-D2 | non |
| Cartons (jaune, rouge) | marqueur de carton rouge, statistique cartons | `v2-attributs-restants/09a` (existant) | **oui**, hors de ce chantier |
| Remplacements | numéros des entrants, banc vivant | `v2-coach-et-gestion-de-match/05` (existant) | oui, hors de ce chantier |
| Danger créé (qualité des tirs) pour un vrai momentum | histogramme plus fidèle | EM-X4 après D2 | non |

Rien de ce chantier ne modifie le moteur de simulation, ni la physique, ni les déplacements, ni le calcul du temps de match.
