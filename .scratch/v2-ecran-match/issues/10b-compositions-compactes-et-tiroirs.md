# EM-10b — Compositions compactes et tiroirs (V) — 95 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Ticket parent : `10-compositions-en-cartes.md` (découpé en 10a et 10b). Précédent : `10a-compositions-en-cartes-grands-ecrans.md`
(livré le 19/11/2026). Chantier : `.scratch/v2-ecran-match/spec.md`.

- **Problème** : après 10a, la colonne défile dès qu'elle mesure moins de 562 px de haut (mesures avant le code, trace
  `em10a`, 9 remplaçants par équipe) : 844×390 (tiroir de 288 px) 274 px de défilement, 8 cartes visibles sur 20 ;
  915×412 252 px, 9 sur 20 ; 960×600 160 px, 12 sur 20 ; 1100×700 60 px, 17 sur 20 ; 1280×720 40 px, 18 sur 20 ;
  1024×768 et 1280×800 tiennent.
- **Écart à la spec signalé avant le code** : la spec prévoyait des cartes compactes par **largeur** (960 à 1279 px :
  numéro + nom, poste en pastille). La place manque en **hauteur** : 1024×768 tient déjà, 1280×720 défile au-dessus du
  seuil. En largeur, passer de 220 à 200 px ne fait tomber les noms que d'environ 19 à 16 caractères avant troncature.
  Le poste est donc gardé, et la densité est choisie d'après la hauteur réelle de la colonne.
- **Dépendances** : EM-04 (colonnes, tiroirs de 260 px, languette), 10a (cartes).

## Comments

### 19/11/2026 — estimation, constantes et critères validés par le propriétaire

- **Estimation** (travail effectif) : analyse 15 min, développement 40 min, tests et mesures 25 min, intégration et
  clôture 15 min, **total 1 h 35**, confiance moyenne ; + 20 min sur les 75 du découpage initial (choix par hauteur,
  reprises de 10a). Temps machine hors total : suite complète (environ 15 min). Hypothèse : ni l'API ni la mise en page
  d'EM-04 (largeurs, tiroir de 260 px, languette) ne changent.
- **Constantes validées (« je valide les trois niveaux et le choix par hauteur », 19/11/2026)** : la colonne mesure sa
  hauteur (ResizeObserver) et prend le niveau le plus aéré dont le budget tient :
  - **complet** (10a inchangé), colonne ≥ 562 px : cartes 26 / 20 px, pastilles 20 / 16 px, en-tête sur deux lignes (44 px) ;
  - **compact**, ≥ 500 px : cartes 22 / 18 px, pastilles 18 / 16 px, en-tête sur deux lignes ;
  - **serré**, en dessous : cartes 20 / 18 px, pastilles 16 / 16 px, en-tête sur une ligne de 28 px (écusson 20 px +
    club), « formation · entraîneur » au survol et pour les lecteurs d'écran ; titulaires seuls 280 px, banc atteint en
    défilant.
