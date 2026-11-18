# EM-05 — Terrain : pelouse, marquages, suppression du cadre rouge (V) — 120 min (moyenne)

**Status:** livré (18/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

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

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 40 min |
| Tests (mesures, captures) | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **120 min** |

Confiance : moyenne. Au seuil indicatif, pas au-delà : pas de découpage. Temps machine hors total : suite complète, passes de mesure.

## Décisions du propriétaire (18/11/2026)

- Constantes, « Valider tel quel » : gazon `#24603A` / `#2A6B3F` (18 bandes) ; lignes blanches à 85 %, 1,5 px à l'écran (trait non mis à l'échelle, au lieu de 0,15 m) ; marge de pelouse de 3 m (6 m avant), piste rouge supprimée, sol sombre `#0E141B` ; bancs à leur place d'avant jusqu'à EM-06 ; vignette ≤ 8 % ; côté lointain 6 % plus sombre.
- Gazon et règle de couleurs d'EM-03, « Règle sur le nouveau gazon » : `PITCH_COLORS` (`ui/src/utils/teamColors.js`) prend les nouvelles teintes. Effet mesuré sur les 341 kits à secondaire (`.scratch/v2-ecran-match/mesures/em05-gazon-et-regle-de-couleurs.mjs`) : secondaire désormais refusée pour 5 (Real Madrid `#505050`, US Sassuolo `#202a21`, Derby County `#5d5b5b`, Argentine `#4c5964`, Malaisie `#3c3718`), désormais acceptée pour 10 (Cercle Brugge `#4dbb49`, Oud-Heverlee Leuven `#8aa694`, RAAL La Louvière `#26b77a`, Casa Pia AC `#94835e`, Moreirense FC `#969882`, Bulgarie `#8b8e83`, Cameroun `#b6bf5d`, Irlande du Nord `#95b7ac`, Italie `#999682`, Comores `#939f62`).
- C4, « Accepter +13,9 % » : le seuil de +15 % posé avant le code n'est pas atteint à 1280×720 (le terrain y devient limité par la hauteur, que consomme la bande des bancs, 12 m sous le gazon, ticket EM-06) ; seuil ramené à la mesure, le gain restant est dans EM-06.

## Critères d'acceptation (chiffrés avant le code ; C4 révisé par décision)

- [x] C1 : 5 points (coins (0, 0) et (105, 68), centre, deux points de penalty) projetés par `project` puis par la matrice d'écran du SVG, comparés aux marquages dessinés : écart 0 px aux 5 tailles, avant comme après (`project` inchangé).
- [x] C2 : plus aucune zone rouge (`#9c4a3c` absent du dessin) aux 5 tailles.
- [x] C3 : lignes de 1,5 px à l'écran à toutes les tailles (avant : 0,52 px à 844×390, 1,02 px à 1280×720).
- [x] C4 : rectangle de jeu (105 × 68 m) à 1280×720 : 715×379 → 763×405 px, +13,9 % (seuil révisé) ; +12,0 % à 844×390, +18,8 % à 1024×768, +12,0 % à 1366×768 et 1920×1080 ; aucun défilement de page.
- [x] C5 : `npm test` 18/18 (test du gazon adapté : il lit `PITCH_COLORS` au lieu d'une teinte écrite en dur) ; build OK ; lint 0 erreur, 5 avertissements préexistants.
- [x] Déterminisme : deux passes de mesure après identiques octet pour octet.

## Comments

- 18/11/2026, implémentation. `V2Pitch.jsx` : `MARGIN` 6 → 3 m, `TRACK` et la piste supprimés, sol `FLOOR`, dégradés `v2-depth` et `v2-vignette` posés sur la pelouse, lignes `LINE` en trait non mis à l'échelle ; bancs figés à leur place d'avant (`BENCH_Y = W + 11`, bas du dessin `FLOOR_BOTTOM = W + 15`) ; viewBox recadré (`-MARGIN`), coordonnées et `project` intacts. `teamColors.js` : `PITCH_COLORS` aux nouvelles teintes ; `teamColors.test.js` : le test « secondaire confondue avec le gazon » lit la constante. `index.css` inchangé. Mesures : `.scratch/v2-ecran-match/mesures/em05-*` (trace `em04`, minute 30, en pause).
- 18/11/2026, passage 1, clôture : expert APPROVED (empreinte `038de516`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/05/cloture`).
  - A1 [facultatif] : en 2e période, les remplaçants à l'échauffement (y jusqu'à W + 4,3 m) débordent de la pelouse réduite (W + 3 m) sur le sol sombre ; commentaire « entre la ligne de touche et la piste » périmé. Reporté à EM-06 (noté dans son ticket).
  - A2 [facultatif] : vignette et dégradé se cumulent jusqu'à environ 13,5 % au coin lointain ; à surveiller sur téléphone.
  - A3 [facultatif] : C1 est vrai par construction (`project` inchangé) ; un test node de `project` sur 5 points rendrait l'invariant vérifiable dans le dépôt.
  - QC, réserve non bloquante : rendu visuel à confirmer à l'écran (captures envoyées au propriétaire).
- **Durée réelle** : environ 55 min de travail effectif (analyse 15, développement 15, tests et mesures 20, intégration 5 hors clôture), contre 120 min estimées : − 54 %. Cause : dessin concentré dans `PitchGround` et quelques constantes ; outillage de mesure d'EM-04 repris ; le couplage gazon / règle de couleurs repéré et chiffré avant le code (une décision au lieu d'une reprise) ; expert APPROVED et QC VALIDÉ au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : suite complète (13 min 58), trois passes de mesure.
