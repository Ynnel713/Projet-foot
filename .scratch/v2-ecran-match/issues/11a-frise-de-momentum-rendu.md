# EM-11a — Frise de momentum : rendu (V) — 95 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Ticket parent : `11-momentum-histogramme-symetrique.md` (découpé en 11a rendu et 11b données). Chantier :
`.scratch/v2-ecran-match/spec.md` (§ 1.3, § « Momentum et timeline »). Suite : 11b (`momentum.js`, échelle fixe, minute
en cours limitée aux images vues, libellé « Pression territoriale »).

- **Problème** : frise de 72 px au plus mais dessinée en `viewBox` proportionnel, donc large d'environ 700 px seulement
  (environ 7 px par barre) au centre de la zone basse ; fonds teintés sur toute la durée, futur compris ; pas de repères
  de minutes ; pas de curseur de lecture ; trait de mi-temps posé au début réel de la 2e période dès le coup d'envoi
  (dévoile la durée du temps additionnel de la 1re période).
- **Dépendances** : EM-01 (mémoïsation), EM-03 (jetons `--team-*-ui`), EM-04 (zone basse de 110 px, frise de 72 px).

## Comments

### 19/11/2026 — estimation, constantes et critères validés par le propriétaire

- **Estimation** (travail effectif) : analyse 20 min, développement 35 min, tests et mesures 25 min, intégration et
  clôture 15 min, **total 1 h 35**, confiance moyenne. Temps machine hors total : enregistrement de trois traces,
  banc de fluidité, suite complète.
- **Écart à la spec signalé avant le code** : la spec prévoit une frise de 150 px ; la décision du 18/11/2026 (EM-04)
  plafonne la zone basse à 110 px et la frise à 72 px. Gardé : 72 px.
- **Données** (formule actuelle, 4 traces réelles : Francfort–Gladbach `em10a`, Lens–Brest, OM–OL, PSG–Le Havre
  10-0, enregistrées par `scripts/record_v2_trace.py` ; 409 minutes) : |valeur| par minute médiane 0,09, p90 0,44,
  p95 0,51, p99 0,71, max 0,80 (max théorique 1,15) ; durées de 99 à 105 minutes.
- **Constantes validées (« je valide 72 px, 105 minutes et l'échelle à 0,6 », 19/11/2026)** :
  - 11a : frise de 72 px (barres ±22 px, rangées de buts de 8 px au-dessus et en dessous, repères sur 12 px) ;
    pleine largeur de la zone basse, en px mesurés (pas de déformation) ; domaine fixe de 105 minutes (davantage
    seulement si le match dure plus) ; écart entre barres 2 px ; repères 0', 15', 30', 45', trait de mi-temps au début
    de la 2e période, 60', 75', 90' comptés depuis ce début, en 11 px gris ; zone future : ligne de base seule (fonds
    teintés retirés) ; curseur blanc de 1,5 px à l'instant lu, seul élément redessiné à chaque image ; ballons de but
    actuels conservés (EM-12) ;
  - 11b : échelle fixe 0,6 = pleine hauteur, écrêtée au-delà ; 1 px au moins pour une minute jouée ; minutes terminées
    seulement ; libellé « Pression territoriale ».
