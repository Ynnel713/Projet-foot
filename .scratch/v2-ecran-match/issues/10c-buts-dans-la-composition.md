# EM-10c — Buts dans la composition (V) — 50 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md`. Demande du propriétaire (19/11/2026) : « Dans la compo un logo à côté du
nom doit dire s'il a marqué, passe décisive, carton jaune, rouge, ou remplacé ou entrant ». Suite d'EM-10a / EM-10b.

- **Données disponibles** : buts seulement (`trace.goals[]`, `scorer`, `own_goal`). Passe décisive : absente de la trace
  (`v2-mise-en-scene/01`) ; cartons : non produits par le moteur V2 (`v2-attributs-restants/09a`) ; remplacements : non
  produits (`v2-coach-et-gestion-de-match/05a`).
- **Décisions du propriétaire** (19/11/2026) : passe décisive « Attendre le moteur » ; cartons et remplacements
  « Seulement but et passe » (rien de préparé). Ce ticket livre donc l'icône de but ; la passe s'ajoutera avec le passeur.
- **Dépendances** : EM-10a, EM-10b, EM-08c (mêmes buts révélés).

## Comments

### 19/11/2026 — estimation, choix et critères

- **Estimation** (travail effectif) : analyse 10 min, développement 15 min, tests et mesures 15 min, clôture 10 min,
  **total 50 min**, confiance moyenne. Temps machine hors total : suite complète, mesures navigateur.
- **Choix de forme (à confirmer à l'écran)** : ballon SVG de 12 px (blanc, pentagone sombre) après le nom, côté
  intérieur (miroir pour l'extérieur) ; « ×n » au-delà d'un but ; but contre son camp : même ballon en rouge, sur la carte
  du joueur qui l'a marqué ; info-bulle et texte pour lecteur d'écran (« 2 buts », « but contre son camp ») ; pas d'emoji
  (spec : « plus d'emoji »).
- **Critères d'acceptation** : icône seulement pour les buts déjà révélés (même règle que le score) ; nombre affiché =
  buts du joueur ; aucune icône sans but ; aucun défilement de colonne ajouté ; nom tronqué au besoin, icône toujours
  entière ; `npm test`, lint 0 erreur, build OK ; suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** : `utils/lineupCards.js` `goalsByPlayer(goals)` (buts et csc par nom, buteur inconnu ignoré) ;
  `LineupPanel.jsx` `BallIcon`, `GoalMarks`, prop `stats` jusqu'à `PlayerCard` ; `MatchScreen.jsx` calcule
  `playerGoals` une fois par but révélé (`useMemo` sur le nombre de buts révélés, comme les buteurs du HUD) et le passe aux
  colonnes et aux tiroirs.
- **Tests** : `utils/lineupCards.test.js` + 1 test (buts, csc, buteur inconnu, liste vide) ; `npm test` 72 passés.
- **Mesures** (`mesures/em10c-mesure.cjs`, traces réelles `em11-om-ol` et `em11-psg-havre`, résultats `em10c-apres.json`,
  captures `em10c/`, 9 cas) :
  - révélation : aucune icône à 1' ; Openda (but) à 2,05' ; à 10' Gouiri 1, Openda ×2 ; à 104' Gouiri ×4, Abdelli,
    Paixão, Openda ×3 (= buteurs de la trace) ; PSG 10-0 : Kvaratskhelia ×5, Dembélé ×3, Doué, Neves ;
  - défilement des colonnes : 0 px aux 9 cas ; noms tronqués à 1366 px pour Dembélé et Kvaratskhelia (icône entière).
- **Effet d'EM-08c relevé ici** (non modifié dans ce ticket) : le HUD grandit avec les buteurs, la colonne des
  compositions rétrécit et sa densité (EM-10b) change en cours de match : 1366×768 complet (570 px) → compact au 1er but
  (556 px, 527 px à 3 lignes) ; 1280×720 compact (522 px) → serré (479 px) ; 1920×1080 reste complet (882 → 839 px).
  Décision du propriétaire (19/11/2026) : « On garde comme ça ».
- **Vérifications** : lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 437 passés, 0 ignoré, 14 désélectionnés.
- **Déterminisme** : affichage seul.
- **À vérifier à l'écran** : lisibilité du ballon de 12 px, ballon rouge du csc (aucun csc dans les traces mesurées : vu
  en test seulement).

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `390f1e62`) : **APPROVED**. A1 [facultatif] buts indexés par nom seul : deux homonymes dans les deux
  équipes partageraient leurs icônes (improbable ; la clé `p.name` suppose déjà des noms uniques).
- Contrôle qualité : **VALIDÉ** (même remarque, non bloquante).
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 50 min ; réelle environ 45 min de travail effectif (analyse 10, développement 15, tests et mesures
  15, clôture 5), écart − 10 %. Temps machine hors total : mesures navigateur, suite complète (14 min 52).
- 26/11/2026 (audit du mode « moments clés ») : `v2-mise-en-scene/01` est découpé et le moteur n'écrit plus le passeur dans la trace. Le passeur est déduit du journal côté serveur et servi par l'API au ticket `v2-mise-en-scene/01e` ; c'est là qu'il faut le lire. La passe décisive dans la composition reste à afficher après 01e.