- **Critères d'acceptation** (DOM, trace `em10a`, 9 tailles : 844×390, 915×412, 960×600, 1024×768, 1100×700, 1280×720,
  1280×800, 1366×768, 1920×1080) : 11 titulaires visibles sans défilement partout ; 20 cartes sans défilement dès que la
  colonne fait au moins 500 px ; 1366×768 et 1920×1080 identiques à 10a (mêmes positions) ; symétrie 0 px et aucun
  débordement horizontal partout ; 844×390 : tiroir ouvert en un toucher, titulaires visibles ; niveau dépendant de la
  seule taille de la colonne (pas d'aller-retour pendant la lecture) ; reprises de 10a : A2 (test de budget à 570 px),
  A3 (budget lié au rendu), A4 (commentaire sur `color`) ; `npm test`, lint 0 erreur, build OK ; suite Python à 3 437
  passés.

### 19/11/2026 — implémentation

- **Code** :
  - `ui/src/utils/lineupCards.js` : `DENSITIES` (hauteurs des trois niveaux), `lineupColumnHeight(starters, bench,
    density)`, `lineupDensity(available, starters, bench)` (premier niveau dont le budget tient, sinon serré) ;
  - `components/match/LineupPanel.jsx` : reçoit `density`, lit toutes ses hauteurs dans `DENSITIES` (en-tête, cartes,
    pastilles, écusson), ce qui lie le budget testé au rendu (A3) ; en serré, sous-titre en `sr-only` et `title` sur
    l'en-tête ; attribut `data-density` ;
  - `components/match/MatchScreen.jsx` : hook `useColumnDensity` (ResizeObserver + `useLayoutEffect`, mesure avant
    affichage), un par colonne et un par tiroir ; commentaire sur `color` réservé à la languette (A4).
  - Pas d'aller-retour : la hauteur mesurée est celle du conteneur défilant, fixée par la grille, que la densité ne
    change pas.
- **Tests** : `utils/lineupCards.test.js` porté à 8 tests : colonne de référence à 570 px (A2), budgets des trois niveaux
  (562, 500, 280 px), table des seuils (882 → 0 px), titulaires en serré ≤ 288 px, banc vide.
- **Mesures** (`mesures/em10b-mesure.cjs` et `em10b-tiroir.cjs`, Playwright, serveur de développement, trace `em10a` ;
  résultats `em10b-apres.json`, `em10b-tiroir.json`, captures `em10b/`) :

  | Taille | Colonne | Niveau | Défilement (avant → après) | Titulaires visibles | Cartes visibles |
  |---|---|---|---|---|---|
  | 844×390 (tiroir) | 260×288 | serré | 274 → 174 px | 11/11 | 11/20 |
  | 915×412 (tiroir) | 260×310 | serré | 252 → 152 px | 11/11 | 11/20 |
  | 960×600 | 200×402 | serré | 160 → 60 px | 11/11 | 17/20 |
  | 1024×768 | 200×570 | complet | 0 → 0 | 11/11 | 20/20 |
  | 1100×700 | 200×502 | compact | 60 → 0 | 11/11 | 20/20 |
  | 1280×720 | 220×522 | compact | 40 → 0 | 11/11 | 20/20 |
  | 1280×800 | 220×602 | complet | 0 → 0 | 11/11 | 20/20 |
  | 1366×768 | 220×570 | complet | 0 → 0 | 11/11 | 20/20 |
  | 1920×1080 | 220×882 | complet | 0 → 0 | 11/11 | 20/20 |

  - symétrie : positions des 20 cartes identiques à gauche et à droite aux 9 tailles ; débordement horizontal 0 px
    partout ; aucun défilement de page ;
  - 1366×768 et 1920×1080 : positions des cartes identiques à celles de 10a (`em10a-apres.json`) ;
  - 844×390 : un toucher sur la languette domicile ouvre le tiroir (bord gauche à 0 px, `aria-hidden` faux), 11
    titulaires visibles, niveau serré.
- **Vérifications** : suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (attendu inchangé) ; `npm test` 51 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ; build OK.
- **Déterminisme** : rendu seul, aucun aléa ni horloge ajoutés ; le niveau ne dépend que de la taille du conteneur.
- **À vérifier à l'écran** : en tiroir, l'intertitre « Remplaçants » apparaît coupé en bas, ce qui signale le
  défilement ; passage d'un niveau à l'autre en redimensionnant la fenêtre ; pastilles des clubs à couleur très sombre
  (EM-03).
- **Durée** : estimée 1 h 35 ; réelle environ 1 h 10 de travail effectif (analyse 15, développement 25, tests et
  mesures 15, intégration et clôture 15), écart − 26 % (sous 30 %) : trace, scripts de mesure et dossier de revue de 10a
  réutilisés. Temps machine hors total : mesures navigateur (environ 3 min), suite complète (14 min 52).

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `39fe6048`) : **APPROVED**. Budgets recalculés (562, 500, 280 px) et retrouvés dans le DOM
  (premières cartes à 70 / 70 / 54 px, premiers remplaçants à 376 / 332 / 294 px) ; absence d'aller-retour vérifiée
  dans le code. Points facultatifs :
  - A1 marges faibles au-dessus des seuils (1100×700 : 2 px ; 1024×768 et 1366×768 : 8 px) : relancer
    `em10b-mesure.cjs` dans tout ticket qui touche au HUD ou à la zone basse ;
  - A2 sous 500 px de haut, sélectionner un joueur peut agrandir la zone basse et réduire le tiroir sous 280 px (déduit
    du code, non mesuré ; hérité d'EM-04) : à couvrir dans EM-15 ;
  - A3 effet non relancé si la composition redevient nulle puis revient identique (cas très improbable).
- Contrôle qualité : **VALIDÉ** (remarque non bloquante : densité calculée sur 0 px quand l'élément est masqué,
  recalculée à l'affichage).
- **Décision de clôture** : VALIDÉ.

