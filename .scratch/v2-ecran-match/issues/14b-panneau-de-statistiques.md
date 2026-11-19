# EM-14b — Statistiques : panneau (V) — 95 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Ticket parent : `14-panneau-de-statistiques.md`. Dépendances : EM-14a (`utils/matchStats.js`), EM-18 (événements en
direct), EM-08 (HUD), EM-03 (couleurs d'équipe), EM-13 (carte de fin).

## Comments

### 19/11/2026 — décisions, estimation et critères

- **Décision du propriétaire** (19/11/2026, « Oui, comme la spec ») : bouton « Stats » dans le HUD, à côté des vitesses ;
  tiroir de 340 px à droite qui recouvre la composition extérieure (HUD, terrain et frise visibles) ; sur petit écran,
  feuille depuis le bas ; le match continue ; bouton « Statistiques » dans la carte de fin ; lignes symétriques « valeur
  domicile — barre — valeur extérieur » aux couleurs d'équipe : possession, tirs, tirs cadrés, corners, fautes,
  hors-jeu, cartons (« — »).
- **Choix de détail (à confirmer à l'écran)** : feuille du bas sous 960 px de large, 60 % de la hauteur au plus ;
  fermeture par la croix, par le bouton Stats ou par Échap ; barre : part de chaque équipe (moitié chacune à 0-0) ;
  valeurs recalculées une fois par seconde de match lue au plus (pas à chaque image) ; possession calculée seulement
  tiroir ouvert ; temps lu = minute du moteur (réserve A2 d'EM-14a).
- **Estimation** (travail effectif) : analyse 15 min, développement 40 min, tests et mesures 25 min, clôture 15 min,
  **total 1 h 35**, confiance moyenne. Temps machine hors total : suite complète, mesures navigateur, banc de fluidité.
- **Critères d'acceptation** : valeurs affichées = `matchStats` au temps lu (trace réelle, 3 instants) ; jamais de futur ;
  tiroir de 340 px ouvert : HUD, terrain et frise visibles, lecture qui continue (minute qui avance à × 8) ; feuille du
  bas à 844×390 ; score toujours centré (écart ≤ 1 px) avec le bouton Stats ; aucun défilement de page ; cartons « — » ;
  bouton Statistiques de la carte de fin qui ouvre le panneau ; fluidité ≥ avant tiroir fermé (banc d'EM-01) ; captures
  à × 1 et × 8 ; `npm test`, lint 0 erreur, build OK ; suite Python 3 438 passés.

### 19/11/2026 — implémentation

- **Code** :
  - `components/match/StatsDrawer.jsx` (nouveau) : tiroir de 340 px à droite (feuille du bas sous 960 px, 60 % de la
    hauteur au plus), lignes symétriques (valeurs, libellé, barre de part à la couleur de chaque équipe ; « — » sans
    valeur), Échap et croix pour fermer ; possession (`possessionPrefix(holderTeams(trace.ticks))`) calculée à
    l'ouverture et à chaque nouvelle tranche d'images, valeurs recalculées une fois par seconde lue (`Math.floor(shownS)`,
    minute du moteur) ;
  - `MatchHud.jsx` : bouton « Stats » (icône + libellé, `aria-pressed`) ; `MatchScreen.jsx` : état `statsOpen`, panneau
    dans la zone centrale ; `MatchBanner.jsx` : bouton « Statistiques » de la carte de fin (ouvre le panneau, referme la
    carte).
- **Changement en cours de route (décision du propriétaire du 19/11/2026, « À gauche, après Retour »)** : placé à côté
  des vitesses, le bouton élargissait les deux colonnes latérales du HUD (largeurs égales pour centrer le score) ; le
  centre perdait environ 160 px et les noms de club tombaient à « OLY… » (1024 px) et « 0.. » (844 px). Le bouton est
  dans la colonne de gauche, plus étroite : colonnes du HUD, largeur visible des noms, centrage et hauteur **identiques**
  à avant aux 4 tailles (`mesures/em14b-hud-avant.json`, `em14b-hud-apres.json` : 230/348/230 px à 844, 253/482/253 à
  1024, noms 96 et 130 px visibles comme avant).
- **Mesures** (`mesures/em14b-mesure.cjs`, trace réelle `em11-om-ol`, valeurs attendues calculées à part par
  `em14b-attendu.mjs` avec `matchStats`, résultats `em14b-apres.json`, captures `em14b/`) :
  - valeurs affichées = attendues (0 écart) à 10', 45' et 103,9', à 1024, 1366 et 1920 px et à 844×390 ; à 45' :
    possession 59-41, tirs 13-9, cadrés 4-5, corners 2-0, fautes 2-14, hors-jeu 0-1, cartons « — » ;
  - tiroir 340 px de large (556 px de haut à 1366×768) ; HUD, terrain et frise visibles ; score centré (0 px) ; aucun
    défilement de page ; fermeture par Échap ;
  - 844×390 : feuille du bas de 844 × 234 px (le bas du terrain est recouvert, HUD visible) ;
  - lecture qui continue à × 8 panneau ouvert : tirs 6 → 7 et possession 57 → 59 % en 6 s ;
  - carte de fin : « Statistiques » ouvre le panneau et referme la carte.
- **Fluidité** (`mesures/em14b-fluidite.txt`) : panneau fermé, médiane 16,7 ms des deux côtés, script 1,72 → 1,76 ms par
  image (+ 2,5 %, bruit) ; panneau ouvert à × 8 : médiane 16,7 ms, p95 16,8 ms, comme fermé.
- **Vérifications** : `npm test` 82 passés ; lint 0 erreur, 5 avertissements (un avertissement de dépendance de mémo
  corrigé en cours) ; build OK ; suite Python 3 438 passés, 0 ignoré, 14 désélectionnés.
- **Déterminisme** : affichage seul.
- **À vérifier à l'écran** : feuille du bas sur téléphone (recouvre le bas du terrain) ; bouton Stats à gauche du HUD ;
  lisibilité des barres.

### 19/11/2026 — revue experte (passage 1) et correctif

- Expert (empreinte `c34e5c60`) : **APPROVED_WITH_RESERVATIONS**.
  - A1 [réserve] à 844×390, la feuille du bas (60 vh = 234 px) ne laisse que 50 à 90 px de terrain : le match qui
    continue est presque invisible (`terrainVisible: false`).
  - A2 [facultatif] en direct, panneau ouvert, `holderTeams(trace.ticks)` reparcourt toute la trace à chaque tranche
    (une par seconde) ; coût non mesuré en direct.
- Contrôle qualité (passage 1) : **VALIDÉ**.
- **Décision du propriétaire sur A1** (19/11/2026, « Tiroir latéral en paysage ») : sous 500 px de haut, tiroir latéral
  de 340 px pleine hauteur ; la feuille du bas reste pour les écrans étroits d'au moins 500 px de haut (portrait).
- **Correctif** (`StatsDrawer.jsx`) : variantes de la feuille du bas sous `(max-width: 959.98px) and (min-height: 500px)`.
  Mesure refaite (`em14b-apres.json`, + cas 390×844) : 844×390 → tiroir 340 × 288 px à droite, terrain visible ;
  390×844 → feuille 390 × 359 px en bas, terrain visible ; autres tailles inchangées ; 0 écart de valeur partout.
  `npm test` 82 passés ; lint 0 erreur, 5 avertissements ; build OK. Suite Python non relancée : correctif limité aux
  classes d'un composant JavaScript (3 438 passés sur l'état du passage 1).
- **Constaté en passant (hors périmètre, antérieur au ticket)** : à 390 px de large (téléphone en portrait), la colonne
  centrale du HUD tombe à 0 px (colonnes 230 / 0 / 230 px) et le score est décalé de 92,9 px : mesuré à l'identique
  sur l'état d'avant le ticket (`f6d455f`). À traiter à part (HUD en portrait).

### 19/11/2026 — revue experte (passage 2), contrôle qualité et clôture

- Expert (empreinte `b81933e6`) : **APPROVED** ; A1 résolue. A2 [facultatif] coût de `holderTeams` en direct non
  mesuré ; A3 [facultatif] à 844×390 le tiroir couvre environ le tiers droit du terrain (largeur réduite possible,
  constante à soumettre si gênant).
- Contrôle qualité (passage 2) : **VALIDÉ**.
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 1 h 35 ; réelle environ 2 h 05 (analyse 15, développement 45 dont le déplacement du bouton et le
  correctif A1, tests et mesures 45, clôture 20), écart + 32 % : deux reprises décidées par le propriétaire (bouton Stats
  à gauche, tiroir latéral en paysage) et un second passage de revue. Temps machine hors total : mesures navigateur,
  deux builds et six passes de fluidité, suite complète (15 min 29).
