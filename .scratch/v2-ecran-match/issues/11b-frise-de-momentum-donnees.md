# EM-11b — Frise de momentum : données (V) — 75 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Ticket parent : `11-momentum-histogramme-symetrique.md` (découpé en 11a rendu et 11b données). Chantier :
`.scratch/v2-ecran-match/spec.md` (§ 1.3, § « Momentum et timeline »). Précédent : `11a-frise-de-momentum-rendu.md`
(réserve A1 acceptée, correctif ici).

- **Problème** (spec § 1.3, limites 2 et 3 ; réserve A1 de 11a) : échelle verticale recalculée sur les minutes jouées,
  donc les barres anciennes changent de hauteur quand une grosse minute arrive ; barre de la minute en cours affichée
  entière dès qu'elle est entamée (jusqu'à environ 11 px au-delà du curseur à 1366 px) et moyennée sur des images reçues
  mais pas encore vues ; nom « Match momentum » trompeur (c'est une pression territoriale + possession).
- **Dépendances** : EM-11a.

## Comments

### 19/11/2026 — estimation, constantes et critères

- **Estimation** (travail effectif) : analyse 15 min, développement 20 min, tests et mesures 25 min, intégration et
  clôture 15 min, **total 1 h 15**, confiance moyenne (60 min au découpage ; + 15 min pour le banc de fluidité et la
  mesure de référence). Temps machine hors total : deux builds de production et six passes de fluidité, suite complète.
- **Constantes** (validées par le propriétaire le 19/11/2026, au ticket 11a) : échelle fixe 0,6 = pleine hauteur (22 px),
  écrêtée au-delà ; 1 px au moins pour une minute jouée ; minutes terminées seulement ; libellé « Pression
  territoriale ». Formule inchangée (`dx·|dx|` ± 0,15 au porteur, moyenne par minute).
- **Critères d'acceptation** : aucune barre dont la **fin** dépasse le curseur (`x + largeur ≤ curseur`, critère du banc
  corrigé, réserve A1) ; une barre affichée garde sa hauteur jusqu'à la fin (barres 5 et 20 de 10' à 104') ; hauteur de
  chaque barre = min(22, max(1, |v| / 0,6 × 22)) avec v recalculé à part par l'ancienne formule (écart ≤ 0,01 px) ;
  dernière minute du match affichée une fois le match lu jusqu'au bout ; libellé « Pression territoriale » ; fluidité ≥
  11a (médiane d'image, temps de script) ; `npm test`, lint 0 erreur, build OK ; suite Python 3 437 passés.
- **Écart signalé** : libellé placé en info-bulle (`<title>`) et `aria-label`, comme l'ancien « Match momentum » ; pas de
  libellé visible : la frise de 72 px n'a pas de rangée libre et le texte (environ 110 px) ne tient pas après le repère
  90' (76 px restants à 1024 px).

### 19/11/2026 — implémentation

- **Code** :
  - `ui/src/utils/momentum.js` (nouveau, sans import, testé sous node) : `tickPush` (formule d'avant, recopiée),
    `completedMinutes(shownMin, lastMinute, done)` (minutes terminées ; la dernière minute, souvent incomplète, compte
    une fois le match fini et lu jusqu'au bout), `momentumByMinute(ticks, complete, length)` (minutes terminées
    seulement, donc images toutes vues), `barHeight` (échelle fixe 0,6, 1 px au moins, 22 px au plus), `LABEL` ;
  - `components/match/MomentumTimeline.jsx` : formule et échelle automatique retirées, calcul lu dans `momentum.js` ;
    partie fixe mémoïsée sur (images, minutes terminées) ; libellé « Pression territoriale » ; valeur nulle posée côté
    domicile (1 px) ;
  - `MatchScreen.jsx` : prop `played` (minutes entamées) retirée, la frise calcule ses minutes terminées.
- **Tests** : `utils/momentum.test.js` (8 tests), sur une trace réelle tronquée `utils/fixtures/momentum-om-ol-3min.json`
  (OM–OL, 3 min 15 s, 390 images, joueurs réduits au porteur, 34 Ko) : constantes, minutes terminées, dernière minute en
  fin de match, mêmes valeurs que l'ancienne formule (recopiée de `b0c7490`, écart < 1e-12), aucune image non vue
  utilisée, barres figées quand le match avance, échelle fixe et écrêtage ; ajouté au script `npm test`.
- **Mesures** (`mesures/em11b-mesure.cjs`, Playwright, serveur de développement, trace réelle `em11-om-ol` ; référence
  calculée à part en Python avec l'ancienne formule ; résultats `em11b-apres.json`, captures `em11b/`) :
  - 0 barre au-delà du curseur aux 8 cas (1366 × 768 à 10', 30', 51,5', 60', 103,9', 104' ; 1024 et 1920 à 60') ; à
    51,5' la dernière barre (minute 50) finit à 652,8 px pour un curseur à 660,2 px (avant : barre 51 jusqu'à 6,2 px
    au-delà) ;
  - écart maximal de hauteur à la référence : 0 px sur toutes les barres de tous les cas ;
  - barre 5 : 1,08 px et barre 20 : 22 px (écrêtée), identiques de 10' (30' pour la 20) à 104' ;
  - fin de match (104') : 104 barres, la minute 103 comprise ; à 103,9' (non fini) : 103 barres ;
  - sur les 104 minutes : 17 barres à 1 px (|v| < 0,027) et 5 écrêtées à 22 px (|v| > 0,6 ; max 0,80).
- **Fluidité** (`mesures/em11b-fluidite.txt`, banc d'EM-01, builds de production avant (`c8ba3e3`) et après, trace
  `em11-om-ol`, ×8, 3 passes alternées de 15 s, suite Python en parallèle) : médiane d'image 16,7 ms des deux côtés ;
  script 1,830 → 1,547 ms par image (− 15,5 %) ; 324 nœuds SVG des deux côtés.
- **Vérifications** : `npm test` 66 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ; build OK ;
  suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (15 min 12, attendu inchangé).
- **Déterminisme** : rendu seul, calcul pur sans aléa ni horloge ; mêmes hauteurs que la référence indépendante.
- **À vérifier à l'écran** : barres à 1 px des minutes neutres (17 sur 104 sur OM–OL) ; barres écrêtées (5 sur 104) ;
  apparition d'une barre à chaque minute pleine (et non plus dès la minute entamée) ; info-bulle « Pression
  territoriale » au survol de la frise.

### 19/11/2026 — revue experte (passage 1) et correctif

- Expert (empreinte `ba3e5704`) : **APPROVED_WITH_RESERVATIONS**.
  - A1 [réserve] fin de match en milieu de minute : la barre de la dernière minute (comptée une fois le match fini)
    occupe tout son créneau et dépasse le curseur de (ceil(L) − L)·w − 1 px (jusqu'à environ 12 px à 1366) ; le banc ne
    le voyait pas, la trace mesurée finissant à 103,99'.
  - A2 [facultatif] le test « aucune image non vue » coupait entre deux minutes terminées, égal par construction.
- **Correctif** (dans le périmètre : critère n° 1 du ticket), sans passer par l'acceptation de la réserve :
  - `momentumLayout.js` : `barBox(m, width, domain, endMinute)` borne la barre d'une dernière minute incomplète à
    l'instant de fin (1 px au moins, recalée pour finir au curseur) ; sans effet sur les autres barres ni pendant le jeu
    (barres m < floor(instant lu) ≤ dernière image) ; `MomentumTimeline` lui passe la minute de la dernière image ;
  - test node ajouté dans `momentumLayout.test.js` (fins à 96,3', 96,95', 96,02', 103,99' : fin de barre ≤ curseur,
    barre précédente inchangée, largeur 0,3 × 12,82 − 1 px à 96,3') ; test A2 renforcé (lu à 2,5', la minute 2 entamée
    dépend des images non vues ; la frise ne la calcule pas).
  - Banc : trace `em11b-fin-96` (OM–OL tronquée à 96,3', finie, développement seulement) ajoutée à
    `em11b-mesure.cjs` ; résultats `em11b-apres-fin-96.json` : 97 barres, fin de la barre 96 = curseur (1234,5 px à
    1366, 920,8 à 1024, 1742,6 à 1920), 0 barre au-delà, écart de hauteur 0 ; cas OM–OL complets inchangés
    (`em11b-apres.json` refait).
  - `npm test` 67 passés ; lint 0 erreur, 5 avertissements ; build OK. Suite Python non relancée : correctif limité à
    deux fichiers JavaScript de l'interface (3 437 passés sur l'état précédent).

### 19/11/2026 — revue experte (passage 2), contrôle qualité et clôture

- Expert (empreinte `46e0b12a`) : **APPROVED**. Bornage recalculé (96,3' sur 1346 px : barre de 2,846 px finissant à
  L·w ; 96,02' : 1 px recalé, sans chevauchement ; aucun effet pendant le jeu). A1 [facultatif] la dernière barre bornée
  touche le curseur, sans l'espace de 1 px des autres (esthétique, non corrigé).
- Contrôle qualité : **VALIDÉ** (remarque : fluidité mesurée avant le correctif A1, sans effet plausible).
- **Décision de clôture** : VALIDÉ (journal, 19/11/2026).
- **Durée** : estimée 1 h 15 ; réelle environ 1 h 35 de travail effectif (analyse 15, développement 15, tests et mesures
  30, correctif A1 et 2e passage 20, clôture 15), écart + 27 % (sous 30 %) : correctif de la réserve A1 et cas de banc
  d'une fin en milieu de minute, non prévus. Temps machine hors total : deux builds de production et six passes de
  fluidité, suite complète (15 min 12), trois séries de mesures navigateur.