- **Critères d'acceptation 11a** : frise pleine largeur à 1024, 1366 et 1920 px, 72 px de haut ; aucune barre au-delà
  du curseur ; largeur et position d'une barre inchangées de la 10e minute à la fin ; repères 45' et 60' alignés sur la
  mi-temps de la trace (une fois atteinte) ; fluidité ≥ avant (médiane d'image, temps de script, banc d'EM-01) ;
  `npm test`, lint 0 erreur, build OK ; suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** :
  - `ui/src/utils/momentumLayout.js` (nouveau, sans import, testé sous node) : constantes de la frise,
    `domainMinutes`, `minuteX`, `barBox` (écart de 2 px, 1 px au moins), `ticks(secondHalfStart, halfReached)` ;
  - `components/match/MomentumTimeline.jsx` (nouveau, remplace `Momentum.jsx`, supprimé) : largeur lue par
    ResizeObserver, SVG en px ; partie fixe `Bars` mémoïsée (barres, axe, repères, trait de mi-temps, buts), redessinée
    au changement de minute, de but, de largeur ou à la mi-temps ; curseur hors mémo. Formule et échelle verticale
    automatique inchangées (11b) ;
  - `MatchScreen.jsx` : appelle `MomentumTimeline` avec l'instant lu (`shownMin`) ; frise en hauteur fixe (`shrink-0`) au
    lieu de se contracter.
  - Repères de 2e période : tant que la lecture n'a pas atteint le début de la 2e période, ils sont posés comme si elle
    commençait à 45' et le trait de mi-temps n'est pas dessiné (avant : trait au début réel dès le coup d'envoi).
- **Tests** : `utils/momentumLayout.test.js` (7 tests : hauteurs, domaine de 105 minutes, barre identique de la 10e
  minute à la fin, écart et largeur minimale, abscisse, repères avant et après la mi-temps, début de 2e période inconnu),
  ajouté au script `npm test`.
- **Mesures** (`mesures/em11a-mesure.cjs`, Playwright, serveur de développement, trace réelle `em11-om-ol` : 2e période
  à 52', fin à 104' ; résultats `em11a-apres.json`, captures `em11a/`) :
  - frise 1346 × 72 px à 1366×768 (zone basse intérieure 1346 px), 1004 × 72 à 1024×768, 1900 × 72 à 1920×1080 ;
    12,8 px par minute à 1366 (9,6 à 1024, 18,1 à 1920) ; masquée à 844×390 (règle d'EM-04) ;
  - aucune barre au-delà du curseur aux 8 cas ; barres 5 et 20 à la même position et de même largeur (x 65,1 et
    257,4 px, largeur 10,8 px) à 10', 30', 51,5', 60' et 103,9' ; leur hauteur varie encore (échelle automatique, 11b) ;
  - repères à 51,5' : 60' à 769,1 px (provisoire, sans trait) ; à 60' : trait de mi-temps à 666,6 px (= 52 × 12,82),
    60' à 858,9 px (= 67 × 12,82) ; défilement de la zone basse 0, aucun défilement de page.
- **Fluidité** (`mesures/em11a-fluidite.txt`, banc d'EM-01, build de production avant (b0c7490) et après, trace
  `em11-om-ol`, ×8, 3 passes alternées de 15 s ; harnais copié avec le bouton « ×8 » d'EM-09) : médiane d'image 16,7 ms
  des deux côtés ; script 1,010 → 1,030 ms par image (+2,0 %) ; 319 → 324 nœuds SVG.
- **Vérifications** : suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (14 min 51, attendu inchangé) ; `npm test` 58 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ; build OK.
- **Déterminisme** : rendu seul, aucun aléa ni horloge ajoutés.
- **À vérifier à l'écran** : barres presque invisibles des minutes neutres (seuil de 1 px en 11b) ; contraste des repères gris ;
  saut des repères 60', 75', 90' à l'arrivée de la 2e période (de 7 minutes sur OM–OL).
- **Durée** : estimée 1 h 35 ; réelle environ 1 h 30 de travail effectif (analyse 25, développement 25, tests et mesures
  25, intégration et clôture 15), écart − 5 %. Temps machine hors total : trois traces enregistrées (environ 9 min en
  parallèle), deux builds de production et six passes de fluidité de 15 s, suite complète (14 min 51).

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `bc6870d2`) : **APPROVED_WITH_RESERVATIONS**. Géométrie recalculée (52 → 666,6 px, 67 → 858,9 px,
  barre 5 à 65,10 px sur 10,82 px).
  - A1 [réserve] la barre de la minute en cours (`played = ceil`) s'affiche entière alors que le curseur est en cours de
    minute (6,2 px au-delà à 51,5', jusqu'à environ 11 px à 1366) et moyenne des images pas encore vues ; le banc ne
    vérifiait que le début de la barre. Comportement antérieur à 11a.
  - A2 [facultatif] image maximale à 33,3 ms dans 2 passes « après » sur 3 (médiane et p95 inchangés).
- Contrôle qualité : **VALIDÉ**.
- **Réserve acceptée par le propriétaire** : « j'accepte A1, correctif en 11b » (19/11/2026). Correctif en 11b :
  minutes terminées seulement (constante déjà validée), et critère du banc sur la fin de barre (`x + width ≤ curseur`).
- **Décision de clôture** : VALIDÉ.

