# EM-06 — Bancs et bord de terrain (V) — 90 min (moyenne)

**Status:** livré (18/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : bancs compacts et cohérents avec le nouveau terrain (décision propriétaire en 4).
- **Problème** : zone de 7 m dessinée en gris, rustique, qui prend de la hauteur.
- **Résultat** : bancs resserrés à la ligne de touche (zone de 4,5 m proposée), sièges aux couleurs d'équipe, échauffement
  conservé (comportement et constantes `WARMING_UP`, `BENCH_GAP` inchangés).
- **Composants** : `Bench` (dans `PitchView2`). **Critères** : numéros lisibles ; échauffement dès la 2e période identique ;
  hauteur du dessin −6 % minimum ; **reporté d'EM-04 (décision du propriétaire du 18/11/2026)** : surface dessinée du
  terrain ≥ +30 % à 1280×720 par rapport à l'état d'avant EM-04 (820×505 px, `.scratch/v2-ecran-match/mesures/em04-avant.json`),
  mesurée par `.scratch/v2-ecran-match/mesures/em04-mesure.cjs` ; **reporté d'EM-05 (remarque A1 de l'expert, 18/11/2026)** :
  depuis la marge de 3 m, les remplaçants à l'échauffement (y jusqu'à W + 4,3 m, `V2Pitch.jsx`) sortent de la pelouse
  (W + 3 m) ; les ramener sur l'herbe ou redéfinir la zone des bancs, et corriger le commentaire « entre la ligne de
  touche et la piste » (plus de piste).
- **Tests** : captures x1 en 1re et 2e période ; build, lint.
- **Dépendances** : EM-05, EM-03. **Risques** : constantes validées le 04/11 (modifier la zone demande leur accord).

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 30 min |
| Tests (captures, mesures) | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **90 min** |

Confiance : moyenne. Temps machine hors total : suite complète, passes de mesure.

## Décisions du propriétaire (18/11/2026)

- Constantes, « Valider tel quel » : zone des bancs de 4,5 m sous la pelouse (12 m de sol avant), axe des bancs à W + 5,25 m, bas du dessin à W + 7,5 m ; banc au fond sombre, contour à la couleur de l'équipe (blanc avant) ; remplaçants à l'échauffement sur l'herbe, couloirs à W + 0,7 / 1,4 / 2,1 m (1,5 / 2,9 / 4,3 avant), rond de 0,75 m comme les assis (0,9 avant) ; `WARMING_UP`, `BENCH_GAP` et le va-et-vient inchangés.
- Critère reporté d'EM-04, « Retenir la mesure » : le +30 % à 1280×720 est hors d'atteinte avec les colonnes de 220 px et la marge de 3 m (terrain limité par la largeur, plafond ≈ +19,6 % pour le rectangle de jeu, même sans bancs) ; remplacé par « rectangle de jeu ≥ +18 % à 1280×720 par rapport à avant EM-04 », mesuré par `em05-mesure.cjs`.

## Critères d'acceptation (chiffrés avant le code)

- [x] C1 : hauteur du dessin −6 % minimum : 70,45 → 64,30 m (viewBox), −8,7 %.
- [x] C2 : rectangle de jeu à 1280×720 ≥ +18 % par rapport à avant EM-04. Référence calculée depuis `em04-avant.json` (dessin de 820×505 px pour un viewBox de 121 m de large et (W + 23)·cos 35° de haut) : 711,6 × 377,4 px, 268 550 px² ; après : 779×414 px, 322 308 px², **+20,0 %** (+4,3 % par rapport à EM-05). Autres tailles par rapport à EM-05 : 844×390 +20,0 %, 1366×768 +6,4 %, 1920×1080 +13,5 %, 1024×768 inchangé (limité par la largeur dès EM-05).
- [x] C3 : remplaçants à l'échauffement sur l'herbe : centres au sol à 68,7 / 69,4 / 70,1 m, rond de 0,75 m **à l'écran** (cercle projeté), soit un bord au sol à W + 2,1 + 0,75 / cos 35° = W + 3,02 m au plus pour le 3e, au ras du bas de la pelouse (W + 3 m ; dépassement de 0,013 m à l'écran, environ 0,1 px à 1280×720, invisible) ; avant : 69,5 / 70,9 / 72,3 m, rond de 0,9 m. Formulation corrigée après la remarque A1 de l'expert (premier texte : « W + 2,85 m », rayon écran ajouté à une coordonnée au sol).
- [x] C4 : échauffement dès la 2e période identique (logique `warmUpFromS` et `WARMING_UP` inchangées : aucun remplaçant qui s'échauffe à la 30e minute, trois par équipe à la 60e, avant comme après) ; numéros des sièges et de l'échauffement de même taille qu'avant (0,9 et 1 m), lisibles sur les captures.
- [x] C5 : 5 points de projection à 0 px aux 5 tailles ; aucun défilement de page ; `npm test` 18/18, build OK, lint 0 erreur (5 avertissements préexistants) ; deux passes de mesure identiques.

## Comments

- 18/11/2026, implémentation. `V2Pitch.jsx` : `BENCH_ZONE` 4,5 m, `BENCH_Y` et `FLOOR_BOTTOM` dérivés de `MARGIN` et `BENCH_ZONE`, contour du banc `style={{ stroke: color }}`, `WARM_LANES` et `SUB_R` pour l'échauffement, commentaire « entre la ligne de touche et la piste » corrigé (remarque A1 d'EM-05 traitée). Mesures : `.scratch/v2-ecran-match/mesures/em06-*` (captures hors dépôt, scratchpad de la session).
- 18/11/2026, passage 1, clôture : expert APPROVED (empreinte `1af061ef`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/06/cloture`).
  - A1 [facultatif] : erreur d'unités dans la preuve de C3 (rayon d'écran ajouté à une coordonnée au sol) ; texte de C3 corrigé (bord au sol W + 3,02 m, au ras de la pelouse, écart invisible). Code inchangé.
  - A2 [facultatif] : le remplaçant du couloir W + 0,7 m peut chevaucher d'environ 0,45 m à l'écran un joueur sur la ligne de touche côté bancs (joueur dessiné devant) ; à surveiller sur une touche en 2e période (x ≈ 16-29 m et 76-89 m).
  - QC, réserve non bloquante : lisibilité des numéros à confirmer à l'écran (captures envoyées au propriétaire ; tailles inchangées).
- **Durée réelle** : environ 40 min de travail effectif (analyse 10, développement 10, tests et mesures 15, intégration 5 hors clôture), contre 90 min estimées : − 56 %. Cause : changement de quelques constantes dans `Bench` ; outillage de mesure d'EM-05 repris tel quel ; plafond du +30 % calculé avant le code (une décision au lieu d'une itération) ; expert APPROVED et QC VALIDÉ au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : suite complète (13 min 47), passes de mesure.
